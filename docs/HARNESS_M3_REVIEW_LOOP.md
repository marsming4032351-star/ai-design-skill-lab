# Harness M3 Review Loop

Date: 2026-05-08
Status: implemented as a mock runtime loop

## Purpose

Harness M3 adds the smallest closed review loop on top of the M2 mock lifecycle:

```text
planner -> generator -> critic -> feedback -> retry -> critic -> review -> archive
```

The runtime still does not call real LLMs, external APIs, or the existing `scripts/` pipeline. All M3 behavior is deterministic and lives in the harness-native mock stages.

## Runtime Behavior

`HarnessRuntime.run()` now runs `planner` once, then runs `generator` and `critic` as a retryable pair.

If the critic decision is `pass`:

- the runtime records `critic_passed`
- the archive review gate is requested
- an approved review continues to `archive`
- `state["final_state"]` becomes `ARCHIVED` when archive succeeds

If the critic decision is not `pass`:

- the runtime records `critic_failed`
- the critic feedback is stored as `state["generator_feedback"]`
- if `retry_count < max_retries`, the runtime records `retry_started`, increments `retry_count`, and runs `generator` again
- after the retry critic finishes, the runtime records `retry_finished`
- if the retry still fails after `max_retries`, `state["final_state"]` becomes `FAILED`

If the archive review gate rejects, `state["final_state"]` becomes `REVIEW_REQUIRED`.

## Configuration

`max_retries` defaults to `1`. It can be supplied through the task inputs or at the top level of the demo YAML:

```yaml
max_retries: 1
inputs:
  critic_decision: pass
```

For deterministic tests, `critic_decisions` can provide one decision per attempt:

```yaml
inputs:
  critic_decisions:
    - fail
    - pass
```

The mock critic uses `retry_count` as the index into this list. If the list is exhausted, the final listed decision is reused.

## Observability

M3 keeps the M2 `step_history` behavior and intentionally records every generator and critic attempt. A failed-then-passed run has repeated entries:

```text
planner
generator
critic
generator
critic
archive
```

M3 adds these event types:

- `critic_failed`
- `critic_passed`
- `retry_started`
- `retry_finished`

The existing `review_requested`, `review_approved`, `review_rejected`, and `run_finished` events remain in place.

## Verification

The M3 test coverage includes:

- retry succeeds after an initial critic failure
- runtime stops with `FAILED` after exceeding `max_retries`
- `step_history` shows repeated generator and critic attempts
- `event_log` includes retry and critic pass/fail events

Run:

```bash
python3 -m pytest -q
python3 scripts/run_harness_demo.py examples/harness_goal.yaml
```
