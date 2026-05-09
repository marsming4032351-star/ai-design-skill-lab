# Harness Blocked State Design

Date: 2026-05-09
Status: Design note, no implementation

## Purpose

Harness M3 already models deterministic retry for critic feedback. That retry loop is useful when the next attempt can be improved by agent-controlled input, such as generator feedback from a failed critique.

The same retry behavior is wrong for external dependencies. When a run reaches a boundary that only a human or an external authority can resolve, the runtime should stop trying and enter an explicit blocked or waiting state.

Recent examples include:

- `lark-cli config init --new`
- OAuth login and consent
- external authorization screens
- human confirmation before a write, delete, publish, or ownership transfer

These are not transient model-quality failures. The agent cannot autonomously repair them. Retrying consumes time and obscures the true state of the run.

## Current Problem

### Agent Infinite Retry

The current M3 mental model has a retryable pair:

```text
generator -> critic -> feedback -> generator -> critic
```

That loop assumes the failure can be corrected by new generated output. This assumption does not hold for blocked external operations.

If a command waits for OAuth or user configuration, repeated attempts usually create more pending sessions instead of progress. The runtime needs to distinguish "try again with better input" from "pause until someone else acts."

### Human Boundary Is Not Explicit

The current runtime can record review events, but it does not yet have a general state for human boundaries outside the archive review gate.

That means several different situations can collapse into the same rough behavior:

- waiting for a user to open an authorization link
- waiting for a user to approve a risky filesystem or Git operation
- waiting for an external app to grant a token
- waiting for missing configuration to be restored
- waiting for a human decision that changes the allowed next action

These are different from ordinary failure and should be visible in `state`, `event_log`, and operator-facing output.

### External Dependency Detection Is Missing

The runtime also needs a way to recognize operations that depend on external systems. Examples:

- a command prints an OAuth URL and blocks
- a CLI returns a config or keychain error
- a tool asks for user approval
- a connector reports missing scope or permission
- a process reaches a timeout while waiting for browser or account interaction

Without detection, the runtime can only see "the step did not finish." That is too coarse for an AI runtime.

## Proposed Runtime States

The following states should be added as design-level runtime outcomes or intermediate statuses.

| State | Meaning | Typical Resume Condition |
|---|---|---|
| `WAITING_HUMAN` | Runtime needs human input, approval, or a decision before continuing. | Human provides the requested answer or approval. |
| `WAITING_AUTH` | Runtime needs authentication, OAuth consent, scope grant, or credential repair. | User completes auth/config and the runtime verifies credentials. |
| `BLOCKED_EXTERNAL` | Runtime is blocked by an external system or dependency that the agent cannot fix. | External dependency becomes available, or operator chooses an alternate path. |
| `PAUSED` | Runtime intentionally stopped at a safe checkpoint. | Operator resumes the same run or cancels it. |
| `RESUMABLE` | Runtime has enough persisted context to continue from a known step. | Runtime receives a resume command with the prior run context. |

These states should be separate from `FAILED`. A failed run means the runtime reached a terminal negative outcome. A blocked run means progress is possible after external action.

## When Runtime Should Pause

The runtime should pause instead of retrying when any of these conditions appear:

1. A step requires OAuth, browser login, QR scan, consent, or account selection.
2. A CLI reports missing credentials, missing keychain entry, missing scope, or permission denied that requires user or admin action.
3. A command is waiting for human input and has produced an actionable instruction, such as an authorization URL.
4. A requested operation is high risk and requires explicit human confirmation.
5. A tool call is blocked by external service state, quota, account policy, or app installation.
6. A timeout occurs while waiting for a human or external system, and retrying cannot change the input.
7. The next action would duplicate pending external requests, such as launching multiple auth flows.

The key rule is:

```text
Retry only when the agent can change the next attempt.
Pause when progress depends on a human or external authority.
```

## Human Resume Flow

A blocked runtime should preserve enough context for a clean resume.

Suggested flow:

```text
1. detect blocked condition
2. record blocked event
3. set runtime state to WAITING_HUMAN, WAITING_AUTH, or BLOCKED_EXTERNAL
4. persist resume context
5. surface exact human action required
6. stop active retry loop
7. wait for operator resume
8. verify precondition
9. record runtime_resumed
10. continue from the next safe step
```

The resume context should include:

- `run_id`
- `blocked_state`
- `blocked_step`
- `blocked_reason`
- `required_human_action`
- `resume_after`
- `safe_to_retry_command`
- `pending_external_reference`, such as an auth URL or request id when safe to store
- prior `step_history`
- prior `event_log`

The runtime should not assume that human action succeeded. On resume, it should run a small verification step first, such as checking that credentials exist or that the required permission is now present.

## Event Log Additions

The event log should make blocked states first-class. Suggested new event types:

- `blocked_detected`: runtime identified that the current step cannot proceed autonomously.
- `waiting_human`: runtime is waiting for human input or confirmation.
- `auth_required`: runtime needs login, OAuth, scope grant, or credential repair.
- `runtime_paused`: runtime stopped at a safe checkpoint.
- `runtime_resumed`: runtime resumed after a human or external dependency changed.

Example event sequence:

```text
run_started
step_started
blocked_detected
auth_required
waiting_human
runtime_paused
runtime_resumed
step_started
step_finished
run_finished
```

These events should live alongside existing M3 events such as `critic_failed`, `retry_started`, `review_requested`, and `run_finished`.

## Why This Is Core To AI Runtime Design

AI runtimes are not just retry machines. They coordinate work across models, tools, files, accounts, external services, and humans.

The hardest failures are often not model failures. They are boundary failures:

- the model cannot grant OAuth consent
- the agent cannot approve a risky operation on behalf of the user
- a connector cannot access data without scope changes
- an external service can block, rate limit, or require account action
- a human needs to decide whether a side effect is allowed

If those boundaries are represented as ordinary failures, the runtime will either retry forever or hide the real reason it stopped. If they are represented as blocked states, the runtime becomes inspectable and governable.

For Harness specifically, blocked states protect the design memory loop. A run should not archive, promote, publish, or mutate long-lived knowledge after an unresolved external boundary. It should pause, explain the required human action, and resume only after the boundary has been cleared.

## Non-Goals

This document does not implement the state model.

It intentionally does not:

- modify `harness/runtime.py`
- modify `harness/task.py`
- add tests
- run `lark-cli`
- call OAuth or external authorization flows
- change the current M3 retry implementation

The immediate goal is to record the design requirement clearly before implementation.
