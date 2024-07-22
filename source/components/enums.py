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
