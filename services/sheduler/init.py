from asyncio import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from httpx import AsyncClient
from openai import AsyncOpenAI
from redis.asyncio import from_url
from redisvl.index import AsyncSearchIndex
from tortoise import Tortoise
from components.pydantic_models import Connection, RedisConnection
from config import REDISVL_YAML_URL, AI_API_TOKEN, PROXY6NET_PROXIES, REDIS_URL, APP_NAME, TORTOISE_CONFIG
from modules.logger import Logger


async def start_sheduler(sch: AsyncIOScheduler) -> None:
    """
    Функция для запуска APSheduler
    (по инструкции https://github.com/agronholm/apscheduler/blob/3.x/examples/schedulers/asyncio_.py)
    :param sch: объект таск менеджера AsyncIOScheduler
    """
    try:
        sch.start()
        await Logger(APP_NAME).success(msg="Планировщик запущен.", func_name="startup")
        while True:
            await sleep(1000)
    except (KeyboardInterrupt, SystemExit):
        pass


async def init_conn() -> Connection:
    """
    Функция для создания индекса и подключений к redis, боту, ai.
    :return:
    """
    index: AsyncSearchIndex = AsyncSearchIndex.from_yaml(REDISVL_YAML_URL)
    # подключаемся к redis, берет REDIS_URL из env
    await index.connect()
    # создаем индекс (по умолчанию не создает если есть, либо указать overwrite=True, если нужно пересоздать)
    await index.create()

    conn = Connection(
        ai_client=AsyncOpenAI(api_key=AI_API_TOKEN, http_client=AsyncClient(proxies=PROXY6NET_PROXIES)),
        rs=RedisConnection(
            questions=await from_url(url=REDIS_URL, db=14, decode_responses=True),  # новые вопросы хранятся в бд 14
            index=index
        )
    )

    return conn


async def init_db():
    await Tortoise.init(config=TORTOISE_CONFIG)
