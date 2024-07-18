from datetime import timedelta, datetime
from traceback import print_exc

from cryptography.fernet import Fernet
from fastapi import FastAPI, Security
from fastapi_jwt import JwtAuthorizationCredentials, JwtRefreshBearer, JwtAccessBearerCookie
from tortoise import run_async
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from config import JWT_SECRET, SECRET_KEY, TORTOISE_CONFIG
from init_db import init_db
from models import User, Stats, Activity

app = FastAPI()

register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

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
async def registration(chat_id: int, token: str, country: str):
    try:
        stats = await Stats.create()
        activity = await Activity.create()
        encrypt_token = Fernet(SECRET_KEY).encrypt(token.encode())
        user = await User.create(chat_id=chat_id, country=country, stats=stats, activity=activity, token=encrypt_token)
    except Exception:
        print_exc()
        return {"message": "Пользователь уже зарегистрирован."}

    payload = {"id": user.id}
    access_token = access_security.create_access_token(subject=payload)
    refresh_token = refresh_security.create_refresh_token(subject=payload)

    return {"message": "Пользователь создан.",
            "data": payload | {"access_token": access_token, "refresh_token": refresh_token}}


@app.post("/auth/login")
async def login(chat_id: int, token: str):
    user = await User.filter(chat_id=chat_id).first()
    encrypt_token = Fernet(SECRET_KEY).encrypt(token.encode())

    if user:
        if user.token == encrypt_token:
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
    в минуту, соответственно ставим ограничение на запрос - 1 минута для пользователя, 600 кликов. Метод срабатывает раз
    в минуту, пока пользователь в меню кликов.
    :param clicks: число кликов
    :param credentials: authorization headers
    :return:
    """

    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "stats", "activity").first()

    if user.activity.last_time_sync > (datetime.now() + timedelta(minutes=1)):
        return {"message": "Рановато для синхрона."}

    user.activity.last_time_sync = datetime.now()
    await user.activity.save()

    if clicks > 600:
        return {"message": "Уупс, кажется ddos."}

    # В случае если все окей -------------------------------------------------------------------------------------------
    if clicks > user.stats.energy:
        clicks = user.stats.energy

    user.stats.coins += clicks * user.rank.press_force
    user.stats.energy -= clicks
    await user.stats.save()

    return {"message": "Синхронизация завершена."}


@app.post("/user/bonus/inspiration")
async def use_inspiration_boost(credentials: JwtAuthorizationCredentials = Security(refresh_security)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()

    if user.rank.id < 1:
        return {"message": "Сперва нужно повысить ранг."}

    if user.stats.inspirations == 0:
        return {"message": "На счету кончились бустеры вдохновения."}

    if user.activity.last_time_use_inspiration < (user.activity.last_time_use_inspiration + timedelta(seconds=15)):
        return {"message": "Вдохновение уже активно, дождитесь завершения."}

    user.activity.last_time_use_inspiration = datetime.now()
    await user.activity.save()

    user.stats.inspirations -= 1
    await user.stats.save()

    return {"message": "Вдохновение активировано."}


@app.post("/user/bonus/inspiration")
async def use_surge_of_energy_boost(credentials: JwtAuthorizationCredentials = Security(refresh_security)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank").first()

    if user.rank.id < 2:
        return {"message": "Сперва нужно повысить ранг."}

    if user.stats.surge_energies == 0:
        return {"message": "На счету кончились бустеры прилива."}

    user.stats.energy = user.rank.max_energy
    user.stats.surge_energies -= 1
    await user.stats.save()

    return {"message": "Вдохновение активировано."}


if __name__ == "__main__":
    # run(init_db())
    run("app:app", reload=True)
