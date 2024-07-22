from datetime import timedelta, datetime
from math import floor
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from pytz import timezone
from config import ACCESS_SECURITY
from models import User


router = APIRouter()


@router.post("/user/sync_game")
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
