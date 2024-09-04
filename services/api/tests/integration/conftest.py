from typing import AsyncIterator
import pytest_asyncio
from httpx import AsyncClient
from tortoise import Tortoise
from app import app
from init import init

pytest_plugins = ("pytest_asyncio",)
client_url = "http://127.0.0.1:8000/api"
drop_db = True
db_url = "sqlite://:memory:" if drop_db else "sqlite:///test.db"


@pytest_asyncio.fixture(scope='session')
async def init_db():
    """
    Фикстура для инициализации Sqlite.db, и выполнение функции Fastapi startup
    """
    await Tortoise.init(db_url=db_url, modules={'api': ['db_models.api']}, _create_db=True,
                        use_tz=True, timezone='Europe/Moscow')
    await Tortoise.generate_schemas()
    await init()
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
