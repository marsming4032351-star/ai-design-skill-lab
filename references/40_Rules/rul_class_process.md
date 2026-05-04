---
id: "rul_class_process"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - process

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:process"
precedence: 50
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "draft"
    - "sketch"
    - "wireframe"
    - "screenshot"
    - "wip"
    - "iter"
    - "iteration"
    - "rev"
    - "revision"
    - "过程"
    - "草稿"
    - "修改"
    - "迭代"
    - "截图"
    - "草图"
    - "中间稿"
  filename_pattern_hints:
    # 文件名中常见的过程信号（regex）
    - pattern: "v\\d+(?![a-z])"            # v1, v2, v10（但不是 vMORE）
      weight: medium
      example: "logo_v3.psd"
    - pattern: "(?i)(rev|revision)\\d+"    # rev1, revision2
      weight: medium
    - pattern: "_(draft|wip|tmp)"
      weight: high
    - pattern: "screenshot.*\\.(png|jpg)"
      weight: high
  extension_hints:
    high_signal: []
    medium_signal: [".png", ".jpg", ".psd", ".sketch", ".fig"]
  output:
    category: process
    base_confidence: medium  # process 默认置信度低于其他类目
  scoring:
    keyword_hits_required_for_high: 2
    keyword_hits_required_for_medium: 1
    pattern_match_bonus: true   # 文件名 regex 命中可叠加置信度
    cap_at_base: true   # process 类故意压制为 medium，避免误升为主类目

replaces: null
replaced_by: null

test_cases:
  - id: tc_process_01
    input:
      path: "/projects/foo/迭代/草稿_v2.psd"
    expect:
      category: process
      confidence: high
      reason_contains: ["迭代", "草稿"]
  - id: tc_process_02
    input:
      path: "/x/wireframe_draft_v1.fig"
    expect:
      category: process
      confidence: high
      reason_contains: ["wireframe", "draft", "v1"]
  - id: tc_process_03
    input:
      path: "/projects/x/screenshot_20260504.png"
    expect:
      category: process
      confidence: high
      reason_contains: ["screenshot"]
  - id: tc_process_04
    input:
      path: "/x/logo_v3.ai"
    expect:
      category: process
      confidence: medium
      reason_contains: ["v\\d 模式"]
      conflict_warning: "也命中 brand (logo, .ai)；hybrid 应判 brand 主类 + process 子状态"
  - id: tc_process_05
    input:
      path: "/x/main_kv_rev2.psd"
    expect:
      category: process
      confidence: medium
      reason_contains: ["rev2"]
      conflict_warning: "也命中 poster (kv)；hybrid 应判 poster + process"
---

# Rule: process 分类

## Intent
识别过程稿、中间稿、迭代版本、草图、wireframe、截图等"工作中产物"。

## 高信号关键词
- 中文：过程 / 草稿 / 修改 / 迭代 / 截图 / 草图 / 中间稿
- 英文：draft / sketch / wireframe / screenshot / wip / iter / rev / revision

## 文件名模式（regex）
process 是**唯一启用 regex 命中**的分类规则，因为版本号是核心信号：
- `v\d+` → v1/v2/v3
- `rev\d+` / `revision\d+`
- `_(draft|wip|tmp)`
- `screenshot.*\.(png|jpg)`

## 扩展名信号
process 没有专属扩展名，常见 .png .jpg .psd .sketch .fig。
**单独扩展名不足以判定。**

## Confidence 判定
- ≥ 2 关键词 → high
- 1 关键词 + regex 命中 → high
- 1 关键词或 regex 命中 → medium
- 默认 base_confidence 是 medium 而非 high（process 类容易被误判）

## precedence: 50（最低）
**关键设计**：process 优先级故意设最低。
理由：很多 process 文件同时是 poster/brand/space 的过程稿（如 `logo_v3.ai`）。
应当让 hybrid 路由把它们标为"主类目 + process 子状态"，而不是直接判为 process。

实现层面：
- 单独跑此规则得到 process 命中 → 仅作为"family_role: variant"信号
- 是否最终归 process，由 hybrid 路由决定（见 `rul_class_router`）

## Change Log
- 1.0.0 (2026-05-04): 初版；引入 filename_pattern_hints；precedence 故意设为最低
