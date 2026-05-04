---
id: "rul_class_poster"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - poster

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:poster"
precedence: 60
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "poster"
    - "海报"
    - "keyvisual"
    - "kv"
    - "campaign"
    - "event"
    - "banner"
    - "social"
    - "主视觉"
    - "活动"
    - "宣传图"
    - "推广图"
  extension_hints:
    high_signal: [".psd", ".ai", ".tif", ".tiff"]
    medium_signal: [".jpg", ".jpeg", ".png", ".pdf"]
  output:
    category: poster
    base_confidence: high
  scoring:
    keyword_hits_required_for_high: 2
    keyword_hits_required_for_medium: 1

replaces: null
replaced_by: null

test_cases:
  - id: tc_poster_01
    input:
      path: "/projects/acme/posters/main_kv_v2.psd"
    expect:
      category: poster
      confidence: high
      reason_contains: ["poster", "kv"]
  - id: tc_poster_02
    input:
      path: "/clients/foo/海报/双十一_主视觉_final.jpg"
    expect:
      category: poster
      confidence: high
      reason_contains: ["海报", "主视觉"]
  - id: tc_poster_03
    input:
      path: "/x/social_banner_v1.png"
    expect:
      category: poster
      confidence: high
      reason_contains: ["social", "banner"]
  - id: tc_poster_04
    input:
      path: "/x/event_flyer.png"
    expect:
      category: poster
      confidence: medium
      reason_contains: ["event"]
  - id: tc_poster_05_negative
    input:
      path: "/x/random_photo.jpg"
    expect:
      category: null
      confidence: null
---

# Rule: poster 分类

## Intent
识别海报、主视觉、活动推广图、社媒分发图等"传播类视觉"。

## 高信号关键词
- 中文：海报 / 主视觉 / 活动 / 宣传图 / 推广图
- 英文：poster / keyvisual / kv / campaign / event / banner / social

## 扩展名信号
- 高信号：.psd .ai .tif .tiff（设计原文件）
- 中信号：.jpg .png .pdf

## Confidence 判定
- ≥ 2 个关键词命中 → high
- 1 个关键词命中 → medium
- 仅扩展名命中 → low（由 hybrid 路由处理）

## 已知误判风险
- "banner" 也可能是网页设计 → 由 hybrid 路由结合上下文消歧
- "social" 路径下可能混入 process（截图）→ process 规则 precedence 更高

## Change Log
- 1.0.0 (2026-05-04): 从 classification-rules.md 迁移；增加 extension_hints
