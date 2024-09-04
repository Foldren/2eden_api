from tortoise.exceptions import OperationalError
from config import APP_NAME
from db_models.api import Stats, Leader
from modules.logger import Logger


async def send_reward_to_leaders():
    """
    Таск на отправку наград первым 50 лидерам по добычи в неделю, обнуляет добычу в неделю у игроков.
    Выполняется в 3:00 каждое воскресенье.
    """

    leaders_stats = await Stats.all().order_by('-earned_week_coins').limit(50)

    # Начисляем награды
    for i, stats in enumerate(leaders_stats, 1):
        if i == 1:
            stats.coins += int(stats.earned_week_coins * 0.5)
        if i <= 3:
            stats.coins += int(stats.earned_week_coins * 0.4)
        if i <= 5:
            stats.coins += int(stats.earned_week_coins * 0.3)
        if i <= 10:
            stats.coins += int(stats.earned_week_coins * 0.2)
        if i <= 15:
            stats.coins += int(stats.earned_week_coins * 0.1)
        if i <= 25:
            stats.coins += 10000

        stats.replenishments += 1

    await Stats.bulk_update(leaders_stats, ['earned_week_coins', 'replenishments', 'coins'])

    # Добавляем новых лидеров в таблицу, чтобы смотреть предыдущих
    try:
        await Leader.all().delete()
    except OperationalError:
        pass

    leaders = []
    for i, stats in enumerate(leaders_stats, 1):
        leaders.append(Leader(place=i, user_id=stats.user_id, earned_week_coins=stats.earned_week_coins))

    await Leader.bulk_create(leaders)

    # Обновляем еженедельный доход у юзеров
    users_stats = await Stats.all()
    for stats in users_stats:
        stats.earned_week_coins = 0

    await Stats.bulk_update(users_stats, ['earned_week_coins'])

    await Logger(APP_NAME).info(msg="Награды лидерам выплачены, следующие будут через неделю.",
                                func_name="leaderboard_reward")
