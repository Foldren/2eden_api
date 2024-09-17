from enum import Enum


class RankName(str, Enum):
    ACOLYTE = "Acolyte"
    DEACON = "Deacon"
    PRIEST = "Priest"
    ARCHDEACON = "Archdeacon"
    BISHOP = "Bishop"
    ARCHBISHOP = "Archbishop"
    METROPOLITAN = "Metropolitan"
    CARDINAL = "Cardinal"
    PATRIARCH = "Patriarch"
    MASTER = "Master"
    POPE = "Pope"


class RewardTypeName(str, Enum):
    LAUNCHES_SERIES = "launches_series"
    INVITE_FRIENDS = "invite_friends"
    LEADERBOARD = "leaderboard"
    TASK = "task"
    REFERRAL = "referral"
    AI_QUESTION = "ai_question"


class QuestionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    HAVE_ANSWER = "have_answer"
    RECEIVED_REWARD = "received_reward"


# Перечисление для типов условий выполнения задач
class ConditionType(str, Enum):
    TG_CHANNEL = "tg_channel"
    VISIT_LINK = "visit_link"


# Перечисление для типов условий видимости задач
class VisibilityType(str, Enum):
    ALLWAYS = "allways"
    RANK = "rank"
    
