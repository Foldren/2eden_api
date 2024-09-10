from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import validate_telegram_hash
from db_models.api import Stats, User, Rank

router = APIRouter(prefix="/user", tags=["User"])


@router.get(path="/leaderboard", description="Эндпойнт на получение лидерборда (50 лидеров по количеству заработанных монет за неделю) earned_week_coins обнуляется и начисляет награды в воскресенье в таск менеджере (отдельный сервис).")
@cache(expire=30)
async def get_leaderboard(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на получение лидерборда (50 лидеров по количеству заработанных монет за неделю)
    earned_week_coins обнуляется и начисляет награды в воскресенье в таск менеджере (отдельный сервис).
    :param init_data: данные юзера telegram
    :return:
    """
    users_stats = (await Stats.all()
                   .order_by('earned_week_coins')
                   .limit(50).values(id="id", coins="earned_week_coins"))

    users_stats.reverse()

    return CustomJSONResponse(data={"leaders": users_stats},
                              message="Выведен список лидеров на текущую неделю.")


@router.patch(path="/promote", description="Эндпойнт для повышения ранга (если хватает монет).")
async def update_rank(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт для повышения ранга (если хватает монет).
    :param init_data: данные юзера telegram
    :return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).select_related("stats").first()

    if user.rank_id >= 20:
        return CustomJSONResponse(message="У вас максимальный ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    next_rank = await Rank.filter(id=(user.rank_id + 1)).first()

    if user.stats.coins < next_rank.price:
        return CustomJSONResponse(message="Не хватает монет для повышения.",
                                  status_code=status.HTTP_409_CONFLICT)

    user.stats.coins -= next_rank.price
    user.rank_id = next_rank.id

    await user.stats.save()
    await user.save()

    return CustomJSONResponse(message="Ранг повышен.",
                              status_code=status.HTTP_202_ACCEPTED)
