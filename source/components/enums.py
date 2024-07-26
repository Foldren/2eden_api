from enum import Enum


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


class RewardTypeName(str, Enum):
    launches_series = "launches_series"
    invite_friends = "invite_friends"
    leaderboard = "leaderboard"
    task = "task"


# Перечисление для типов условий выполнения задач
class ConditionType(str, Enum):
    TG_CHANNEL = "tg_channel"
    VISIT_LINK = "visit_link"


# Перечисление для типов условий видимости задач
class VisibilityType(str, Enum):
    ALLWAYS = "allways"
    RANK = "rank"
    
