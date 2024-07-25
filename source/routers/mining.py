from datetime import timedelta, datetime
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from pytz import timezone
from tortoise.functions import Sum

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

    if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.next_mining:
        return {"message": "Майнинг уже активен."}

    if user.activity.is_active_mining:
        return {"message": "Сперва заберите награду."}

    user.activity.next_mining = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(minutes=1)
    user.activity.is_active_mining = True
    await user.activity.save()

    return {"message": "Майнинг активирован.", "data": {"max_extraction": user.rank.max_energy}}


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

    if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.next_mining:
        return {"message": "Майнинг еще не завершен."}

    if not user.activity.is_active_mining:
        return {"message": "Сперва начните майнинг."}

    user.activity.is_active_mining = False
    await user.activity.save()

    referals_5_perc = await (User.filter(referrer_id=1)
                             .select_related("rank")
                             .values_list("rank__max_energy", "id"))

    referals_5_perc_energ = [e[0] for e in referals_5_perc]

    referals_5_perc_ids = [e[1] for e in referals_5_perc]

    referals_1_perc_energ = await (User.filter(referrer_id__in=referals_5_perc_ids)
                                   .select_related("rank")
                                   .values_list("rank__max_energy", flat=True))

    user.stats.coins += user.rank.max_energy + int(sum(referals_5_perc_energ) * 0.05) + \
                        int(sum(referals_1_perc_energ) * 0.01)
    # максимум можно заработать max_energy + добыча от рефералов

    await user.stats.save()

    return {"message": "Майнинг завершен.", "data": {"max_extraction": user.rank.max_energy}}
