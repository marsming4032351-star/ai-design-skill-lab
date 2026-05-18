# Runs

This directory stores lightweight Agent Runtime run records.

Each `*.yaml` file represents one task instance and should follow `run_template.yaml`.

## Required Runtime Fields

- `run_id`
- `project_name`
- `task`
- `current_agent`
- `current_step`
- `status`
- `inputs`
- `outputs`
- `review_score`
- `approved`
- `next_action`
- `history`

## Status Values

- `pending`
- `running`
- `review`
- `done`
- `blocked`
- `archived`

## History Rule

`history` is append-only. Every state transition or major review should append an entry with time, agent, status change, action, summary, and decision fields where relevant.
