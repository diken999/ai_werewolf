from __future__ import annotations

from ai_werewolf.engine import alive_players, role_label, wolf_ids
from ai_werewolf.models import Player, Role, Speech
from ai_werewolf.state import GameState


def _alive_summary(players: dict[str, Player]) -> str:
    return "、".join(f"{p.name}(id={p.id})" for p in alive_players(players))


def _recent_speeches(speeches: list[Speech], day: int) -> str:
    today = [s for s in speeches if s.day == day]
    if not today:
        return "（尚无发言）"
    return "\n".join(f"- {s.player_id}号：{s.content}" for s in today)


def build_player_view(state: GameState, player_id: str) -> str:
    """按身份过滤可见信息，防止串台。"""
    players = state["players"]
    me = players[player_id]
    lines = [
        f"你是 {me.name}（id={me.id}），身份：{role_label(me.role)}。",
        f"当前是第 {state['day']} 天，阶段：{state['phase']}。",
        f"存活玩家：{_alive_summary(players)}。",
        "规则：死者只公布号数，身份不公开（除非你自己验到/本就知情）。",
        "",
        "【公开事件】",
        *(state["public_log"][-12:] or ["（暂无）"]),
        "",
        f"【第 {state['day']} 天发言】",
        _recent_speeches(state["speeches"], state["day"]),
    ]

    if me.role == Role.WEREWOLF:
        mates = [wid for wid in wolf_ids(players, only_alive=False) if wid != me.id]
        mate_names = "、".join(f"玩家{wid}" for wid in mates) or "无"
        lines += [
            "",
            "【狼人私有信息】",
            f"你的狼队友：{mate_names}",
            *(state["wolf_log"][-8:] or ["（暂无）"]),
        ]
    elif me.role == Role.SEER:
        lines += [
            "",
            "【预言家私有信息】",
            *(state["seer_log"][-8:] or ["（暂无）"]),
        ]
    else:
        lines += ["", "【注意】你看不到任何人的隐藏身份与夜间行动细节。"]


    return "\n".join(lines)
