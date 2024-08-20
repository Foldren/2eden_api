from datetime import datetime, timedelta
from enum import Enum
from typing import Union

from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials as JwtAuth
from pydantic import BaseModel, Field
from pytz import timezone
from config import ACCESS_SECURITY
from db_models.api import User, Task, VisitLinkCondition, TgChannelCondition, UserTask, UserQuestion, UserAnswer

WAITING_STATUS_MESSAGE = "I need some time to think about your question. Please wait a little bit."
AVAILABLE_STATUS_MESSAGE = "You can ask me a question."
UNAVAILABLE_STATUS_MESSAGE = "You can't ask me a question right now."
NOT_VALID_QUESTION_MESSAGE = "No, I can't answer this question, try to rephrase it or ask another one."
MAX_QUESTIONS_PER_DAY = 3


# todo: перенести схемы в отдельный файл
class QuestionType(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    WAITING = "WAITING"
    READY = "READY"


class AvailableStatusResponse(BaseModel):
    status: QuestionType = Field(QuestionType.AVAILABLE, const=True)
    message: str = Field(AVAILABLE_STATUS_MESSAGE, const=True)


class UnavailableStatusResponse(BaseModel):
    status: QuestionType = Field(QuestionType.UNAVAILABLE, const=True)
    message: str = Field(UNAVAILABLE_STATUS_MESSAGE, const=True)
    next_available: datetime


class WaitingStatusResponse(BaseModel):
    status: QuestionType = Field(QuestionType.WAITING, const=True)
    message: str = Field(WAITING_STATUS_MESSAGE, const=True)
    waiting_time: int  # в минутах


class ReadyStatusResponse(BaseModel):
    status: QuestionType = Field(QuestionType.READY, const=True)
    message: str  # сообщение может быть динамическим в зависимости от ответа
    inspiration_reward: bool  # можно ли получить награду "вдохновение"
    rebirth_reward: bool  # можно ли получить награду "пополнение"


QuestionStatusResponse = Union[
    AvailableStatusResponse,
    UnavailableStatusResponse,
    WaitingStatusResponse,
    ReadyStatusResponse
]

router = APIRouter(prefix="/questions", tags=["Questions"])


class Question(BaseModel):
    question: str
    answer: str
    is_secret: bool
    time: datetime


class QuestionsHistoryResponse(BaseModel):
    questions: list[Question]


async def calculate_question_status(user) -> QuestionStatusResponse:
    user_last_question = await user.questions.all().order_by("-id").first().select_related("answer")
    answer = user_last_question.answer if user_last_question.answer else None

    # если вопросов не было, то можно задать вопрос
    if not user_last_question:
        return AvailableStatusResponse()

    # если ответа на вопрос еще нет, то статус ожидания
    if not answer:
        # todo: высчитывать среднее время ожидания ответа
        return WaitingStatusResponse(
            waiting_time=10  # Пример среднего времени ожидания ответа в минутах
        )

    # если ответ на вопрос уже есть, но награда не получена, то статус готовности ответа
    if not answer.rewarded:
        return ReadyStatusResponse(
            message=user_last_question.answer.text,
            inspiration_reward=answer.base_reward,
            rebirth_reward=answer.secret_reward
        )
    # иначе, прошлый вопрос уже полностью обработан и нужно проверить, можно ли задать новый вопрос
    # todo: проверить, правильно ли считаются лимиты
    user_questions_today = await user.questions.filter(
        create_time__gte=datetime.now(timezone("Europe/Moscow")).replace(hour=0, minute=0, second=0)).count()
    if user_questions_today >= MAX_QUESTIONS_PER_DAY:
        next_available_time = datetime.now(timezone("Europe/Moscow")).replace(hour=0, minute=0, second=0) + timedelta(
            days=1)
        return UnavailableStatusResponse(
            next_available=next_available_time
        )

    return AvailableStatusResponse()


# todo: Структура ответа
@router.post("/ask")
async def create_question(question: str, credentials: JwtAuth = Security(ACCESS_SECURITY)) -> QuestionStatusResponse:
    """
    Создание нового вопроса пользователем.
    :param question: текст вопроса
    :param credentials: authorization headers
    :return: status
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank").first()

    # проверяем текущий статус вопроса
    question_status = await calculate_question_status(user)
    if question_status.status != QuestionType.AVAILABLE:
        return question_status

    # todo: добавить моментальные проверки на валидность вопроса
    question_valid = True
    if not question_valid:
        return ReadyStatusResponse(
            message=NOT_VALID_QUESTION_MESSAGE,
            inspiration_reward=False,
            rebirth_reward=False,
        )

    # todo: создание задачи длинной проверки вопроса

    return WaitingStatusResponse(waiting_time=10)


# todo: задача на проверку потерянных вопросов
@router.get("/status")
async def status(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> QuestionStatusResponse:
    """
    Проверка статуса вопроса пользователя.
    :param credentials: authorization headers
    :return: status
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "activity").first()

    return await calculate_question_status(user)


@router.post("/accept_reward/")
async def accept_reward(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> QuestionStatusResponse:
    """
    Метод для получения награды за вопрос к ИИ.
    :param credentials: authorization headers
    :param task_id: id задачи
    :return: status
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats").first()

    user_last_question = await user.questions.all().order_by("-id").first().select_related("answer")

    # проверка на то, что статус вопроса READY (вопрос есть, ответ есть, награда не получена)
    current_status = await calculate_question_status(user)
    if current_status.status != QuestionType.READY:
        # todo: решить, что возвращать в случае, если награда не доступна по логике
        return current_status

    # начисление награды
    if user_last_question.answer.base_reward:
        user.stats.inspirations += 1
    if user_last_question.answer.secret_reward:
        user.stats.replenishments += 1
    user_last_question.answer.rewarded = True
    # todo: обработка ошибок при сохранении
    await user.stats.save()
    await user_last_question.answer.save()

    return await calculate_question_status(user)


@router.post("/history/")
async def get_history(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> QuestionsHistoryResponse:
    user_id = credentials.subject.get("id")
    user = await User.filter(id=user_id).prefetch_related("questions__answer").first()

    questions = [
        Question(
            question=q.text,
            answer=q.answer.text if q.answer else None,
            is_secret=q.answer.secret_reward if q.answer else False,
            time=q.created
        )
        for q in user.questions
    ]
    return QuestionsHistoryResponse(questions=questions)
