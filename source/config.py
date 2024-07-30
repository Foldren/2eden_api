from datetime import timedelta
from os import environ
from dotenv import load_dotenv
from fastapi_jwt import JwtRefreshBearerCookie, JwtAccessBearerCookie

load_dotenv()

JWT_SECRET = environ['JWT_SECRET']

SECRET_KEY = environ['SECRET_KEY']

TORTOISE_CONFIG = {
    "connections": {
        "api": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": ".test.db",
                "foreign_keys": "ON",
            },
        }
    },
    "apps": {
        "api": {"models": ["db_models.api"], "default_connection": "api"}
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
