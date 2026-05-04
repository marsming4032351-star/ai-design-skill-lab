---
id: "rul_class_proposal"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - proposal

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:proposal"
precedence: 78
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "proposal"
    - "deck"
    - "plan"
    - "presentation"
    - "brief"
    - "方案"
    - "报价"
    - "提案"
    - "汇报"
    - "投标"
    - "招标"
    - "策划案"
    - "执行方案"
  extension_hints:
    high_signal: [".ppt", ".pptx", ".key", ".doc", ".docx"]
    medium_signal: [".pdf"]
  output:
    category: proposal
    base_confidence: high
  scoring:
    keyword_hits_required_for_high: 1
    keyword_hits_required_for_medium: 0
    extension_only_confidence: medium  # 单纯一个 pptx 也大概率是 proposal

replaces: null
replaced_by: null

test_cases:
  - id: tc_proposal_01
    input:
      path: "/clients/acme/方案/Q4提案_v2.pptx"
    expect:
      category: proposal
      confidence: high
      reason_contains: ["方案", "提案", ".pptx"]
  - id: tc_proposal_02
    input:
      path: "/projects/x/proposal_v1.pdf"
    expect:
      category: proposal
      confidence: high
      reason_contains: ["proposal"]
  - id: tc_proposal_03
    input:
      path: "/x/汇报_20260504.pptx"
    expect:
      category: proposal
      confidence: high
      reason_contains: ["汇报", ".pptx"]
  - id: tc_proposal_04_extension_only
    input:
      path: "/x/random_deck.key"
    expect:
      category: proposal
      confidence: medium
      reason_contains: [".key"]
  - id: tc_proposal_05
    input:
      path: "/clients/foo/招标文件.pdf"
    expect:
      category: proposal
      confidence: medium
      reason_contains: ["招标"]
---

# Rule: proposal 分类

## Intent
识别提案、方案、汇报、报价、招投标等"叙事/商务类"文档。

## 高信号关键词
- 中文：方案 / 报价 / 提案 / 汇报 / 投标 / 招标 / 策划案 / 执行方案
- 英文：proposal / deck / plan / presentation / brief

## 扩展名信号（重要）
- 高信号：.ppt .pptx .key .doc .docx（演示/文档类型几乎只服务 proposal）
- 中信号：.pdf（PDF 跨类目，需配合关键词）

## 特殊行为
**仅 ppt/pptx/key/doc/docx 扩展名命中即可判 medium**：
这些扩展名在设计行业基本只承载提案、方案、汇报。

## Confidence 判定
- ≥ 1 个关键词命中 → high
- 仅高信号扩展名命中 → medium
- PDF 必须配合关键词

## precedence: 78
理由：略低于 brand (80)，高于 space (75)；扩展名信号极强，但关键词如 "plan" 易跨类目。

## 已知冲突
- "brief" 也可能在素材夹里指 brand brief → 一般无大碍
- 客户给的 PDF 既可能是 brief（proposal 输入）也可能是参考资料 → 由路径上下文消歧

## Change Log
- 1.0.0 (2026-05-04): 初版；增加投标/招标/策划案中文关键词；扩展名 medium 兜底
