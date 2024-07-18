from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from config import TORTOISE_CONFIG
from models import Rank, RankName


async def init_db():
    ranks = await Rank.all()

    if not ranks:
        ranks_list = [
            Rank(name=RankName.acolyte, press_force=1, max_energy=1000, energy_per_sec=1,
                 boost_inspiration=0, boost_surge_energy=0, mining=0),
            Rank(name=RankName.deacon, press_force=2, max_energy=1000, energy_per_sec=1,
                 boost_surge_energy=0, mining=0),
            Rank(name=RankName.priest, press_force=2, max_energy=2000, energy_per_sec=1,
                 mining=0),
            Rank(name=RankName.bishop, press_force=2, max_energy=3000, energy_per_sec=1),
            Rank(name=RankName.archbishop, press_force=3, max_energy=4000, energy_per_sec=1),
            Rank(name=RankName.metropolitan, press_force=3, max_energy=5000, energy_per_sec=2),
            Rank(name=RankName.cardinal, press_force=4, max_energy=6000, energy_per_sec=2),
            Rank(name=RankName.patriarch, press_force=5, max_energy=7000, energy_per_sec=2),
            Rank(name=RankName.master, press_force=6, max_energy=8000, energy_per_sec=2),
            # Rank(name=RankName.pope, press_force=12, max_energy=10000, energy_per_sec=3),
        ]

        await Rank.bulk_create(ranks_list)
