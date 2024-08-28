from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import UJSONResponse, RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin import BaseAdmin, DropDown
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from admin import UserView, RankView, ActivityView, RewardsView, StatsView
from components.admin.auth import CustomAuthProvider
from config import TORTOISE_CONFIG, ADMIN_MW_SECRET_KEY, PSQL_CPUS, HOST
from db_models.api import User, Rank, Stats, Activity, Reward
from init import init
from routers import synchronization, mining, rewarding, leaderboard, tasks

# Используемые базы данных Redis
# db9 - Для asgi_limit
# db10 - Кеш fastapi_cache

# Ставим самый быстрый декодер Ujson
app = FastAPI(default_response_class=UJSONResponse)

# Подключаем Tortoise ORM
register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

# Добавляем cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE", "PATCH"],
    allow_headers=["X-Telegram-Init-Data"],
)

# Инициализируем все
app.add_event_handler("startup", init)

# Подключаем роутеры
app.include_router(synchronization.router)
app.include_router(mining.router)
app.include_router(rewarding.router)
app.include_router(leaderboard.router)
app.include_router(tasks.router)


@app.get("/")
async def index():
    return RedirectResponse("/docs")


# Настраиваем админку
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
    # workers = число потоков (1 процесс = 1 поток)
    run("app:app", interface="asgi3", workers=max(PSQL_CPUS, 1), lifespan="on", host=HOST)
