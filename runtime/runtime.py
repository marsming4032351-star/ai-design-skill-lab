"""File-driven runtime for lightweight design agents.

This module intentionally stays small: YAML run records are the source of
truth, queue folders are filesystem markers, and agent execution is mocked.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from runtime.dispatcher import dispatch_agent
except ModuleNotFoundError:  # pragma: no cover - exercised by direct script execution
    from dispatcher import dispatch_agent


QUEUE_STATUSES = ("pending", "running", "review", "done")
APPROVAL_THRESHOLD = 8
SHA_TZ = timezone(timedelta(hours=8))


def run_once(
    runs_dir: Path | str = Path("runs"),
    queue_dir: Path | str = Path("queue"),
) -> list[dict[str, str | None]]:
    runs_path = Path(runs_dir)
    queue_path = Path(queue_dir)
    _ensure_queues(queue_path)

    results: list[dict[str, str | None]] = []
    for run_file in sorted(runs_path.glob("*.yaml")):
        if _is_template_run(run_file):
            continue
        run = _load_run(run_file)
        before = run.get("status")
        _advance_run(run)
        after = run.get("status")
        _save_run(run_file, run)
        _write_queue_reference(queue_path, runs_path, run_file, run)
        results.append(
            {
                "run_id": str(run.get("run_id") or run_file.stem),
                "from_status": _string_or_none(before),
                "to_status": _string_or_none(after),
            }
        )
    return results


def _advance_run(run: dict[str, Any]) -> None:
    status = run.get("status") or "pending"
    agent = run.get("current_agent") or _choose_next_agent(run)
    run["current_agent"] = agent
    run.setdefault("history", [])

    if status == "pending":
        _mock_execute_agent(run, agent)
        _transition(
            run,
            from_status="pending",
            to_status="running",
            action="mock_execute_agent",
            summary=f"Assigned {agent} and started mock execution.",
        )
        return

    if status == "running":
        next_agent = _choose_next_agent(run)
        run["current_agent"] = next_agent
        run["current_step"] = f"Review output with {next_agent}."
        _transition(
            run,
            from_status="running",
            to_status="review",
            action="route_to_review",
            summary=f"Mock output is ready; routed to {next_agent}.",
            next_agent=next_agent,
        )
        return

    if status == "review":
        if dispatch_agent(run):
            _append_history(
                run,
                from_status="review",
                to_status="review",
                action="execute_design_critic",
                summary="Executed local rule-based Design Critic.",
                next_agent=None,
            )
        score = run.get("review_score")
        approved = run.get("approved")
        if approved is None:
            score = APPROVAL_THRESHOLD
            approved = True
            run["review_score"] = score
            run["approved"] = approved
        if approved and int(score or 0) >= APPROVAL_THRESHOLD:
            next_agent = _choose_next_agent(run, approved=True)
            run["current_agent"] = next_agent
            run["next_action"] = "Archive or publish approved output."
            _transition(
                run,
                from_status="review",
                to_status="done",
                action="approve_mock_review",
                summary="Mock review approved the output.",
                next_agent=next_agent,
            )
            return
        next_agent = _choose_next_agent(run, approved=False)
        run["current_agent"] = next_agent
        run["next_action"] = "Revise output according to review notes."
        _transition(
            run,
            from_status="review",
            to_status="running",
            action="route_retry",
            summary="Mock review requested revision.",
            next_agent=next_agent,
        )
        return

    if status in {"done", "archived"}:
        _sync_history(run, status, "noop_done", "Run is already closed.")
        return

    if status == "blocked":
        _sync_history(run, status, "noop_blocked", "Run remains blocked.")
        return

    run["status"] = "blocked"
    run["next_action"] = f"Unsupported status: {status}"
    _sync_history(run, "blocked", "unsupported_status", run["next_action"])


def _mock_execute_agent(run: dict[str, Any], agent: str) -> None:
    outputs = run.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        outputs = {"notes": str(outputs)}
        run["outputs"] = outputs
    outputs["notes"] = f"Mock executed {agent}; no LLM API was called."
    run["next_action"] = "Continue to the next runtime state."


def _choose_next_agent(run: dict[str, Any], approved: bool | None = None) -> str:
    requested_next = run.get("next_agent")
    if approved is None and requested_next:
        return str(requested_next)

    if approved is True:
        return "publisher"
    if approved is False:
        return "prompt_optimizer"

    status = run.get("status")
    current = run.get("current_agent")
    if status == "running":
        return "design_critic"
    if not current:
        return "design_ingest"
    return str(current)


def _transition(
    run: dict[str, Any],
    *,
    from_status: str,
    to_status: str,
    action: str,
    summary: str,
    next_agent: str | None = None,
) -> None:
    run["status"] = to_status
    _append_history(run, from_status, to_status, action, summary, next_agent)


def _sync_history(run: dict[str, Any], status: str, action: str, summary: str) -> None:
    _append_history(run, status, status, action, summary, None)


def _append_history(
    run: dict[str, Any],
    from_status: str | None,
    to_status: str | None,
    action: str,
    summary: str,
    next_agent: str | None,
) -> None:
    entry: dict[str, Any] = {
        "at": datetime.now(SHA_TZ).replace(microsecond=0).isoformat(),
        "agent": "orchestrator",
        "from_status": from_status,
        "to_status": to_status,
        "action": action,
        "summary": summary,
        "review_score": run.get("review_score"),
        "approved": run.get("approved"),
    }
    if next_agent:
        entry["next_agent"] = next_agent
    run.setdefault("history", []).append(entry)


def _ensure_queues(queue_dir: Path) -> None:
    for status in QUEUE_STATUSES:
        (queue_dir / status).mkdir(parents=True, exist_ok=True)


def _write_queue_reference(
    queue_dir: Path,
    runs_dir: Path,
    run_file: Path,
    run: dict[str, Any],
) -> None:
    run_id = str(run.get("run_id") or run_file.stem)
    for status in QUEUE_STATUSES:
        ref = queue_dir / status / f"{run_id}.yaml"
        if ref.exists():
            ref.unlink()

    status = str(run.get("status") or "pending")
    queue_status = status if status in QUEUE_STATUSES else "pending"
    target = queue_dir / queue_status / f"{run_id}.yaml"
    relative = _relative_reference(target.parent, run_file)
    target.write_text(f"{relative}\n", encoding="utf-8")


def _relative_reference(from_dir: Path, to_file: Path) -> str:
    try:
        return to_file.relative_to(from_dir).as_posix()
    except ValueError:
        import os

        return os.path.relpath(to_file, from_dir)


def _load_run(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Run file must contain a mapping: {path}")
    return data


def _is_template_run(path: Path) -> bool:
    return path.name == "run_template.yaml"


def _save_run(path: Path, run: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(run, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the lightweight file-driven Agent Runtime once.")
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--queue-dir", type=Path, default=Path("queue"))
    args = parser.parse_args()

    results = run_once(runs_dir=args.runs_dir, queue_dir=args.queue_dir)
    for result in results:
        print(f"{result['run_id']}: {result['from_status']} -> {result['to_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
