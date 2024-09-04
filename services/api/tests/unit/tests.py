from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from pytz import timezone
from starlette.status import HTTP_200_OK
from components.tools import assert_status_code
from db_models.api import User, Activity, Stats, Reward
import services.api.tests.unit.params as params
from services.api.tests.unit.conftest import chat_id


@pytest.mark.parametrize("init_data, status_code", params.login_params)
async def test_init_data(client: AsyncClient, init_data: str, status_code: int) -> None:
    client.headers["X-Telegram-Init-Data"] = init_data
    response = await client.get(url="/user/profile")

    if init_data == "invalid":
        frmt_text = f"[Message: {response.json()["detail"]}]"
    else:
        frmt_text = f"[Message: {response.json()["message"]["text"]}]"

    assert response.status_code == status_code, frmt_text


async def test_get_leaderboard(client: AsyncClient) -> None:
    response = await client.get(url="/user/leaderboard")
    await assert_status_code(response, HTTP_200_OK)


@pytest.mark.parametrize("variant, status_code", params.update_rank_params)
async def test_update_rank(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_coins":
            await Stats.filter(id=1).update(coins=99999999999)
        case "with_max_rank":
            await User.filter(id=chat_id).update(rank_id=20)

    response = await client.patch(url="/user/promote")
    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.start_mining_params)
async def test_start_mining(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_small_rank":
            await User.filter(id=chat_id).update(rank_id=1)
            response = await client.post(url="/mining/start")
        case "without_constraints":
            await User.filter(id=chat_id).update(rank_id=4)
            response = await client.post(url="/mining/start")
        case "with_active_mining":
            response = await client.post(url="/mining/start")
        case _:
            tnm = datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=1)
            await Activity.filter(id=1).update(next_mining=tnm)
            response = await client.post(url="/mining/start")

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.end_mining_params)
async def test_end_mining(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "without_constraints":
            await User.filter(id=chat_id).update(rank_id=4)
            tnm = datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=1)
            await Activity.filter(id=1).update(next_mining=tnm)
            response = await client.post(url="/mining/claim")
        case "with_small_rank":
            await User.filter(id=chat_id).update(rank_id=1)
            response = await client.post(url="/mining/claim")
        case "with_not_end_mining":
            await User.filter(id=chat_id).update(rank_id=4)
            await client.post(url="/mining/start")
            response = await client.post(url="/mining/claim")
        case _:
            tnm = datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=1)
            await Activity.filter(id=1).update(next_mining=tnm, is_active_mining=False)
            response = await client.post(url="/mining/claim")

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.get_reward_list_params)
async def test_get_reward_list(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_rewards":
            response = await client.get(url="/reward/list")
        case _:
            await Reward.filter(user_id=chat_id).delete()
            response = await client.get(url="/reward/list")

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.get_reward_params)
async def test_get_reward(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "without_rewards":
            response = await client.post(url="/reward", json={"reward_id": 2})
        case "with_someone_else_reward":
            reward = await Reward.create(user_id=chat_id)
            response = await client.post(url="/reward", json={"reward_id": reward.id})
        case _:
            reward = await Reward.create(user_id=chat_id)
            response = await client.post(url="/reward", json={"reward_id": reward.id})

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.sync_clicks_params)
async def test_sync_clicks(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_energy":
            response = await client.patch(url="/user/sync_clicks", json={"clicks": 5000})
        case _:
            response = await client.patch(url="/user/sync_clicks", json={"clicks": 5000})

    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.inspiration_params)
async def test_sync_inspiration_clicks(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_small_rank":
            await User.filter(id=chat_id).update(rank_id=1)
        case "without_boosts":
            await User.filter(id=chat_id).update(rank_id=2)
        case "without_constraints":
            await Stats.filter(id=1).update(inspirations=2)

    response = await client.patch(url="/user/bonus/sync_inspiration_clicks", json={"clicks": 5000})
    await assert_status_code(response, status_code)


@pytest.mark.parametrize("variant, status_code", params.replenishment_params)
async def test_use_replenishment(client: AsyncClient, variant: str, status_code: int) -> None:
    match variant:
        case "with_small_rank":
            await User.filter(id=chat_id).update(rank_id=1)
        case "without_boosts":
            await User.filter(id=chat_id).update(rank_id=3)
        case "with_max_energy":
            await Stats.filter(id=1).update(replenishments=2, energy=10000)
        case "without_constraints":
            await Stats.filter(id=1).update(energy=0)

    response = await client.post(url="/user/bonus/replenishment")
    await assert_status_code(response, status_code)


async def test_get_user_profile(client: AsyncClient) -> None:
    response = await client.get(url="/user/profile")
    await assert_status_code(response, HTTP_200_OK)
