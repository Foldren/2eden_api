import json

from cryptography.fernet import Fernet
from fastapi import APIRouter
from fastapi import Security
from fastapi_jwt import JwtAuthorizationCredentials
from starlette.responses import Response
from components.tools import get_daily_reward, get_referral_reward, sync_energy
from config import SECRET_KEY, REFRESH_SECURITY, ACCESS_SECURITY
from models import User, Stats, Activity

router = APIRouter()


@router.post("/auth/registration")
async def registration(chat_id: int, token: str, country: str, referral_code: str = ""):
    try:
        encrypt_token = Fernet(SECRET_KEY).encrypt(token.encode())
        user = await User.create(chat_id=chat_id, country=country, token=encrypt_token, rank_id=1)

        await Stats.create(user_id=user.id)
        await Activity.create(user_id=user.id)

        if referral_code:
            await get_referral_reward(user, referral_code)

        await get_daily_reward(user.id)  # получаем ежедневную награду за вход

    except Exception:
        return {"message": "Пользователь уже зарегистрирован."}

    payload = {"id": user.id}
    access_token = ACCESS_SECURITY.create_access_token(subject=payload)
    refresh_token = REFRESH_SECURITY.create_refresh_token(subject=payload)

    json_c = json.dumps({"message": "Пользователь создан.",
                         "data": payload | {"access_token": access_token, "refresh_token": refresh_token}}, indent=4)
    response = Response(content=json_c)

    ACCESS_SECURITY.set_access_cookie(response, access_token)
    REFRESH_SECURITY.set_refresh_cookie(response, refresh_token)

    return response


@router.post("/auth/login")
async def login(chat_id: int, token: str):
    user = await User.filter(chat_id=chat_id).select_related("activity", "stats", "rank").first()

    if user:
        decrypt_token = Fernet(SECRET_KEY).decrypt(user.token).decode("utf-8")

        if decrypt_token == token:
            payload = {"id": user.id}
            await get_daily_reward(user.id)  # получаем ежедневную награду за вход
            await sync_energy(user)

            access_token = ACCESS_SECURITY.create_access_token(subject=payload)
            refresh_token = REFRESH_SECURITY.create_refresh_token(subject=payload)

            json_c = json.dumps({"message": "Авторизация прошла успешно!",
                                 "data": {"access_token": access_token, "refresh_token": refresh_token}}, indent=4)
            response = Response(content=json_c)

            ACCESS_SECURITY.set_access_cookie(response, access_token)
            REFRESH_SECURITY.set_refresh_cookie(response, refresh_token)

            return response
        else:
            return {"message": "Уупс, токен неверный."}
    else:
        return {"message": "Не вижу такого пользователя."}


@router.post("/auth/refresh")
async def refresh(credentials: JwtAuthorizationCredentials = Security(REFRESH_SECURITY)):
    user_id = credentials.subject.get("id")
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()
    await get_daily_reward(user_id)  # получаем ежедневную награду за вход
    await sync_energy(user)

    access_token = ACCESS_SECURITY.create_access_token(subject=credentials.subject)
    refresh_token = REFRESH_SECURITY.create_refresh_token(subject=credentials.subject)

    json_c = json.dumps({"data": {"access_token": access_token, "refresh_token": refresh_token}}, indent=4)
    response = Response(content=json_c)

    ACCESS_SECURITY.set_access_cookie(response, access_token)
    REFRESH_SECURITY.set_refresh_cookie(response, refresh_token)

    return response
