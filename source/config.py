from datetime import timedelta
from os import environ, getcwd
import yaml
from dotenv import load_dotenv
from fastapi.security.http import HTTPBase
from fastapi_jwt import JwtRefreshBearerCookie, JwtAccessBearerCookie

load_dotenv()

TG_AUTH_SCHEMA = HTTPBase(scheme="basic")

IS_THIS_LOCAL = "Pycharm" in getcwd()

JWT_SECRET = environ['JWT_SECRET']

JWT_ALGORITHM = environ['JWT_ALGORITHM']

SECRET_KEY = environ['SECRET_KEY']

REDIS_URL = environ['REDIS_URL']

PG_CONFIG = yaml.load(environ['PG_CONFIG'], Loader=yaml.Loader)

TOKEN = environ['TOKEN']

HOST = "127.0.0.1" if IS_THIS_LOCAL else "0.0.0.0"

# используем 13 потоков для 500RPS:
# -- Масштабируется --
# 5 потоков -> psql = 20 connections
# 5 потоков -> uvicron workers
# -- Не масштабируется --
# 1 поток -> asyncpg = 2 maxsize
# 1 поток -> redis
# ~1 поток -> nginx

PSQL_CPUS = 1 if IS_THIS_LOCAL else 5  # RPS = PSQL_CPUS * 100 (500)

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
        "api": {"models": ["db_models.api"], "default_connection": "api"},
    },
    'use_tz': True,
    'timezone': 'Europe/Moscow'
}

# Read access token from bearer header and cookie (bearer priority)
ACCESS_SECURITY = JwtAccessBearerCookie(
    secret_key=JWT_SECRET,
    auto_error=True,
    access_expires_delta=timedelta(minutes=15))  # change access token validation timedelta

# Read refresh token from bearer header only
REFRESH_SECURITY = JwtRefreshBearerCookie(
    secret_key=JWT_SECRET,
    auto_error=True,  # automatically raise HTTPException: HTTP_401_UNAUTHORIZED
    access_expires_delta=timedelta(days=90))

ADMIN_NAME = environ['ADMIN_NAME']

ADMIN_HASH_PASSWORD = environ['ADMIN_HASH_PASSWORD']

ADMIN_SECRET_KEY = environ['ADMIN_SECRET_KEY']

ADMIN_MW_SECRET_KEY = environ['ADMIN_MW_SECRET_KEY']
