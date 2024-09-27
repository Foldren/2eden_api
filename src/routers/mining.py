from datetime import timedelta, datetime
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends
from pytz import timezone
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import send_referral_mining_reward, validate_telegram_hash
from models import User

router = APIRouter(prefix="/mining", tags=["Mining"])


@router.post(path="/start", description="Эндпойнт для начала майнинга. Изменяет время старта.")
async def start_mining(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт для начала майнинга. Изменяет время старта.
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("rank", "activity").first()

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

    resp_data = {"max_extraction": user.rank.max_energy, "next_mining_dt": user.activity.next_mining}

    return CustomJSONResponse(message="Майнинг активирован.",
                              data=resp_data,
                              status_code=status.HTTP_202_ACCEPTED)


@router.post(path="/claim", description="Эндпойнт для окончания майнинга.")
async def end_mining(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт для окончания майнинга.
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("stats", "rank", "activity").first()

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
