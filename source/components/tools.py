from datetime import timedelta, datetime
from typing import Any
from httpx import Response
from pytz import timezone
from components import enums
from components.enums import VisibilityType
from components.app.responses import CustomJSONResponse
from config import REFRESH_SECURITY, ACCESS_SECURITY
from db_models.api import User, Reward, Task, RankVisibility


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
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=500)
            case 2:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=1000)
            case 3:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=1000,
                                    inspirations=1)
            case 4:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=1000,
                                    inspirations=1, replenishments=1)
            case 5:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=1000,
                                    inspirations=2, replenishments=1)
            case 6:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=5000,
                                    inspirations=2, replenishments=2)
            case 7:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=10000,
                                    inspirations=2, replenishments=2)
            case _:
                await Reward.create(type_name=enums.RewardTypeName.LAUNCHES_SERIES, user_id=user_id, amount=10000,
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
                await Reward.create(type_name=enums.RewardTypeName.INVITE_FRIENDS, user_id=referrer.id, amount=2000)
            case 5:
                await Reward.create(type_name=enums.RewardTypeName.INVITE_FRIENDS, user_id=referrer.id, amount=5000)
            case 100:
                await Reward.create(type_name=enums.RewardTypeName.INVITE_FRIENDS, user_id=referrer.id, amount=50000)
            case 1000:
                await Reward.create(type_name=enums.RewardTypeName.INVITE_FRIENDS, user_id=referrer.id, amount=250000)


async def send_referral_mining_reward(extraction: int, referrer_id: int = None) -> None:
    """
    Отправка процентов с добычи по майнингу реферреру.
    :param referrer_id: айди реферрера
    :param extraction: добыча с майнинга реферала
    """

    # Если нет реферрера то не выполняем
    if referrer_id is None:
        return

    referrer_rw = await Reward.filter(user_id=referrer_id, type_name=enums.RewardTypeName.REFERRAL).first()
    income_5_perc = int(extraction * 0.05)

    if referrer_rw:
        referrer_rw.amount += income_5_perc
        await referrer_rw.save()
    else:
        await Reward.create(user_id=referrer_id, type_name=enums.RewardTypeName.REFERRAL, amount=income_5_perc)

    referrer_upper_id = (await User.filter(id=referrer_id).values_list('referrer_id', flat=True))[0]

    # Если у реферрера нет реферрера то не выполняем
    if referrer_upper_id is None:
        return

    referrer_upper_rw = await Reward.filter(user_id=referrer_upper_id, type_name=enums.RewardTypeName.REFERRAL).first()
    income_1_perc = int(extraction * 0.01)

    if referrer_upper_rw:
        referrer_upper_rw.amount += income_1_perc
        await referrer_upper_rw.save()
    else:
        await Reward.create(user_id=referrer_upper_id, type_name=enums.RewardTypeName.REFERRAL, amount=income_1_perc)


# async def pydantic_from_queryset(pydantic_model: PydanticListModel, qs: QuerySet) -> tuple[dict[str, Any]]:
#     """
#     Функция для преобразования запроса QuerySet в tuple[dict]. Для преобразования 1+? записей из бд.
#     :param pydantic_model: Pydantic модель бд
#     :param qs: QuerySet к бд
#     :return:
#     """
#     from_qs = await pydantic_model.from_queryset(qs)
#     return from_qs.model_dump()
#
#
# async def pydantic_from_model(pydantic_model: PydanticModel, orm_model: Model) -> dict[str, Any]:
#     """
#     Функция для преобразования ORM модели в dict. Для преобразования одной записи из бд.
#     :param pydantic_model: Pydantic модель бд
#     :param orm_model: ORM модель бд
#     :return:
#     """
#     from_orm = await pydantic_model.from_tortoise_orm(orm_model)
#     return from_orm.model_dump()


async def sync_energy(user: User) -> None:
    """
    Функция для синхронизации энергии. Обновляет дату синхронизации и меняет кол-во энергии.
    :param user: объект модели User с включенными: activity, stats, rank
    """
    dt_last_sync_energy = datetime.fromisoformat(user.activity.last_sync_energy.isoformat())
    secs_from_last_sync = (datetime.now(tz=timezone("Europe/Moscow")) - dt_last_sync_energy).seconds

    accumulated_energy = max(secs_from_last_sync, 1) * user.rank.energy_per_sec
    user.stats.energy += accumulated_energy

    if user.stats.energy > user.rank.max_energy:
        user.stats.energy = user.rank.max_energy

    user.activity.last_sync_energy = datetime.now(tz=timezone("Europe/Moscow"))

    await user.stats.save()
    await user.activity.save()


async def check_task_visibility(task: Task, user: User):
    if task.visibility.type == VisibilityType.RANK:
        rank_visibility = await RankVisibility.get(visibility=task.visibility)
        return user.rank.league >= rank_visibility.rank.league

    elif task.visibility.type == VisibilityType.ALLWAYS:
        return True

    return False


async def get_jwt_cookie_response(payload: dict[str, Any], status_code: int,
                                  message: str | None = None) -> CustomJSONResponse:
    """
    Функция для генерции JSONResponse с куками (access, refresh tokens).
    :param payload: payload для токена
    :param status_code: статус код
    :param message: сообщение на вывод
    :return:
    """
    access_token = ACCESS_SECURITY.create_access_token(subject=payload)
    refresh_token = REFRESH_SECURITY.create_refresh_token(subject=payload)

    data = {"access_token": access_token, "refresh_token": refresh_token}
    response = CustomJSONResponse(message=message, data=data, status_code=status_code)

    ACCESS_SECURITY.set_access_cookie(response, access_token)
    REFRESH_SECURITY.set_refresh_cookie(response, refresh_token)

    return response


async def assert_status_code(response: Response, status_code: int) -> None:
    """
    Функция для быстрой генерации assert по status code, для тестов.
    :param response: httpx.Response
    :param status_code: Starlette.status
    """
    frmt_text = f"[Message: {response.json()["message"]["text"]}]"
    assert response.status_code == status_code, frmt_text
    print(frmt_text)
