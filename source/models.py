from datetime import datetime, timedelta
from enum import Enum
from tortoise import Model
from tortoise.fields import BigIntField, DateField, CharEnumField, CharField, DatetimeField, \
    ReverseRelation, OnDelete, ForeignKeyField, BooleanField, OneToOneField, BinaryField


class User(Model):
    id = BigIntField(pk=True)
    rank = ForeignKeyField(model_name="api.Rank", on_delete=OnDelete.CASCADE, related_name="users", default=0)
    stats = OneToOneField(model_name="api.Stats", on_delete=OnDelete.CASCADE, related_name="user")
    activity = OneToOneField(model_name="api.Activity", on_delete=OnDelete.CASCADE, related_name="user")
    chat_id = BigIntField(index=True)
    token = BinaryField()
    registration_date = DateField(default=datetime.now())  # -
    country = CharField(max_length=50)  # -

    class Meta:
        table = "users"


class Activity(Model):
    id = BigIntField(pk=True)
    user: ReverseRelation["User"]
    last_login_date = DateField(default=datetime.now())  # -
    last_time_sync = DatetimeField(default=datetime.now())
    last_time_use_inspiration = DatetimeField(default=(datetime.now()-timedelta(days=1)))

    class Meta:
        table = "activities"


class Stats(Model):
    id = BigIntField(pk=True)
    user: ReverseRelation["User"]
    coins = BigIntField(default=1000)
    energy = BigIntField(default=1000)
    invited_friends = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    surge_energies = BigIntField(default=0)

    class Meta:
        table = "stats"


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
    # pope = "Pope"


# В системе изначально создаются все 10 рангов
class Rank(Model):
    id = BigIntField(pk=True)
    users: ReverseRelation["User"]
    name = CharEnumField(enum_type=RankName, default=RankName.acolyte, description='Ранг')
    press_force = BigIntField()
    max_energy = BigIntField()
    energy_per_sec = BigIntField()
    inspiration = BooleanField(default=1)
    surge_energy = BooleanField(default=1)
    mining = BooleanField(default=1)

    class Meta:
        table = "ranks"
