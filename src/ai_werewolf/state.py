from __future__ import annotations

import operator
from typing import Annotated, NotRequired, TypedDict

from ai_werewolf.models import Player, Speech, VoteRecord, Winner


class GameState(TypedDict):
    """整局共享状态。私有信息不要直接塞进发给村民的 prompt。"""

    players: dict[str, Player]
    phase: str
    day: int

    # 公开日志 / 发言（所有人可见）
    public_log: Annotated[list[str], operator.add]
    speeches: Annotated[list[Speech], operator.add]

    # 私有日志：节点里按角色过滤后再给 LLM
    seer_log: Annotated[list[str], operator.add]
    wolf_log: Annotated[list[str], operator.add]

    # 夜间行动（引擎结算用）
    pending_kill: str | None
    pending_seer_check: str | None

    # 白天流程（votes 整表替换，便于每日清空）
    speak_queue: list[str]
    current_speaker: str | None
    vote_queue: list[str]
    current_voter: str | None
    votes: dict[str, str]
    vote_history: Annotated[list[VoteRecord], operator.add]

    winner: Winner
    dry_run: NotRequired[bool]
