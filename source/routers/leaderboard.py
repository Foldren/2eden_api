from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials
from components.tools import pydantic_from_queryset
from config import ACCESS_SECURITY
from models import Stats, Stats_Pydantic_List, User, Rank

router = APIRouter()


@router.get("/leaderboard")
async def get_leaderboard(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    query_set = Stats.all().order_by('earned_week_coins').limit(50)
    stats_pydantic_list = await pydantic_from_queryset(pydantic_model=Stats_Pydantic_List, qs=query_set)

    return {"data": {"leaders": stats_pydantic_list}}


@router.patch("/user/promote")
async def update_rank(credentials: JwtAuthorizationCredentials = Security(ACCESS_SECURITY)):
    """
    Метод для повышения ранга (если хватает монет).
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank").first()

    if user.rank.id == 20:
        return {"message": "У вас максимальный ранг."}

    next_rank = await Rank.filter(id=(user.rank.id + 1)).first()

    if user.stats.coins < next_rank.price:
        return {"message": "Не хватает монет для повышения."}

    user.stats.coins -= next_rank.price
    user.rank_id = next_rank.id

    await user.stats.save()
    await user.save()

    return {"message": "Ранг повышен."}
