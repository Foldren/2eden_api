from cryptography.fernet import Fernet
from fastapi import APIRouter
from fastapi import Security
from fastapi_jwt import JwtAuthorizationCredentials
from starlette import status
from tortoise.exceptions import IntegrityError
from components.responses import CustomJSONResponse
from components.tools import get_daily_reward, get_referral_reward, sync_energy, get_jwt_cookie_response
from config import SECRET_KEY, REFRESH_SECURITY
from db_models.api import User, Stats, Activity

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/registration")
async def registration(chat_id: int, token: str, country: str, referral_code: str = "") -> CustomJSONResponse:
    """
    Эндпойнт регистрации, берет из телеграм бота chat_id, страну и токен, по ним регистрирует
    пользователя. При наличии реферального кода (отправленного в сообщении к боту с командой старт)
    обновляет число приглашенных рефералов для реферрера.
    :param chat_id: айди юзера в телеграм
    :param token: токен из телеграм
    :param country: страна из телеграм
    :param referral_code: реферальный код
    :return:
    """
    try:
        encrypt_token = Fernet(SECRET_KEY).encrypt(token.encode())
        user = await User.create(chat_id=chat_id, country=country, token=encrypt_token, rank_id=1)

        await Stats.create(user_id=user.id)
        await Activity.create(user_id=user.id)

        if referral_code:
            await get_referral_reward(user, referral_code)

        await get_daily_reward(user.id)  # получаем ежедневную награду за вход

    except IntegrityError:
        return CustomJSONResponse(message="Пользователь уже зарегистрирован.",
                                  status_code=status.HTTP_208_ALREADY_REPORTED)

    payload = {"id": user.id}
    response = await get_jwt_cookie_response(message="Пользователь создан.",
                                             payload=payload,
                                             status_code=status.HTTP_201_CREATED)

    return response


@router.post("/login")
async def login(chat_id: int, token: str) -> CustomJSONResponse:
    """
    Эндпойнт авторизации, авторизует в боте по токену и айди пользователя телеграм.
    :param chat_id: айди юзера в телеграм
    :param token: токен из телеграм
    :return:
    """
    user = await User.filter(chat_id=chat_id).select_related("activity", "stats", "rank").first()

    if not user:
        return CustomJSONResponse(message="Не вижу такого пользователя.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    decrypt_token = Fernet(SECRET_KEY).decrypt(user.token).decode("utf-8")

    if decrypt_token != token:
        return CustomJSONResponse(message="Уупс, токен неверный.",
                                  status_code=status.HTTP_400_BAD_REQUEST)

    payload = {"id": user.id}
    await get_daily_reward(user.id)  # получаем ежедневную награду за вход
    await sync_energy(user)

    response = await get_jwt_cookie_response(message="Авторизация прошла успешно!",
                                             payload=payload,
                                             status_code=status.HTTP_202_ACCEPTED)

    return response


@router.patch("/refresh")
async def refresh(credentials: JwtAuthorizationCredentials = Security(REFRESH_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт на обновление JWT токенов по Refresh токену (время жизни 3 месяца).
    :param credentials: authorization Refresh header
    :return:
    """
    user_id = credentials.subject.get("id")
    payload = {"id": user_id}
    user = await User.filter(id=user_id).select_related("activity", "stats", "rank").first()

    await get_daily_reward(user_id)  # получаем ежедневную награду за вход
    await sync_energy(user)  # синхронизируем энергию

    response = await get_jwt_cookie_response(payload=payload,
                                             status_code=status.HTTP_200_OK)
    return response
