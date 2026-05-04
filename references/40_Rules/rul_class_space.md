---
id: "rul_class_space"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - space

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:space"
precedence: 75
engine: keyword

body:
  match: any
  case_sensitive: false
  scope: [path, filename]
  keywords:
    - "space"
    - "interior"
    - "retail"
    - "exhibition"
    - "booth"
    - "store"
    - "render"
    - "rendering"
    - "3d"
    - "空间"
    - "展厅"
    - "展陈"
    - "门店"
    - "效果图"
    - "施工"
    - "平面图"
    - "立面图"
    - "剖面"
    - "动线"
  extension_hints:
    high_signal: [".dwg", ".skp", ".max", ".obj", ".fbx", ".3dm"]
    medium_signal: [".jpg", ".png", ".pdf", ".tiff"]
  output:
    category: space
    base_confidence: high
  scoring:
    keyword_hits_required_for_high: 1
    keyword_hits_required_for_medium: 0  # 仅扩展名也可走到 medium（CAD/3D 文件信号极强）
    extension_only_confidence: medium

replaces: null
replaced_by: null

test_cases:
  - id: tc_space_01
    input:
      path: "/projects/foo/空间/门店效果图_v3.jpg"
    expect:
      category: space
      confidence: high
      reason_contains: ["空间", "门店", "效果图"]
  - id: tc_space_02
    input:
      path: "/exhibition_booth/render_final.png"
    expect:
      category: space
      confidence: high
      reason_contains: ["exhibition", "booth", "render"]
  - id: tc_space_03
    input:
      path: "/plans/store_layout.dwg"
    expect:
      category: space
      confidence: high
      reason_contains: ["store"]
  - id: tc_space_04_extension_only
    input:
      path: "/random/scene01.skp"
    expect:
      category: space
      confidence: medium
      reason_contains: [".skp"]
  - id: tc_space_05
    input:
      path: "/projects/bar/平面图_一层.pdf"
    expect:
      category: space
      confidence: high
      reason_contains: ["平面图"]
---

# Rule: space 分类

## Intent
识别空间设计相关产物：室内、展陈、零售、动线、施工图、3D 渲染。

## 高信号关键词
- 中文：空间 / 展厅 / 展陈 / 门店 / 效果图 / 施工 / 平面图 / 立面图 / 剖面 / 动线
- 英文：space / interior / retail / exhibition / booth / store / render / 3d

## 扩展名信号
- 高信号：.dwg .skp .max .obj .fbx .3dm（专业空间/3D 工具）
- 中信号：.jpg .png .pdf

## 特殊行为
**仅扩展名命中也可判为 medium**：CAD/3D 文件类型本身是极强信号，不需要文件名再有关键词。
这是 space 规则相对其他类目的特异性配置。

## Confidence 判定
- ≥ 1 个关键词命中 → high
- 仅扩展名命中（在 extension_hints.high_signal 中）→ medium
- 否则不命中

## precedence: 75（高于 poster 的 60）
理由：space 关键词专一性强，误判风险低于 poster 的 "banner/social/event" 等通用词。

## Change Log
- 1.0.0 (2026-05-04): 初版；增加 CAD/3D 扩展名信号；引入 extension_only_confidence 机制
