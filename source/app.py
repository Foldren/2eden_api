from datetime import timedelta
from fastapi import FastAPI, Security
from fastapi_jwt import JwtAuthorizationCredentials, JwtRefreshBearer, JwtAccessBearerCookie
from tortoise import run_async
from uvicorn import run
from config import JWT_SECRET
from init_db import init
from models import User

app = FastAPI()

# Read access token from bearer header and cookie (bearer priority)
access_security = JwtAccessBearerCookie(
    secret_key=JWT_SECRET,
    auto_error=True,
    access_expires_delta=timedelta(minutes=15))  # change access token validation timedelta

# Read refresh token from bearer header only
refresh_security = JwtRefreshBearer(
    secret_key=JWT_SECRET,
    auto_error=True,  # automatically raise HTTPException: HTTP_401_UNAUTHORIZED
    access_expires_delta=timedelta(days=90))


# Аутентификация -------------------------------------------------------------------------------------------------------
@app.post("/auth/register")
async def register(chat_id: int, country: str):
    try:
        user = await User.create(chat_id=chat_id, country=country)
    except Exception:
        return {"message": "Пользователь уже зарегистрирован."}

    payload = {"id": user.id}
    access_token = access_security.create_access_token(subject=payload)
    refresh_token = refresh_security.create_refresh_token(subject=payload)

    return {"message": "Пользователь создан.",
            "data": payload | {"access_token": access_token, "refresh_token": refresh_token}}


@app.post("/auth/login")
async def login(chat_id: int, passwd_token: str):
    user = await User.filter(chat_id=chat_id).first()

    if user:
        if user.passwd_token == passwd_token:
            payload = {"id": user.id}
            access_token = access_security.create_access_token(subject=payload)
            refresh_token = refresh_security.create_refresh_token(subject=payload)
            return {"message": "Авторизация прошла успешно!",
                    "data": {"access_token": access_token, "refresh_token": refresh_token}}
        else:
            return {"message": "Уупс, токен неверный."}
    else:
        return {"message": "Не вижу такого пользователя."}


@app.post("/auth/refresh")
async def refresh(credentials: JwtAuthorizationCredentials = Security(refresh_security)):
    access_token = access_security.create_access_token(subject=credentials.subject)
    refresh_token = refresh_security.create_refresh_token(subject=credentials.subject)

    return {"data": {"access_token": access_token, "refresh_token": refresh_token}}


# Энергия и монеты -----------------------------------------------------------------------------------------------------

@app.post("/user/sync_game")
async def sync_game(clicks: int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    """
    Метод синхронизации кликов с монетами. Механически 2 пальцами можно делать около 10 кликов в секунду = 600 кликов
    в минуту, соответственно ставим ограничение.
    :param clicks: число кликов
    :param credentials: authorization headers
    :return:
    """

    user_id = credentials.subject.get("id")
    user = await User.filter(id=user_id).first()


    return {"message": "Обновили монеты."}


if __name__ == "__main__":
    run_async(init(app))
    run("app:app", reload=True)
