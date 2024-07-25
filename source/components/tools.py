from datetime import timedelta, datetime
from typing import Any
from pytz import timezone
from starlette.responses import JSONResponse
from tortoise import Model
from tortoise.contrib.pydantic import PydanticListModel, PydanticModel
from tortoise.queryset import QuerySet
from components import enums
from config import ACCESS_SECURITY, REFRESH_SECURITY
from models import User, Reward


async def get_daily_reward(user_id: str) -> None:
    """
    Функция для получения награды за серию авторизаций в игре.
    :param user_id: айди авторизовавшегося юзера
    """
    user = await User.filter(id=user_id).select_related("activity", "rank", "rewards").first()

    dt_after_get_rw = datetime.fromisoformat(user.activity.last_daily_reward.isoformat()).replace(
        tzinfo=timezone("Europe/Moscow"))
    dt_last_login = datetime.fromisoformat(user.activity.last_login_date.isoformat()).replace(
        tzinfo=timezone("Europe/Moscow"))

    time_d_after_get_reward = datetime.now(tz=timezone("Europe/Moscow")) - dt_after_get_rw
    time_d_after_login = datetime.now(tz=timezone("Europe/Moscow")) - dt_last_login

    if timedelta(days=2) > time_d_after_get_reward > timedelta(days=1):
        user.activity.active_days += 1
        user.activity.last_daily_reward = datetime.now(tz=timezone("Europe/Moscow"))

        match user.activity.active_days:
            case 1:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=500)
            case 2:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=1000)
            case 3:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=1000,
                                    inspirations=1)
            case 4:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=1000,
                                    inspirations=1, replenishments=1)
            case 5:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=1000,
                                    inspirations=2, replenishments=1)
            case 6:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=5000,
                                    inspirations=2, replenishments=2)
            case 7:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=10000,
                                    inspirations=2, replenishments=2)
            case _:
                await Reward.create(type_name=enums.RewardTypeName.launches_series, user_id=user_id, amount=10000,
                                    inspirations=2, replenishments=2)

    if timedelta(days=2) <= time_d_after_login:
        user.activity.active_days = 0
        user.activity.last_daily_reward = datetime.now(tz=timezone("Europe/Moscow"))

    user.activity.last_login_date = datetime.now(tz=timezone("Europe/Moscow"))
    await user.activity.save()


async def get_referral_reward(lead: User, referral_code: str) -> None:
    """
    Функция для получения награды за зарегистрированного реферала.
    :param lead: объект модели User лида
    :param referral_code: код из реферальной ссылки
    """
    referrer = await User.filter(referral_code=referral_code).select_related("stats").first()
    if referrer:
        lead.referrer_id = referrer.id
        await lead.save()

        referrer.stats.invited_friends += 1
        await referrer.stats.save()

        match referrer.stats.invited_friends:
            case 1:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=referrer.id, amount=2000)
            case 5:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=referrer.id, amount=5000)
            case 100:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=referrer.id, amount=50000)
            case 1000:
                await Reward.create(type_name=enums.RewardTypeName.invite_friends, user_id=referrer.id, amount=250000)


async def pydantic_from_queryset(pydantic_model: PydanticListModel, qs: QuerySet) -> tuple[dict[str, Any]]:
    """
    Функция для преобразования запроса QuerySet в tuple[dict]. Для преобразования 1+? записей из бд.
    :param pydantic_model: Pydantic модель бд
    :param qs: QuerySet к бд
    :return:
    """
    from_qs = await pydantic_model.from_queryset(qs)
    return from_qs.model_dump()


async def pydantic_from_model(pydantic_model: PydanticModel, orm_model: Model) -> dict[str, Any]:
    """
    Функция для преобразования ORM модели в dict. Для преобразования одной записи из бд.
    :param pydantic_model: Pydantic модель бд
    :param orm_model: ORM модель бд
    :return:
    """
    from_orm = await pydantic_model.from_tortoise_orm(orm_model)
    return from_orm.model_dump()


async def sync_energy(user: User) -> None:
    """
    Функция для синхронизации энергии. Обновляет дату синхронизации и меняет кол-во энергии.
    :param user: объект модели User с включенными: activity, stats, rank
    """
    dt_last_sync_energy = datetime.fromisoformat(user.activity.last_sync_energy.isoformat()).replace(
        tzinfo=timezone("Europe/Moscow"))
    secs_from_last_sync = (datetime.now(tz=timezone("Europe/Moscow")) - dt_last_sync_energy).seconds

    accumulated_energy = secs_from_last_sync * user.rank.energy_per_sec
    user.stats.energy += accumulated_energy

    if user.stats.energy > user.rank.max_energy:
        user.stats.energy = user.rank.max_energy

    user.activity.last_sync_energy = datetime.now(tz=timezone("Europe/Moscow"))

    await user.stats.save()
    await user.activity.save()


# async def get_jwt_response(content: Any, payload: dict) -> JSONResponse:
#     access_token = ACCESS_SECURITY.create_access_token(subject=payload)
#     refresh_token = REFRESH_SECURITY.create_refresh_token(subject=payload)
#
#     response = JSONResponse(content=content)
#
#     ACCESS_SECURITY.set_access_cookie(response, access_token)
#     REFRESH_SECURITY.set_refresh_cookie(response, refresh_token)
#
#     return response
