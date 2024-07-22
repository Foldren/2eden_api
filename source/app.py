from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from config import TORTOISE_CONFIG
from init_db import init_db
from routers import authentication, synchronization, mining, rewarding

app = FastAPI()

register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

app.add_event_handler("startup", init_db)
app.include_router(authentication.router)
app.include_router(synchronization.router)
app.include_router(mining.router)
app.include_router(rewarding.router)


# @app.post("/user/promote")
# async def get_next_league(credentials: JwtAuthorizationCredentials = Security(access_security)):
#     """
#     Метод для перехода в следующую лигу (если хватает денег).
#     :param credentials: authorization headers
#     :return:
#     """
#     user_id = credentials.subject.get("id")  # узнаем id юзера из токена
#     user = await User.filter(id=user_id).select_related("stats", "rank", "activity").first()
#
#     if user.rank.id < 4:
#         return {"message": "Маловат ранг."}
#
#     if datetime.now(tz=timezone("Europe/Moscow")) < user.activity.time_end_mining:
#         return {"message": "Майнинг еще не завершен."}
#
#     if not user.activity.is_active_mining:
#         return {"message": "Сперва начните майнинг."}
#
#     user.activity.is_active_mining = False
#     await user.activity.save()
#
#     user.stats.coins += user.rank.max_extr_day_maining
#     await user.stats.save()
#
#     return {"message": "Майнинг завершен.", "data": {"max_extraction": user.rank.max_extr_day_maining}}


if __name__ == "__main__":
    run("app:app", reload=True)
