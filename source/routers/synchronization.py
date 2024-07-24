from datetime import timedelta, datetime
from math import floor
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from pytz import timezone
from config import ACCESS_SECURITY
from models import User


router = APIRouter()


@router.post("/user/sync_clicks")
async def sync_clicks(clicks: int, credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у
    пользователя и дневными ограничениями.
    :param clicks: число кликов
    :param credentials: authorization headers
    :return:
    """

    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "stats", "activity").first()

    if user.stats.energy < user.rank.press_force:
        return {"message": "Не хватает энергии."}

    extraction = clicks * user.rank.press_force

    if extraction > user.stats.energy:  # Обрезаем энергию под количество доступных кликов ^^
        extraction = floor(user.stats.energy / user.rank.press_force) * user.rank.press_force

    if (user.stats.earned_day_coins + extraction) > user.rank.max_extr_day_click:  # Проверяем дневной лимит
        extraction = user.rank.max_extr_day_click - user.stats.earned_day_coins

    if extraction == 0:
        return {"message": "Достигнут дневной лимит добычи кликами."}

    user.stats.earned_day_coins += extraction
    user.stats.coins += extraction
    user.stats.energy -= extraction

    await user.stats.save()

    return {"message": "Синхронизация завершена."}


@router.post("/user/bonus/sync_inspiration_clicks")
async def sync_inspiration_boost_clicks(clicks: int,
                                        credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()

    if user.rank.id < 2:
        return {"message": "Маловат ранг."}

    if user.stats.inspirations == 0:
        return {"message": "На счету кончились бустеры вдохновения."}

    if user.activity.allowed_time_use_inspiration > datetime.now(tz=timezone("Europe/Moscow")):
        return {"message": "Вдохновение уже активно, дождитесь завершения."}

    extraction = clicks * (user.rank.press_force * 3)

    if extraction > user.rank.max_extr_day_inspiration:
        extraction = user.rank.max_extr_day_inspiration

    user.activity.allowed_time_use_inspiration = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(seconds=15)
    await user.activity.save()

    user.stats.inspirations -= 1
    user.stats.coins += extraction
    await user.stats.save()

    return {"message": "Вдохновение активировано."}


@router.post("/user/bonus/replenishment")
async def use_replenishment_boost(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank").first()

    if user.rank.id < 3:
        return {"message": "Маловат ранг."}

    if user.stats.replenishments == 0:
        return {"message": "На счету кончились бустеры прилива."}

    if user.stats.energy == user.rank.max_energy:
        return {"message": "У вас максимум энергии."}

    user.stats.energy = user.rank.max_energy
    user.stats.replenishments -= 1
    await user.stats.save()

    return {"message": "Прилив энергии активирован."}
