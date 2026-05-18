from pathlib import Path

import yaml

from runtime.runtime import run_once


def test_file_runtime_advances_pending_run_and_writes_queue_reference(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    queue_dir = tmp_path / "queue"
    runs_dir.mkdir()

    run_path = runs_dir / "sample.yaml"
    run_path.write_text(
        "\n".join(
            [
                'run_id: "run_sample"',
                'project_name: "Sample"',
                'task: "Test file runtime."',
                'current_agent: "design_ingest"',
                'current_step: "Collect input."',
                'status: "pending"',
                "inputs:",
                '  brief: "raw brief"',
                "outputs:",
                "  files: []",
                '  notes: ""',
                "review_score: null",
                "approved: null",
                'next_action: "Start."',
                "history: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    results = run_once(runs_dir=runs_dir, queue_dir=queue_dir)

    assert results == [{"run_id": "run_sample", "from_status": "pending", "to_status": "running"}]
    updated = yaml.safe_load(run_path.read_text(encoding="utf-8"))
    assert updated["status"] == "running"
    assert updated["current_agent"] == "design_ingest"
    assert updated["history"][-1]["action"] == "mock_execute_agent"
    assert (queue_dir / "running" / "run_sample.yaml").read_text(encoding="utf-8") == "../../runs/sample.yaml\n"
    assert not (queue_dir / "pending" / "run_sample.yaml").exists()


def test_file_runtime_uses_next_agent_when_routing_running_run_to_review(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    queue_dir = tmp_path / "queue"
    runs_dir.mkdir()

    run_path = runs_dir / "sample.yaml"
    run_path.write_text(
        "\n".join(
            [
                'run_id: "run_route"',
                'current_agent: "prompt_optimizer"',
                'next_agent: "design_critic"',
                'current_step: "Mock production."',
                'status: "running"',
                "outputs:",
                '  notes: "draft ready"',
                "review_score: null",
                "approved: null",
                'next_action: "Review draft."',
                "history: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_once(runs_dir=runs_dir, queue_dir=queue_dir)

    updated = yaml.safe_load(run_path.read_text(encoding="utf-8"))
    assert updated["status"] == "review"
    assert updated["current_agent"] == "design_critic"
    assert updated["history"][-1]["next_agent"] == "design_critic"
    assert (queue_dir / "review" / "run_route.yaml").exists()


def test_file_runtime_moves_approved_review_run_to_done(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    queue_dir = tmp_path / "queue"
    runs_dir.mkdir()

    run_path = runs_dir / "sample.yaml"
    run_path.write_text(
        "\n".join(
            [
                'run_id: "run_review"',
                'current_agent: "design_critic"',
                'current_step: "Review draft."',
                'status: "review"',
                "outputs:",
                '  notes: "reviewed"',
                "review_score: 9",
                "approved: true",
                'next_action: "Publish."',
                "history: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_once(runs_dir=runs_dir, queue_dir=queue_dir)

    updated = yaml.safe_load(run_path.read_text(encoding="utf-8"))
    assert updated["status"] == "done"
    assert updated["current_agent"] == "publisher"
    assert updated["approved"] is True
    assert updated["history"][-1]["action"] == "approve_mock_review"
    assert (queue_dir / "done" / "run_review.yaml").exists()


def test_file_runtime_calls_design_critic_executor_and_retries_failed_review(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    queue_dir = tmp_path / "queue"
    runs_dir.mkdir()

    run_path = runs_dir / "sample.yaml"
    run_path.write_text(
        "\n".join(
            [
                'run_id: "run_critic"',
                'current_agent: "design_critic"',
                'current_step: "Review poster."',
                'status: "review"',
                "inputs:",
                "  critique_flags:",
                "    text_overlap: true",
                "    font_too_small: true",
                "    visual_overload: false",
                "    style_mismatch: true",
                "outputs:",
                '  notes: "draft ready"',
                "review_score: null",
                "approved: null",
                'next_action: "Review."',
                "history: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    run_once(runs_dir=runs_dir, queue_dir=queue_dir)

    updated = yaml.safe_load(run_path.read_text(encoding="utf-8"))
    report = updated["outputs"]["review_report"]
    assert updated["status"] == "running"
    assert updated["current_agent"] == "prompt_optimizer"
    assert updated["approved"] is False
    assert updated["review_score"] < 8
    assert updated["recommendation"] == "retry"
    assert report["issues"]["text_overlap"]["failed"] is True
    assert report["issues"]["font_too_small"]["failed"] is True
    assert report["issues"]["visual_overload"]["failed"] is False
    assert report["issues"]["style_mismatch"]["failed"] is True
    assert updated["history"][-2]["action"] == "execute_design_critic"
    assert updated["history"][-1]["action"] == "route_retry"
    assert (queue_dir / "running" / "run_critic.yaml").exists()


def test_file_runtime_ignores_run_template_file(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    queue_dir = tmp_path / "queue"
    runs_dir.mkdir()

    template_path = runs_dir / "run_template.yaml"
    template_path.write_text(
        "\n".join(
            [
                'run_id: "run_YYYYMMDD_project_task"',
                'current_agent: "design_ingest"',
                'status: "pending"',
                "history: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    results = run_once(runs_dir=runs_dir, queue_dir=queue_dir)

    assert results == []
    assert yaml.safe_load(template_path.read_text(encoding="utf-8"))["status"] == "pending"
