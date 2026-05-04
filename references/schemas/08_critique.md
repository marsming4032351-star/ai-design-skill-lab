# Schema · Critique

> Critique = 一次 design-critic 跑出的"评分 + 决策"。**不可变**。
> Critique 不修改 Plan 或 Asset；它只产出新的 Critique 实体并通过 `decision` 触发下游动作。
> Plan.status 的转移由 design-critic 在写完 Critique 之后单独执行（可 `--no-update-plan` 跳过）。

## 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `id` | string | ✓ | `crt_<target_id_short>_<yyyymmdd_hhmmss>_<rand4>` |
| `type` | const | ✓ | 固定为 `critique` |
| `schema_version` | string | ✓ | 当前 `1.0` |
| `created_at` | ISO8601 | ✓ | |
| `updated_at` | ISO8601 | ✓ | |
| `status` | enum | ✓ | `active` / `deprecated`（Critique 是不可变实体，类比 Run） |
| `created_by` | string | ✓ | `skill:design-critic` |
| `source_run_id` | string | ✓ | 产生此 Critique 的 critic run_id |
| `tags` | string[] | | |
| **专属字段** | | | |
| `target_type` | enum | ✓ | `plan_direction` / `plan` / `asset`（P1 仅支持 plan_direction） |
| `target_plan_id` | string | ✓ | 被评审的 Plan id |
| `target_direction_id` | string \| null | | 当 target_type=plan_direction 时必填 |
| `project_id` | string | ✓ | |
| `rubric_id` | string | ✓ | 评分用的 Rule id |
| `rubric_version` | string | ✓ | Rule version 快照 |
| `prompt_id` | string \| null | | 若用 LLM 评审则填 |
| `prompt_version` | string \| null | | |
| `prompt_inputs_hash` | string \| null | | |
| `scores` | object[] | ✓ | 每个维度的得分（结构见下） |
| `weighted_score` | float | ✓ | 加权总分 |
| `decision` | enum | ✓ | `pass` / `revise` / `fail` |
| `decision_rationale` | string | ✓ | 决策理由（≤ 500 字符） |
| `strengths` | string[] | | 亮点 |
| `weaknesses` | string[] | | 短板 |
| `actionable_feedback` | string[] | | 可执行修改建议 |
| `llm_mode` | enum | ✓ | `dry-run` / `hook` / `live` |
| `replaces` | string \| null | | 上一版 Critique（同一 target 多次评） |
| `replaced_by` | string \| null | | |

### scores 子结构

```yaml
scores:
  - dimension_id: "strategy_fit"        # 来自 rubric.body.dimensions[*].id
    label: "战略契合度"                 # 冗余字段，便于阅读
    score: 4                            # int，落在 rubric 定义的 scale 内
    weight: 0.20                        # 来自 rubric 定义
    rationale: "..."                    # 单维度理由
```

### decision 决策规则（来自 rubric）

rubric 的 `engine: weighted` 在 body 中定义：
```yaml
pass_threshold: 3.5
fail_threshold: 2.5
decision_rule: |
  weighted_score >= pass_threshold AND no_dimension < 2  → pass
  weighted_score < fail_threshold OR any_dimension == 1  → fail
  else                                                    → revise
```
`design-critic` 应用此规则，把结果写到 `decision` 字段。

## YAML 模板

```yaml
---
id: "crt_dir_001_20260504_165500_abcd"
type: critique
schema_version: "1.0"
created_at: "2026-05-04T16:55:00Z"
updated_at: "2026-05-04T16:55:00Z"
status: active
created_by: "skill:design-critic"
source_run_id: "run_critic_20260504_165500_abcd"
tags:
  - design-critic
  - concept

target_type: plan_direction
target_plan_id: "pln_acme_q4_campaign_concept_20260504_153012_b8c7"
target_direction_id: "dir_001"
project_id: "prj_acme_q4_campaign"
rubric_id: "rul_score_concept_direction"
rubric_version: "1.0.0"
prompt_id: "prm_critic_concept"
prompt_version: "1.0.0"
prompt_inputs_hash: "..."

scores:
  - dimension_id: "strategy_fit"
    label: "战略契合度"
    score: 4
    weight: 0.25
    rationale: "..."
  # 其他维度

weighted_score: 3.85
decision: pass
decision_rationale: "weighted_score 3.85 >= pass_threshold 3.5；无维度 < 2"

strengths:
  - "差异化清晰"
weaknesses:
  - "缺乏对社媒分发版本的考虑"
actionable_feedback:
  - "补充 social_banner 版本草图"

llm_mode: dry-run
replaces: null
replaced_by: null
---

# Critique · dir_001 · pass

## Decision
pass (weighted_score 3.85)

## Scores
（渲染 scores 表）
```

## 校验规则

```
required: 全部上面标 ✓ 的字段
constraints:
  - id MUST match pattern: ^crt_[a-z0-9_]+_\d{8}_\d{6}_[a-f0-9]{4}$
  - target_type in {plan_direction, plan, asset}
  - if target_type == plan_direction: target_direction_id MUST be set
  - decision in {pass, revise, fail}
  - len(decision_rationale) <= 500
  - len(scores) >= 1
  - each score.dimension_id MUST be unique within this critique
  - each score.score MUST be integer (P1 简化)
  - sum(weights) MUST be approximately 1.0 (±0.01)
  - weighted_score MUST equal sum(score * weight) within ±0.01
  - status in {active, deprecated}
  - llm_mode in {dry-run, hook, live}
  - if prompt_id: prompt_version + prompt_inputs_hash MUST also be set
```

## 状态生命周期

```
active (写出后默认)
   ↓ 人工或新 critique 复评
deprecated  (作为历史保留)
```

不可变性：写出后禁止修改 scores / decision / weighted_score。重新评审 = 新建 critique + replaces。

## 反模式

- ❌ 修改 active critique 的 scores / decision → 必须新建并 replaces
- ❌ scores 的 dimension_id 与 rubric 不一致 → schema 校验拒绝
- ❌ weighted_score 与 sum(score * weight) 不符 → 校验拒绝
- ❌ critic 只读 Plan，禁止修改 Plan.directions → critic 是评审者，不是编辑者
- ❌ Plan.status 转移由 critic 触发但**写在 critic skill 代码里**，禁止写在 Critique 实体内 → 实体只描述事实，状态转移是动作
