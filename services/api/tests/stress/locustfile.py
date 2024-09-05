import hashlib
import hmac
import random
from asyncio import run, sleep
from operator import itemgetter
from os import system
from urllib.parse import parse_qsl
from locust import task, HttpUser, events, constant
from locust.env import Environment
from tortoise import Tortoise
from config import TOKEN, LOCUST_T_CONFIG
from db_models.api import User, Activity, Stats

# Количество пользователей
number_users = 4600


class Api2EdenUser(HttpUser):
    # Настройка на 10000 юзеров и ~ 500 RPS
    wait_time = constant(20)  # RPS ~ USERS / WAIT_TIME, WAIT_TIME = USERS / желаемый RPS

    def on_start(self) -> None:
        """
        На старте авторизуем юзера
        """
        idt = (f"query_id=AAGdJCdOAgAAAJ0kJ04EMHZk&"
               f"user={random.randint(1, number_users)}"
               f"first_name%22%3A%22Anna%22%2C%22"
               f"last_name%22%3A%22%22%2C%22"
               f"username%22%3A%22sobored19%22%2C%22"
               f"language_code%22%3A%22en%22%2C%22"
               f"allows_write_to_pm%22%3Atrue%7D&"
               f"auth_date=1725451498&"
               f"hash=c2f6fe2f69777ed02138b13a25896c226aaeb20d72d49b588cfe265a292fa232")

        parsed_data = dict(parse_qsl(idt, strict_parsing=True))
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0)))
        secret_key = hmac.new(key=b"WebAppData", msg=TOKEN.encode(), digestmod=hashlib.sha256)
        calculated_hash = hmac.new(key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()

        idt = (f"query_id=AAGdJCdOAgAAAJ0kJ04EMHZk&"
         f"user={random.randint(1, number_users)}"
         f"first_name%22%3A%22Anna%22%2C%22"
         f"last_name%22%3A%22%22%2C%22"
         f"username%22%3A%22sobored19%22%2C%22"
         f"language_code%22%3A%22en%22%2C%22"
         f"allows_write_to_pm%22%3Atrue%7D&"
         f"auth_date=1725451498&"
         f"hash={calculated_hash}")

        self.client.headers["X-Telegram-Init-Data"] = idt

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


# async def create_users() -> None:
#     await Tortoise.init(config=LOCUST_T_CONFIG)
#     await Tortoise.generate_schemas()
#
#     for i in range(1, number_users):
#         user = await User.create(country="RU")
#         await Stats.create(user_id=user.id)
#         await Activity.create(user_id=user.id)
#         await sleep(0.01)
#
#
# async def drop_database() -> None:
#     await Tortoise.init(config=LOCUST_T_CONFIG)
#     await Tortoise._drop_databases()
#
#
# @events.test_start.add_listener
# def on_startup(environment: Environment, **kwargs) -> None:
#     run(create_users())
#
#
# @events.test_stop.add_listener
# def on_shutdown(environment: Environment, **kwargs) -> None:
#     run(drop_database())


if __name__ == '__main__':
    system("locust --config locust.conf")
