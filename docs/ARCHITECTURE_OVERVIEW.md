# Architecture Overview

Date: 2026-05-08
Status: Harness M3 overview

## Plain-English Summary

The Harness is a small runtime for AI-native design work.

Instead of asking an AI model for one image and stopping there, the Harness treats design work as a lifecycle: define a goal, plan the work, generate a mock visual, critique it, retry if needed, ask for review, and archive what passed.

The current implementation is deterministic. It uses mock stages and does not call real LLMs. That makes the runtime behavior easy to test and reason about.

## Runtime

The Runtime is the coordinator.

It receives a `TaskSpec`, creates a `RunContext`, runs each stage, records results, and decides what happens next. It owns the state machine:

```text
planner -> generator -> critic -> review -> archive
```

In M3, the Runtime also owns the retry loop:

```text
generator -> critic -> feedback -> generator -> critic
```

## Lifecycle

The lifecycle is the ordered path a design task follows.

Each stage returns a `StepResult`. The runtime stores every result in `step_history`, so a run can be inspected after it finishes.

For a retrying run, `step_history` intentionally shows repeated generator and critic steps:

```text
planner
generator
critic
generator
critic
archive
```

That history is important because it shows how many attempts were made and which stage produced each result.

## Event System

The event system is the runtime audit trail.

`event_log` records what happened during the run:

- run started
- step started
- step finished
- critic failed
- retry started
- retry finished
- critic passed
- review requested
- review approved or rejected
- run finished

`step_history` answers "what did each stage return?" `event_log` answers "what happened over time?"

## Review Loop

The review loop is the governance gate before archive.

When the critic passes, the runtime requests review for archive. If review is approved, the archive stage runs. If review is rejected, the runtime stops and records `final_state` as `REVIEW_REQUIRED`.

The demo uses the default reviewer, which auto-approves. The runtime still records the review events so the governance point is visible.

## Critic System

The critic system evaluates the generated mock visual.

In M3, the critic is deterministic. It reads configured decisions such as `pass` or `fail` from task inputs. This keeps tests stable and avoids any dependency on live models.

When the critic fails, it also returns mock feedback. The runtime stores that feedback so the next generator attempt can use it.

## Retry Mechanism

The retry mechanism turns critic failure into another generation attempt.

The runtime tracks:

- `retry_count`: how many retries have started
- `max_retries`: how many retries are allowed

If critic fails and retry budget remains, the runtime records `retry_started`, sends feedback to the generator, and runs generator/critic again. After the retry critic finishes, it records `retry_finished`.

If critic still fails after the retry budget is exhausted, the run stops before archive and records `final_state` as `FAILED`.

## Archive System

The archive system promotes a passing result into reusable design knowledge.

In the current mock Harness, archive creates a deterministic pattern record from the passing visual and critique. In later milestones, archive should connect more deeply to memory so successful patterns can influence future planning.

Archive is deliberately after critic and review. That keeps the design memory clean: only accepted outputs should become reusable patterns.
