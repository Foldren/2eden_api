from pydantic import BaseModel


class GetRewardRequest(BaseModel):
    reward_id: int  # ID награды


class SyncClicksRequest(BaseModel):
    clicks: int  # количество кликов


class ChangeRegionRequest(BaseModel):
    country: str  # страна
