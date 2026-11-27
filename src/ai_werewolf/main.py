from __future__ import annotations

import argparse
import json

from ai_werewolf.engine import create_players, role_label
from ai_werewolf.graph import build_graph
from ai_werewolf.models import Phase
from ai_werewolf.nodes import reveal_roles_line


def initial_state(*, seed: int | None, dry_run: bool) -> dict:
    players = create_players(seed=seed)
    return {
        "players": players,
        "phase": Phase.SETUP.value,
        "day": 1,
        "public_log": ["游戏开始：6人局（2狼 / 1预言家 / 3村民）。死亡只公布号数，身份终局揭晓。"],
        "speeches": [],
        "seer_log": [],
        "wolf_log": [],
        "pending_kill": None,
        "pending_seer_check": None,
        "speak_queue": [],
        "current_speaker": None,
        "vote_queue": [],
        "current_voter": None,
        "votes": {},
        "vote_history": [],
        "winner": None,
        "dry_run": dry_run,
    }


def _emit(line: str = "") -> None:
    print(line, flush=True)


def print_recap(final: dict) -> None:
    _emit("\n========== 复盘 ==========")
    _emit(reveal_roles_line(final))
    if final.get("seer_log"):
        _emit("预言家私有：" + " | ".join(final["seer_log"]))
    if final.get("wolf_log"):
        _emit("狼人私有：" + " | ".join(final["wolf_log"]))
    winner = final.get("winner")
    if winner == "werewolf":
        _emit("结果：狼人胜利")
    elif winner == "villager":
        _emit("结果：好人胜利")
    else:
        _emit("结果：未分胜负（异常结束）")


def run_stream(app, state: dict) -> dict:
    """按节点推进并即时刷出公开日志。"""
    _emit("\n========== 对局进行中 ==========")
    for line in state.get("public_log") or []:
        _emit(line)

    printed = len(state.get("public_log") or [])
    final = state
    config = {"recursion_limit": 200}
    for values in app.stream(state, config=config, stream_mode="values"):
        final = values
        log = values.get("public_log") or []
        for line in log[printed:]:
            _emit(line)
        printed = len(log)
    return final


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AI 狼人杀最小骨架")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="不调用 LLM，用随机/占位决策跑通图",
    )
    parser.add_argument("--seed", type=int, default=42, help="身份发牌随机种子")
    parser.add_argument(
        "--dump-json",
        action="store_true",
        help="结束后额外打印可序列化摘要",
    )
    args = parser.parse_args(argv)

    state = initial_state(seed=args.seed, dry_run=args.dry_run)
    _emit("开局身份（调试可见，正式对局应对观众隐藏）：")
    for p in state["players"].values():
        _emit(f"  {p.id}号 {p.name}: {role_label(p.role)}")

    app = build_graph()
    final = run_stream(app, state)
    print_recap(final)

    if args.dump_json:
        summary = {
            "winner": final.get("winner"),
            "day": final.get("day"),
            "public_log": final.get("public_log"),
            "roles": {
                pid: {"role": p.role.value, "alive": p.alive}
                for pid, p in final["players"].items()
            },
        }
        _emit("\n" + json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
