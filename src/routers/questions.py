from datetime import datetime
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from deep_translator import GoogleTranslator
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from pytz import timezone
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import validate_telegram_hash, ai_msg_base_check
from models import Question, Reward, Questions_Pydantic_List, RewardType, QuestionStatus

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post(path="/ask", description="Эндпойнт для создания нового вопроса для AI.")
async def ask_question(question: str,
                       init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт для создания нового вопроса для AI.
    @param question: текст вопроса
    @param init_data: данные юзера telegram
    @return:
    """
    user_id = init_data.user.id  # узнаем id юзера из Telegram-IniData
    last_question = await Question.filter(user_id=user_id).order_by("-id").first()

    if last_question is not None:
        # Проверка на статус
        if last_question.status == QuestionStatus.IN_PROGRESS:
            return CustomJSONResponse(
                message="Я еще думаю.",
                status_code=status.HTTP_208_ALREADY_REPORTED)

        elif last_question.status == QuestionStatus.HAVE_ANSWER:
            return CustomJSONResponse(
                message="Сперва забери награду.",
                status_code=status.HTTP_409_CONFLICT)

        # Проверка на ограничение сообщения раз в день
        # if last_question.time_sent.date() == datetime.now(tz=timezone("Europe/Moscow")).date():
        #     return CustomJSONResponse(
        #         message="Сегодня я не могу ответить на еще один твой вопрос, сын мой, приходи завтра.",
        #         status_code=status.HTTP_208_ALREADY_REPORTED)

    # Переводим текст на английский
    transl_question = GoogleTranslator(source='auto', target='en').translate(question)

    # Проводим базовые проверки
    try:
        await ai_msg_base_check(transl_question)
    except Exception as e:
        return CustomJSONResponse(message=str(e), status_code=status.HTTP_406_NOT_ACCEPTABLE)

    # Если вс окэй
    await Question.create(user_id=user_id, text=transl_question, u_text=question)

    return CustomJSONResponse(message="Я пошел думать над твоим вопросом.")


@router.get(path="/status", description="Эндпойнт на проверку статуса вопроса к AI.")
@cache(expire=30)
async def get_status(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на проверку статуса вопроса к AI.
    @param init_data: данные юзера telegram
    @return:
    """
    user_id = init_data.user.id  # узнаем id юзера из Telegram-IniData
    last_question = await Question.filter(user_id=user_id).order_by("-id").first()
    resp_data = {"status": last_question.status}

    if not last_question:
        return CustomJSONResponse(message="Пользователь не задал ни одного вопроса.")

    if last_question.status == QuestionStatus.HAVE_ANSWER:
        qst_reward = await Reward.filter(user_id=user_id, type=RewardType.AI_QUESTION).order_by("-id").first()
        resp_data["reward_id"] = qst_reward.id

    return CustomJSONResponse(message="Выведен статус последнего вопроса.", data=resp_data)


@router.get(path="/history", description="Эндпойнт для получения истории диалога с AI.")
@cache(expire=10)
async def get_history(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт для получения истории диалога с AI.
    @param init_data: данные юзера telegram
    @return:
    """

    user_id = init_data.user.id  # узнаем id юзера из Telegram-IniData
    questions = await Questions_Pydantic_List.from_queryset(Question.filter(user_id=user_id))

    if not questions:
        return CustomJSONResponse(message="Пока не задано ниодного вопроса.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    return CustomJSONResponse(message="Выведены вопросы пользователя.",
                              data={"questions": questions.model_dump(mode="json")})
