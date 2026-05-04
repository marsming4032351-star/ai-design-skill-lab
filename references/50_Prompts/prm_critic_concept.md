---
id: "prm_critic_concept"
type: prompt
schema_version: "1.0"
created_at: "2026-05-04T16:30:00Z"
updated_at: "2026-05-04T16:30:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - design-critic
  - concept

prompt_version: "1.0.0"
applies_to:
  - "skill:design-critic"
  - "stage:concept"
  - "target_type:plan_direction"
model_hint: "claude-opus-4-7"
temperature_hint: 0.2     # 评审需要低温度，追求一致性

inputs:
  - name: project_id
    type: string
    required: true
  - name: client
    type: string
    required: true
  - name: brief_summary
    type: string
    required: true
  - name: project_type
    type: string
    required: true
  - name: deliverables
    type: list
    required: true
  - name: direction
    type: dict
    required: true
    description: "Plan 中被评审的 direction 对象（含 name/core_idea/visual_approach/rationale）"
  - name: peer_directions
    type: list
    required: false
    default: []
    description: "Plan 中其他方向，用于差异化对比"
  - name: rubric
    type: dict
    required: true
    description: "rubric body，含 dimensions/scale/anchors"
  - name: pattern_refs
    type: list
    required: false
    default: []

output_format: json
output_schema:
  type: object
  required: [scores, strengths, weaknesses, actionable_feedback]
  properties:
    scores:
      type: object
      description: "key 是 dimension_id, value 是 {score: int, rationale: str}"
    strengths:
      type: array
      items: {type: string}
    weaknesses:
      type: array
      items: {type: string}
    actionable_feedback:
      type: array
      items: {type: string}

system_prompt: |
  你是一个严格的设计评审者。你必须严格按 rubric 给分，不能给出"安全"的全 3 分。
  评审有差异化对比时，要在分数和 rationale 中体现该方向相对于其他方向的取舍。
  低分（1-2）必须给出具体可执行的修改建议；高分（4-5）必须指出可被沉淀为 Pattern 的部分。

template: |
  ## 项目背景
  - Project: {{project_id}} ({{client}})
  - Type: {{project_type}}
  - Brief: {{brief_summary}}
  - Deliverables: {{deliverables_block}}

  ## 待评审方向
  {{direction_block}}

  ## 同 Plan 中其他方向（用于差异化对比）
  {{peer_directions_block}}

  ## Rubric（评分维度与锚点）
  {{rubric_block}}

  ## 历史可参考 Pattern
  {{pattern_refs_block}}

  请按 rubric 中每个 dimension 给出 1-5 整数分 + 单维度理由。
  严格 JSON 输出：

  {
    "scores": {
      "<dimension_id>": {"score": <int>, "rationale": "<≤80字>"},
      ...
    },
    "strengths": ["..."],
    "weaknesses": ["..."],
    "actionable_feedback": ["..."]
  }

replaces: null
replaced_by: null

test_cases: []

safety_notes:
  - "评分理由不引用真实公众人物作为参照对象"
  - "actionable_feedback 不指定具体 vendor 或第三方资源"
---

# Prompt: design-critic · concept (v1)

## Intent
对 Plan 中某个 direction 应用 rubric，输出每维度评分 + 优缺点 + 可执行反馈。
**design-critic skill 自己计算 weighted_score 和 decision，不交给 LLM。**
LLM 只产出原始评分和叙述性反馈。

## Variables
- `direction` - 被评审的方向对象（design-critic 渲染前注入）
- `peer_directions` - Plan 中其他方向（差异化对比用）
- `rubric` - 整个 rubric body（design-critic 从 Rule 实体取出）
- 其他与 prm_run_concept 一致

## Change Log
- 1.0.0 (2026-05-04): 初版
