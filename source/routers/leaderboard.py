from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials as JwtAuth
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import pydantic_from_queryset
from config import ACCESS_SECURITY
from models import Stats, Stats_Pydantic_List, User, Rank

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/leaderboard")
async def get_leaderboard(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт на получение лидерборда (50 лидеров по количеству заработанных монет за неделю)
    :param credentials: authorization headers
    :return:
    """
    query_set = Stats.all().order_by('earned_week_coins').limit(50)
    stats_pydantic_list = await pydantic_from_queryset(pydantic_model=Stats_Pydantic_List, qs=query_set)

    return CustomJSONResponse(data={"leaders": stats_pydantic_list})


@router.patch("/promote")
async def update_rank(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт для повышения ранга (если хватает монет).
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена
    user = await User.filter(id=user_id).select_related("stats", "rank").first()

    if user.rank.id == 20:
        return CustomJSONResponse(error="У вас максимальный ранг.",
                                  status_code=status.HTTP_409_CONFLICT)

    next_rank = await Rank.filter(id=(user.rank.id + 1)).first()

    if user.stats.coins < next_rank.price:
        return CustomJSONResponse(error="Не хватает монет для повышения.",
                                  status_code=status.HTTP_409_CONFLICT)

    user.stats.coins -= next_rank.price
    user.rank_id = next_rank.id

    await user.stats.save()
    await user.save()

    return CustomJSONResponse(message="Ранг повышен.",
                              status_code=status.HTTP_202_ACCEPTED)
