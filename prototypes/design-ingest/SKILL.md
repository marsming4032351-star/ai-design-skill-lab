---
name: design-ingest
description: Use when a user wants to inventory, classify, describe, and prepare design files such as posters, spatial renders, soft-furnishing references, PDFs, proposals, moodboards, and image folders for a design knowledge base or Obsidian vault. Trigger for design asset intake, design archive preparation, project folder cleanup, visual material classification, and Design Data Factory ingestion.
---

# Design Ingest

Prepare raw design project files for a reusable design knowledge base.

This skill is for intake and metadata preparation, not for destructive file organization. Default to `--dry-run`, produce reviewable Markdown and JSONL manifests, and ask for confirmation before writing into a real Obsidian vault or moving source assets.

## Workflow

1. Confirm the inbox path, output path, project name, and whether the run is read-only.
2. Read `references/classification-rules.md` before classifying files.
3. Read `references/obsidian-schema.md` before generating Markdown.
4. Run `scripts/scan_inbox.py` in dry-run mode to create a manifest.
5. Review uncertain files with the user before generating vault notes.
6. Only after explicit confirmation, write Markdown notes or copy assets to the configured vault staging area.

## Safety Rules

- Never modify, rename, delete, or move source files during the first pass.
- Never write to an Obsidian vault unless the user provides the vault path and confirms a write run.
- Keep generated output in a staging folder by default.
- Preserve original filenames, paths, modified times, and hashes in metadata.
- Mark low-confidence classification as `needs_review`.

## Expected Inputs

- Inbox folder containing design files.
- Optional project name or client name.
- Optional Obsidian vault staging folder.
- Optional taxonomy override for the studio or project.

## Expected Outputs

- `manifest.jsonl`: one record per discovered file.
- `asset-index.md`: a human-readable summary grouped by category.
- One Markdown note per asset or per asset group when enabled.

## File Categories

Use these first-pass categories:

- `poster`: posters, campaign visuals, key art, event graphics.
- `space`: interior, exhibition, retail, installation, landscape, wayfinding, or architectural visuals.
- `soft-decoration`: furniture, textile, material, lighting, styling, prop, moodboard, and furnishing references.
- `brand`: logos, identity systems, typography, color, packaging, brand guideline pages.
- `proposal`: PDFs, decks, client proposals, quotations, and narrative plans.
- `process`: sketches, drafts, screenshots, wireframes, iterations, and working files.
- `reference`: inspiration, benchmark, competitor, cultural, and research materials.
- `unknown`: files that cannot be confidently classified.

## Script Usage

Dry-run scan:

```bash
python3 <skill-path>/scripts/scan_inbox.py --inbox "/path/to/inbox" --out "/path/to/staging"
```

With a project label:

```bash
python3 <skill-path>/scripts/scan_inbox.py --inbox "/path/to/inbox" --out "/path/to/staging" --project "Client Project"
```

The script currently performs filesystem inventory and rule-based classification only. Visual AI captioning, OCR, thumbnail generation, PDF page extraction, and Obsidian writes are planned extensions and must remain opt-in.

## Compatibility

Codex and Claude Code can both use this skill because it follows the Agent Skills folder pattern: `SKILL.md` for workflow instructions, `references/` for domain rules, `scripts/` for deterministic helpers, and `assets/` for reusable templates. Keep shell examples portable and avoid platform-specific dependencies unless documented.
