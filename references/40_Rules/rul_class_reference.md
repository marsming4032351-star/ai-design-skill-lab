---
id: "rul_class_reference"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - reference

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:reference"
precedence: 65
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "reference"
    - "ref"
    - "benchmark"
    - "inspiration"
    - "research"
    - "mood"
    - "案例"
    - "参考"
    - "竞品"
    - "灵感"
    - "资料"
    - "调研"
    - "对标"
    - "学习"
    - "收藏"
  path_signal_hints:
    # 父目录命中即强信号
    folder_keywords:
      - "reference"
      - "refs"
      - "参考"
      - "案例"
      - "竞品"
      - "调研"
      - "灵感"
      - "inspiration"
      - "research"
    folder_match_confidence: high
  extension_hints:
    high_signal: []
    medium_signal: [".jpg", ".jpeg", ".png", ".pdf", ".webp", ".gif"]
  output:
    category: reference
    base_confidence: medium
  scoring:
    keyword_hits_required_for_high: 1
    folder_match_bonus: true   # 父目录命中升级到 high

replaces: null
replaced_by: null

test_cases:
  - id: tc_ref_01
    input:
      path: "/projects/foo/参考/竞品案例_001.jpg"
    expect:
      category: reference
      confidence: high
      reason_contains: ["参考", "竞品", "案例"]
  - id: tc_ref_02
    input:
      path: "/projects/x/inspiration/mood_001.png"
    expect:
      category: reference
      confidence: high
      reason_contains: ["folder:inspiration", "mood"]
  - id: tc_ref_03
    input:
      path: "/research/benchmark_brands.pdf"
    expect:
      category: reference
      confidence: high
      reason_contains: ["folder:research", "benchmark"]
  - id: tc_ref_04
    input:
      path: "/projects/y/调研报告_2026.pdf"
    expect:
      category: reference
      confidence: high
      reason_contains: ["调研"]
  - id: tc_ref_05
    input:
      path: "/refs/random_001.jpg"
    expect:
      category: reference
      confidence: high
      reason_contains: ["folder:refs"]
  - id: tc_ref_06_negative
    input:
      path: "/x/reference_design.psd"  # 文件名带 reference 但不在 ref 文件夹下
    expect:
      category: reference
      confidence: medium
      reason_contains: ["reference"]
---

# Rule: reference 分类

## Intent
识别参考资料：竞品、案例、灵感、调研、moodboard 输入素材。

## 高信号关键词
- 中文：案例 / 参考 / 竞品 / 灵感 / 资料 / 调研 / 对标 / 学习 / 收藏
- 英文：reference / ref / benchmark / inspiration / research / mood

## 路径专属信号（关键）
**父目录命中是 reference 类的最强信号**。
如果文件位于 `/参考/`、`/refs/`、`/inspiration/` 等目录下，无论文件名如何，
都极可能是参考素材。这是 reference 与其他类目的核心区分点。

## 扩展名信号
没有专属扩展名（reference 是"用途分类"而非"格式分类"）。

## Confidence 判定
- 父目录命中 folder_keywords → high
- 文件名命中关键词 → medium（`base_confidence: medium`）
- 文件名命中 + 文件夹也命中 → high

## 已知冲突
- 与 soft-decoration 的 `moodboard` 重叠 → 看是"作为输入参考"还是"作为本项目产出"
  - 路径在 `/refs/` 下 → reference
  - 路径在 `/软装/moodboard/` 下 → soft-decoration
  - 由 hybrid 路由用路径上下文判断

## precedence: 65
理由：reference 是"用途"分类，优先级中等；明确路径信号时升级到 high。

## Change Log
- 1.0.0 (2026-05-04): 初版；引入 path_signal_hints（父目录优先级）
