from typing import Optional
from pydantic import BaseModel


class RegistrationRequest(BaseModel):
    chat_id: int  # chat_id пользователя в telegram
    token: str  # token пользователя в telegram
    country: str  # страна пользователя в telegram
    referral_code: Optional[str] = ""  # реферальный код реферрера


class LoginRequest(BaseModel):
    chat_id: int  # chat_id пользователя в telegram
    token: str  # token пользователя в telegram


class GetRewardRequest(BaseModel):
    reward_id: int  # ID награды


class SyncClicksRequest(BaseModel):
    clicks: int  # количество кликов
