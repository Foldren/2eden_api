from datetime import datetime
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from deep_translator import GoogleTranslator
from fastapi import APIRouter, Depends
from pytz import timezone
from starlette import status
from tortoise.expressions import F
from tortoise.functions import Sum
from components.enums import QuestionStatus, RewardTypeName
from components.responses import CustomJSONResponse
from components.tools import validate_telegram_hash, ai_msg_base_check
from models import Question, Stats, Reward

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/ask")
async def ask_question(question: str,
                       init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Создание нового вопроса для AI.
    @param question: текст вопроса
    @param init_data: данные юзера telegram
    @return:
    """
    user_id = init_data.user.id  # узнаем id юзера из Telegram-IniData
    last_question = await Question.filter(user_id=user_id).order_by("-id").first()

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
    if last_question.date_sent == datetime.now(tz=timezone("Europe/Moscow")).date():
        return CustomJSONResponse(
            message="Сегодня я не могу ответить на еще один твой вопрос, сын мой, приходи завтра.",
            status_code=status.HTTP_208_ALREADY_REPORTED)

    # Переводим текст на английский
    transl_question = GoogleTranslator(source='auto', target='en').translate(question)

    # Проводим базовые проверки
    try:
        await ai_msg_base_check(transl_question)
    except Exception as e:
        return CustomJSONResponse(message=str(e), status_code=status.HTTP_406_NOT_ACCEPTABLE)

    # Если вс окэй
    await Question.create(user_id=user_id)

    return CustomJSONResponse(message="Я пошел думать над твоим вопросом.")


@router.get("/status")
async def get_status(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Проверка статуса вопроса к AI.
    @param init_data: данные юзера telegram
    @return:
    """
    user_id = init_data.user.id  # узнаем id юзера из Telegram-IniData
    last_question = await Question.filter(user_id=user_id).order_by("-id").first()

    if last_question.status == QuestionStatus.HAVE_ANSWER:
    #todo

    return CustomJSONResponse(message="Выведен статус последнего вопроса.",
                              data={"status": last_question.status, "reward_id": reward_id})


@router.get("/history")
async def get_history(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Метод для получения диалога с AI.
    @param init_data: данные юзера telegram
    @return:
    """
    user_id = init_data.user.id  # узнаем id юзера из Telegram-IniData
    questions = await Question.filter(user_id=user_id).values("id", "date_sent", "text", "answer")

    if not questions:
        return CustomJSONResponse(message="Пока не задано ниодного вопроса.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    return CustomJSONResponse(message="Выведены вопросы пользователя.", data={"questions": questions})
