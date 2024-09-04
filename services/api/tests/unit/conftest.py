from typing import AsyncIterator
import pytest_asyncio
from httpx import AsyncClient
from tortoise import Tortoise
from app import app
from db_models.api import User, Stats, Activity
from services.api.init import init

# config_data
pytest_plugins = ("pytest_asyncio",)
client_url = "http://127.0.0.1:8000/api"
drop_db = True
db_url = "sqlite://:memory:" if drop_db else "sqlite:///test.db"

# user_data
init_data = ("query_id=AAGdJCdOAgAAAJ0kJ04fz7iU&user=%7B%22id%22%3A5606155421%2C%22first_name%22%3A%22Anna%22%2C%22"
             "last_name%22%3A%22%22%2C%22username%22%3A%22sobored19%22%2C%22language_code%22%3A%22en%22%2C%22allows"
             "_write_to_pm%22%3Atrue%7D&auth_date=1725299335&hash=41a8bd9bc9158a428d43ca95e3a1bd76accf840d395eea60"
             "eea2316733d864f3")
chat_id = 5606155421


@pytest_asyncio.fixture(scope='session')
async def init_db():
    """
    Фикстура для инициализации Sqlite.db, и выполнение функции Fastapi startup
    """
    await Tortoise.init(db_url=db_url, modules={'api': ['db_models.api']}, _create_db=True,
                        use_tz=True, timezone='Europe/Moscow')
    await Tortoise.generate_schemas()
    await init(pytest=True)

    # Создаем юзера
    user = await User.create(id=chat_id, country="RU", rank_id=1)
    await Stats.create(user_id=user.id)
    await Activity.create(user_id=user.id)
    yield


@pytest_asyncio.fixture(scope='session')
async def client(init_db) -> AsyncIterator[AsyncClient]:
    """
    Фикстура создания псевдоприложения Fastapi для тестирования,
    при закрытии соединения удаляем тестовую базу при drop_db = True
    """
    async with AsyncClient(app=app, base_url=client_url) as ac:
        yield ac
    await Tortoise._drop_databases()
