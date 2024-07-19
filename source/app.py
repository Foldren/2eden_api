from datetime import timedelta, datetime
from math import floor
from traceback import print_exc
from cryptography.fernet import Fernet
from fastapi import FastAPI, Security
from fastapi_jwt import JwtAuthorizationCredentials, JwtAccessBearerCookie, JwtRefreshBearerCookie
from pytz import timezone
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

app.add_event_handler("startup", init_db)

# Read access token from bearer header and cookie (bearer priority)
access_security = JwtAccessBearerCookie(
    secret_key=JWT_SECRET,
    auto_error=True,
    access_expires_delta=timedelta(minutes=15))  # change access token validation timedelta

# Read refresh token from bearer header only
refresh_security = JwtRefreshBearerCookie(
    secret_key=JWT_SECRET,
    auto_error=True,  # automatically raise HTTPException: HTTP_401_UNAUTHORIZED
    access_expires_delta=timedelta(days=90))


# Аутентификация -------------------------------------------------------------------------------------------------------
@app.post("/auth/register")
async def registration(chat_id: int, token: str, country: str):
    try:
        encrypt_token = Fernet(SECRET_KEY).encrypt(token.encode())
        user = await User.create(chat_id=chat_id, country=country, token=encrypt_token, rank_id=1)

        await Stats.create(user_id=user.id)
        await Activity.create(user_id=user.id)

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
async def sync_clicks(clicks: int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    """
    Метод синхронизации кликов. Сколько бы кликов не отправили, все обрезается энергией, на счету у
    пользователя и дневными ограничениями.
    :param clicks: число кликов
    :param credentials: authorization headers
    :return:
    """

    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("rank", "stats", "activity").first()

    if user.stats.energy < user.rank.press_force:
        return {"message": "Не хватает энергии."}

    extraction = clicks * user.rank.press_force

    if extraction > user.stats.energy:  # Обрезаем энергию под количество доступных кликов ^^
        extraction = floor(user.stats.energy / user.rank.press_force) * user.rank.press_force

    if (user.stats.earned_day_coins + extraction) > user.rank.max_extr_day_click:  # Проверяем дневной лимит
        extraction = user.rank.max_extr_day_click - user.stats.earned_day_coins

    if extraction == 0:
        return {"message": "Достигнут дневной лимит добычи кликами."}

    user.stats.earned_day_coins += extraction
    user.stats.coins += extraction
    user.stats.energy -= extraction

    await user.stats.save()

    return {"message": "Синхронизация завершена."}


@app.post("/user/bonus/inspiration")
async def sync_inspiration_boost_clicks(clicks: int, credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()

    if user.stats.inspirations == 0:
        return {"message": "На счету кончились бустеры вдохновения."}

    if user.activity.allowed_time_use_inspiration > datetime.now(tz=timezone("Europe/Moscow")):
        return {"message": "Вдохновение уже активно, дождитесь завершения."}

    extraction = clicks * (user.rank.press_force * 3)

    if extraction > user.rank.max_extr_day_inspiration:
        extraction = user.rank.max_extr_day_inspiration

    user.activity.allowed_time_use_inspiration = datetime.now(tz=timezone("Europe/Moscow")) + timedelta(seconds=15)
    await user.activity.save()

    user.stats.inspirations -= 1
    user.stats.coins += extraction
    await user.stats.save()

    return {"message": "Вдохновение активировано."}


@app.post("/user/bonus/replenishment")
async def use_replenishment_boost(credentials: JwtAuthorizationCredentials = Security(access_security)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank").first()

    if user.stats.replenishments == 0:
        return {"message": "На счету кончились бустеры прилива."}

    if user.stats.energy == user.rank.max_energy:
        return {"message": "У вас максимум энергии."}

    user.stats.energy = user.rank.max_energy
    user.stats.replenishments -= 1
    await user.stats.save()

    return {"message": "Прилив энергии активирован."}


if __name__ == "__main__":
    run("app:app", reload=True)
