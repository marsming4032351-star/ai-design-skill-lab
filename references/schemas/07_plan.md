# Schema · Plan

> Plan = 一次 design-run 产出的"概念方向 + 下一步行动"决策物。**半不可变**：Plan 一旦写出，
> frontmatter 中的 `directions` / `prompt_inputs_hash` 不可改；可改的只有 `status` 和
> 用户后续追加的 `decision_notes`。

## 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `id` | string | ✓ | `pln_<project_slug>_<stage>_<yyyymmdd_hhmmss>_<rand4>` |
| `type` | const | ✓ | 固定为 `plan` |
| `schema_version` | string | ✓ | 当前 `1.0` |
| `created_at` | ISO8601 | ✓ | |
| `updated_at` | ISO8601 | ✓ | |
| `status` | enum | ✓ | `draft` / `reviewed` / `adopted` / `superseded` / `deprecated` |
| `created_by` | string | ✓ | `skill:design-run` |
| `source_run_id` | string | ✓ | 产生此 Plan 的 design-run run_id |
| `tags` | string[] | | |
| **专属字段** | | | |
| `project_id` | string | ✓ | 必须存在 |
| `stage` | enum | ✓ | `kickoff` / `concept` / `iteration` / `review` / `final` |
| `prompt_id` | string | ✓ | 渲染时使用的 Prompt id |
| `prompt_version` | string | ✓ | Prompt semver，写入时快照 |
| `prompt_inputs_hash` | string | ✓ | sha256(canonical_json(prompt_inputs)) |
| `directions` | object[] | ✓ | 概念方向数组（≥ 1） |
| `next_actions` | string[] | ✓ | 可执行下一步 |
| `open_questions_for_client` | string[] | | 给客户的问题 |
| `consumed_assets` | string[] | ✓ | 这次 plan 实际看到的 Asset id |
| `consumed_patterns` | string[] | | 这次 plan 引用的 Pattern id |
| `llm_mode` | enum | ✓ | `dry-run` / `hook` / `live` |
| `decision_notes` | string \| null | | 人类后续追加 |
| `adopted_direction_id` | string \| null | | 当 status=adopted 时必填 |
| `superseded_by` | string \| null | | 升级时填 |

### directions 子结构

```yaml
directions:
  - id: "dir_001"
    name: "克制冷感"            # ≤ 8 字
    core_idea: "..."           # 一句话核心主张
    visual_approach: "..."     # 视觉手法
    rationale: "..."           # 为什么服务 brief
    referenced_patterns: []    # 借鉴的 Pattern id
    referenced_assets: []      # 借鉴的 Asset id（来自 manifest）
```

## YAML 模板

```yaml
---
id: "pln_acme_q4_concept_20260504_153012_b8c7"
type: plan
schema_version: "1.0"
created_at: "2026-05-04T15:30:12Z"
updated_at: "2026-05-04T15:30:12Z"
status: draft
created_by: "skill:design-run"
source_run_id: "run_run_20260504_153012_b8c7"
tags:
  - design-run
  - concept

project_id: "prj_acme_q4_campaign"
stage: concept
prompt_id: "prm_run_concept"
prompt_version: "1.0.0"
prompt_inputs_hash: "..."

directions:
  - id: "dir_001"
    name: "克制冷感"
    core_idea: "..."
    visual_approach: "..."
    rationale: "..."
    referenced_patterns: ["pat_three_section_kv"]
    referenced_assets: ["ast_a1b2c3d4e5f6"]

next_actions:
  - "本周内完成 dir_001 的 v1 草稿"
next_actions:
  - "..."

open_questions_for_client: []

consumed_assets:
  - "ast_a1b2c3d4e5f6"
consumed_patterns: []

llm_mode: dry-run
decision_notes: null
adopted_direction_id: null
superseded_by: null
---

# Plan · ACME Q4 · concept

## Brief recap
（人类可读摘要）

## Directions
（渲染 directions 数组）
```

## 校验规则

```
required: 全部上面标 ✓ 的字段
constraints:
  - id MUST match pattern: ^pln_[a-z0-9_]+_\d{8}_\d{6}_[a-z0-9]{4}$
  - status transitions: draft → reviewed → adopted; reviewed → superseded
  - len(directions) >= 1
  - each direction.id MUST be unique within this plan
  - if status == adopted: adopted_direction_id MUST be in directions[*].id
  - prompt_inputs_hash MUST be valid sha256
  - llm_mode in {dry-run, hook, live}
  - consumed_assets entries MUST exist as Asset ids in manifest at run time
  - project_id MUST reference an existing Project
```

## 状态机

```
draft  →  reviewed  →  adopted          (主路径：方向被选中执行)
              ↓
         superseded                     (有更好的方案替代)
              ↓
         deprecated                     (终态)
```

## 反模式

- ❌ 修改 active plan 的 directions → 必须新建 plan + superseded_by
- ❌ adopted 但 adopted_direction_id 为空 → 强制校验
- ❌ consumed_assets 引用不在 project.asset_refs 中的 Asset → 越权
- ❌ Plan 不写 source_run_id → Plan 必须可追溯到产生它的 run
