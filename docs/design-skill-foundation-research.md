# Design Skill Foundation Research

Date: 2026-05-04

Scope: cloned and reviewed `openai/skills`, `anthropics/skills`, and `VoltAgent/awesome-agent-skills` in `~/ai-design-skill-lab/repos/`. This report is limited to Skill foundation research and a safe `design-ingest` prototype. No Obsidian vault or production design assets were modified.

## Repository Snapshot

| Repository | Local path | Reviewed commit |
|---|---|---|
| `openai/skills` | `repos/openai-skills` | `af9b54f` from 2026-05-01, `add hatch skill (#384)` |
| `anthropics/skills` | `repos/anthropics-skills` | `d230a6d` from 2026-05-03, `Remove non-existent purpose field from Files API examples (#1081)` |
| `VoltAgent/awesome-agent-skills` | `repos/awesome-agent-skills` | `23d2395` from 2026-05-03, `Merge pull request #510 from voidborne-d/add-humanize-chinese` |

## Key Findings

`openai/skills` is the best Codex distribution reference. Its README frames Agent Skills as folders of instructions, scripts, and resources that Codex can discover and use. Its repository structure separates `.system` and `.curated` skills, and many curated skills include `agents/openai.yaml`, `assets/`, `references/` or `reference/`, examples, and evaluations.

`anthropics/skills` is the best authoring and rich-package reference. It has many complete examples for Claude, including document skills with scripts, design/brand skills, and `skill-creator`, whose own structure explicitly documents `SKILL.md`, `scripts/`, `references/`, and `assets/` as the reusable bundle anatomy.

`VoltAgent/awesome-agent-skills` is not a direct foundation to clone for implementation. It is an index and discovery layer across many official and community skills. It is valuable for finding adjacent ideas such as Figma, Notion, visual review, product design review, image generation, PDF processing, content modeling, and design-system skills.

## Closest Skill Examples

### For `design-ingest`

- `openai/notion-knowledge-capture`: strongest analogy for turning messy context into structured, linkable knowledge records. Borrow its database/reference schema pattern, examples folder, and clear stepwise workflow.
- `anthropics/pdf`: strongest analogy for deterministic document helpers. Borrow script-first handling for PDF extraction/OCR later.
- `openai/screenshot`: useful pattern for bundled OS-specific scripts and safety preflight. Borrow the idea that scripts prevent agents from re-deriving fragile commands.
- `openai/figma`: useful for design context acquisition and asset handling, especially if later ingest supports Figma URLs or MCP.

### For `design-run`

- `openai/notion-spec-to-implementation`: closest pattern for turning a project entry/spec into tasks and execution plans.
- `openai/linear`: useful if future design tasks are represented as workflow tickets.
- `anthropics/mcp-builder`: useful as a workflow skill with scripts and references when external systems are involved.

### For `design-critic`

- `anthropics/brand-guidelines`: strongest simple example for applying visual identity rules.
- `anthropics/canvas-design`: useful as a high-level design philosophy and craft-quality evaluation reference, though it is generative rather than critical.
- `garrytan/plan-design-review` and `garrytan/design-review` from the VoltAgent index: useful references for rubric-driven design review, rating dimensions, and AI-output critique.
- `microsoft/frontend-design-review` from the VoltAgent index: useful for a review-style skill, but should be inspected directly before borrowing.

## Structure Comparison

| Repository | Skill structure | Suitable for Codex | Suitable for Claude Code | Supports scripts | Suitable for `design-ingest` | Borrow | Avoid |
|---|---|---:|---:|---:|---:|---|---|
| `openai/skills` | `skills/.system/<skill>/SKILL.md`, `skills/.curated/<skill>/SKILL.md`, plus optional `agents/`, `assets/`, `references/` or `reference/`, `examples/`, `evaluations/`, `scripts/` | High | Medium to high, if kept to Agent Skills standard | Yes, examples include scripts such as `screenshot/scripts` | High | Codex-compatible packaging, install/distribution thinking, `agents/openai.yaml`, Notion knowledge capture, Figma MCP patterns, safety-focused scripts | Some skills are connector-specific; not all are reusable outside Codex or MCP setup |
| `anthropics/skills` | `skills/<skill>/SKILL.md`, optional `scripts/`, `references/`, `assets/`, `agents/`, templates, document-specific reference files | Medium to high, if no Claude-only assumptions | High | Yes, document and skill-creator examples use scripts heavily | High | Best complete Skill authoring examples, progressive disclosure, script/reference/assets anatomy, document/PDF handling | Some document skills are proprietary/source-available; some examples are Claude-product-specific |
| `VoltAgent/awesome-agent-skills` | Single curated README index with links to external Skill sources | Medium as discovery source only | Medium as discovery source only | Not directly | Medium as research map, low as code base | Broad market map, design/visual/PDF/Notion/Figma references, security warning for third-party skills | Not a direct implementation base; linked skills require separate audit and cloning |

## Recommended Foundation

Use a hybrid foundation:

1. Use `anthropics/skills` as the authoring model because it has the clearest mature Skill folder anatomy.
2. Use `openai/skills` as the Codex compatibility and packaging model because it reflects how Codex discovers, distributes, and installs curated skills.
3. Use `VoltAgent/awesome-agent-skills` only as a discovery radar for adjacent design review, visual AI, Figma, Notion, and document-processing skills.

For the first Design Data Factory skill, start from the `anthropics/skill-creator` anatomy plus the `openai/notion-knowledge-capture` workflow style. Do not start by forking an entire repository. Create a focused first-party skill folder that is portable across Codex and Claude Code.

## Design Data Factory Skill Standard

Recommended standard directory:

```text
design-ingest/
├── SKILL.md
├── scripts/
│   └── scan_inbox.py
├── references/
│   ├── classification-rules.md
│   └── obsidian-schema.md
├── assets/
│   └── .gitkeep
├── examples/
│   └── optional sample manifests and notes
└── evals/
    └── optional test prompts and expected outputs
```

### `SKILL.md`

Put the trigger description, safety boundaries, end-to-end workflow, required confirmation gates, output contract, and short script usage examples here. Keep it concise enough to load into context whenever the skill triggers. It should tell the agent what to do and when to load deeper references.

### `references/`

Put domain rules that are too detailed for the main skill:

- Design industry taxonomy.
- Classification rules for poster, space, soft decoration, brand, proposal, process, and reference materials.
- Obsidian frontmatter schema.
- Naming conventions.
- Archive status model.
- Future scoring rubrics for `design-critic`.

The agent should read only the relevant reference file for the current task.

### `scripts/`

Put deterministic helpers:

- Inbox inventory.
- Hashing and duplicate detection.
- File type detection.
- PDF text extraction or thumbnail extraction.
- Manifest generation.
- Markdown note generation.
- Dry-run validation.

Scripts should default to non-destructive behavior and print exactly what they write.

### `assets/`

Put reusable static material:

- Markdown note templates.
- Example frontmatter.
- Placeholder icon or preview template.
- Optional taxonomy seed files.
- Future style/rubric cards.

Avoid placing real client assets here.

### Compatibility With Codex and Claude Code

Use the common Agent Skills convention: one folder per skill and a required `SKILL.md` with YAML frontmatter containing at least `name` and `description`.

Keep the skill runtime portable:

- Prefer Python standard library for first-pass scripts.
- Document optional dependencies but do not auto-install them.
- Avoid hard-coded absolute paths to Obsidian or client folders.
- Default to staging output, not direct vault mutation.
- Keep examples in shell commands that both Codex and Claude Code can reason about.
- Add Codex-specific metadata such as `agents/openai.yaml` only later if distribution requires it; do not make it required for core behavior.

## First Skill Set Proposal

### 1. `design-ingest`

Purpose: convert raw design folders into staged Markdown knowledge assets.

Initial scope:

- Scan inbox.
- Classify files by folder/filename/media type.
- Hash files.
- Produce `manifest.jsonl`.
- Produce `asset-index.md`.
- Mark uncertain items as review queue.

Later opt-in scope:

- OCR and PDF text extraction.
- Image captioning.
- Thumbnail generation.
- Duplicate clustering.
- Obsidian note generation.
- Vault write mode.

### 2. `design-run`

Purpose: use a project entry note to drive a design workflow.

Likely inputs:

- Project brief.
- Current stage.
- Deliverables.
- Asset links.
- Open questions.

Likely outputs:

- Next action plan.
- Task checklist.
- Required references.
- Review checkpoints.

### 3. `design-critic`

Purpose: review design outputs with a domain rubric.

Likely rubric dimensions:

- Strategy fit.
- Visual hierarchy.
- Brand consistency.
- Spatial/material coherence.
- Craft and detail.
- Cultural signal.
- Production feasibility.
- Reuse potential.

### 4. `design-archive`

Purpose: promote approved design outputs into reusable assets.

Likely outputs:

- Pattern notes.
- Reuse tags.
- Final asset package manifest.
- Links from project notes to asset library notes.

## Generated Prototype

Prototype path:

```text
~/ai-design-skill-lab/prototypes/design-ingest/
├── SKILL.md
├── references/
│   ├── classification-rules.md
│   └── obsidian-schema.md
├── scripts/
│   └── scan_inbox.py
└── assets/
```

The current `scan_inbox.py` is a minimal implementation:

- Uses only Python standard library.
- Reads source files.
- Computes SHA-256 hashes.
- Classifies by folder and filename keywords.
- Writes `manifest.jsonl` and `asset-index.md`.
- Does not move, rename, delete, or edit source assets.
- Does not write to Obsidian.

## Next Step: Obsidian Integration

Do not connect directly to the Obsidian vault yet. The next implementation stage should add a staged write mode:

1. User provides vault path and confirms the staging folder, for example `DesignOS/00_Inbox_Staging/`.
2. Script validates the vault path exists and contains expected marker folders.
3. Script generates notes into a separate staging run folder.
4. User reviews `asset-index.md` and low-confidence records.
5. Only after confirmation, copy or link selected assets into the vault structure.
6. Keep original source folders untouched unless a later `design-archive` skill explicitly handles asset promotion.

Recommended next implementation checkpoint:

- Add `--write-notes` for staged Markdown note generation.
- Add `--vault-staging-path` but keep it disabled unless explicitly passed.
- Add collision-safe note naming.
- Add tests using a synthetic inbox under the lab directory.

## Pause Gate

This research phase is complete when the user reviews the report and prototype. Do not install dependencies, run scanners on real design folders, modify Obsidian, or move assets until the user confirms the implementation phase.
