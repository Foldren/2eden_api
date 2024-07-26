from datetime import timedelta, datetime
from math import floor
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials as JwtAuth
from pytz import timezone
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import sync_energy
from config import ACCESS_SECURITY
from models import User

router = APIRouter(prefix="/user", tags=["User"])


@router.patch("/sync_clicks")
async def sync_clicks(clicks: int, credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у
    пользователя и дневными ограничениями.
    :param clicks: число кликов
    :param credentials: authorization headers
    :return:
    """

    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "stats", "activity").first()

    await sync_energy(user)

    if user.stats.energy < user.rank.press_force:
        return CustomJSONResponse(message="Не хватает энергии.",
                                  status_code=status.HTTP_409_CONFLICT)

    extraction = clicks * user.rank.press_force

    if extraction > user.stats.energy:  # Обрезаем энергию под количество доступных кликов ^^
        extraction = floor(user.stats.energy / user.rank.press_force) * user.rank.press_force

    user.stats.coins += extraction
    user.stats.energy -= extraction
    user.stats.earned_week_coins += extraction

    await user.stats.save()  # добавить синхронизацию энергии по времени синхронизации кликов
    # (добавить также в авторизацию)

    return CustomJSONResponse(message="Синхронизация завершена.")


@router.patch("/bonus/sync_inspiration_clicks")
async def sync_inspiration_boost_clicks(clicks: int,
                                        credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт синхронизации кликов под бустером - вдохновение. Сколько бы кликов не отправили,
    все обрезается по формуле user.rank.max_energy * 1.2.
    :param clicks: число кликов
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()
    max_extraction = int(user.rank.max_energy * 1.2)  # максимум можно заработать max_energy + 20%

    await sync_energy(user)

    if user.rank.id < 2:
        return CustomJSONResponse(message="Маловат ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.stats.inspirations == 0:
        return CustomJSONResponse(message="На счету кончились бустеры вдохновения.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.activity.next_inspiration > datetime.now(tz=timezone("Europe/Moscow")):
        return CustomJSONResponse(message="Вдохновение уже активно, дождитесь завершения.",
                                  status_code=status.HTTP_409_CONFLICT)

    extraction = clicks * (user.rank.press_force * 3)

    if extraction > max_extraction:
        extraction = max_extraction

    user.activity.next_inspiration = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(seconds=15)
    await user.activity.save()

    user.stats.inspirations -= 1
    user.stats.coins += extraction
    user.stats.earned_week_coins += extraction
    await user.stats.save()

    return CustomJSONResponse(message="Вдохновение активировано.")


@router.post("/bonus/replenishment")
async def use_replenishment_boost(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт на использование бустера - прилива, полностью востанавливает энергию игрока.
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()

    if user.rank.id < 3:
        return CustomJSONResponse(message="Маловат ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.stats.replenishments == 0:
        return CustomJSONResponse(message="На счету кончились бустеры прилива.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.stats.energy == user.rank.max_energy:
        return CustomJSONResponse(message="У вас максимум энергии.",
                                  status_code=status.HTTP_409_CONFLICT)

    user.stats.energy = user.rank.max_energy
    user.stats.replenishments -= 1
    await user.stats.save()

    return CustomJSONResponse(message="Прилив энергии активирован.")
