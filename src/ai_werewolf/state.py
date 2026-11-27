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
    # 发言
    speeches: Annotated[list[Speech], operator.add]

    # 预言家私有日志
    seer_log: Annotated[list[str], operator.add]
    # 狼人私有日志
    wolf_log: Annotated[list[str], operator.add]

    # 夜间行动（引擎结算用）
    pending_kill: str | None
    # 夜间预言家行动（引擎结算用）
    pending_seer_check: str | None

    # 白天流程（votes 整表替换，便于每日清空）
    speak_queue: list[str]
    # 当前发言者
    current_speaker: str | None
    # 投票队列
    vote_queue: list[str]
    # 当前投票者
    current_voter: str | None
    # 投票记录
    votes: dict[str, str]
    # 投票记录
    vote_history: Annotated[list[VoteRecord], operator.add]
    # 胜负

    winner: Winner
    # 是否为 dry-run
    dry_run: NotRequired[bool]
