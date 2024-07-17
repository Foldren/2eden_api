from datetime import datetime
from enum import Enum
from tortoise import Model
from tortoise.fields import BigIntField, DateField, CharEnumField, CharField, DatetimeField, \
    ReverseRelation, OnDelete, ForeignKeyField, BooleanField


class User(Model):
    id = BigIntField(pk=True)
    chat_id = BigIntField()
    passwd_token = CharField(max_length=150)
    coins = BigIntField(default=1000)
    rank = ForeignKeyField(model_name="models.Rank", on_delete=OnDelete.CASCADE, related_name="users", default=0)
    registration_date = DateField(default=datetime.now())
    last_login_date = DateField(default=datetime.now())
    last_coins_sync = DatetimeField(auto_now=True)
    country = CharField(max_length=50)

    class Meta:
        table = "users"


class RankName(str, Enum):
    acolyte = "Acolyte"
    deacon = "Deacon"
    priest = "Priest"
    bishop = "Bishop"
    archbishop = "Archbishop"
    metropolitan = "Metropolitan"
    cardinal = "Cardinal"
    patriarch = "Patriarch"
    master = "Master"
    pope = "Pope"


# В системе изначально создаются все 10 рангов
class Rank(Model):
    name = CharEnumField(enum_type=RankName, default=RankName.acolyte, description='Ранг')
    press_force = BigIntField()
    max_energy = BigIntField()
    energy_per_sec = BigIntField()
    boost_inspiration = BooleanField(default=1)
    boost_surge_energy = BooleanField(default=1)
    mining = BooleanField(default=1)
    users: ReverseRelation["User"]

    class Meta:
        table = "ranks"

