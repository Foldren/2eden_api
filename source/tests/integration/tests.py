from datetime import datetime, timedelta
from typing import Dict, Any
import pytest
from httpx import AsyncClient
from pytz import timezone
from starlette.status import HTTP_201_CREATED, HTTP_208_ALREADY_REPORTED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, \
    HTTP_202_ACCEPTED, HTTP_409_CONFLICT, HTTP_200_OK
from components.tools import assert_status_code
from db_models.api import User, Activity, Stats, Reward

register_params = (
    pytest.param({"chat_id": 1, "token": "1", "country": "ru"}, "no_referral_code", HTTP_201_CREATED,
                 id="without_referral_code"),
    pytest.param({"chat_id": 2, "token": "2", "country": "ru"}, "referral_code", HTTP_201_CREATED,
                 id="with_referral_code"),
    pytest.param({"chat_id": 2, "token": "2", "country": "ru"}, "with_register_ci", HTTP_208_ALREADY_REPORTED,
                 id="with_register_chat_id"),
)

login_params = (
    pytest.param({"chat_id": 3, "token": "1"}, "bad_login", HTTP_404_NOT_FOUND, id="with_bad_login"),
    pytest.param({"chat_id": 1, "token": "2"}, "bad_token", HTTP_400_BAD_REQUEST, id="with_bad_token"),
    pytest.param({"chat_id": 1, "token": "1"}, "auth", HTTP_202_ACCEPTED, id="without_constraints"),
)

update_rank_params = (
    pytest.param("without_coins", HTTP_409_CONFLICT, id="without_coins"),
    pytest.param("with_coins", HTTP_202_ACCEPTED, id="with_coins"),
    pytest.param("with_max_rank", HTTP_409_CONFLICT, id="with_max_rank"),
)

start_mining_params = (
    pytest.param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    pytest.param("without_constraints", HTTP_202_ACCEPTED, id="without_constraints"),
    pytest.param("with_active_mining", HTTP_409_CONFLICT, id="with_active_mining"),
    pytest.param("with_reward", HTTP_409_CONFLICT, id="with_reward"),
)

end_mining_params = (
    pytest.param("without_constraints", HTTP_202_ACCEPTED, id="without_constraints"),
    pytest.param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    pytest.param("with_not_end_mining", HTTP_409_CONFLICT, id="with_not_end_mining"),
    pytest.param("with_not_active_mining", HTTP_409_CONFLICT, id="with_not_active_mining"),
)

get_reward_list_params = (
    pytest.param("with_rewards", HTTP_200_OK, id="with_rewards"),
    pytest.param("without_rewards", HTTP_404_NOT_FOUND, id="without_rewards"),
)

get_reward_params = (
    pytest.param("without_rewards", HTTP_404_NOT_FOUND, id="without_rewards"),
    pytest.param("with_someone_else_reward", HTTP_404_NOT_FOUND, id="with_someone_else_reward"),
    pytest.param("with_own_reward", HTTP_200_OK, id="with_own_reward"),
)

sync_clicks_params = (
    pytest.param("with_energy", HTTP_200_OK, id="with_energy"),
    pytest.param("without_energy", HTTP_409_CONFLICT, id="without_energy"),
)

inspiration_params = (
    pytest.param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    pytest.param("without_boosts", HTTP_409_CONFLICT, id="without_boosts"),
    pytest.param("without_constraints", HTTP_200_OK, id="without_constraints"),
    pytest.param("with_active_boost", HTTP_409_CONFLICT, id="with_active_boost"),
)

replenishment_params = (
    pytest.param("with_small_rank", HTTP_409_CONFLICT, id="with_small_rank"),
    pytest.param("without_boosts", HTTP_409_CONFLICT, id="without_boosts"),
    pytest.param("with_max_energy", HTTP_409_CONFLICT, id="with_max_energy"),
    pytest.param("without_constraints", HTTP_200_OK, id="without_constraints"),
)


@pytest.mark.parametrize("data, variant, status_code", register_params)
async def test_register(client: AsyncClient, data: Dict[str, Any], variant: str, status_code: int) -> None:
    match variant:
        case "no_referral_code":
            response = await client.post(url="/auth/registration", params=data)
        case "referral_code":
            referrer = await User.first()
            data["referral_code"] = referrer.referral_code
            response = await client.post(url="/auth/registration", params=data)
        case _:
            response = await client.post(url="/auth/registration", params=data)

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("data, variant, status_code", login_params)
async def test_login(client: AsyncClient, data: Dict[str, Any], variant: str, status_code: int) -> None:
    response = await client.post(url="/auth/login", params=data)
    await assert_status_code(response, status_code)


async def test_refresh(client: AsyncClient) -> None:
    response = await client.patch(url="/auth/refresh")
    await assert_status_code(response, HTTP_200_OK)


async def test_get_leaderboard(client: AsyncClient) -> None:
    response = await client.get(url="/user/leaderboard")
    await assert_status_code(response, HTTP_200_OK)


@pytest.mark.parametrize("variant, status_code", update_rank_params)
async def test_update_rank(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_coins":
            await Stats.filter(id=1).update(coins=99999999999)
        case "with_max_rank":
            await User.filter(id=1).update(rank_id=20)

    response = await client.patch(url="/user/promote")
    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", start_mining_params)
async def test_start_mining(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_small_rank":
            await User.filter(id=1).update(rank_id=1)
            response = await client.post(url="/mining/start")
        case "without_constraints":
            await User.filter(id=1).update(rank_id=4)
            response = await client.post(url="/mining/start")
        case "with_active_mining":
            response = await client.post(url="/mining/start")
        case _:
            tnm = datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=1)
            await Activity.filter(id=1).update(next_mining=tnm)
            response = await client.post(url="/mining/start")

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", end_mining_params)
async def test_end_mining(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "without_constraints":
            await User.filter(id=1).update(rank_id=4)
            tnm = datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=1)
            await Activity.filter(id=1).update(next_mining=tnm)
            response = await client.post(url="/mining/claim")
        case "with_small_rank":
            await User.filter(id=1).update(rank_id=1)
            response = await client.post(url="/mining/claim")
        case "with_not_end_mining":
            await User.filter(id=1).update(rank_id=4)
            await client.post(url="/mining/start")
            response = await client.post(url="/mining/claim")
        case _:
            tnm = datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=1)
            await Activity.filter(id=1).update(next_mining=tnm, is_active_mining=False)
            response = await client.post(url="/mining/claim")

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", get_reward_list_params)
async def test_get_reward_list(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_rewards":
            response = await client.get(url="/reward/list")
        case _:
            await Reward.filter(user_id=1).delete()
            response = await client.get(url="/reward/list")

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", get_reward_params)
async def test_get_reward(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "without_rewards":
            response = await client.post(url="/reward", params={"reward_id": 2})
        case "with_someone_else_reward":
            reward = await Reward.create(user_id=2)
            response = await client.post(url="/reward", params={"reward_id": reward.id})
        case _:
            reward = await Reward.create(user_id=1)
            response = await client.post(url="/reward", params={"reward_id": reward.id})

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", sync_clicks_params)
async def test_sync_clicks(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_energy":
            response = await client.patch(url="/user/sync_clicks", params={"clicks": 5000})
        case _:
            response = await client.patch(url="/user/sync_clicks", params={"clicks": 5000})

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", inspiration_params)
async def test_sync_inspiration_clicks(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_small_rank":
            await User.filter(id=1).update(rank_id=1)
        case "without_boosts":
            await User.filter(id=1).update(rank_id=2)
        case "without_constraints":
            await Stats.filter(id=1).update(inspirations=2)

    response = await client.patch(url="/user/bonus/sync_inspiration_clicks", params={"clicks": 5000})
    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", replenishment_params)
async def test_use_replenishment(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_small_rank":
            await User.filter(id=1).update(rank_id=1)
        case "without_boosts":
            await User.filter(id=1).update(rank_id=3)
        case "with_max_energy":
            await Stats.filter(id=1).update(replenishments=2, energy=10000)
        case "without_constraints":
            await Stats.filter(id=1).update(energy=0)

    response = await client.post(url="/user/bonus/replenishment")
    await assert_status_code(response, status_code)


async def test_get_user_profile(client: AsyncClient) -> None:
    response = await client.get(url="/user/profile")
    await assert_status_code(response, HTTP_200_OK)
