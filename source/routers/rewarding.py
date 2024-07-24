from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from components.tools import pydantic_from_model, pydantic_from_queryset
from config import ACCESS_SECURITY
from models import Reward, Reward_Pydantic, Reward_Pydantic_List

router = APIRouter()


@router.get("/reward/list")
async def get_reward_list(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена

    try:
        query_set = Reward.filter(user_id=user_id)
        rewards_pydantic_list = await pydantic_from_queryset(pydantic_model=Reward_Pydantic_List,
                                                             qs=query_set)
    except Exception:
        return {"message": "Вознаграждений 0."}

    return {"data": {"rewards": rewards_pydantic_list}}


@router.get("/reward")
async def get_reward(reward_id: int, credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена

    try:
        model_obj = await Reward.filter(user_id=user_id, id=reward_id).first()
        reward_pydantic = await pydantic_from_model(pydantic_model=Reward_Pydantic,
                                                    orm_model=model_obj)
    except Exception:
        return {"message": "Вознаграждения не существует."}

    return {"data": reward_pydantic}
