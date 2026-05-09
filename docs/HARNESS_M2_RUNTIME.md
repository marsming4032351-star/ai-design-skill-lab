# Harness M2 Runtime

Date: 2026-05-08
Status: Implemented mock runtime

## Goal

Harness M2 proves that `HarnessRuntime` can orchestrate a complete task lifecycle without changing the existing Design Data Factory pipeline.

The lifecycle is:

```text
planner -> generator -> critic -> review -> archive
```

This is intentionally not a complex Agent system. It is a minimal runtime exercise that validates task orchestration, context state, step history, event logging, and review gates.

## Files Added

```text
harness/
├── archive.py
├── critic.py
├── events.py
├── generator.py
└── planner.py

tests/test_harness_runtime_execution.py
docs/HARNESS_M2_RUNTIME.md
```

## Files Extended

```text
harness/runtime.py
harness/task.py
```

## Runtime Behavior

`HarnessRuntime.run(task, workspace=...)` creates a new `RunContext` with:

- `run_id`: generated as `run_harness_<timestamp>_<hash>`
- `workspace`: caller-provided workspace path
- `artifacts_dir`: `<workspace>/harness_runs/<run_id>`
- `state`: mutable runtime state
- `step_history`: ordered list of `StepResult`
- `event_log`: ordered list of `RuntimeEvent`

M2 uses harness-native mock stages only. It does not execute `scripts/run_design.py`, `scripts/critic_design.py`, `scripts/archive_design.py`, or any other existing CLI.

## Step Results

Every lifecycle stage returns a `StepResult`:

- `planner`: creates mock plan state.
- `generator`: creates mock visual state from the plan.
- `critic`: creates mock critique state with deterministic dry-run decision.
- `archive`: creates mock archive state when critique decision is `pass`.

If review rejects archive, the archive step is represented by a rejected `StepResult`, so every attempted lifecycle still has explicit history.

## Runtime Events

M2 adds `RuntimeEvent` in `harness/events.py`.

Current event sequence for a successful run:

```text
run_started
step_started
step_finished
step_started
step_finished
step_started
step_finished
review_requested
review_approved
step_started
step_finished
run_finished
```

The event log is intentionally simple and in-memory. It is a foundation for later persistence into Run records.

## Review Loop

M2 adds the smallest useful review gate before archive:

- If no reviewer is configured, the runtime auto-approves with reason `no reviewer configured`.
- If a reviewer rejects, runtime records `review_rejected`, appends a rejected archive `StepResult`, and finishes without archive state.
- If a reviewer approves, runtime records `review_approved` and proceeds to archive.

This keeps human governance visible without adding UI, external services, or provider calls.

## Non-Goals

- No real LLM calls.
- No external APIs.
- No changes to existing ingest/run/critic/archive scripts.
- No workflow YAML loader.
- No durable Run Store.
- No artifact writes from runtime stages.
- No provider abstraction beyond mock stage functions.

## Verification

Run the M2 focused tests:

```bash
python3 -m pytest tests/test_harness_runtime_execution.py -q
```

Run the full suite:

```bash
python3 -m pytest -q
```

Expected result: all tests pass, including existing M1 and Design Data Factory tests.
