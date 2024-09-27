from datetime import datetime
from typing import Annotated, List, Union
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from pytz import timezone
from starlette import status
from tortoise.exceptions import DoesNotExist
from components.responses import CustomJSONResponse
from components.tools import check_task_visibility, validate_telegram_hash
from models import User, Task, VisitLinkCondition, TgChannelCondition, UserTask, ConditionType

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class RewardResponse(BaseModel):
    coins: int
    inspirations: int
    replenishments: int

class VisitLinkConditionResponse(BaseModel):
    url: str

class TgChannelConditionResponse(BaseModel):
    channel_id: str

class TaskResponse(BaseModel):
    id: int
    description: str
    reward: RewardResponse
    condition: Union[VisitLinkConditionResponse, TgChannelConditionResponse]
    condition_type: ConditionType
    is_started: bool = False

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]

class UserStatsResponse(BaseModel):
    coins: int
    inspirations: int
    replenishments: int

class CompleteTaskResponse(BaseModel):
    task_id: int
    completion_time: str
    reward: RewardResponse
    user_stats: UserStatsResponse

class StartTaskResponse(BaseModel):
    task: TaskResponse

async def get_condition_response(task: Task) -> Union[VisitLinkConditionResponse, TgChannelConditionResponse]:
    """
    Преобразует условие задачи в соответствующий ответ API.
    :param task: объект задачи
    :return: объект ответа с условием задачи
    """
    if task.condition.type == ConditionType.VISIT_LINK:
        visit_link = await VisitLinkCondition.get(condition=task.condition)
        return VisitLinkConditionResponse(url=visit_link.url)
    elif task.condition.type == ConditionType.TG_CHANNEL:
        tg_channel = await TgChannelCondition.get(condition=task.condition)
        return TgChannelConditionResponse(channel_id=tg_channel.channel_id)
    else:
        raise ValueError(f"Неизвестный тип условия: {task.condition.type}")

@router.get("/", response_model=TaskListResponse)
@cache(expire=10)
async def get_tasks(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]):
    """
    Метод для получения списка доступных задач.
    :param init_data: данные юзера telegram
    :return:
    """
    user = await User.filter(id=init_data.user.id).select_related("rank").first()
    all_tasks = await Task.all().prefetch_related("reward", "condition")
    
    user_tasks = await UserTask.filter(user=user).all()
    started_task_ids = {ut.task_id for ut in user_tasks if not ut.is_completed}
    
    filtered_tasks = []
    for task in all_tasks:
        if await check_task_visibility(task, user):
            condition_data = await get_condition_response(task)
            
            task_response = TaskResponse(
                id=task.id,
                description=task.description,
                reward=RewardResponse(
                    coins=task.reward.tokens,
                    inspirations=task.reward.inspirations,
                    replenishments=task.reward.replenishments
                ),
                condition=condition_data,
                condition_type=task.condition.type,
                is_started=task.id in started_task_ids
            )
            filtered_tasks.append(task_response)
    
    return TaskListResponse(tasks=filtered_tasks)

@router.post("/{task_id}/start", response_model=StartTaskResponse)
async def start_task(task_id: int, init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]):
    """
    Метод для начала Таска. Создает для пользователя задачу для выполнения.
    :param task_id: id задачи
    :param init_data: данные юзера telegram
    :return:
    """
    user = await User.filter(id=init_data.user.id).select_related("rank").first()
    task = await Task.get_or_none(id=task_id).prefetch_related("reward", "condition")
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    if not await check_task_visibility(task, user):
        raise HTTPException(status_code=403, detail="Задача недоступна")
    
    user_task, created = await UserTask.get_or_create(user=user, task=task)
    if not created:
        raise HTTPException(status_code=400, detail="Задача уже взята")
    
    condition_data = await get_condition_response(task)
    
    task_response = TaskResponse(
        id=task.id,
        description=task.description,
        reward=RewardResponse(
            coins=task.reward.tokens,
            inspirations=task.reward.inspirations,
            replenishments=task.reward.replenishments
        ),
        condition=condition_data,
        condition_type=task.condition.type,
        is_started=True
    )
    
    return StartTaskResponse(task=task_response)

@router.post("/{task_id}/complete", response_model=CompleteTaskResponse)
async def complete_task(task_id: int, init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]):
    """
    Метод для завершения задачи. Отмечает задачу как выполненную и начисляет награду.
    :param task_id: id задачи
    :param init_data: данные юзера telegram
    :return:
    """
    user = await User.filter(id=init_data.user.id).select_related("rank", "stats").first()
    user_task = await UserTask.get_or_none(user=user, task_id=task_id).select_related("task__condition", "task__reward")
    
    if not user_task:
        raise HTTPException(status_code=404, detail="Задача не найдена или не взята")
    if user_task.is_completed:
        raise HTTPException(status_code=400, detail="Задача уже завершена")

    task = user_task.task
    
    if task.condition.type == ConditionType.TG_CHANNEL:
        # TODO: Реализовать проверку подписки на канал
        raise HTTPException(status_code=501, detail="Проверка подписки на канал пока не реализована")

    # Отмечаем задачу как выполненную
    user_task.completed_time = datetime.now(tz=timezone("Europe/Moscow"))
    await user_task.save()

    # Начисляем награду
    user.stats.coins += task.reward.tokens
    user.stats.inspirations += task.reward.inspirations
    user.stats.replenishments += task.reward.replenishments
    await user.stats.save()

    response_data = CompleteTaskResponse(
        task_id=task.id,
        completion_time=user_task.completed_time.isoformat(),
        reward=RewardResponse(
            coins=task.reward.tokens,
            inspirations=task.reward.inspirations,
            replenishments=task.reward.replenishments
        ),
        user_stats=UserStatsResponse(
            coins=user.stats.coins,
            inspirations=user.stats.inspirations,
            replenishments=user.stats.replenishments
        )
    )

    return response_data
