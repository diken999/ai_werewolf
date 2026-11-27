from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# 角色
class Role(str, Enum):
    WEREWOLF = "werewolf"
    SEER = "seer"
    VILLAGER = "villager"

# 游戏阶段
class Phase(str, Enum):
    # 初始化
    SETUP = "setup"
    # 夜间狼人行动
    NIGHT_WEREWOLF = "night_werewolf"
    # 夜间预言家行动
    NIGHT_SEER = "night_seer"
    # 夜间行动结算
    RESOLVE_NIGHT = "resolve_night"
    # 白天发言
    DAY_SPEAK = "day_speak"
    # 白天投票
    DAY_VOTE = "day_vote"
    # 投票结算
    RESOLVE_VOTE = "resolve_vote"
    # 检查胜负
    CHECK_WIN = "check_win"
    # 结束
    END = "end"

# 玩家
class Player(BaseModel):
    id: str
    name: str
    role: Role
    alive: bool = True

# 发言
class Speech(BaseModel):
    day: int
    player_id: str
    content: str

# 投票记录
class VoteRecord(BaseModel):
    day: int
    voter_id: str
    target_id: str


# --- LLM structured outputs ---

# 狼人夜间刀人
class KillChoice(BaseModel):
    """狼人夜间刀人。"""

    target_id: str = Field(description="要击杀的存活玩家 id，不能是狼人自己人")
    reason: str = Field(description="简短理由，仅狼人可见")

# 预言家夜间验人
class SeerCheckChoice(BaseModel):
    """预言家夜间验人。"""

    target_id: str = Field(description="要查验的存活玩家 id，不能是自己")
    reason: str = Field(description="简短理由，仅预言家可见")

# 白天发言
class SpeechChoice(BaseModel):
    """白天发言。"""

    content: str = Field(description="公开发言内容，1～3 句话")

# 白天投票
class VoteChoice(BaseModel):
    """白天投票。"""

    target_id: str = Field(description="要放逐的存活玩家 id，不能投自己")
    reason: str = Field(description="公开可复述的简短理由")

# 胜负
Winner = Literal["werewolf", "villager"] | None
