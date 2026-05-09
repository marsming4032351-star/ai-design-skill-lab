from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run_harness_demo_executes_example_goal() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_harness_demo.py"),
            str(ROOT / "examples" / "harness_goal.yaml"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "run_id: run_harness_" in result.stdout
    assert "review_required: true" in result.stdout
    assert "retry_count: 0" in result.stdout
    assert "max_retries: 1" in result.stdout
    assert "final_state: ARCHIVED" in result.stdout
    assert "final state:" in result.stdout
    assert "step_history:" in result.stdout
    assert "event_log:" in result.stdout
    assert "task_demo_design_loop:planner" in result.stdout
    assert "task_demo_design_loop:generator" in result.stdout
    assert "task_demo_design_loop:critic" in result.stdout
    assert "task_demo_design_loop:archive" in result.stdout
    assert "critic_passed" in result.stdout
    assert "review_requested" in result.stdout
    assert "review_approved" in result.stdout
