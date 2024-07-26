from datetime import timedelta, datetime
from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials as JwtAuth
from pytz import timezone
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import send_referral_mining_reward
from config import ACCESS_SECURITY
from models import User

router = APIRouter(prefix="/mining", tags=["Mining"])


@router.post("/start")
async def start_mining(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт для начала майнинга. Изменяет время старта.
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "activity").first()

    if user.rank.id < 4:
        return CustomJSONResponse(message="Маловат ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.next_mining:
        return CustomJSONResponse(message="Майнинг уже активен.",
                                  status_code=status.HTTP_409_CONFLICT)

    if user.activity.is_active_mining:
        return CustomJSONResponse(message="Сперва заберите награду.",
                                  status_code=status.HTTP_409_CONFLICT)

    user.activity.next_mining = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(minutes=1)
    user.activity.is_active_mining = True
    await user.activity.save()

    return CustomJSONResponse(message="Майнинг активирован.",
                              data={"max_extraction": user.rank.max_energy},
                              status_code=status.HTTP_202_ACCEPTED)


@router.post("/claim")
async def end_mining(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт для окончания майнинга.
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank", "activity").first()

    if user.rank.id < 4:
        return CustomJSONResponse(message="Маловат ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.next_mining:
        return CustomJSONResponse(message="Майнинг еще не завершен.",
                                  status_code=status.HTTP_409_CONFLICT)

    if not user.activity.is_active_mining:
        return CustomJSONResponse(message="Сперва начните майнинг.",
                                  status_code=status.HTTP_409_CONFLICT)

    user.activity.is_active_mining = False
    await user.activity.save()

    # Обновляем награду реферерров за майнинг реферала
    await send_referral_mining_reward(referrer_id=user.referrer_id, extraction=user.rank.max_energy)

    user.stats.coins += user.rank.max_energy
    user.stats.earned_week_coins += user.rank.max_energy

    await user.stats.save()

    return CustomJSONResponse(message="Майнинг завершен.",
                              data={"max_extraction": user.rank.max_energy},
                              status_code=status.HTTP_202_ACCEPTED)
