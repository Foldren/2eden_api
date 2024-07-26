from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials as JwtAuth
from starlette import status
from components.responses import CustomJSONResponse
from config import ACCESS_SECURITY
from models import Reward, Stats

router = APIRouter(prefix="/reward", tags=["Reward"])


@router.get("/list")
async def get_reward_list(credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт на получение списка наград юзера (приглашение, серия авторизаций, таск, лидерборд, реферал)
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена

    try:
        rewards_values = await (Reward.filter(user_id=user_id)
                                .values("id", "type_name", "amount", "inspirations", "replenishments"))
    except Exception:
        return CustomJSONResponse(message="Вознаграждений 0.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    return CustomJSONResponse(data={"rewards": rewards_values})


@router.get("")
async def get_reward(reward_id: int,
                     credentials: JwtAuth = Security(ACCESS_SECURITY)) -> CustomJSONResponse:
    """
    Эндпойнт на получение награды по айди (приглашение, серия авторизаций, таск, лидерборд, реферал)
    :param reward_id: айди награды
    :param credentials: authorization headers
    :return:
    """
    user_id = credentials.subject.get("id")  # узнаем id юзера из токена

    try:
        reward = await Reward.filter(user_id=user_id, id=reward_id).first()
        user_stats = await Stats.filter(user_id=user_id).first()

        user_stats.coins += reward.amount
        user_stats.inspirations += reward.inspirations
        user_stats.replenishments += reward.replenishments
        user_stats.earned_week_coins += reward.amount

        await user_stats.save()
        await reward.delete()

    except Exception:
        return CustomJSONResponse(message="У вас нет этого вознаграждения.",
                                  status_code=status.HTTP_404_NOT_FOUND)

    return CustomJSONResponse(message="Награда выдана!")
