from starlette.requests import Request
from starlette_admin import IntegerField, StringField, FloatField, DateTimeField, BooleanField, EnumField, ImageField, \
    CountryField
from models import RankName, RewardType, QuestionStatus
from admin.tortoise_view import TortoiseModelView


class RankView(TortoiseModelView):
    identity = "rank"
    name = "Rank"
    label = "Ранги"
    icon = "fa fa-trophy"
    pk_attr = "id"
    fields = (
        IntegerField("id"),
        StringField("league"),
        EnumField("name", enum=RankName),
        FloatField("press_force"),
        FloatField("max_energy"),
        FloatField("energy_per_sec"),
        IntegerField("price")
    )


class UserView(TortoiseModelView):
    identity = "user"
    name = "User"
    label = "Основная информация"
    icon = "fa fa-user"
    pk_attr = "id"
    fields = (
        IntegerField("id", label="Chat ID"),
        IntegerField("rank_id", label="RANK"),
        StringField("username"),
        StringField("country"),
        StringField("referral_code")
    )

    def can_create(self, request: Request) -> bool: return False


class ActivityView(TortoiseModelView):
    identity = "user-activity"
    name = "Activity"
    label = "Активность"
    icon = "fa fa-calendar"
    pk_attr = "id"
    fields = (
        IntegerField("user_id", label="Chat ID"),
        StringField("reg_date"),
        IntegerField("active_days"),
        BooleanField("is_active_mining"),
        DateTimeField("last_login_date"),
        DateTimeField("last_daily_reward"),
        DateTimeField("last_sync_energy"),
        DateTimeField("next_inspiration"),
        DateTimeField("next_mining")
    )

    def can_create(self, request: Request) -> bool: return False
    def can_delete(self, request: Request) -> bool: return False


class StatsView(TortoiseModelView):
    identity = "user-stats"
    name = "Stats"
    label = "Статистика"
    icon = "fa fa-area-chart"
    pk_attr = "id"
    fields = (
        IntegerField("user_id", label="Chat ID"),
        IntegerField("coins"),
        IntegerField("energy"),
        IntegerField("earned_week_coins"),
        IntegerField("invited_friends"),
        IntegerField("inspirations"),
        IntegerField("replenishments"),
    )

    def can_create(self, request: Request) -> bool: return False
    def can_delete(self, request: Request) -> bool: return False


class RewardsView(TortoiseModelView):
    identity = "user-rewards"
    name = "Rewards"
    label = "Награды"
    icon = "fa fa-gift"
    pk_attr = "id"
    fields = (
        IntegerField("user_id", label="Chat ID"),
        EnumField("type", enum=RewardType),
        IntegerField("amount"),
        IntegerField("inspirations"),
        IntegerField("replenishments")
    )


class QuestionsView(TortoiseModelView):
    identity = "user-questions"
    name = "Questions"
    label = "Вопросы"
    icon = "fa fa-commenting"
    pk_attr = "id"
    fields = (
        IntegerField("user_id", label="Chat ID"),
        DateTimeField("time_sent"),
        StringField("u_text", label="Text"),
        StringField("answer"),
        EnumField("status", enum=QuestionStatus),
    )

    def can_create(self, request: Request) -> bool: return False
