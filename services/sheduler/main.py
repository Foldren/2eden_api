from asyncio import run
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from deep_translator import GoogleTranslator
from tortoise import run_async
from init import start_sheduler, init_db  # , init_conn
# from tasks.ai_bot import get_ai_answers
from tasks.api import send_reward_to_leaders


async def main():
    """
    Функция запуска планировщика
    """
    # Инициализируем соединения с Redis, Google, OpenAI
    # conn = await init_conn()  # Redis подключения
    # gt = GoogleTranslator(source='en', target='ru')  # Google

    # Инициализируем шедулер
    scheduler = AsyncIOScheduler()

    # Подключаем таски
    # scheduler.add_job(get_ai_answers, trigger="interval", seconds=5, kwargs={'conn': conn, "gt": gt})
    scheduler.add_job(send_reward_to_leaders, trigger="cron", day_of_week=6, hour=3, minute=0)

    # Запускаем таск менеджер
    await start_sheduler(scheduler)

if __name__ == '__main__':
    run_async(init_db())
    run(main())
