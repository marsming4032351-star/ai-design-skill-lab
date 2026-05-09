# Runtime Evolution Architecture

Date: 2026-05-09
Status: Architecture narrative, no implementation

## Purpose

This document explains the architecture shift behind the current Harness Runtime work.

The important change is not just adding another script. The repository is moving from prompt-centered AI work toward a runtime-centered system: a system that can carry state, detect boundaries, retry when useful, pause when blocked, ask for review, archive accepted outputs, and later reuse memory.

In this direction, `ai-design-skill-lab` is best understood as an **AI Native Design Runtime OS**.

## Evolution: Prompt To Context To Harness To Runtime

### 1. Prompt

The first layer of AI work is the prompt.

A prompt can describe intent, style, constraints, and output format. It is useful, but it is not enough for durable work because it does not own:

- state
- retries
- review decisions
- tool execution
- memory
- external dependencies
- audit history

A prompt can ask for an output. It cannot reliably manage the lifecycle around that output.

### 2. Context

The next layer is context.

Context gives the model better inputs: project briefs, assets, patterns, rules, prior runs, schemas, and examples. In this repository, the Design Data Factory v6 layer already created much of that foundation through structured entities and loaders.

Context improves answer quality, but context alone is still passive. It can influence a model call, but it does not decide what happens after the call.

### 3. Harness

The Harness layer turns AI work into an inspectable lifecycle.

Instead of treating generation as a one-shot request, the Harness defines stages:

```text
goal -> planner -> generator -> critic -> review -> archive
```

It also defines normalized records such as `TaskSpec`, `RunContext`, `StepResult`, `ReviewDecision`, and `RuntimeEvent`. This makes design work observable instead of conversational only.

### 4. Runtime

The Runtime is the operating layer.

It owns the state machine, decides whether to continue, retry, pause, wait for a human, or finish. It is responsible for turning model and tool activity into a controlled process.

Runtime is where AI work becomes production infrastructure:

```text
intent + context + tools + memory + review + events + state = runtime
```

## Current Runtime Core Modules

### Lifecycle

Lifecycle defines the ordered path of a task.

Current M3 lifecycle:

```text
planner -> generator -> critic -> review -> archive
```

The runtime records each stage as a `StepResult` in `step_history`. If a retry happens, repeated generator and critic steps are intentionally preserved.

### Event System

The event system is the audit trail.

`event_log` answers what happened over time:

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

The event system is what turns a run from a black box into an inspectable process.

### Review Loop

The review loop is the governance point before archive.

If the critic passes, the runtime requests review before allowing archive. If review is approved, archive runs. If review is rejected, the runtime stops with `REVIEW_REQUIRED`.

This establishes an important principle: accepted design memory should be created only after evaluation and governance.

### Retry

Retry is useful only when the agent can change the next attempt.

In M3, retry is designed for critic feedback:

```text
generator -> critic -> feedback -> generator -> critic
```

The runtime tracks `retry_count` and `max_retries`. If the critic fails and budget remains, feedback is passed back to the generator. If retry budget is exhausted, the run ends as `FAILED`.

### Blocked State

Blocked state covers cases where retry is the wrong behavior.

When progress depends on a human or an external authority, the runtime should pause instead of retrying. Examples include OAuth, app configuration, missing credentials, external authorization, and human confirmation.

Proposed blocked states:

- `WAITING_HUMAN`
- `WAITING_AUTH`
- `BLOCKED_EXTERNAL`
- `PAUSED`
- `RESUMABLE`

Blocked state is not failure. It means the runtime reached a boundary it cannot cross autonomously.

### Archive

Archive promotes accepted output into reusable knowledge.

In the current mock Harness, archive creates a deterministic pattern record from the passing visual and critique. In the longer architecture, archive should become the promotion gate into design memory.

Archive should stay after critic and review. That ordering protects long-lived memory from unreviewed model output.

### Memory, Future

Memory is the next major runtime layer.

Future memory should let the runtime use prior patterns, run history, project context, and accepted decisions as planning input. It should make design knowledge compound across runs.

Memory should likely separate:

- working memory: temporary state within a run
- episodic memory: prior run records
- semantic memory: reusable patterns and design principles
- procedural memory: prompts, rules, skills, and agent manifests

### Evaluator, Future

Evaluator is the layer that makes quality measurable.

Future evaluator work should add repeatable cases and regression checks for prompts, rules, critic behavior, generator output, and archive decisions. It should support quality gates before promotion into memory.

Evaluator makes the runtime not just executable, but improvable.

## Runtime State Machine

Current and proposed states can be viewed as one larger state machine:

```text
                         +----------------+
                         |   run_started  |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         |    planner     |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         |   generator    |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         |     critic     |
                         +---+--------+---+
                             |        |
                      pass   |        | fail, retry budget remains
                             v        v
                    +-------------+  +----------------+
                    | review gate |  | retry_started  |
                    +------+------+  +--------+-------+
                           |                  |
             approved      |                  v
                           v          +----------------+
                    +-------------+   |   generator    |
                    |   archive   |<--+----------------+
                    +------+------+          |
                           |                 v
                           v          +----------------+
                    +-------------+   |     critic     |
                    |  ARCHIVED   |   +----------------+
                    +-------------+

             rejected
                |
                v
        +-----------------+
        | REVIEW_REQUIRED |
        +-----------------+

             fail, no retry budget
                |
                v
           +--------+
           | FAILED |
           +--------+

             human or external boundary detected anywhere
                |
                v
        +------------------+
        | blocked_detected |
        +---------+--------+
                  |
      +-----------+------------+
      |            |           |
      v            v           v
+-------------+ +--------------+ +------------------+
|WAITING_HUMAN| | WAITING_AUTH | | BLOCKED_EXTERNAL |
+------+------+ +------+-------+ +---------+--------+
       |               |                   |
       +---------------+-------------------+
                       |
                       v
                 +-----------+
                 |  PAUSED   |
                 +-----+-----+
                       |
                       v
                 +-----------+
                 | RESUMABLE |
                 +-----+-----+
                       |
                       v
              +-----------------+
              | runtime_resumed |
              +--------+--------+
                       |
                       v
              continue from safe step
```

## Human Boundary Detection

Human boundary detection is the runtime's ability to notice that progress depends on a person, account, or external authority.

Signals include:

- OAuth URL or browser login request
- QR scan requirement
- missing keychain entry or missing credential
- permission denied with required scope or admin action
- user confirmation needed before a risky side effect
- external service quota, installation, account, or policy block
- a timeout while waiting for human action

The design rule is:

```text
Retry when the agent can improve the next attempt.
Pause when progress requires a human or external authority.
```

This is a core runtime responsibility. Without it, a system can waste time, duplicate pending auth requests, or hide the real reason a task stopped.

## Why Runtime Matters More Than Prompt

Prompts are important, but they are not the operating system of AI work.

A prompt can shape one model response. A runtime shapes the full lifecycle:

- what goal is being pursued
- what context is loaded
- which tool or stage runs next
- what output contract must be satisfied
- whether a result should be critiqued
- whether retry is useful
- whether human review is required
- whether an external dependency blocks progress
- whether output can be archived into memory
- how the run can be audited or resumed

For real work, the durable advantage is not a clever prompt. It is the system that can repeatedly convert intent into governed, observable, reusable outcomes.

## Why Future AI Companies Become Runtime Companies

As models become more capable and more interchangeable, value moves upward into runtime.

Future AI companies will compete on:

- orchestration across models, tools, memory, and humans
- reliable state management
- evaluation and quality gates
- auditability and compliance
- human approval and blocked-state handling
- domain-specific memory and feedback loops
- safe side-effect execution
- replay, resume, and continuous improvement

The model is the engine, but the runtime is the operating system around the engine.

In that world, the best AI product is not only the one with the best prompt. It is the one with the best loop: the loop that can plan, act, evaluate, wait, resume, learn, and compound.

## ai-design-skill-lab Positioning

The current repository is no longer just a design prompt lab or a collection of scripts.

Its emerging position is:

```text
ai-design-skill-lab = AI Native Design Runtime OS
```

That means:

- design work is represented as lifecycle, not one-shot output
- prompts, rules, patterns, assets, critiques, and runs are structured knowledge
- runtime stages are explicit and inspectable
- review and blocked states are part of the system, not exceptions
- memory and evaluator layers become first-class future modules
- design knowledge should compound across runs

The short-term Harness M3 runtime is intentionally small and deterministic. That is the right foundation. A runtime OS should be testable before it becomes autonomous.

## Non-Goals

This document is architecture narrative only.

It does not:

- modify runtime code
- add tests
- run tests
- call external tools
- implement Memory or Evaluator
- change the current Harness M3 behavior
