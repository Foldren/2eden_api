import base64
from typing import Annotated
from aiogram.utils.web_app import WebAppInitData
from deep_translator import GoogleTranslator
from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from starlette import status
from components.requests import ChangeRegionRequest
from components.responses import CustomJSONResponse
from components.tools import sync_energy, validate_telegram_hash, get_daily_reward
from models import User, User_Pydantic, Stats, Rank
import pycountry

router = APIRouter(prefix="/user", tags=["User"])


@router.get(path="/profile", description="Эндпойнт на получение данных игрока.")
@cache(expire=10)
async def get_user_profile(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на получение данных игрока.
    @param init_data: данные юзера telegram
    @return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data

    user = await User.filter(id=user_chat_id).prefetch_related("activity", "stats", "rank", "leads",
                                                               "rewards", "leader_place").first()
    await get_daily_reward(user)  # получаем ежедневную награду за вход
    await sync_energy(user)  # синхронизируем энергию

    from_orm = await User_Pydantic.from_tortoise_orm(user)
    user_dump = from_orm.model_dump(mode="json")  # Мод как решение проблемы с сериализацией даты
    user_dump["base64_avatar"] = base64.b64encode(user.avatar).decode("utf-8")

    return CustomJSONResponse(data=user_dump, message="Выведены данные профиля.")


@router.post(path="/change_region", description="Эндпойнт на изменение региона пользователя.")
async def change_user_region(req: ChangeRegionRequest,
                             init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на изменение региона пользователя (вводить в любом формате).
    @param req: request объект с названием региона ChangeRegionRequest
    @param init_data: данные юзера telegram
    @return:
    """
    user_chat_id = init_data.user.id  # узнаем chat_id юзера из init_data
    user = await User.filter(id=user_chat_id).first()

    if "(changed)" in user.country:
        return CustomJSONResponse(message="Вы уже меняли страну.",
                                  status_code=status.HTTP_409_CONFLICT)
    else:
        try:
            transl_country = GoogleTranslator(source='auto', target='en').translate(req.country)
            f_country = pycountry.countries.search_fuzzy(transl_country)[0]
            user.country = f_country.alpha_2 + " (changed)"
            await user.save()
            return CustomJSONResponse(message="Страна изменена.")
        except LookupError:
            return CustomJSONResponse(message="Страна задана неверно.",
                                      status_code=status.HTTP_409_CONFLICT)


@router.get(path="/leaderboard", description="Эндпойнт на получение лидерборда (50 лидеров по количеству заработанных монет за неделю) earned_week_coins обнуляется и начисляет награды в воскресенье в таск менеджере (отдельный сервис).")
@cache(expire=3600)
async def get_leaderboard(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
    """
    Эндпойнт на получение лидерборда (50 лидеров по количеству заработанных монет за неделю)
    earned_week_coins обнуляется и начисляет награды в воскресенье в таск менеджере (отдельный сервис).
    :param init_data: данные юзера telegram
    :return:
    """
    users_stats = (await Stats.all()
                   .order_by('earned_week_coins')
                   .limit(50)
                   .select_related("user").values(id="user__id", coins="earned_week_coins",
                                                  rank="user__rank_id", username="user__username"))

    users_stats.reverse()

    return CustomJSONResponse(data={"leaders": users_stats},
                              message="Выведен список лидеров на текущую неделю.")


@router.patch(path="/rank", description="Эндпойнт для повышения ранга (если хватает монет).")
async def promote_rank(init_data: Annotated[WebAppInitData, Depends(validate_telegram_hash)]) -> CustomJSONResponse:
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

