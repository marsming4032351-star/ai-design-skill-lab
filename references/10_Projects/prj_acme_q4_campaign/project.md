---
id: prj_acme_q4_campaign
type: project
schema_version: '1.0'
created_at: '2026-05-01T08:00:00Z'
updated_at: '2026-05-04T23:09:41Z'
status: active
created_by: human
source_run_id: null
tags:
- design-os
client: ACME
project_type: poster_campaign
stage: concept
start_date: '2026-05-01'
target_date: '2026-06-30'
closed_date: null
brief_summary: ACME 2026 双十一主视觉与社媒分发，覆盖 5 个 SKU，定位高端冷感。
deliverables:
- id: del_main_kv
  name: 主视觉海报
  category: poster
  qty: 3
  status: in_progress
  target_date: '2026-06-15'
  output_refs: []
- id: del_social
  name: 社媒分发图
  category: poster
  qty: 12
  status: pending
  target_date: '2026-06-25'
  output_refs: []
asset_refs: []
pattern_refs: []
derived_pattern_refs:
- pat_dryrun
prompt_overrides:
  prm_run_concept:
    tone_override: 高端冷静，避免促销感
    must_avoid:
    - 夸张促销字
    - 霓虹色
rule_overrides: {}
run_history: []
open_questions:
- 是否需要为东南亚市场单独本地化？
- 客户对 KV 是否要求出现产品本体？
---
# ACME Q4 Campaign

## Brief
ACME 2026 双十一主视觉与社媒分发，覆盖 5 个 SKU。
品牌调性高端、冷感，避免传统电商促销感。

## Stage Notes
- 5/1 项目启动
- 5/4 完成第一轮素材 ingest

## Asset Index
（ingest 后由人工或自动同步填入 asset_refs）
