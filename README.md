# Design Data Factory v6

Design Data Factory is an AI-powered design production system that turns design work into reusable, structured data assets.

It models a complete loop:

```text
ingest -> run -> critic -> archive -> pattern reuse
                -> generate -> critic-visual -> archive
```

Instead of treating design as static files, this repository treats assets, prompts, rules, plans, critiques, runs, and patterns as versioned knowledge that can be inspected, tested, and reused.

## Product Architecture

![Design Data Factory product architecture](docs/assets/design-data-factory-architecture.png)

## Why This Exists

Design teams repeatedly solve similar problems: collect source material, interpret a brief, generate directions, review quality, preserve what worked, and reuse it later. Design Data Factory makes that loop explicit and operable by agents.

The result is a small but complete foundation for a "Design OS":

- structured design data stored as Markdown frontmatter, JSONL, and YAML;
- deterministic dry-run execution for local testing;
- prompt, rule, and schema entities that can evolve independently;
- pattern recommendation so past work influences future runs;
- audit-friendly run logs for every major step.

## Core Workflow

| Stage | Script | Output | Purpose |
|---|---|---|---|
| Ingest | `scripts/scan_inbox.py` | `manifest.jsonl`, asset notes, run log | Structure raw design files into Asset entities |
| Run | `scripts/run_design.py` | Plan Markdown, Plan JSONL, prompt snapshot, run log | Generate concept directions from project context |
| Critic | `scripts/critic_design.py` | Critique Markdown, Critique JSONL, run log | Score a direction with rubric rules |
| Archive | `scripts/archive_design.py` | Pattern Markdown, Pattern JSONL, run log | Promote a passed direction into reusable knowledge |
| Generate | `scripts/generate_design.py` | Visual Markdown/JSONL, manifest.jsonl, run log | Turn Plan directions into visual posters via Lovart or mock |

## Key Features

- **Closed-loop design memory**: archive successful directions into Patterns, then recommend those Patterns in later runs.
- **Agent-operable pipeline**: CLI scripts expose each workflow step with explicit inputs and outputs.
- **Structured entities**: Project, Asset, Prompt, Rule, Plan, Critique, Pattern, and Run records use parseable frontmatter.
- **Dry-run first**: core scripts work without live LLM calls, making the pipeline testable and safe by default.
- **LLM hook support**: `--llm hook --llm-hook <path>` allows real model calls without coupling providers into the core scripts.
- **Auditable by design**: prompt snapshots, JSONL outputs, consumed assets, consumed patterns, and run logs make decisions traceable.

## Repository Layout

```text
.
├── scripts/        # CLI entry points: ingest, run, critic, archive
├── shared/         # loaders, schema validation, prompt rendering, engines
├── references/     # sample projects, prompts, rules, patterns, schemas, runs
├── tests/          # focused regression tests
├── docs/           # project notes and Codex operating guide
└── imports/        # historical imports and merge snapshots
```

## Quick Start

Check the repository:

```bash
git status --short --branch
python3 scripts/run_design.py --help
python3 -m pytest -q
```

Run the test suite:

```bash
python3 -m pytest -q
```

Generate a concept Plan from an existing Project and manifest:

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --patterns-dir references/30_Patterns \
  --rules-dir references/40_Rules \
  --llm dry-run
```

Generate a Visual from a Plan direction:

```bash
python3 scripts/generate_design.py \
  --plan <run-output-dir>/<plan-id>.md \
  --direction dir_001 \
  --out <generate-output-dir> \
  --llm dry-run
```

Or generate from a manual prompt (no Plan needed):

```bash
python3 scripts/generate_design.py \
  --prompt "暗调留白风格，高端餐饮海报" \
  --manifest <staging-dir>/manifest.jsonl \
  --asset-ids ast_abc123 \
  --out <generate-output-dir> \
  --llm dry-run
```

Review a generated direction:

```bash
python3 scripts/critic_design.py \
  --plan <run-output-dir>/<plan-id>.md \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --direction dir_001 \
  --rules-dir references/40_Rules \
  --prompts-dir references/50_Prompts \
  --out <critic-output-dir> \
  --llm dry-run
```

## Data Model

The pipeline is built around durable entities:

- `Project`: project brief, deliverables, overrides, and run history.
- `Asset`: classified source material with hash, category, family role, and evidence.
- `Prompt`: structured instruction template with declared inputs and output schema.
- `Rule`: classification, recommendation, or rubric logic.
- `Plan`: generated concept directions and next actions.
- `Critique`: weighted score, decision, strengths, weaknesses, and feedback.
- `Pattern`: reusable design knowledge extracted from accepted work.
- `Visual`: generated image/poster entity with provenance, hash, and style metadata.
- `Run`: audit record for a pipeline execution.

## LLM Integration

The safe default is `--llm dry-run`. For real model calls, use hook mode:

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --patterns-dir references/30_Patterns \
  --rules-dir references/40_Rules \
  --llm hook \
  --llm-hook ./scripts/<your_llm_hook>
```

The hook receives rendered prompt JSON on stdin and must write model output JSON to stdout. Keep API keys out of the repository.

## Documentation

- [Codex 操作指南](docs/CODEX_GUIDE.md): how to use Codex safely in this repository.
- [v6 Change Notes](docs/CHANGES.md): current v6 behavior and architecture decisions.
- [v6 Diff Report](docs/v6_diff_report.md): merge comparison report.
- [Design Skill Foundation Research](docs/design-skill-foundation-research.md): background research notes.

## Development Notes

- This repository currently has no root `requirements.txt`, `pyproject.toml`, or Makefile.
- `pytest` is used directly for tests.
- PyYAML is required by the frontmatter loader.
- Keep generated or experimental outputs in staging directories unless they are intentionally promoted into `references/`.
- Do not commit secrets, live API keys, or private client assets.

## Vision

Build the Design OS for the AI era: a system where design knowledge is structured, reusable, traceable, and continuously improved by each run.
