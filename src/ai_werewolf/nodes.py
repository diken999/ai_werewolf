from __future__ import annotations

from ai_werewolf.agents import (
    choose_seer_check,
    choose_speech,
    choose_vote,
    choose_werewolf_kill,
)
from ai_werewolf.engine import (
    alive_ids,
    check_winner,
    find_seer,
    kill_player,
    resolve_night_kill,
    role_label,
    tally_votes,
    wolf_ids,
)
from ai_werewolf.models import Phase, Speech, VoteRecord
from ai_werewolf.state import GameState

# 狼人行动
def night_werewolf_node(state: GameState) -> dict:
    choice = choose_werewolf_kill(state)
    return {
        "phase": Phase.NIGHT_WEREWOLF.value,
        "pending_kill": choice.target_id,
        "wolf_log": [f"第{state['day']}夜刀玩家{choice.target_id}：{choice.reason}"],
        "public_log": [f"=== 第 {state['day']} 夜 ===", "狼人正在行动…"],
    }

# 预言家行动
def night_seer_node(state: GameState) -> dict:
    seer = find_seer(state["players"])
    if seer is None or not seer.alive:
        # 不向公开日志暴露预言家是否仍存活
        return {
            "phase": Phase.NIGHT_SEER.value,
            "pending_seer_check": None,
        }

    choice = choose_seer_check(state, seer.id)
    target = state["players"][choice.target_id]
    camp = "狼人" if target.role.value == "werewolf" else "好人"
    return {
        "phase": Phase.NIGHT_SEER.value,
        "pending_seer_check": choice.target_id,
        "seer_log": [
            f"第{state['day']}夜查验玩家{choice.target_id} → {camp}（{choice.reason}）"
        ],
    }

# 夜间行动结算
def resolve_night_node(state: GameState) -> dict:
    pending = state.get("pending_kill")
    players, log = resolve_night_kill(state["players"], pending)
    return {
        "players": players,
        "phase": Phase.RESOLVE_NIGHT.value,
        "pending_kill": None,
        "pending_seer_check": None,
        "public_log": [log],
    }

# 准备白天发言
def prepare_day_node(state: GameState) -> dict:
    queue = alive_ids(state["players"])
    return {
        "phase": Phase.DAY_SPEAK.value,
        "speak_queue": queue,
        "current_speaker": queue[0] if queue else None,
        "votes": {},
        "vote_queue": [],
        "current_voter": None,
        "public_log": [f"=== 第 {state['day']} 天白天：按座位依次发言 ==="],
    }

# 白天发言
def speak_node(state: GameState) -> dict:
    speaker = state["current_speaker"]
    if speaker is None:
        return {}

    choice = choose_speech(state, speaker)
    remaining = list(state["speak_queue"][1:])
    next_speaker = remaining[0] if remaining else None
    return {
        "speeches": [Speech(day=state["day"], player_id=speaker, content=choice.content)],
        "public_log": [f"{speaker}号发言：{choice.content}"],
        "speak_queue": remaining,
        "current_speaker": next_speaker,
    }

# 准备投票
def prepare_vote_node(state: GameState) -> dict:
    queue = alive_ids(state["players"])
    return {
        "phase": Phase.DAY_VOTE.value,
        "vote_queue": queue,
        "current_voter": queue[0] if queue else None,
        "votes": {},
        "public_log": ["=== 开始投票 ==="],
    }

# 投票
def vote_node(state: GameState) -> dict:
    voter = state["current_voter"]
    if voter is None:
        return {}

    choice = choose_vote(state, voter)
    remaining = list(state["vote_queue"][1:])
    next_voter = remaining[0] if remaining else None
    votes = {**(state.get("votes") or {}), voter: choice.target_id}
    return {
        "votes": votes,
        "vote_history": [
            VoteRecord(day=state["day"], voter_id=voter, target_id=choice.target_id)
        ],
        "public_log": [f"{voter}号 → {choice.target_id}号（{choice.reason}）"],
        "vote_queue": remaining,
        "current_voter": next_voter,
    }

# 投票结算
def resolve_vote_node(state: GameState) -> dict:
    victim, summary = tally_votes(state["players"], state.get("votes") or {})
    players = state["players"]
    logs = [summary]
    if victim:
        players = kill_player(players, victim)
        # 死亡只公布号数，身份仅在终局复盘揭晓
        logs.append(f"玩家{victim} 出局。")
    return {
        "players": players,
        "phase": Phase.RESOLVE_VOTE.value,
        "public_log": logs,
        "votes": {},
    }

# 检查胜负
def _end_if_winner(state: GameState) -> dict | None:
    winner = check_winner(state["players"])
    if not winner:
        return None
    label = "狼人阵营" if winner == "werewolf" else "好人阵营"
    return {
        "winner": winner,
        "phase": Phase.END.value,
        "public_log": [f"=== 游戏结束：{label}胜利 ==="],
    }

# 检查夜间胜负
def check_win_after_night_node(state: GameState) -> dict:
    ended = _end_if_winner(state)
    if ended:
        return ended
    return {
        "winner": None,
        "phase": Phase.CHECK_WIN.value,
        "public_log": [f"第 {state['day']} 夜结束，进入白天。"],
    }

# 检查投票胜负
def check_win_after_vote_node(state: GameState) -> dict:
    ended = _end_if_winner(state)
    if ended:
        return ended
    nxt = state["day"] + 1
    return {
        "winner": None,
        "phase": Phase.CHECK_WIN.value,
        "day": nxt,
        "public_log": [f"胜负未分，进入第 {nxt} 夜。"],
    }

# 揭晓身份
def reveal_roles_line(state: GameState) -> str:
    parts = [
        f"{p.id}号={role_label(p.role)}{'💀' if not p.alive else ''}"
        for p in state["players"].values()
    ]
    wolves = ",".join(wolf_ids(state["players"], only_alive=False))
    return f"身份表：{'; '.join(parts)}｜狼:{wolves}"
