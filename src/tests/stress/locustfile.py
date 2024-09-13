import random
from asyncio import run, sleep
from os import system
from locust import task, HttpUser, events, constant
from locust.env import Environment
from tortoise import Tortoise
from models import User, Activity, Stats
from ...config import LOCUST_T_CONFIG

# Количество пользователей
number_users = 4600
init_data = (f"query_id=AAGdJCdOAgAAAJ0kJ04EMHZk&user=%7B%22id%22%3A5606155421%2C%22first_name%22%3A%22Anna"
             f"%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22sobored19%22%2C%22language_code%22%3A%2"
             f"2en%22%2C%22allows_write_to_pm%22%3Atrue%7D&auth_date=1725451498&hash=c2f6fe2f69777ed02138b1"
             f"3a25896c226aaeb20d72d49b588cfe265a292fa232")
user_id = 5606155421


class Api2EdenUser(HttpUser):
    # Настройка на 10000 юзеров и ~ 500 RPS
    wait_time = constant(20)  # RPS ~ USERS / WAIT_TIME, WAIT_TIME = USERS / желаемый RPS

    def on_start(self) -> None:
        """
        На старте авторизуем юзера
        """
        self.client.headers["X-Telegram-Init-Data"] = init_data

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


async def create_user() -> None:
    await Tortoise.init(config=LOCUST_T_CONFIG)
    await Tortoise.generate_schemas()

    # Создаем юзера для тестов в бд, будем работать с одним init_data
    await User.create(id=user_id, country="RU")
    await Stats.create(user_id=user_id)
    await Activity.create(user_id=user_id)
    await sleep(0.01)


async def drop_database() -> None:
    await Tortoise.init(config=LOCUST_T_CONFIG)
    await Tortoise._drop_databases()


@events.test_start.add_listener
def on_startup(environment: Environment, **kwargs) -> None:
    run(create_user())


@events.test_stop.add_listener
def on_shutdown(environment: Environment, **kwargs) -> None:
    run(drop_database())


if __name__ == '__main__':
    system("locust --config locust.conf")
