---
id: "prm_archive_pattern_extract"
type: prompt
schema_version: "1.0"
created_at: "2026-05-04T17:00:00Z"
updated_at: "2026-05-04T17:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - design-archive
  - pattern

prompt_version: "1.0.0"
applies_to:
  - "skill:design-archive"
  - "stage:concept"
model_hint: "claude-opus-4-7"
temperature_hint: 0.3

inputs:
  - name: project_id
    type: string
    required: true
  - name: client
    type: string
    required: true
  - name: project_type
    type: string
    required: true
  - name: brief_summary
    type: string
    required: true
  - name: direction
    type: dict
    required: true
    description: "被沉淀的 direction（含 name/core_idea/visual_approach/rationale）"
  - name: critique_summary
    type: dict
    required: true
    description: "Critique 摘要 {weighted_score, decision, scores, strengths}"
  - name: evidence_assets
    type: list
    required: true
    description: "证据 Asset 列表 {id, category, name}"
  - name: existing_patterns
    type: list
    required: false
    default: []
    description: "已有 Pattern 的 title 列表，用于查重和定位 related_patterns"

output_format: json
output_schema:
  type: object
  required:
    - title
    - summary
    - applicable_when
    - core_elements
    - not_applicable_when
    - related_patterns
  properties:
    title:
      type: string
      maxLength: 30
      description: "Pattern 名称，≤ 30 字"
    summary:
      type: string
      maxLength: 200
      description: "一句话核心主张"
    slug:
      type: string
      description: "用于 pattern_id 的英文 slug，snake_case，可选；省略则代码自动生成"
    applicable_when:
      type: object
      properties:
        project_types: {type: array, items: {type: string}}
        categories: {type: array, items: {type: string}}
        client_traits: {type: array, items: {type: string}}
        brief_signals: {type: array, items: {type: string}}
        stages: {type: array, items: {type: string}}
    not_applicable_when:
      type: array
      items: {type: string}
    core_elements:
      type: array
      minItems: 1
      items:
        type: object
        required: [aspect, description, must_have]
        properties:
          aspect:
            type: string
            enum: [composition, color, typography, material, motion, cultural]
          description: {type: string}
          must_have: {type: boolean}
          parameters: {type: object}
    related_patterns:
      type: array
      items: {type: string}

system_prompt: |
  你是设计模式抽象专家。任务：把一个具体项目方向抽象成可复用的 Pattern 骨架。
  关键原则：
  - 区分"项目特定"和"可迁移骨架"。客户名、SKU、时间节点 = 特定，必须剥离。
  - 构图比例、色彩关系、材质组合、字体层级 = 骨架，是 Pattern 的核心。
  - 如果某个 element 不去掉具体执行就无法描述，它就不是 Pattern 元素，是项目特例。
  - applicable_when 必须从 brief_signals 反推，不要复制项目本身。
  - 至少识别 1 个 must_have=true 的 core_element。
  - 如已有相似 Pattern，列出 related_patterns 而非重新发明。

template: |
  ## 项目背景
  - Project: {{project_id}} ({{client}})
  - Type: {{project_type}}
  - Brief: {{brief_summary}}

  ## 被沉淀的方向
  {{direction_block}}

  ## 评审摘要（已通过）
  {{critique_summary_block}}

  ## 证据资产
  {{evidence_assets_block}}

  ## 已有 Pattern 库
  {{existing_patterns_block}}

  请抽象出一个可复用 Pattern。注意：
  1. title ≤ 30 字，summary ≤ 200 字
  2. 至少 1 个 must_have=true 的 core_element
  3. applicable_when 描述"什么样的项目能用"，不复制本项目
  4. core_elements 描述"骨架是什么"，不复制本项目细节

  严格 JSON 输出。

replaces: null
replaced_by: null

test_cases: []

safety_notes:
  - "Pattern 描述不引用具体客户名（除非作为反例）"
  - "Pattern 不复制原创性敏感的具体视觉描述"
---

# Prompt: design-archive · pattern extraction (v1)

## Intent
把通过 critic 的 direction 抽象成可复用 Pattern 骨架。
LLM 负责"抽象"，design-archive 代码负责实体写入和链接更新。

## Variables
- `direction` - 被沉淀的方向
- `critique_summary` - 评审结果，含 strengths 用于识别"哪些是亮点骨架"
- `evidence_assets` - 来自 Plan.consumed_assets，作为 Pattern 的证据
- `existing_patterns` - Pattern 库，避免重复发明 + 识别 related_patterns

## Change Log
- 1.0.0 (2026-05-04): 初版
