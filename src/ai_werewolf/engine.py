from __future__ import annotations

import random
from collections import Counter

from ai_werewolf.models import Phase, Player, Role, Winner


ROLE_SETUP_6 = (
    Role.WEREWOLF,
    Role.WEREWOLF,
    Role.SEER,
    Role.VILLAGER,
    Role.VILLAGER,
    Role.VILLAGER,
)


def create_players(seed: int | None = None) -> dict[str, Player]:
    """固定 6 人局，随机发身份。"""
    rng = random.Random(seed)
    roles = list(ROLE_SETUP_6)
    rng.shuffle(roles)
    players: dict[str, Player] = {}
    for i, role in enumerate(roles, start=1):
        pid = str(i)
        players[pid] = Player(id=pid, name=f"玩家{i}", role=role)
    return players


def alive_players(players: dict[str, Player]) -> list[Player]:
    return [p for p in players.values() if p.alive]


def alive_ids(players: dict[str, Player]) -> list[str]:
    return [p.id for p in alive_players(players)]


def wolf_ids(players: dict[str, Player], *, only_alive: bool = True) -> list[str]:
    return [
        p.id
        for p in players.values()
        if p.role == Role.WEREWOLF and (p.alive if only_alive else True)
    ]


def find_seer(players: dict[str, Player]) -> Player | None:
    for p in players.values():
        if p.role == Role.SEER:
            return p
    return None


def kill_player(players: dict[str, Player], target_id: str) -> dict[str, Player]:
    updated = dict(players)
    target = updated[target_id].model_copy(update={"alive": False})
    updated[target_id] = target
    return updated


def validate_target(
    players: dict[str, Player],
    target_id: str,
    *,
    actor_id: str | None = None,
    forbid_wolves: bool = False,
) -> str | None:
    """合法则返回 None，否则返回错误信息。"""
    if target_id not in players:
        return f"未知玩家: {target_id}"
    if not players[target_id].alive:
        return f"玩家{target_id} 已死亡"
    if actor_id is not None and target_id == actor_id:
        return "不能选择自己"
    if forbid_wolves and players[target_id].role == Role.WEREWOLF:
        return "不能刀自己人"
    return None


def resolve_night_kill(
    players: dict[str, Player], pending_kill: str | None
) -> tuple[dict[str, Player], str]:
    if not pending_kill:
        return players, "夜晚无人被刀（无效行动），平安夜。"
    err = validate_target(players, pending_kill, forbid_wolves=True)
    if err:
        # 非法刀人时兜底：随机刀一名村民阵营
        candidates = [
            p.id
            for p in alive_players(players)
            if p.role != Role.WEREWOLF
        ]
        if not candidates:
            return players, f"夜晚刀人失败（{err}），且无合法目标。"
        pending_kill = random.choice(candidates)
        log = f"夜晚刀人非法（{err}），系统改刀玩家{pending_kill}。"
    else:
        log = f"天亮了：玩家{pending_kill} 被狼人杀害。"
    return kill_player(players, pending_kill), log


def tally_votes(
    players: dict[str, Player], votes: dict[str, str]
) -> tuple[str | None, str]:
    """返回 (放逐目标或 None, 公开说明)。平票则放逐失败。"""
    alive = set(alive_ids(players))
    valid = {
        voter: target
        for voter, target in votes.items()
        if voter in alive and target in alive and voter != target
    }
    if not valid:
        return None, "投票无效，今日无人出局。"

    counts = Counter(valid.values())
    top = counts.most_common()
    if len(top) >= 2 and top[0][1] == top[1][1]:
        detail = ", ".join(f"玩家{t}:{c}票" for t, c in top)
        return None, f"平票（{detail}），今日无人出局。"

    victim, n = top[0]
    detail = ", ".join(f"玩家{t}:{c}票" for t, c in top)
    return victim, f"投票结果：{detail}。玩家{victim} 以 {n} 票出局。"


def check_winner(players: dict[str, Player]) -> Winner:
    wolves = [p for p in alive_players(players) if p.role == Role.WEREWOLF]
    good = [p for p in alive_players(players) if p.role != Role.WEREWOLF]
    if not wolves:
        return "villager"
    if len(wolves) >= len(good):
        return "werewolf"
    return None


def role_label(role: Role) -> str:
    return {
        Role.WEREWOLF: "狼人",
        Role.SEER: "预言家",
        Role.VILLAGER: "村民",
    }[role]


def public_role_of_dead(player: Player) -> str:
    """死亡后公开身份（最小规则：死亡即爆身份，便于复盘）。"""
    return role_label(player.role)
