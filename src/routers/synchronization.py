from datetime import timedelta, datetime
from math import floor
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from pytz import timezone
from starlette import status
from components.requests import SyncClicksRequest
from components.responses import CustomJSONResponse
from components.tools import sync_energy, validate_telegram_hash, get_daily_reward
from models import User, User_Pydantic

router = APIRouter(prefix="/user", tags=["User"])


@router.patch(path="/sync_clicks", description="Эндпойнт синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у пользователя и дневными ограничениями.")
async def sync_clicks(req: SyncClicksRequest, init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у
    пользователя и дневными ограничениями.
    :param req: request объект с кол-вом кликов SyncClicksRequest
    :param init_data: данные юзера telegram
    :return:
    """

    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("rank", "stats", "activity", "rewards").first()

    await get_daily_reward(user)  # получаем ежедневную награду за вход
    await sync_energy(user)  # синхронизируем энергию

    if user.stats.energy < user.rank.press_force:
        return CustomJSONResponse(message="Не хватает энергии.",
                                  status_code=status.HTTP_409_CONFLICT)

    extraction = req.clicks * user.rank.press_force

    if extraction > user.stats.energy:  # Обрезаем энергию под количество доступных кликов ^^
        extraction = floor(user.stats.energy / user.rank.press_force) * user.rank.press_force

    user.stats.coins += extraction
    user.stats.energy -= extraction
    user.stats.earned_week_coins += extraction

    await user.stats.save()

    return CustomJSONResponse(message="Синхронизация завершена.")


@router.patch(path="/bonus/sync_inspiration_clicks", description="Эндпойнт синхронизации кликов под бустером - вдохновение. Сколько бы кликов не отправили, все обрезается по формуле user.rank.max_energy * 1.2.")
async def sync_inspiration_clicks(req: SyncClicksRequest,
                                  init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт синхронизации кликов под бустером - вдохновение. Сколько бы кликов не отправили,
    все обрезается по формуле user.rank.max_energy * 1.2.
    :param req: request объект с кол-вом кликов SyncClicksRequest
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("activity", "stats", "rank").first()
    max_extraction = int(user.rank.max_energy * 1.2)  # максимум можно заработать max_energy + 20%

    if user.rank.id < 2:
        return CustomJSONResponse(message="Маловат ранг.", #todo ошибка
                                  status_code=status.HTTP_409_CONFLICT)

    if user.stats.inspirations == 0:
        return CustomJSONResponse(message="На счету кончились бустеры вдохновения.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.activity.next_inspiration > datetime.now(tz=timezone("Europe/Moscow")):
        return CustomJSONResponse(message="Вдохновение уже активно, дождитесь завершения.",
                                  status_code=status.HTTP_409_CONFLICT)

    extraction = req.clicks * (user.rank.press_force * 3)

    if extraction > max_extraction:
        extraction = max_extraction

    user.activity.next_inspiration = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(seconds=15)
    await user.activity.save()

    user.stats.inspirations -= 1
    user.stats.coins += extraction
    user.stats.earned_week_coins += extraction
    await user.stats.save()

    return CustomJSONResponse(message="Вдохновение активировано.")


@router.post(path="/bonus/replenishment", description="Эндпойнт на использование бустера - прилива, полностью востанавливает энергию игрока.")
async def use_replenishment(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на использование бустера - прилива, полностью востанавливает энергию игрока.
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("activity", "stats", "rank").first()

    if user.rank.id < 3:
        return CustomJSONResponse(message="Маловат ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.stats.replenishments == 0:
        return CustomJSONResponse(message="На счету кончились бустеры прилива.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.stats.energy >= user.rank.max_energy:
        return CustomJSONResponse(message="У вас максимум энергии.",
                                  status_code=status.HTTP_409_CONFLICT)

    user.stats.energy = user.rank.max_energy
    user.stats.replenishments -= 1
    await user.stats.save()

    return CustomJSONResponse(message="Прилив энергии активирован.")


@router.get(path="/profile", description="Эндпойнт на получение данных игрока.")
@cache(expire=30)
async def get_user_profile(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на получение данных игрока.
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data

    user = await User.filter(id=user_chat_id).prefetch_related("activity", "stats", "rank", "leads",
                                                        "rewards", "leader_place").first()
    await get_daily_reward(user)  # получаем ежедневную награду за вход
    await sync_energy(user)  # синхронизируем энергию

    from_orm = await User_Pydantic.from_tortoise_orm(user)
    user_dump = from_orm.model_dump(mode='json')  # Мод как решение проблемы с сериализацией даты

    return CustomJSONResponse(data=user_dump, message="Выведены данные профиля.")


