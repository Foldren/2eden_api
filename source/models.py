from datetime import datetime, timedelta
from pytz import timezone
from tortoise import Model
from tortoise.fields import BigIntField, DateField, CharEnumField, CharField, DatetimeField, \
    OnDelete, ForeignKeyField, OneToOneField, BinaryField, \
    OneToOneRelation, ReverseRelation, FloatField, BooleanField
from components.enums import RankName, RewardTypeName


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
    last_get_daily_reward_date = DateField(null=True)
    allowed_time_use_inspiration = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(days=1)))
    time_end_mining = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(days=1)))
    is_active_mining = BooleanField(default=False)
    active_days = BigIntField(default=1)

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
    week_extr_coins = BigIntField(default=0)

    class Meta:
        table = "stats"


class Reward(Model):
    id = BigIntField(pk=True)
    type_name = CharEnumField(enum_type=RewardTypeName, default=RankName.acolyte, description='Награда')
    user = ForeignKeyField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="rewards")
    amount = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)

    class Meta:
        table = "rewards"
