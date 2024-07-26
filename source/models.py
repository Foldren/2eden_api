from datetime import datetime, timedelta
from uuid import uuid4
from pytz import timezone
from tortoise import Model
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator
from tortoise.fields import BigIntField, DateField, CharEnumField, CharField, DatetimeField, \
    OnDelete, ForeignKeyField, OneToOneField, BinaryField, \
    OneToOneRelation, ReverseRelation, FloatField, BooleanField
from components.enums import RankName, RewardTypeName, VisibilityType, ConditionType


class Rank(Model):  # В системе изначально создаются все 10 рангов
    id = BigIntField(pk=True)
    users: ReverseRelation["User"]
    league = BigIntField()
    name = CharEnumField(enum_type=RankName, default=RankName.acolyte, description='Ранг')
    press_force = FloatField()
    max_energy = FloatField()
    energy_per_sec = FloatField()
    price = BigIntField()

    class Meta:
        table = "ranks"


class User(Model):
    id = BigIntField(pk=True)
    rank = ForeignKeyField(model_name="api.Rank", on_delete=OnDelete.CASCADE, related_name="users", default=1)
    referrer = ForeignKeyField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="leads", null=True)
    leads: ReverseRelation["User"]
    stats: OneToOneRelation["Stats"]
    activity: OneToOneRelation["Activity"]
    rewards: ReverseRelation["Reward"]
    chat_id = BigIntField(index=True, unique=True)
    token = BinaryField()
    country = CharField(max_length=50)  # -
    referral_code = CharField(max_length=36, default=uuid4(), unique=True)

    class Meta:
        table = "users"

    class PydanticMeta:
        exclude = ("token",)


class Activity(Model):
    id = BigIntField(pk=True)
    user = OneToOneField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="activity")
    reg_date = DateField(default=datetime.now())  # -
    last_login_date = DateField(default=datetime.now())
    last_daily_reward = DateField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(hours=35)))
    last_sync_energy = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow"))))
    next_inspiration = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(days=1)))
    next_mining = DatetimeField(default=(datetime.now(tz=timezone("Europe/Moscow")) - timedelta(days=1)))
    is_active_mining = BooleanField(default=False)
    active_days = BigIntField(default=0)

    class Meta:
        table = "activities"


class Stats(Model):
    id = BigIntField(pk=True)
    user = OneToOneField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="stats")
    coins = BigIntField(default=1000)
    energy = BigIntField(default=2000)
    earned_week_coins = BigIntField(default=0)
    invited_friends = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)

    class Meta:
        table = "stats"


Stats_Pydantic = pydantic_model_creator(Stats, name="Stats")
Stats_Pydantic_List = pydantic_queryset_creator(Stats, name="StatsList", include=('user_id', 'coins',))


class Reward(Model):
    id = BigIntField(pk=True)
    user = ForeignKeyField(model_name="api.User", on_delete=OnDelete.CASCADE, related_name="rewards")
    type_name = CharEnumField(enum_type=RewardTypeName, default=RankName.acolyte, description='Награда')
    amount = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)

    class Meta:
        table = "rewards"


# ------ Условия выполнения задач ------
class Condition(Model):
    id = BigIntField(pk=True)
    type = CharEnumField(enum_type=ConditionType, max_length=50)


class TgChannelCondition(Model):
    id = BigIntField(pk=True)
    condition = OneToOneField('api.Condition', related_name='tg_channel_condition')
    channel_id = CharField(max_length=100)  # ID телеграмм канала для подписки


class VisitLinkCondition(Model):
    id = BigIntField(pk=True)
    condition = OneToOneField('api.Condition', related_name='visit_link_condition')
    url = CharField(max_length=200)  # URL для посещения


# ------ Конец условий выполнения задач ------

# ------ Условия видимости задач ------
class Visibility(Model):
    id = BigIntField(pk=True)
    type = CharEnumField(enum_type=VisibilityType, max_length=50)


class AllwaysVisibility(Model):
    id = BigIntField(pk=True)
    visibility = OneToOneField('api.Visibility', related_name='allways_visibility')


class RankVisibility(Model):
    id = BigIntField(pk=True)
    visibility = OneToOneField('api.Visibility', related_name='rank_visibility')
    rank = ForeignKeyField('api.Rank', on_delete=OnDelete.CASCADE, related_name='rank_visibilities')


# ------ Конец условий видимости задач ------

class InstantReward(Model):
    id = BigIntField(pk=True)
    tokens = BigIntField(default=0)
    inspirations = BigIntField(default=0)
    replenishments = BigIntField(default=0)


# Задачи приложения
class Task(Model):
    id = BigIntField(pk=True)
    description = CharField(max_length=200)  # Название задачи
    reward = OneToOneField('api.InstantReward', related_name='tasks')
    condition = OneToOneField('api.Condition', related_name='tasks')  # Условие выполнения
    visibility = OneToOneField('api.Visibility', related_name='tasks')  # Условие видимости


# Задача, которую берет пользователь
class UserTask(Model):
    id = BigIntField(pk=True)
    user = ForeignKeyField('api.User', on_delete=OnDelete.CASCADE, related_name='user_tasks')  # ID пользователя
    task = ForeignKeyField('api.Task', on_delete=OnDelete.CASCADE, related_name='user_tasks')  # Связь с задачей
    create_time = DatetimeField(auto_now_add=True)  # Время создания
    completed_time = DatetimeField(null=True)  # Время выполнения (может быть пустым)

    @property
    def is_completed(self):
        return self.completed_time is not None


Reward_Pydantic = pydantic_model_creator(Reward, name="Reward")
Reward_Pydantic_List = pydantic_queryset_creator(Reward, name="RewardList")
