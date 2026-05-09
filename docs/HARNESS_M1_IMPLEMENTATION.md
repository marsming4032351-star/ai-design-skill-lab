# Harness M1 Implementation

Date: 2026-05-08
Status: Implemented skeleton

## Goal

M1 establishes the smallest Python skeleton for a Design Harness layer without changing the existing Design Data Factory pipeline behavior.

It adds structure for:

- `TaskSpec`
- `RunContext`
- `StepResult`
- `SkillRegistry`
- `ReviewDecision`
- `HarnessRuntime`

## Files Added

```text
harness/
├── registry.py
├── review.py
├── runtime.py
└── task.py

tests/test_harness_m1.py
docs/HARNESS_M1_IMPLEMENTATION.md
```

## Module Responsibilities

### `harness/task.py`

Defines the core task records:

- `TaskSpec`: a single requested harness step, including `skill_id`, inputs, metadata, and whether review is required.
- `RunContext`: run-level context such as `run_id`, workspace, artifacts directory, and metadata.
- `StepResult`: normalized result for a resolved harness step, including status, message, outputs, and errors.

### `harness/registry.py`

Defines the in-memory skill registry:

- `SkillSpec`: a registered capability with an id, entrypoint, description, and risk level.
- `SkillRegistry`: a minimal register/get/require API.

M1 keeps this in memory. It does not load YAML manifests yet.

### `harness/review.py`

Defines `ReviewDecision`, the small approval/rejection record used by runtime review gates.

### `harness/runtime.py`

Defines `HarnessRuntime`, which resolves a `TaskSpec` against `SkillRegistry` and applies an optional review callback.

Important M1 constraint: `HarnessRuntime.run_step()` does not execute the resolved entrypoint. It returns `executed: False` so existing `scripts/` behavior remains untouched.

## What M1 Does Not Do

- It does not call real LLMs.
- It does not call external APIs.
- It does not execute `scripts/run_design.py` or any other pipeline CLI.
- It does not modify existing `scripts/` or `shared/` modules.
- It does not add dependencies.
- It does not implement YAML registry loading, workflow execution, or evaluator reports.

## Verification

Run the M1 focused test:

```bash
python3 -m pytest tests/test_harness_m1.py -q
```

Run the full test suite:

```bash
python3 -m pytest -q
```

Expected result: all tests pass, and the existing Design Data Factory scripts continue to be imported and tested through the existing test suite.

## Next Step

The next incremental step should be a declarative registry layer, still without executing pipeline CLIs:

1. Add a small YAML or Markdown registry format under `harness/`.
2. Load it through `SkillRegistry`.
3. Test that registered entrypoints point to existing local files.
4. Keep runtime execution disabled until approval policy and workflow semantics are explicit.
