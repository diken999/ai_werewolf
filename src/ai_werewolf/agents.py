from __future__ import annotations

import random

from ai_werewolf.engine import alive_ids, validate_target, wolf_ids
from ai_werewolf.llm import structured_invoke
from ai_werewolf.models import (
    KillChoice,
    Role,
    SeerCheckChoice,
    SpeechChoice,
    VoteChoice,
)
from ai_werewolf.state import GameState
from ai_werewolf.views import build_player_view


def _rng(state: GameState) -> random.Random:
    # dry-run 下可复现一点：用天数+存活数做种子
    return random.Random(state["day"] * 100 + len(alive_ids(state["players"])))

# 狼人选择击杀目标
def choose_werewolf_kill(state: GameState) -> KillChoice:
    players = state["players"]
    wolves = set(wolf_ids(players))
    candidates = [pid for pid in alive_ids(players) if pid not in wolves]
    if state.get("dry_run"):
        target = _rng(state).choice(candidates)
        return KillChoice(target_id=target, reason="dry-run 随机刀人")

    # 用第一名存活狼人作为「发言代表」读私有视图
    actor = next(pid for pid in alive_ids(players) if pid in wolves)
    view = build_player_view(state, actor)
    result = structured_invoke(
        KillChoice,
        system=(
            "你是狼人阵营的夜间决策者。只能从非狼人存活玩家中选一个击杀。"
            "只输出结构化字段。"
        ),
        user=f"{view}\n\n请选择今晚击杀目标。候选 id：{candidates}",
    )
    if validate_target(players, result.target_id, forbid_wolves=True):
        result = KillChoice(target_id=_rng(state).choice(candidates), reason="非法目标，改随机")
    return result

# 预言家选择查验目标
def choose_seer_check(state: GameState, seer_id: str) -> SeerCheckChoice:
    players = state["players"]
    candidates = [pid for pid in alive_ids(players) if pid != seer_id]
    if state.get("dry_run"):
        target = _rng(state).choice(candidates)
        return SeerCheckChoice(target_id=target, reason="dry-run 随机验人")

    view = build_player_view(state, seer_id)
    result = structured_invoke(
        SeerCheckChoice,
        system="你是预言家。每晚查验一名其他存活玩家的阵营。只输出结构化字段。",
        user=f"{view}\n\n请选择今晚查验目标。候选 id：{candidates}",
    )
    if validate_target(players, result.target_id, actor_id=seer_id):
        result = SeerCheckChoice(
            target_id=_rng(state).choice(candidates), reason="非法目标，改随机"
        )
    return result

# 白天发言
def choose_speech(state: GameState, player_id: str) -> SpeechChoice:
    if state.get("dry_run"):
        return SpeechChoice(
            content=f"（dry-run）我是{player_id}号。听完发言后我会认真投，先听听其他人的逻辑。"
        )

    view = build_player_view(state, player_id)
    role = state["players"][player_id].role
    if role == Role.WEREWOLF:
        tip = "你是狼人，要伪装成好人，可适当带节奏，但不要暴露队友。"
    elif role == Role.SEER:
        tip = "你是预言家，可选择性公开或隐藏验人结果，注意被狼人冲的风险。"
    else:
        tip = "你是村民，根据发言找狼，不要编造夜间信息。"

    return structured_invoke(
        SpeechChoice,
        system=f"你在玩狼人杀。{tip}发言简短，1～3 句。只输出结构化字段。",
        user=f"{view}\n\n请发表今天的公开发言。",
    )

# 投票
def choose_vote(state: GameState, voter_id: str) -> VoteChoice:
    players = state["players"]
    candidates = [pid for pid in alive_ids(players) if pid != voter_id]
    if state.get("dry_run"):
        target = _rng(state).choice(candidates)
        return VoteChoice(target_id=target, reason="dry-run 随机投票")

    view = build_player_view(state, voter_id)
    result = structured_invoke(
        VoteChoice,
        system="你在投票放逐一名玩家。不能投自己。只输出结构化字段。",
        user=f"{view}\n\n请投票。候选 id：{candidates}",
    )
    if validate_target(players, result.target_id, actor_id=voter_id):
        result = VoteChoice(
            target_id=_rng(state).choice(candidates), reason="非法目标，改随机"
        )
    return result
