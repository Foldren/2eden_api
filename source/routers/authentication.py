from cryptography.fernet import Fernet
from fastapi import APIRouter
from fastapi import Security
from fastapi_jwt import JwtAuthorizationCredentials

from components.tools import get_daily_reward, get_referral_reward
from config import SECRET_KEY, REFRESH_SECURITY, ACCESS_SECURITY
from models import User, Stats, Activity, Referral

router = APIRouter()


@router.post("/auth/register")
async def registration(chat_id: int, token: str, country: str, referral_code: str = ""):
    try:
        encrypt_token = Fernet(SECRET_KEY).encrypt(token.encode())
        user = await User.create(chat_id=chat_id, country=country, token=encrypt_token, rank_id=1)

        await Stats.create(user_id=user.id)
        await Activity.create(user_id=user.id)

        if referral_code:
            await get_referral_reward(user.id, referral_code)

        await get_daily_reward(user.id)  # получаем ежедневную награду за вход

    except Exception:
        return {"message": "Пользователь уже зарегистрирован."}

    payload = {"id": user.id}
    access_token = ACCESS_SECURITY.create_access_token(subject=payload)
    refresh_token = REFRESH_SECURITY.create_refresh_token(subject=payload)

    return {"message": "Пользователь создан.",
            "data": payload | {"access_token": access_token, "refresh_token": refresh_token}}


@router.post("/auth/login")
async def login(chat_id: int, token: str):
    user = await User.filter(chat_id=chat_id).select_related("activity").first()
    decrypt_token = Fernet(SECRET_KEY).decrypt(user.token).decode("utf-8")

    if user:
        if decrypt_token == token:
            payload = {"id": user.id}
            await get_daily_reward(user.id)  # получаем ежедневную награду за вход
            access_token = ACCESS_SECURITY.create_access_token(subject=payload)
            refresh_token = REFRESH_SECURITY.create_refresh_token(subject=payload)
            return {"message": "Авторизация прошла успешно!",
                    "data": {"access_token": access_token, "refresh_token": refresh_token}}
        else:
            return {"message": "Уупс, токен неверный."}
    else:
        return {"message": "Не вижу такого пользователя."}


@router.post("/auth/refresh")
async def refresh(credentials: JwtAuthorizationCredentials = Security(REFRESH_SECURITY)):
    user_id = credentials.subject.get("id")
    await get_daily_reward(user_id)  # получаем ежедневную награду за вход
    access_token = ACCESS_SECURITY.create_access_token(subject=credentials.subject)
    refresh_token = REFRESH_SECURITY.create_refresh_token(subject=credentials.subject)

    return {"data": {"access_token": access_token, "refresh_token": refresh_token}}