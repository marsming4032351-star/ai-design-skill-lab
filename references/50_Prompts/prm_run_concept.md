---
id: "prm_run_concept"
type: prompt
schema_version: "1.0"
created_at: "2026-05-04T16:00:00Z"
updated_at: "2026-05-04T16:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - design-run
  - concept

prompt_version: "1.0.0"
applies_to:
  - "skill:design-run"
  - "stage:concept"
model_hint: "claude-opus-4-7"
temperature_hint: 0.7

inputs:
  - name: project_id
    type: string
    required: true
    description: "Project ID"
  - name: brief_summary
    type: string
    required: true
    description: "项目 brief 简述（≤ 280 字符）"
  - name: client
    type: string
    required: true
  - name: project_type
    type: enum
    enum: [poster_campaign, space, brand_system, soft_decor, mixed, other]
    required: true
  - name: deliverables
    type: list
    required: true
    description: "Deliverables 数组（含 name、category、qty）"
  - name: asset_summaries
    type: list
    required: false
    default: []
    description: "相关 Asset 列表，每项 {id, category, name, family_role}"
  - name: pattern_refs
    type: list
    required: false
    default: []
    description: "推荐的历史 Pattern id"
  - name: open_questions
    type: list
    required: false
    default: []
  - name: tone_override
    type: string
    required: false
    default: ""
  - name: must_avoid
    type: list
    required: false
    default: []

output_format: json
output_schema:
  type: object
  required: [directions, next_actions, open_questions_for_client]
  properties:
    directions:
      type: array
      minItems: 2
      maxItems: 4
      items:
        type: object
        required: [name, core_idea, visual_approach, rationale]
        properties:
          name: {type: string, maxLength: 8}
          core_idea: {type: string}
          visual_approach: {type: string}
          rationale: {type: string}
          referenced_patterns: {type: array, items: {type: string}}
          referenced_assets: {type: array, items: {type: string}}
    next_actions:
      type: array
      items: {type: string}
    open_questions_for_client:
      type: array
      items: {type: string}

system_prompt: |
  你是资深设计策略师，擅长把模糊 brief 转化为差异化概念方向。
  本阶段只产出概念方向，不产出执行细节。
  每个方向必须能被一句话差异化表达；不要给出"安全居中"的方向。

template: |
  你正在为客户 {{client}} 的项目 {{project_id}} 产出 concept 阶段方向。

  ## 项目类型
  {{project_type}}

  ## Brief
  {{brief_summary}}

  ## 交付物
  {{deliverables_block}}

  ## 关联素材（来自 ingest manifest）
  {{asset_summaries_block}}

  ## 可参考的历史 Pattern
  {{pattern_refs_block}}

  ## 当前未决问题
  {{open_questions_block}}

  ## 风格要求
  - Tone: {{tone_override_or_default}}
  - 必须避免: {{must_avoid_block}}

  请输出 2~4 个差异化的概念方向，每个方向包含：
  - name（≤ 8 字）
  - core_idea（一句话核心主张）
  - visual_approach（视觉手法）
  - rationale（为什么服务 brief）
  - referenced_patterns / referenced_assets（如借鉴）

  最后给出：
  - next_actions
  - open_questions_for_client

  严格 JSON 输出，符合 output_schema。

replaces: null
replaced_by: null

examples: []

test_cases:
  - id: tc_run_concept_01
    inputs:
      project_id: "prj_test"
      brief_summary: "新茶饮品牌春季限定上新"
      client: "TestCo"
      project_type: poster_campaign
      deliverables:
        - {name: "主视觉", category: poster, qty: 1}
    expect:
      keys_present: [directions, next_actions, open_questions_for_client]
      directions_min: 2

safety_notes:
  - "不引用真实公众人物作为视觉主体"
  - "不使用未授权的第三方品牌素材"
---

# Prompt: design-run · concept (v1)

## Intent
将 brief + manifest assets + pattern refs，转化为 2~4 个差异化的概念方向。

## Variables
所有 `{{...}}` 占位符在 inputs 中声明。带 `_block` 后缀的是渲染器组装的格式化块。

## Change Log
- 1.0.0 (2026-05-04): 初版
