from aiogram import Bot
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict
from redis.asyncio import Redis
from redisvl.index import AsyncSearchIndex


class CustomModel(BaseModel):
    """A base model that allows protocols to be used for fields."""
    model_config = ConfigDict(arbitrary_types_allowed=True)


class RedisConnection(CustomModel):
    questions: Redis
    index: AsyncSearchIndex


class Connection(CustomModel):
    bot: Bot
    ai_client: AsyncOpenAI
    rs: RedisConnection
