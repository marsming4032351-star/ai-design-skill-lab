# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

Start with `MAP.md`. It is the current source of truth for repository structure, task routing, and the boundary between the Pipeline and Harness Runtime. Use this file as Claude-specific execution guidance after the route is clear.

## Project: Design Data Factory v6

An AI-powered design production system that turns design work into reusable, structured data assets. The pipeline models a closed loop: `ingest → run → critic → archive → pattern reuse`.

The repository now has two independent systems:

- **Design Data Factory Pipeline** (`scripts/` + `shared/`): asset production through single-step CLIs.
- **Harness Runtime** (`harness/`): deterministic mock lifecycle for Goal → Plan → Generate → Critic → Review → Archive. It does not currently call Pipeline CLIs or consume the `shared/` asset engines.

## Key Commands

```bash
# Run all tests
python3 -m pytest -q

# Validate MAP.md before documentation or routing changes
python3 scripts/lint_map.py

# Run a single test
python3 -m pytest tests/test_run_design_dependencies.py -q

# Show CLI help for any pipeline stage
python3 scripts/run_design.py --help
python3 scripts/scan_inbox.py --help
python3 scripts/critic_design.py --help
python3 scripts/archive_design.py --help

# Dry-run a concept plan (safe default, no LLM calls)
python3 scripts/run_design.py --project <project.md> --manifest <manifest.jsonl> \
  --prompts-dir references/50_Prompts --out <output-dir> \
  --patterns-dir references/30_Patterns --rules-dir references/40_Rules \
  --llm dry-run

# Real LLM calls via hook
python3 scripts/run_design.py ... --llm hook --llm-hook ./hooks/manual_relay_hook.py
```

## Dependencies

- Python 3 (no root `requirements.txt` or `pyproject.toml`)
- `pytest` for testing
- `pyyaml` — required by `shared/frontmatter.py`
- No Makefile or build system

## Architecture

`MAP.md` is the routing document. Keep this section as implementation notes, not a replacement for MAP.

### Pipeline Stages

| Stage | Script | Input | Output |
|---|---|---|---|
| Ingest | `scripts/scan_inbox.py` | Raw design files | `manifest.jsonl`, asset notes |
| Run | `scripts/run_design.py` | Project + manifest + prompts | Plan Markdown + JSONL |
| Critic | `scripts/critic_design.py` | Plan + project + rubric | Critique Markdown + JSONL |
| Archive | `scripts/archive_design.py` | Critique + plan | Pattern Markdown + JSONL |

### Module Layout

- **`scripts/`** — CLI entry points. Each script is self-contained with explicit `--project`, `--manifest`, `--prompts-dir`, `--out` arguments.
- **`shared/`** — Core library. No circular dependencies; scripts import from shared.
  - `schema.py` — Validates frontmatter dicts for asset, run, plan, critique, pattern entities
  - `frontmatter.py` — PyYAML-based Markdown frontmatter parser (read/write)
  - `prompt_render.py` — Renders prompt templates with `{{var}}` substitution and block synthesis
  - `prompt_loader.py`, `rule_loader.py`, `project_loader.py`, `plan_loader.py`, `critique_loader.py`, `pattern_loader.py` — Entity loaders
  - `rule_engine.py`, `rubric_engine.py` — Weighted scoring engines
  - `recommendation_engine.py` — Pattern recommendation from history (4-dimension weighted)
  - `manifest.py` — Asset manifest handling
  - `entity_updater.py` — Frontmatter field updates
- **`references/`** — Sample data. `10_Projects/`, `30_Patterns/`, `40_Rules/`, `50_Prompts/`, `90_Runs/`, `schemas/`
- **`hooks/`** — LLM hooks for real model calls
- **`tests/`** — Focused regression tests

### Entity Data Model

All entities use Markdown files with YAML frontmatter. Core fields: `id`, `type`, `schema_version`, `created_at`, `updated_at`, `status`, `created_by`.

- **Asset** (`ast_<hash[:12]>`) — Classified source material with sha256 hash, category, family role
- **Run** (`run_<skill>_<timestamp>_<hash>`) — Audit record for pipeline execution
- **Plan** (`pln_<hash>`) — Generated concept directions with next actions
- **Critique** (`crt_<hash>`) — Weighted rubric score with pass/revise/fail decision
- **Pattern** (`pat_<name>`) — Reusable design knowledge with `reuse_score`, `reuse_count`, `core_elements`

### LLM Integration

- `--llm dry-run` (default): deterministic, no external calls, safe for testing
- `--llm hook --llm-hook <path>`: pipe rendered prompt to external model via stdin/stdout JSON protocol
- `--llm live`: direct LLM calls (not yet fully implemented)

### Key Design Decisions

- Pattern recommendation is built into design-run, not a separate skill. Logic lives in Rule entities (`rul_recommend_pattern`) for independent versioning
- Both rubric scoring and pattern recommendation share the same `weighted` engine
- `--pattern pat_id` forces inclusion even if not in library (user override)
- brief signals use conservative lexicon matching (not embeddings) for pattern recommendation
- validation dimension caps `reuse_count` at 5 to prevent winner-takes-all
