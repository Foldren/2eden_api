from datetime import datetime
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from pytz import timezone
from starlette import status
from tortoise.exceptions import DoesNotExist
from components.enums import ConditionType
from components.responses import CustomJSONResponse
from components.tools import check_task_visibility, validate_telegram_hash
from models import User, Task, VisitLinkCondition, TgChannelCondition, UserTask

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(path="/available", description="Метод для получения списка доступных задач.")
@cache(expire=30)
async def get_tasks(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Метод для получения списка доступных задач.
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("rank").first()

    # фильтрация по условию доступности
    all_tasks = await Task.all()
    filtered_tasks = [task for task in all_tasks if check_task_visibility(task, user)]
    # по выполненным задачам не фильтруем
    # todo: выводить более полезную информацию о задачах, а не просто айдишники
    return CustomJSONResponse(data={"tasks": filtered_tasks})


@router.post(path="/start/{task_id}", description="Метод для начала Таска. Создает для пользователя задачу для выполнения.")
async def take_task(task_id: int, init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]):
    """
    Метод для начала Таска. Создает для пользователя задачу для выполнения.
    :param task_id: id задачи
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("rank", "activity").first()

    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        return CustomJSONResponse(message="Такой задачи не существует.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    if not check_task_visibility(task, user):
        return CustomJSONResponse(message="Задача недоступна.",
                                  status_code=status.HTTP_423_LOCKED)

    user_task, created = await UserTask.get_or_create(user=user, task=task)
    if not created:
        return CustomJSONResponse(message="Задача уже взята.",
                                  status_code=status.HTTP_409_CONFLICT)

    return CustomJSONResponse(message="Задача взята.",
                              data={"task": task},
                              status_code=status.HTTP_201_CREATED)


@router.post(path="/complete/{task_id}", description="Метод для завершения задачи. Отмечает задачу как выполненную.")
async def complete_task(task_id: int, init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]):
    """
    Метод для завершения задачи. Отмечает задачу как выполненную.
    :param task_id: id задачи
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("rank", "activity", "stats").first()

    try:
        user_task = await UserTask.get(user=user, task_id=task_id).select_related("task__condition", "task__reward")
    except DoesNotExist:
        return CustomJSONResponse(message="Задача пользователя не найдена.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    if user_task.is_completed:
        return CustomJSONResponse(message="Задача уже завершена.",
                                  status_code=status.HTTP_409_CONFLICT)

    task = user_task.task
    condition = task.condition

    if condition.type == ConditionType.VISIT_LINK:
        # Проверять условие посещения не нужно, т.к. это происходит на фронте
        reach_condition = await VisitLinkCondition.get(condition=condition)
        pass
    elif condition.type == ConditionType.TG_CHANNEL:
        tg_condition = await TgChannelCondition.get(condition=condition)
        # todo: проверка подписки на канал
        return CustomJSONResponse(message="Not implemented yet.",
                                  status_code=status.HTTP_409_CONFLICT)

    # Установка флага выполнения задания
    user_task.completed_time = datetime.now(tz=timezone("Europe/Moscow"))
    # Начисление награды
    user.stats.coins += task.reward.tokens
    user.stats.inspirations += task.reward.inspirations
    user.stats.replenishments += task.reward.replenishments
    # Сохранение
    await user_task.save()
    await user.stats.save()

    return CustomJSONResponse(message="Задача завершена.",
                              data={"task": task, "reward": task.reward},
                              status_code=status.HTTP_202_ACCEPTED)
