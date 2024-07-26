from fastapi import Security, APIRouter
from fastapi_jwt import JwtAuthorizationCredentials as JwtAuth
from starlette import status
from components.responses import CustomJSONResponse
from components.tools import pydantic_from_model, pydantic_from_queryset
from config import ACCESS_SECURITY
from models import Reward, Reward_Pydantic, Reward_Pydantic_List

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
        query_set = Reward.filter(user_id=user_id)
        rewards_pydantic_list = await pydantic_from_queryset(pydantic_model=Reward_Pydantic_List,
                                                             qs=query_set)
    except Exception:
        return CustomJSONResponse(error="Вознаграждений 0.",
                                  status_code=status.HTTP_204_NO_CONTENT)

    return CustomJSONResponse(data={"rewards": rewards_pydantic_list})


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
        model_obj = await Reward.filter(user_id=user_id, id=reward_id).first()
        reward_pydantic = await pydantic_from_model(pydantic_model=Reward_Pydantic,
                                                    orm_model=model_obj)
    except Exception:
        return CustomJSONResponse(error="Вознаграждения не существует.",
                                  status_code=status.HTTP_204_NO_CONTENT)

    return CustomJSONResponse(data=reward_pydantic)
