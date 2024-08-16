import random
from asyncio import run
from os import system
from typing import List, Dict
from cryptography.fernet import Fernet
from locust import task, between, FastHttpUser, events, constant, constant_pacing, constant_throughput
from locust.env import Environment
from tortoise import Tortoise
from config import TORTOISE_CONFIG, SECRET_KEY
from db_models.api import User

# Список данных, созданных пользователей (вначале запустить тесты на регистрацию)
users_cr: List[Dict[str, int | str]] = []


class Api2EdenUser(FastHttpUser):
    # 2000 юзеров ~ 450req/ps  2000/450 ~ 4 (надо умножить between на 4 чтобы получить ту же нагрузку
    wait_time = constant(10)  # between(1, 5)

    def on_start(self) -> None:
        """
        На старте авторизуем юзера
        """
        user = users_cr[random.randint(1, len(users_cr)-1)]
        d_token = Fernet(SECRET_KEY).decrypt(user["token"]).decode("utf-8")
        data = {"chat_id": user["chat_id"], "token": d_token}
        self.client.post("/auth/login", json=data)

    # @task(43)
    # def registration(self):
    #     data = {"chat_id": random.randint(1234, 900252525),
    #             "token": str(random.randint(1234, 900252525)),
    #             "country": str(random.randint(1234, 900252525))
    #             }
    #     self.client.post("/auth/registration", json=data)

    @task(1)
    def refresh(self) -> None:
        self.client.patch("/auth/refresh")

    @task(23)
    def get_leaderboard(self) -> None:
        self.client.get("/user/leaderboard")

    @task(7)
    def update_rank(self) -> None:
        self.client.patch("/user/promote")

    @task(9)
    def start_mining(self) -> None:
        self.client.post("/mining/start")

    @task(4)
    def end_mining(self) -> None:
        self.client.post("/mining/claim")

    @task(24)
    def get_reward_list(self) -> None:
        self.client.get("/reward/list")

    @task(10)
    def get_reward(self) -> None:
        data = {"reward_id": random.randint(1, 3000)}
        self.client.post("/reward", json=data)

    @task(34)
    def sync_clicks(self) -> None:
        data = {"clicks": random.randint(1, 3000)}
        self.client.patch("/user/sync_clicks", json=data)

    @task(17)
    def sync_inspiration_clicks(self) -> None:
        data = {"clicks": random.randint(1, 3000)}
        self.client.patch("/user/bonus/sync_inspiration_clicks", json=data)

    @task(12)
    def use_replenishment(self) -> None:
        self.client.post("/user/bonus/replenishment")

    @task(32)
    def get_user_profile(self) -> None:
        self.client.get("/user/profile")


async def get_users_creds() -> Dict[str, str | int]:
    await Tortoise.init(config=TORTOISE_CONFIG)
    users_qs = await User.all().limit(10000).values("chat_id", "token")
    return users_qs


@events.test_start.add_listener
def get_users_cr_list(environment: Environment, **kwargs) -> None:
    global users_cr
    users_cr = run(get_users_creds())


if __name__ == '__main__':
    system("locust --config locust.conf")
