from asyncio import sleep
from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from config import TORTOISE_CONFIG
from models import Rank, RankName


async def init_db() -> None:
    ranks = await Rank.all()

    if not ranks:
        ranks_list = [
            Rank(name=RankName.acolyte, league=1, press_force=4, max_energy=2000, energy_per_sec=0.2777777778,
                 max_extr_day_click=24000, max_extr_day_maining=6000, max_extr_day_inspiration=2400),
            Rank(name=RankName.deacon, league=2, press_force=6, max_energy=3000, energy_per_sec=0.4166666667,
                 max_extr_day_click=36000, max_extr_day_maining=9000, max_extr_day_inspiration=3600),
            Rank(name=RankName.priest, league=3, press_force=8, max_energy=4000, energy_per_sec=0.5555555556,
                 max_extr_day_click=48000, max_extr_day_maining=12000, max_extr_day_inspiration=4800),
            Rank(name=RankName.archdeacon, league=4, press_force=10, max_energy=5000, energy_per_sec=0.6944444444,
                 max_extr_day_click=60000, max_extr_day_maining=15000, max_extr_day_inspiration=6000),
            Rank(name=RankName.archdeacon, league=4, press_force=11, max_energy=5500, energy_per_sec=0.7638888889,
                 max_extr_day_click=66000, max_extr_day_maining=16500, max_extr_day_inspiration=6600),
            Rank(name=RankName.bishop, league=5, press_force=12, max_energy=6000, energy_per_sec=0.8333333333,
                 max_extr_day_click=72000, max_extr_day_maining=18000, max_extr_day_inspiration=7200),
            Rank(name=RankName.bishop, league=5, press_force=13, max_energy=6500, energy_per_sec=0.9027777778,
                 max_extr_day_click=78000, max_extr_day_maining=19500, max_extr_day_inspiration=7800),
            Rank(name=RankName.bishop, league=5, press_force=14, max_energy=7000, energy_per_sec=0.9722222222,
                 max_extr_day_click=84000, max_extr_day_maining=21000, max_extr_day_inspiration=8400),
            Rank(name=RankName.archbishop, league=6, press_force=16, max_energy=8000, energy_per_sec=1.111111111,
                 max_extr_day_click=96000, max_extr_day_maining=24000, max_extr_day_inspiration=9600),
            Rank(name=RankName.archbishop, league=6, press_force=17, max_energy=8500, energy_per_sec=1.180555556,
                 max_extr_day_click=102000, max_extr_day_maining=25500, max_extr_day_inspiration=10200),
            Rank(name=RankName.archbishop, league=6, press_force=18, max_energy=9000, energy_per_sec=1.25,
                 max_extr_day_click=108000, max_extr_day_maining=27000, max_extr_day_inspiration=10800),
            Rank(name=RankName.metropolitan, league=7, press_force=20, max_energy=10000, energy_per_sec=1.388888889,
                 max_extr_day_click=120000, max_extr_day_maining=30000, max_extr_day_inspiration=12000),
            Rank(name=RankName.metropolitan, league=7, press_force=21, max_energy=10500, energy_per_sec=1.458333333,
                 max_extr_day_click=126000, max_extr_day_maining=31500, max_extr_day_inspiration=12600),
            Rank(name=RankName.metropolitan, league=7, press_force=22, max_energy=11000, energy_per_sec=1.527777778,
                 max_extr_day_click=132000, max_extr_day_maining=33000, max_extr_day_inspiration=13200),
            Rank(name=RankName.cardinal, league=8, press_force=24, max_energy=12000, energy_per_sec=1.666666667,
                 max_extr_day_click=144000, max_extr_day_maining=36000, max_extr_day_inspiration=14400),
            Rank(name=RankName.cardinal, league=8, press_force=25, max_energy=12500, energy_per_sec=1.736111111,
                 max_extr_day_click=150000, max_extr_day_maining=37500, max_extr_day_inspiration=15000),
            Rank(name=RankName.cardinal, league=8, press_force=26, max_energy=13000, energy_per_sec=1.805555556,
                 max_extr_day_click=156000, max_extr_day_maining=39000, max_extr_day_inspiration=15600),
            Rank(name=RankName.patriarch, league=9, press_force=28, max_energy=14000, energy_per_sec=1.944444444,
                 max_extr_day_click=168000, max_extr_day_maining=42000, max_extr_day_inspiration=16800),
            Rank(name=RankName.patriarch, league=9, press_force=29, max_energy=14500, energy_per_sec=2.013888889,
                 max_extr_day_click=174000, max_extr_day_maining=43500, max_extr_day_inspiration=17400),
            Rank(name=RankName.pope, league=10, press_force=30, max_energy=15000, energy_per_sec=2.083333333,
                 max_extr_day_click=180000, max_extr_day_maining=45000, max_extr_day_inspiration=18000)
        ]

        await Rank.bulk_create(ranks_list)
