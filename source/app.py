from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import UJSONResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette_admin import BaseAdmin, DropDown
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from admin import UserView, RankView, ActivityView, RewardsView, StatsView
from components.admin.auth import CustomAuthProvider
from config import TORTOISE_CONFIG, ADMIN_MW_SECRET_KEY, REDIS_URL
from db_models.api import User, Rank, Stats, Activity, Reward
from init import init
from routers import authentication, synchronization, mining, rewarding, leaderboard, tasks
# from ratelimit import Rule, RateLimitMiddleware
# from ratelimit.backends.redis import RedisBackend
# from redis.asyncio import Redis
# from components.tools import auth_function, handle_auth_error

# Используемые базы данных Redis
# db9 - Для asgi_limit
# db10 - Кеш fastapi_cache

# Для масштабирования изменяем число воркеров в uvicorn

app = FastAPI(default_response_class=UJSONResponse)

# Подключаем Tortoise ORM
register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

# Добавляем cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization"],
)

# Добавляем ratelimit middleware, защита от ddos
# app.add_middleware(
#     RateLimitMiddleware,
#     authenticate=auth_function,
#     on_auth_error=handle_auth_error,
#     backend=RedisBackend(Redis.from_url(REDIS_URL, db=9, encoding="utf-8", decode_responses=False)),
#     config={
#         r"^/auth": [Rule(second=2, block_time=30)],
#         r"^/user": [Rule(second=2, block_time=30)],  # ограничение 2 запроса в секунду, иначе блокировка
#         r"^/mining": [Rule(second=2, block_time=30)],
#         r"^/reward": [Rule(second=2, block_time=30)],
#         r"^/tasks": [Rule(second=2, block_time=30)]
#     }
# )

# Инициализируем все
app.add_event_handler("startup", init)

# Подключаем роутеры
app.include_router(authentication.router)
app.include_router(synchronization.router)
app.include_router(mining.router)
app.include_router(rewarding.router)
app.include_router(leaderboard.router)
app.include_router(tasks.router)


# Настраиваем админку
@app.get("/")
async def redirect_admin() -> RedirectResponse:
    return RedirectResponse(url="/docs")


admin = BaseAdmin(title="2Eden Admin",
                  auth_provider=CustomAuthProvider(),
                  middlewares=[Middleware(SessionMiddleware, secret_key=ADMIN_MW_SECRET_KEY)])

admin.add_view(RankView(Rank))
admin.add_view(DropDown("Пользователи",
                        icon="fa fa-user",
                        views=[UserView(User), ActivityView(Activity),
                               StatsView(Stats), RewardsView(Reward)]))

admin.mount_to(app)

if __name__ == "__main__":
    run("app:app", interface="asgi3", workers=5, lifespan="on")  # workers = число потоков (1 процесс = 1 ядро)
