from os import environ
import yaml
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

REDIS_URL = environ['REDIS_URL']

PG_CONFIG = yaml.load(environ['PG_CONFIG'], Loader=yaml.Loader)

TOKEN = environ['TOKEN']

# используем 13 потоков для 500RPS:
# -- Масштабируется --
# 5 потоков -> psql = 20 connections
# 5 потоков -> uvicron workers
# -- Не масштабируется --
# 1 поток -> asyncpg = 2 maxsize
# 1 поток -> redis
# ~1 поток -> nginx

PSQL_CPUS = 1  # RPS = PSQL_CPUS * 100 (5 = 500)

TORTOISE_CONFIG = {
    "connections": {
        "api": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "user": PG_CONFIG["user"],
                "password": PG_CONFIG["psw"],
                "host": PG_CONFIG["host"],
                "port": PG_CONFIG["port"],
                "database": PG_CONFIG["db"],
                "maxsize": max((PSQL_CPUS * 4) / 10, 1),  # maxsize = max_connections / 10, max_connections = CPUs * 4
            }
        }
    },
    "apps": {
        "api": {"models": ["models"], "default_connection": "api"},
    },
    'use_tz': True,
    'timezone': 'Europe/Moscow'
}

LOCUST_T_CONFIG = {
    "connections": {
        "api": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "user": PG_CONFIG["user"],
                "password": PG_CONFIG["psw"],
                "host": "127.0.0.1",
                "port": "15432",
                "database": PG_CONFIG["db"]
            }
        }
    },
    "apps": {
        "api": {"models": ["models"], "default_connection": "api"},
    },
    'use_tz': True,
    'timezone': 'Europe/Moscow'
}

ADMIN_NAME = environ['ADMIN_NAME']

ADMIN_HASH_PASSWORD = environ['ADMIN_HASH_PASSWORD']

ADMIN_SECRET_KEY = environ['ADMIN_SECRET_KEY']

ADMIN_MW_SECRET_KEY = environ['ADMIN_MW_SECRET_KEY']

MODEL = SentenceTransformer('all-MiniLM-L6-v2')
