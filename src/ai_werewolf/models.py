from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Role(str, Enum):
    WEREWOLF = "werewolf"
    SEER = "seer"
    VILLAGER = "villager"


class Phase(str, Enum):
    SETUP = "setup"
    NIGHT_WEREWOLF = "night_werewolf"
    NIGHT_SEER = "night_seer"
    RESOLVE_NIGHT = "resolve_night"
    DAY_SPEAK = "day_speak"
    DAY_VOTE = "day_vote"
    RESOLVE_VOTE = "resolve_vote"
    CHECK_WIN = "check_win"
    END = "end"


class Player(BaseModel):
    id: str
    name: str
    role: Role
    alive: bool = True


class Speech(BaseModel):
    day: int
    player_id: str
    content: str


class VoteRecord(BaseModel):
    day: int
    voter_id: str
    target_id: str


# --- LLM structured outputs ---


class KillChoice(BaseModel):
    """狼人夜间刀人。"""

    target_id: str = Field(description="要击杀的存活玩家 id，不能是狼人自己人")
    reason: str = Field(description="简短理由，仅狼人可见")


class SeerCheckChoice(BaseModel):
    """预言家夜间验人。"""

    target_id: str = Field(description="要查验的存活玩家 id，不能是自己")
    reason: str = Field(description="简短理由，仅预言家可见")


class SpeechChoice(BaseModel):
    """白天发言。"""

    content: str = Field(description="公开发言内容，1～3 句话")


class VoteChoice(BaseModel):
    """白天投票。"""

    target_id: str = Field(description="要放逐的存活玩家 id，不能投自己")
    reason: str = Field(description="公开可复述的简短理由")


Winner = Literal["werewolf", "villager"] | None
