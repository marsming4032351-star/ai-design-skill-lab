# Harness Usage

Date: 2026-05-08
Status: M3 demo entrypoint

## Purpose

This document shows how to manually run the current mock Harness runtime from a terminal.

The demo does not call real LLMs, external APIs, or existing Design Data Factory pipeline scripts. It reads a small YAML goal, creates a `TaskSpec`, and calls `HarnessRuntime.run()`.

## Run The Demo

From the repository root:

```bash
python3 scripts/run_harness_demo.py examples/harness_goal.yaml
```

The command prints:

- `run_id`
- `review_required`
- `retry_count`
- `max_retries`
- `final_state`
- `final state`
- `step_history`
- `event_log`

## Example Goal

The demo input is:

```text
examples/harness_goal.yaml
```

It defines a single mock design task:

```yaml
id: task_demo_design_loop
skill_id: design-harness
requires_review: true
workspace: output/harness_demo
max_retries: 1
inputs:
  brief: 高端冷感海报
  llm: dry-run
  critic_decision: pass
```

## Expected Behavior

The runtime executes this mock lifecycle when the critic passes on the first attempt:

```text
planner -> generator -> critic -> review -> archive
```

If the critic returns `fail`, the runtime sends the mock critic feedback back to the generator and retries the generator/critic pair until `max_retries` is exhausted:

```text
planner -> generator -> critic -> generator -> critic -> review -> archive
```

Each stage returns a `StepResult`. The `RunContext` keeps:

- `state`: final mock plan, visual, critique, and archive records
- `retry_count`: how many retry attempts were started
- `max_retries`: retry limit for critic failures, defaulting to `1`
- `step_history`: one result per lifecycle step, including repeated generator/critic attempts
- `event_log`: runtime events such as `run_started`, `critic_failed`, `retry_started`, `retry_finished`, `critic_passed`, `review_requested`, and `run_finished`

Because no custom reviewer is configured in the demo script, the review loop auto-approves archive with the existing M2 default review behavior.

For deterministic retry demos and tests, use a decision list:

```yaml
inputs:
  critic_decisions:
    - fail
    - pass
  max_retries: 1
```

If all attempts fail after `max_retries`, the runtime stops before archive and sets `final_state` to `FAILED`. If archive review rejects, it sets `final_state` to `REVIEW_REQUIRED`.

## Retry Fields

`retry_count` starts at `0`. It increments only when the runtime starts another generator attempt after a critic failure.

`max_retries` controls how many retry attempts are allowed. The default is `1`, which means the runtime can run one initial generator/critic attempt and one retry attempt.

`final_state` summarizes the terminal runtime outcome:

- `ARCHIVED`: critic passed, review approved, archive succeeded
- `FAILED`: critic or archive failed after the available retry budget
- `REVIEW_REQUIRED`: archive review was rejected or needs human follow-up

## Retry Flow

When the critic fails, the runtime does not archive immediately. It records the failure, stores critic feedback, and passes that feedback into the next generator call.

The second mock visual includes:

- `version: 2`
- `applied_feedback`: the feedback produced by the failing critic

This keeps the loop inspectable without connecting a real LLM.

## Event Log

`event_log` is the chronological runtime audit trail. It is separate from `step_history`.

Use `step_history` to inspect stage outputs. Use `event_log` to inspect runtime decisions and transitions.

Important M3 events:

- `critic_failed`: critic returned a non-pass decision
- `retry_started`: runtime started a retry attempt
- `retry_finished`: retry generator/critic attempt finished
- `critic_passed`: critic returned `pass`
- `review_requested`: runtime reached the archive governance gate
- `run_finished`: runtime reached a terminal state

## Verify

Run:

```bash
python3 -m pytest -q
python3 scripts/run_harness_demo.py examples/harness_goal.yaml
```

The first command should pass the test suite. The second should print all required runtime sections.
