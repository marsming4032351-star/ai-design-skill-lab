---
id: "rul_class_soft_decoration"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - soft-decoration

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:soft-decoration"
precedence: 70
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "soft"
    - "furniture"
    - "material"
    - "textile"
    - "fabric"
    - "lighting"
    - "prop"
    - "moodboard"
    - "软装"
    - "家具"
    - "面料"
    - "材质"
    - "灯具"
    - "摆件"
    - "配色"
    - "饰品"
    - "陈设"
    - "织物"
  extension_hints:
    high_signal: []
    medium_signal: [".jpg", ".jpeg", ".png", ".pdf", ".tiff"]
  output:
    category: soft-decoration
    base_confidence: high
  scoring:
    keyword_hits_required_for_high: 2
    keyword_hits_required_for_medium: 1

replaces: null
replaced_by: null

test_cases:
  - id: tc_soft_01
    input:
      path: "/projects/villa/软装/家具清单.pdf"
    expect:
      category: soft-decoration
      confidence: high
      reason_contains: ["软装", "家具"]
  - id: tc_soft_02
    input:
      path: "/moodboards/textile_fabric_v2.jpg"
    expect:
      category: soft-decoration
      confidence: high
      reason_contains: ["textile", "fabric"]
  - id: tc_soft_03
    input:
      path: "/x/lighting_proposal.pdf"
    expect:
      category: soft-decoration
      confidence: medium
      reason_contains: ["lighting"]
      conflict_warning: "也命中 proposal 关键词"
  - id: tc_soft_04
    input:
      path: "/x/material_board_001.png"
    expect:
      category: soft-decoration
      confidence: high
      reason_contains: ["material", "moodboard 衍生"]
  - id: tc_soft_05
    input:
      path: "/项目A/摆件配色参考.jpg"
    expect:
      category: soft-decoration
      confidence: high
      reason_contains: ["摆件", "配色"]
---

# Rule: soft-decoration 分类

## Intent
识别软装相关产物：家具、面料、材质、灯具、配色、moodboard、摆件、陈设。

## 高信号关键词
- 中文：软装 / 家具 / 面料 / 材质 / 灯具 / 摆件 / 配色 / 饰品 / 陈设 / 织物
- 英文：soft / furniture / material / textile / fabric / lighting / prop / moodboard

## 扩展名信号
软装类没有专有扩展名，统一为常规图像/PDF。
**所以本规则强依赖关键词**，不接受 extension_only 命中。

## Confidence 判定
- ≥ 2 个关键词命中 → high
- 1 个关键词命中 → medium

## 已知冲突
- `lighting`、`material` 在某些项目里也指视觉/品牌的"光感/质感"，可能与 brand 冲突
- `prop` 在影视类项目中指道具，跨类目
- `配色` 与 brand 的 color 冲突 → 需 hybrid 路由仲裁

## precedence: 70
理由：高于 poster (60)，低于 space (75)；专一性中等。

## Change Log
- 1.0.0 (2026-05-04): 从 classification-rules.md 迁移；补充"饰品/陈设/织物"中文关键词
