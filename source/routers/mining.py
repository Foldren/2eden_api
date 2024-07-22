from datetime import timedelta, datetime
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from pytz import timezone
from config import ACCESS_SECURITY
from models import User


router = APIRouter()


@router.post("/mining/start")
async def start_mining(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод для начала майнинга. Изменяет время старта.
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "activity").first()

    if user.rank.id < 4:
        return {"message": "Маловат ранг."}

    if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.time_end_mining:
        return {"message": "Майнинг уже активен."}

    if user.activity.is_active_mining:
        return {"message": "Сперва заберите награду."}

    user.activity.time_end_mining = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(minutes=1)
    user.activity.is_active_mining = True
    await user.activity.save()

    return {"message": "Майнинг активирован.", "data": {"max_extraction": user.rank.max_extr_day_maining}}


@router.post("/mining/claim")
async def end_mining(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод для окончания майнинга.
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank", "activity").first()

    if user.rank.id < 4:
        return {"message": "Маловат ранг."}

    if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.time_end_mining:
        return {"message": "Майнинг еще не завершен."}

    if not user.activity.is_active_mining:
        return {"message": "Сперва начните майнинг."}

    user.activity.is_active_mining = False
    await user.activity.save()

    user.stats.coins += user.rank.max_extr_day_maining
    await user.stats.save()

    return {"message": "Майнинг завершен.", "data": {"max_extraction": user.rank.max_extr_day_maining}}