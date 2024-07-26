from datetime import timedelta, datetime
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from pytz import timezone
from tortoise.exceptions import DoesNotExist
from tortoise.functions import Sum

from config import ACCESS_SECURITY
import models

from components.enums import VisibilityType, ConditionType

router = APIRouter()


async def check_task_visibility(task: models.Task, user: models.User):
    if task.visibility.type == VisibilityType.RANK:
        rank_visibility = await models.RankVisibility.get(visibility=task.visibility)
        return user.rank.league >= rank_visibility.rank.league
    elif task.visibility.type == VisibilityType.ALL:
        return True
    return False


@router.get("/tasks/available")
async def get_tasks(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод для получения списка доступных задач.
    :param credentials: authorization headers
    :return:
    """
    # фильтрация по условию доступности
    all_tasks = await models.Task.all()
    filtered_tasks = [task for task in all_tasks if check_task_visibility(task, credentials.subject)]
    # по выполненным задачам не фильтруем
    # todo: выводить более полезную информацию о задачах, а не просто айдишники
    return {"tasks": filtered_tasks}


@router.post("/tasks/start/{task_id}")
async def take_task(task_id: int, credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод для начала Таска. Создает для пользователя задачу для выполнения.
    :param credentials: authorization headers
    :param task_id: id задачи
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await models.User.filter(id=user_id).select_related("rank", "activity").first()

    try:
        task = await models.Task.get(id=task_id)
    except DoesNotExist:
        return {"message": "Такой задачи не существует."}

    if not check_task_visibility(task, user):
        return {"message": "Задача недоступна."}

    user_task, created = await models.UserTask.get_or_create(user=user, task=task)
    if not created:
        return {"message": "Задача уже взята."}

    return {"message": "Задача взята.", "data": {"task": task}}


@router.post("/tasks/complete/{task_id}")
async def complete_task(task_id: int, credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод для завершения задачи. Отмечает задачу как выполненную.
    :param credentials: authorization headers
    :param task_id: id задачи
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await models.User.filter(id=user_id).select_related("rank", "activity", "stats").first()

    try:
        user_task = await models.UserTask.get(user=user, task_id=task_id).select_related("task__condition", "task__reward")
    except DoesNotExist:
        return {"message": "Задача пользователя не найдена."}

    if user_task.is_completed:
        return {"message": "Задача уже завершена."}

    task = user_task.task
    condition = task.condition

    if condition.type == ConditionType.VISIT_LINK:
        # Проверять условие посещения не нужно, т.к. это происходит на фронте
        reach_condition = await models.VisitLinkCondition.get(condition=condition)
        pass
    elif condition.type == ConditionType.TG_CHANNEL:
        tg_condition = await models.TgChannelCondition.get(condition=condition)
        # todo: проверка подписки на канал
        return {"message": "Not implemented yet."}

    # Установка флага выполнения задания
    user_task.completed_time = datetime.now(tz=timezone("Europe/Moscow"))
    # Начисление награды
    user.stats.coins += task.reward.tokens
    user.stats.inspirations += task.reward.inspirations
    user.stats.replenishments += task.reward.replenishments
    # Сохранение
    await user_task.save()
    await user.stats.save()

    return {"message": "Задача завершена.", "data": {"task": task, "reward": task.reward}}
