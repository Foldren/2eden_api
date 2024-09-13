from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from starlette import status
from components.requests import GetRewardRequest
from components.responses import CustomJSONResponse
from components.tools import validate_telegram_hash
from models import Reward, Stats

router = APIRouter(prefix="/reward", tags=["Reward"])


@router.get(path="/list", description="Эндпойнт на получение списка наград юзера (приглашение, серия авторизаций, таск, лидерборд, реферал)")
@cache(expire=30)
async def get_reward_list(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на получение списка наград юзера (приглашение, серия авторизаций, таск, лидерборд, реферал)
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    rewards_values = await (Reward.filter(user_id=user_chat_id)
                            .values("id", "type_name", "amount", "inspirations", "replenishments"))

    if not rewards_values:
        return CustomJSONResponse(message="Вознаграждений 0.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    return CustomJSONResponse(data={"rewards": rewards_values}, message="Выведен список вознаграждений.")


@router.post(path="", description="Эндпойнт на получение награды по ID (приглашение, серия авторизаций, таск, лидерборд, реферал)")
async def get_reward(req: GetRewardRequest,
                     init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на получение награды по ID (приглашение, серия авторизаций, таск, лидерборд, реферал)
    :param req: request объект с ID награды GetRewardRequest
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data

    try:
        reward = await Reward.filter(user_id=user_chat_id, id=req.reward_id).first()
        user_stats = await Stats.filter(user_id=user_chat_id).first()

        user_stats.coins += reward.amount
        user_stats.inspirations += reward.inspirations
        user_stats.replenishments += reward.replenishments
        user_stats.earned_week_coins += reward.amount

        await user_stats.save()
        await reward.delete()

    except Exception:
        return CustomJSONResponse(message="У вас нет этого вознаграждения.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    return CustomJSONResponse(message="Награда выдана!")
