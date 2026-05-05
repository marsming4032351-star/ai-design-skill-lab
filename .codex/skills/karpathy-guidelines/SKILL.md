---
name: karpathy-guidelines
description: Use when planning, editing, reviewing, or debugging code in this repository to keep Codex work assumption-aware, simple, surgical, and verified by explicit success criteria.
license: MIT
---

# Karpathy Guidelines for Codex

Use these behavioral rules to reduce common LLM coding mistakes in this repository. They are adapted for Codex from the Karpathy-inspired guidelines in `forrestchang/andrej-karpathy-skills`.

These rules bias toward caution over speed. For trivial one-line changes, apply the spirit without ceremony.

## 1. Think Before Coding

Before changing files, make the working assumptions explicit:

- State what you believe the user wants and what files or commands are relevant.
- If the request has multiple plausible meanings, surface the options instead of silently choosing.
- If a simpler path would meet the goal, say so and prefer it.
- If required context is missing and guessing would be risky, stop and ask a concise question.

Codex-specific rule: do not start implementation until the objective has a concrete success condition, even if the task is small.

## 2. Simplicity First

Prefer the smallest implementation that satisfies the verified goal:

- Do not add features, flags, config, abstractions, dependencies, or workflows that were not requested.
- Do not introduce single-use abstractions just to make code look more general.
- Do not add defensive handling for states that cannot occur in the current system.
- If a solution grows beyond the apparent scope, pause and simplify before continuing.

Codex-specific rule: match this repository's existing Python scripts, Markdown entities, and CLI patterns before inventing new structure.

## 3. Surgical Changes

Touch only what the request requires:

- Do not reformat, rename, or refactor adjacent code as a drive-by improvement.
- Do not delete unrelated files, generated history, imports, comments, or dead code that predates the task.
- If your change makes something unused, clean up only the unused artifact your change created.
- If unrelated problems are discovered, mention them separately instead of folding them into the patch.

Codex-specific rule: every staged file and every meaningful changed line must trace back to the current user goal.

## 4. Goal-Driven Execution

Turn every task into a verifiable goal:

- Define the artifact to create or change.
- Define the minimum checks that prove it works.
- For bug fixes, prefer a reproducing test before the fix.
- For docs-only changes, verify the target files, links, and rendered references.
- For code changes, run the relevant tests and report exact commands and results.

For multi-step tasks, use this shape:

```text
1. Change: <artifact or behavior> -> verify: <command or inspection>
2. Change: <artifact or behavior> -> verify: <command or inspection>
3. Publish: <commit/push/tag if requested> -> verify: <git evidence>
```

Codex-specific rule: do not claim completion until the success criteria have fresh evidence from the current workspace.

## Repository-Specific Defaults

- Start with `git status --short --branch` so unrelated local changes are visible.
- Use `rg` / `rg --files` for repository inspection.
- Use `apply_patch` for manual edits.
- Keep changes scoped to `scripts/`, `shared/`, `tests/`, `references/`, `docs/`, or `.codex/skills/` only when the task requires those paths.
- Ignore unrelated untracked local files unless the user asks to manage them.
- Run `python3 -m pytest -q` before commit/push when the task touches executable behavior or repository guidance.
- Before push, confirm `HEAD`, `origin/main`, and the intended commit.
