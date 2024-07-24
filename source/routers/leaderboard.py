from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from components.tools import pydantic_from_model, pydantic_from_queryset
from config import ACCESS_SECURITY
from models import Reward, Reward_Pydantic, Reward_Pydantic_List, User, Stats, Stats_Pydantic_List

router = APIRouter()


@router.get("/leaderboard")
async def get_leaderboard(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    try:
        query_set = Stats.all().group_by('earned_week_coins').limit(50)
        stats_pydantic_list = await pydantic_from_queryset(pydantic_model=Stats_Pydantic_List,
                                                           qs=query_set)
    except Exception:
        return {"message": "Вознаграждений 0."}

    return {"data": {"leaders": stats_pydantic_list}}
