---
id: "rul_class_brand"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - brand

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:brand"
precedence: 80
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "brand"
    - "logo"
    - "identity"
    - "vi"
    - "guideline"
    - "typography"
    - "color"
    - "packaging"
    - "品牌"
    - "标志"
    - "字体"
    - "色彩"
    - "包装"
    - "视觉识别"
    - "品牌手册"
    - "logo规范"
    - "VI手册"
  extension_hints:
    high_signal: [".ai", ".eps", ".svg"]   # 矢量文件强信号
    medium_signal: [".pdf", ".psd", ".png", ".jpg"]
  output:
    category: brand
    base_confidence: high
  scoring:
    keyword_hits_required_for_high: 1
    keyword_hits_required_for_medium: 0  # logo + .ai 这种组合
    extension_only_confidence: low       # 仅 .ai 不足以判 brand（也可能是 poster）

replaces: null
replaced_by: null

test_cases:
  - id: tc_brand_01
    input:
      path: "/clients/foo/品牌/VI手册_v3.pdf"
    expect:
      category: brand
      confidence: high
      reason_contains: ["品牌", "VI手册"]
  - id: tc_brand_02
    input:
      path: "/projects/x/logo_final.ai"
    expect:
      category: brand
      confidence: high
      reason_contains: ["logo", ".ai"]
  - id: tc_brand_03
    input:
      path: "/x/brand_guideline_2026.pdf"
    expect:
      category: brand
      confidence: high
      reason_contains: ["brand", "guideline"]
  - id: tc_brand_04
    input:
      path: "/x/typography_specimens.pdf"
    expect:
      category: brand
      confidence: high
      reason_contains: ["typography"]
  - id: tc_brand_05
    input:
      path: "/projects/foo/包装设计_v2.pdf"
    expect:
      category: brand
      confidence: high
      reason_contains: ["包装"]
  - id: tc_brand_06_conflict
    input:
      path: "/projects/x/color_palette_for_kv.psd"
    expect:
      category: null  # 与 poster (kv) 冲突
      confidence: null
      conflict_warning: "color 命中 brand，kv 命中 poster"
---

# Rule: brand 分类

## Intent
识别品牌系统相关产物：logo、VI、字体、色彩规范、包装、品牌手册。

## 高信号关键词
- 中文：品牌 / 标志 / 字体 / 色彩 / 包装 / 视觉识别 / 品牌手册 / logo规范 / VI手册
- 英文：brand / logo / identity / vi / guideline / typography / color / packaging

## 扩展名信号
- 高信号：.ai .eps .svg（矢量，brand 专属强信号）
- 中信号：.pdf .psd
- ⚠️ `.ai` 单独不足以判 brand，poster 也常用 .ai

## Confidence 判定
- ≥ 1 个关键词命中 → high
- 关键词 + 矢量扩展名 → high
- 仅矢量扩展名命中 → low（交给 hybrid 路由再判）

## 已知冲突
- `color` 与 soft-decoration 的"配色"语义重叠 → 用 precedence 80 > 70 解决
- `packaging` 也可能是 product 设计 → 当前不区分 product 类目，归 brand

## precedence: 80（最高）
理由：brand 关键词专一性最强（VI/logo/identity 几乎不会跨类目），且 brand 是 archive 流程的高价值起点。

## Change Log
- 1.0.0 (2026-05-04): 初版；增加矢量扩展名信号；调高 precedence 至 80
