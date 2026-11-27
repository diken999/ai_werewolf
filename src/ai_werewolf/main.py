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
        "public_log": ["游戏开始：6人局（2狼 / 1预言家 / 3村民）。死亡公开身份。"],
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


def print_result(final: dict) -> None:
    print("\n========== 公开战报 ==========")
    for line in final["public_log"]:
        print(line)
    print("\n========== 复盘 ==========")
    print(reveal_roles_line(final))
    if final.get("seer_log"):
        print("预言家私有：", " | ".join(final["seer_log"]))
    if final.get("wolf_log"):
        print("狼人私有：", " | ".join(final["wolf_log"]))
    winner = final.get("winner")
    if winner == "werewolf":
        print("结果：狼人胜利")
    elif winner == "villager":
        print("结果：好人胜利")
    else:
        print("结果：未分胜负（异常结束）")


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
    print("开局身份（调试可见，正式对局应对观众隐藏）：")
    for p in state["players"].values():
        print(f"  {p.id}号 {p.name}: {role_label(p.role)}")

    app = build_graph()
    # 防止异常死循环；正常 6 人局远小于此
    final = app.invoke(state, config={"recursion_limit": 200})
    print_result(final)

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
        print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
