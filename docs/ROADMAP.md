# Roadmap

Date: 2026-05-08
Status: Harness M3 complete

## Positioning

The repository is evolving from Design Data Factory into an **AI Native Design Harness Runtime**.

The long-term direction is a Design Infrastructure OS: a runtime, memory, evaluator, and agent orchestration layer that makes AI-assisted design work repeatable, inspectable, reusable, and governable.

## Completed Milestones

### M1: Harness Skeleton

M1 established the minimum runtime shell:

- `TaskSpec`
- `RunContext`
- `StepResult`
- skill registry
- review decision model
- runtime entry point

The key constraint was safety: M1 resolved harness tasks without executing the existing production pipeline.

### M2: Runtime Execution

M2 proved the runtime can execute a full deterministic lifecycle:

```text
planner -> generator -> critic -> review -> archive
```

M2 added:

- mock planner
- mock generator
- mock critic
- mock archive
- `step_history`
- `event_log`
- CLI demo through `scripts/run_harness_demo.py`

### M3: Review And Retry Loop

M3 closed the minimum review loop:

```text
generate -> evaluate -> feedback -> retry -> re-evaluate
```

M3 added:

- `retry_count`
- `max_retries`
- critic feedback passed back to generator
- repeated generator/critic attempts in `step_history`
- `critic_failed`
- `critic_passed`
- `retry_started`
- `retry_finished`
- `final_state` values such as `ARCHIVED`, `FAILED`, and `REVIEW_REQUIRED`

## Runtime Evolution

The runtime should evolve in layers, with each layer remaining independently testable.

### Current Runtime

The current runtime is deterministic and local. It uses mock stages so lifecycle behavior can be verified without live model calls, external APIs, or changes to the existing scripts pipeline.

### M4: Memory

M4 should connect runtime output back into design memory:

- use archived patterns as planning context
- expose prior run history to future tasks
- make pattern reuse explicit in runtime state
- preserve deterministic tests for memory selection

### M5: Evaluator

M5 should add evaluation as a first-class runtime capability:

- golden design cases
- repeatable evaluator inputs and outputs
- regression tests for prompt, rule, critic, and generator behavior
- quality gates before archive or promotion

### M6: Multi-Agent Runtime

M6 should coordinate multiple specialized agents:

- planner agent
- generation agent
- critic agent
- memory agent
- archive agent
- human review gate

The goal is orchestration, not autonomy for its own sake. Each agent should have clear inputs, outputs, state transitions, and audit records.

## Long-Term Vision

The Harness should become the operating layer for AI-native design production.

It should answer questions that one-off generation cannot answer:

- What goal produced this design?
- What context and memory influenced it?
- What did the critic reject?
- What feedback changed the next attempt?
- Why was this artifact archived?
- Which patterns are reusable?
- Which runtime behavior is stable enough to automate?

The long-term system is a Design Infrastructure OS where design knowledge compounds across runs instead of disappearing after each model call.
