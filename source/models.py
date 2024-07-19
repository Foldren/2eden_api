from datetime import datetime, timedelta
from enum import Enum
from pytz import timezone
from tortoise import Model
from tortoise.fields import BigIntField, DateField, CharEnumField, CharField, DatetimeField, \
    OnDelete, ForeignKeyField, OneToOneField, BinaryField, \
    OneToOneRelation, ReverseRelation, FloatField


class RankName(str, Enum):
    acolyte = "Acolyte"
    deacon = "Deacon"
    priest = "Priest"
    archdeacon = "Archdeacon"
    bishop = "Bishop"
    archbishop = "Archbishop"
    metropolitan = "Metropolitan"
    cardinal = "Cardinal"
    patriarch = "Patriarch"
    master = "Master"
    pope = "Pope"


# В системе изначально создаются все 10 рангов
class Rank(Model):
    id = BigIntField(pk=True)
    users: ReverseRelation["User"]
    league = BigIntField()
    name = CharEnumField(enum_type=RankName, default=RankName.acolyte, description='Ранг')
    press_force = FloatField()
    max_energy = FloatField()
    energy_per_sec = FloatField()
    max_extr_day_click = BigIntField()
    max_extr_day_maining = BigIntField()
    max_extr_day_inspiration = BigIntField()

    class Meta:
        table = "ranks"


class User(Model):
    id = BigIntField(pk=True)
    rank = ForeignKeyField(model_name="api.Rank", on_delete=OnDelete.CASCADE, related_name="users", default=1)
    stats: OneToOneRelation["Stats"]
    activity: OneToOneRelation["Activity"]
    chat_id = BigIntField(index=True)
    token = BinaryField()
    country = CharField(max_length=50)  # -

    class Meta:
        table = "users"


class Activity(Model):
    id = BigIntField(pk=True)
    user = OneToOneField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="activity")
    registration_date = DateField(default=datetime.now())  # -
    last_login_date = DateField(default=datetime.now())  # -
    allowed_time_use_inspiration = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow"))-timedelta(days=1)))

    class Meta:
        table = "activities"


class Stats(Model):
    id = BigIntField(pk=True)
    user = OneToOneField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="stats")
    coins = BigIntField(default=1000)
    energy = BigIntField(default=2000)
    earned_day_coins = BigIntField(default=0)
    invited_friends = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)

    class Meta:
        table = "stats"
