from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import from_url
from components.coders import UJsonCoder
from components.enums import VisibilityType, ConditionType
from config import REDIS_URL, ADMIN_HASH_PASSWORD, ADMIN_NAME
from db_models.api import Rank, RankName, Task, Condition, VisitLinkCondition, InstantReward, Visibility, \
    RankVisibility, Admin


async def init_cache() -> None:
    """
    Функция инициализации кеша.
    """
    redis = await from_url(REDIS_URL, db=10, encoding="utf-8", decode_responses=False)
    FastAPICache.init(backend=RedisBackend(redis), prefix="fastapi-cache", coder=UJsonCoder)


async def create_necessary_db_objects() -> None:
    """
    Функция для создания необходимых для работы записей в бд.
    """
    # Создание суперадмина ---------------------------------------------------------------------------------------------
    admin = await Admin.first()

    if not admin:  # todo Убрать -> c_aM8x3jGrJdBMOMHTc-xBp6hp0b-g
        await Admin.create(username=ADMIN_NAME, password=ADMIN_HASH_PASSWORD, is_superuser=True)

    # Создание рангов --------------------------------------------------------------------------------------------------
    ranks = await Rank.all()

    if not ranks:
        ranks_list = [
            Rank(name=RankName.ACOLYTE, league=1, press_force=4, max_energy=2000,
                 energy_per_sec=0.2777777778, price=0),
            Rank(name=RankName.DEACON, league=2, press_force=6, max_energy=3000,
                 energy_per_sec=0.4166666667, price=2640),
            Rank(name=RankName.PRIEST, league=3, press_force=8, max_energy=4000,
                 energy_per_sec=0.5555555556, price=7920),
            Rank(name=RankName.ARCHDEACON, league=4, press_force=10, max_energy=5000,
                 energy_per_sec=0.6944444444, price=24200),
            Rank(name=RankName.ARCHDEACON, league=4, press_force=11, max_energy=5500,
                 energy_per_sec=0.7638888889, price=60500),
            Rank(name=RankName.BISHOP, league=5, press_force=12, max_energy=6000,
                 energy_per_sec=0.8333333333, price=145200),
            Rank(name=RankName.BISHOP, league=5, press_force=13, max_energy=6500,
                 energy_per_sec=0.9027777778, price=158400),
            Rank(name=RankName.BISHOP, league=5, press_force=14, max_energy=7000,
                 energy_per_sec=0.9722222222, price=257400),
            Rank(name=RankName.ARCHBISHOP, league=6, press_force=16, max_energy=8000,
                 energy_per_sec=1.111111111, price=300300),
            Rank(name=RankName.ARCHBISHOP, league=6, press_force=17, max_energy=8500,
                 energy_per_sec=1.180555556, price=343200),
            Rank(name=RankName.ARCHBISHOP, league=6, press_force=18, max_energy=9000,
                 energy_per_sec=1.25, price=364650),
            Rank(name=RankName.METROPOLITAN, league=7, press_force=20, max_energy=10000,
                 energy_per_sec=1.388888889, price=514800),
            Rank(name=RankName.METROPOLITAN, league=7, press_force=21, max_energy=10500,
                 energy_per_sec=1.458333333, price=572000),
            Rank(name=RankName.METROPOLITAN, league=7, press_force=22, max_energy=11000,
                 energy_per_sec=1.527777778, price=600600),
            Rank(name=RankName.CARDINAL, league=8, press_force=24, max_energy=12000,
                 energy_per_sec=1.666666667, price=786500),
            Rank(name=RankName.CARDINAL, league=8, press_force=25, max_energy=12500,
                 energy_per_sec=1.736111111, price=1029600),
            Rank(name=RankName.CARDINAL, league=8, press_force=26, max_energy=13000,
                 energy_per_sec=1.805555556, price=1251250),
            Rank(name=RankName.PATRIARCH, league=9, press_force=28, max_energy=14000,
                 energy_per_sec=1.944444444, price=1673100),
            Rank(name=RankName.PATRIARCH, league=9, press_force=29, max_energy=14500,
                 energy_per_sec=2.013888889, price=2002000),
            Rank(name=RankName.POPE, league=10, press_force=30, max_energy=15000,
                 energy_per_sec=2.083333333, price=2488200)
        ]

        await Rank.bulk_create(ranks_list)

    # Создание тасков --------------------------------------------------------------------------------------------------
    tasks = await Task.all()

    if not tasks:
        # Создаем условие для задачи
        condition_link = await Condition.create(type=ConditionType.VISIT_LINK)
        await VisitLinkCondition.create(condition=condition_link, url='https://www.google.com/search?q=2eden')

        # Создаем условие видимости для задачи
        visibility = await Visibility.create(type=VisibilityType.RANK)
        await RankVisibility.create(visibility=visibility, rank=await Rank.get(name=RankName.ACOLYTE))

        # Создаем награду для задачи
        reward = await InstantReward.create(tokens=1000)

        # Создаем задачу с условием
        await Task.create(
            description='Изучи информацию о нашем проекте и получи награду!',
            reward=reward,
            condition=condition_link,
            visibility=visibility
        )


async def init() -> None:
    """
    Функция инициализации SQL дб, Redis, Admin, выполнение миграций.
    """
    await init_cache()  # инициализируем кеш
    await create_necessary_db_objects()  # создаем записи бд при необходимости
