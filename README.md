# AI 狼人杀（最小规则骨架）

用 LangGraph 编排的 6 人局多 Agent 狼人杀骨架：

- 配置：2 狼人 / 1 预言家 / 3 村民
- 夜晚：狼人刀一人 → 预言家验一人 → 引擎结算
- 白天：存活玩家各发言 1 次 → 投票 → 引擎结算（平票无人出局）
- 死亡公开身份；胜负由代码判定，不交给 LLM

## 设计要点

| 模块 | 职责 |
|------|------|
| `engine.py` | 发牌、校验目标、结算刀人/投票、胜负判定（确定性） |
| `views.py` | 按角色过滤可见信息，防止串台 |
| `agents.py` | LLM structured output；`--dry-run` 时用占位决策 |
| `nodes.py` / `graph.py` | LangGraph 节点与阶段流转 |

## 快速开始

```bash
cd ai_werewolf
uv sync

# 不调 LLM，先验证图能否跑通
uv run python -m ai_werewolf.main --dry-run --seed 42

# 调用 DeepSeek（读取本目录 .env，或复用 ../langchain_study/.env）
cp .env.example .env   # 填入 DEEPSEEK_API_KEY
uv run python -m ai_werewolf.main --seed 42
```

## 图结构（简图）

```
START → 夜刀 → 夜验 → 结算夜 → 胜负?
                      ├─ END
                      └─ 发言循环 → 投票循环 → 结算票 → 胜负?
                                           ├─ END
                                           └─ 下一夜
```

## 后续可扩展

- 女巫 / 猎人等角色（继续把规则放进 `engine`）
- 狼人夜间多轮协商子图
- checkpointer 落盘整局复盘
- 不同模型/温度区分阵营风格
