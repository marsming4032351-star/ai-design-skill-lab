---
id: pat_dryrun
type: pattern
schema_version: '1.0'
created_at: '2026-05-04T15:35:15Z'
updated_at: '2026-05-04T15:35:50Z'
status: active
created_by: skill:design-archive
source_run_id: run_archive_20260504_153515_4f99
tags:
- design-archive
- poster_campaign
pattern_version: 1.0.0
category: poster
title: 克制冷感（dry-run）
summary: 以高端冷调主导的 poster_campaign 路线，强调材质感与留白。（dry-run 抽取）
applicable_when:
  project_types:
  - poster_campaign
  categories:
  - poster
  client_traits: []
  brief_signals: []
  stages:
  - concept
not_applicable_when:
- dry-run 抽取，未识别反例
core_elements:
- aspect: composition
  description: （dry-run 占位）核心构图骨架
  must_have: true
  parameters: {}
  id: elem_001
evidence_assets:
- ast_2164d554b78b
- ast_a1b6d1bd7644
- ast_4250130075f7
- ast_6026ebf2b656
derived_from_projects:
- prj_acme_q4_campaign
derived_from_runs:
- run_critic_20260504_153515_21f1
- run_run_20260504_153515_dd35
- run_archive_20260504_153515_4f99
derived_from_critique_id: crt_dir_001_20260504_153515_8bf1
reuse_score: 1.0
reuse_count: 2
related_patterns: []
replaces: null
replaced_by: null
usage_examples:
- project_id: prj_acme_q4_campaign
  asset_id: ast_2164d554b78b
  note: 首次抽取自 critique crt_dir_001_20260504_153515_8bf1
---
# Pattern · 克制冷感（dry-run）

- Category: poster
- reuse_score: 1.0
- Derived from: [[prj_acme_q4_campaign]] / [[crt_dir_001_20260504_153515_8bf1]]

## Summary
以高端冷调主导的 poster_campaign 路线，强调材质感与留白。（dry-run 抽取）

## Applicable when
- project_types: poster_campaign
- categories: poster
- stages: concept

## Not applicable when
- dry-run 抽取，未识别反例

## Core elements

### elem_001 · composition **[must-have]**
（dry-run 占位）核心构图骨架

## Evidence

- [[ast_2164d554b78b]]
- [[ast_a1b6d1bd7644]]
- [[ast_4250130075f7]]
- [[ast_6026ebf2b656]]

## Origin

Derived from direction `dir_001` (克制冷感) of plan.
Critique decision: pass (score: see [[crt_dir_001_20260504_153515_8bf1]])
