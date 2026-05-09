# Runtime Flow

This diagram describes the current AI Native Design Runtime lifecycle: human goal intake, deterministic Harness execution, review boundary, retry loop, blocked state, and archive flow.

## Runtime Lifecycle

```mermaid
flowchart LR
    human[Human Goal] --> task[TaskSpec]
    task --> runtime[HarnessRuntime]
    runtime --> context[RunContext]
    context --> planner[Planner]
    planner --> generator[Generator]
    generator --> critic[Critic]
    critic -->|pass| review{review_required?}
    critic -->|fail and retry_count < max_retries| retry[Retry Loop]
    retry --> generator
    critic -->|fail and retries exhausted| failed[FAILED]
    review -->|yes| humanReview[Human Review Boundary]
    review -->|no| archive[Archive]
    humanReview -->|approved| archive
    humanReview -->|needs changes| retry
    archive --> pattern[Reusable Pattern Memory]
    archive --> finished[ARCHIVED]
```

## Human Review Boundary

```mermaid
flowchart TD
    run[Runtime Run] --> gate{Requires human decision?}
    gate -->|no| auto[Continue automatic execution]
    gate -->|yes| pause[Pause runtime]
    pause --> queue[Review Queue]
    queue --> human[Human approves, rejects, or changes goal]
    human -->|approve| continue[Continue]
    human -->|request changes| retry[Retry with feedback]
    human -->|reject| stopped[STOPPED]
```

## Retry Loop

```mermaid
sequenceDiagram
    participant G as Generator
    participant C as Critic
    participant R as HarnessRuntime

    G->>C: candidate output
    C->>R: failed with feedback
    R->>R: increment retry_count
    alt retry_count < max_retries
        R->>G: regenerate with critic feedback
        G->>C: revised output
        C->>R: pass
    else retries exhausted
        R->>R: final_state = FAILED
    end
```

## Blocked State

```mermaid
flowchart TD
    runtime[HarnessRuntime] --> external{External boundary?}
    external -->|no| execute[Continue execution]
    external -->|yes| classify[Classify blocked state]
    classify --> auth[WAITING_AUTH]
    classify --> permission[BLOCKED_EXTERNAL]
    classify --> human[WAITING_HUMAN]
    auth --> action[Show required human action]
    permission --> action
    human --> action
    action --> pause[Pause instead of infinite retry]
    pause --> resume[Resume after human confirms boundary is cleared]
```

## Archive Flow

```mermaid
flowchart LR
    passed[Critic Passed Output] --> review{Review Required}
    review -->|yes| approval[Human Approval]
    review -->|no| archive[Archive]
    approval --> archive
    archive --> event[append archive event]
    archive --> memory[pattern memory]
    archive --> report[Feishu / README / Git report]
```

## Runtime OS Architecture

```mermaid
flowchart TB
    goal[Human Goal] --> codex[Codex Worker]
    codex --> harness[Harness Runtime]
    harness --> planner[Planner]
    harness --> generator[Generator]
    harness --> critic[Critic]
    harness --> review[Review Required]
    harness --> retry[Retry Count / Max Retries]
    harness --> blocked[Blocked State]
    harness --> eventlog[Event Log]
    harness --> history[Step History]
    harness --> archive[Archive]
    archive --> memory[Design Memory]
    eventlog --> dashboard[Runtime Dashboard]
    history --> timeline[Runtime Timeline]
    review --> human[Human Boundary]
    dashboard --> feishu[Feishu Workspace]
    timeline --> feishu
    codex --> git[Git / GitHub]
```
