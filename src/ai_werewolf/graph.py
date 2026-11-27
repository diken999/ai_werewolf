from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from ai_werewolf.nodes import (
    check_win_after_night_node,
    check_win_after_vote_node,
    night_seer_node,
    night_werewolf_node,
    prepare_day_node,
    prepare_vote_node,
    resolve_night_node,
    resolve_vote_node,
    speak_node,
    vote_node,
)
from ai_werewolf.state import GameState

# 判断是否继续发言
def _route_after_speak(state: GameState) -> Literal["speak", "prepare_vote"]:
    return "speak" if state.get("current_speaker") else "prepare_vote"

# 判断是否继续投票
def _route_after_vote(state: GameState) -> Literal["vote", "resolve_vote"]:
    return "vote" if state.get("current_voter") else "resolve_vote"

# 判断是否继续夜间行动
def _route_after_check(state: GameState) -> Literal["night_werewolf", "__end__"]:
    return END if state.get("winner") else "night_werewolf"

# 判断是否继续白天发言
def _route_after_night_check(state: GameState) -> Literal["prepare_day", "__end__"]:
    return END if state.get("winner") else "prepare_day"

# 构建游戏图
def build_graph():
    """
    最小闭环：

    夜刀 → 夜验 → 结算夜晚 → 胜负?
         ├─ 结束
         └─ 白天依次发言 → 依次投票 → 结算放逐 → 胜负?
              ├─ 结束
              └─ 下一夜
    """
    g = StateGraph(GameState)

    g.add_node("night_werewolf", night_werewolf_node)
    g.add_node("night_seer", night_seer_node)
    g.add_node("resolve_night", resolve_night_node)
    g.add_node("check_win_after_night", check_win_after_night_node)
    g.add_node("prepare_day", prepare_day_node)
    g.add_node("speak", speak_node)
    g.add_node("prepare_vote", prepare_vote_node)
    g.add_node("vote", vote_node)
    g.add_node("resolve_vote", resolve_vote_node)
    g.add_node("check_win_after_vote", check_win_after_vote_node)

    g.add_edge(START, "night_werewolf")
    g.add_edge("night_werewolf", "night_seer")
    g.add_edge("night_seer", "resolve_night")
    g.add_edge("resolve_night", "check_win_after_night")
    g.add_conditional_edges(
        "check_win_after_night",
        _route_after_night_check,
        {"prepare_day": "prepare_day", END: END},
    )
    g.add_edge("prepare_day", "speak")
    g.add_conditional_edges(
        "speak",
        _route_after_speak,
        {"speak": "speak", "prepare_vote": "prepare_vote"},
    )
    g.add_edge("prepare_vote", "vote")
    g.add_conditional_edges(
        "vote",
        _route_after_vote,
        {"vote": "vote", "resolve_vote": "resolve_vote"},
    )
    g.add_edge("resolve_vote", "check_win_after_vote")
    g.add_conditional_edges(
        "check_win_after_vote",
        _route_after_check,
        {"night_werewolf": "night_werewolf", END: END},
    )

    return g.compile()
