from datetime import datetime, timedelta
from math import floor
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends
from pytz import timezone
from starlette import status
from components.requests import SyncClicksRequest
from components.responses import CustomJSONResponse
from components.tools import validate_telegram_hash, get_daily_reward, sync_energy
from models import User

router = APIRouter(prefix="/game_actions", tags=["Game Actions"])


@router.patch(path="/sync_clicks", description="Эндпойнт синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у пользователя и дневными ограничениями.")
async def sync_clicks(req: SyncClicksRequest,
                      init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у
    пользователя и дневными ограничениями.
    @param req: request объект с кол-вом кликов SyncClicksRequest
    @param init_data: данные юзера telegram
    @return:
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


@router.patch(path="/sync_inspiration", description="Эндпойнт синхронизации кликов под бустером - вдохновение. Сколько бы кликов не отправили, все обрезается по формуле user.rank.max_energy * 1.2.")
async def sync_inspiration(req: SyncClicksRequest,
                           init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт синхронизации кликов под бустером - вдохновение. Сколько бы кликов не отправили,
    все обрезается по формуле user.rank.max_energy * 1.2.
    @param req: request объект с кол-вом кликов SyncClicksRequest
    @param init_data: данные юзера telegram
    @return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("activity", "stats", "rank").first()
    max_extraction = int(user.rank.max_energy * 1.2)  # максимум можно заработать max_energy + 20%

    if user.rank.id < 2:
        return CustomJSONResponse(message="Маловат ранг.",
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


@router.post(path="/use_replenishment", description="Эндпойнт на использование бустера - прилива, полностью востанавливает энергию игрока.")
async def use_replenishment(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на использование бустера - прилива, полностью востанавливает энергию игрока.
    @param init_data: данные юзера telegram
    @return:
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
