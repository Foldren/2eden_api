from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import run
from config import TORTOISE_CONFIG
from init_db import init_db
from routers import authentication, synchronization, mining, rewarding, leaderboard, tasks

app = FastAPI(default_response_class=UJSONResponse)

register_tortoise(app=app,
                  config=TORTOISE_CONFIG,
                  generate_schemas=True,
                  add_exception_handlers=True)

app.add_event_handler("startup", init_db)

app.include_router(authentication.router)
app.include_router(synchronization.router)
app.include_router(mining.router)
app.include_router(rewarding.router)
app.include_router(leaderboard.router)
app.include_router(tasks.router)


if __name__ == "__main__":
    run("app:app", reload=True)  # guvicorn
