# v6 完整版 vs 仓库现状 比对报告

生成时间: Tue May  5 06:49:07 CST 2026

## 1. 仓库缺失文件（必须从 v6 拷贝）

```
MISSING: references/50_Prompts/prm_archive_pattern_extract.md
MISSING: references/50_Prompts/prm_run_concept.md
MISSING: references/50_Prompts/prm_critic_concept.md
MISSING: references/schemas/08_critique.md
MISSING: references/schemas/07_plan.md
MISSING: references/schemas/06_pattern.md
MISSING: references/40_Rules/rul_class_poster.md
MISSING: references/40_Rules/rul_class_reference.md
MISSING: references/40_Rules/rul_score_concept_direction.md
MISSING: references/40_Rules/rul_class_router.md
MISSING: references/40_Rules/rul_class_process.md
MISSING: references/40_Rules/rul_class_proposal.md
MISSING: references/40_Rules/rul_class_space.md
MISSING: references/40_Rules/rul_class_soft_decoration.md
MISSING: references/40_Rules/rul_recommend_pattern.md
MISSING: references/40_Rules/rul_class_brand.md
MISSING: references/10_Projects/prj_acme_q4_campaign/project.md
MISSING: shared/entity_updater.py
MISSING: shared/critique_loader.py
MISSING: shared/rubric_engine.py
MISSING: shared/rule_engine.py
MISSING: shared/plan_loader.py
MISSING: scripts/critic_design.py
MISSING: scripts/scan_inbox.py
MISSING: scripts/archive_design.py
MISSING: example_output/round2_with_patterns/run_run_20260504_153521_5473.md
MISSING: example_output/round2_with_patterns/pln_acme_q4_campaign_concept_20260504_153521_5d74.md
MISSING: example_output/round1_no_patterns/pln_acme_q4_campaign_concept_20260504_153515_cef1.md
MISSING: example_output/round1_no_patterns/sealed_pattern.md
MISSING: example_output/round1_no_patterns/run_run_20260504_153515_dd35.md
MISSING: CHANGES.md
```

## 2. 仓库独有文件（Codex 自己加的，需要保留）

```
EXTRA: references/30_Patterns/sealed_pattern.md
EXTRA: references/90_Runs/run_run_20260504_153521_5473.md
EXTRA: references/40_Rules/recommendation/rul_recommend_pattern.md
EXTRA: tests/test_run_design_dependencies.py
```

## 3. 内容差异分析（两边都存在的文件）

DIFF: shared/manifest.py  (v6=      66 lines, repo=      61 lines, delta=5)
DIFF: shared/rule_loader.py  (v6=     111 lines, repo=      63 lines, delta=48)
DIFF: shared/__init__.py  (v6=      17 lines, repo=       2 lines, delta=15)
DIFF: shared/prompt_render.py  (v6=     347 lines, repo=      64 lines, delta=283)
DIFF: shared/pattern_loader.py  (v6=      88 lines, repo=      69 lines, delta=19)
DIFF: shared/project_loader.py  (v6=     101 lines, repo=      76 lines, delta=25)
DIFF: shared/prompt_loader.py  (v6=     101 lines, repo=      79 lines, delta=22)
DIFF: shared/schema.py  (v6=     392 lines, repo=      33 lines, delta=359)
