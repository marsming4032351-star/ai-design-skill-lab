from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import pattern_loader, recommendation_engine, rule_loader


def test_run_design_help_imports_dependency_chain() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_design.py"), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "design-run skill" in result.stdout
    assert "--patterns-dir" in result.stdout
    assert "pre-check: Think" in result.stdout
    assert "execution: Surgical" in result.stdout
    assert "post-check: Verify" in result.stdout


def test_pattern_recommendation_loads_rule_and_increments_reuse_count(tmp_path: Path) -> None:
    pattern_path = tmp_path / "pat_test.md"
    pattern_path.write_text(
        """---
id: pat_test
type: pattern
title: Test Pattern
status: active
created_at: '2026-05-04T00:00:00Z'
applicable_when:
  project_types: [poster_campaign]
  categories: [poster]
  stages: [concept]
reuse_score: 1.0
reuse_count: 2
---
# Pattern
""",
        encoding="utf-8",
    )

    patterns = pattern_loader.load_patterns(tmp_path)
    rules = rule_loader.load_rules(ROOT / "references" / "40_Rules")
    ctx = recommendation_engine.ProjectContext(
        project_id="prj_test",
        project_type="poster_campaign",
        deliverable_categories=["poster"],
        brief_signals=[],
        stage="concept",
    )

    recommendations = recommendation_engine.recommend_patterns(
        rules["rul_recommend_pattern"],
        list(patterns.values()),
        ctx,
        now=datetime(2026, 5, 5, tzinfo=timezone.utc),
    )

    assert [r.pattern_id for r in recommendations] == ["pat_test"]
    assert pattern_loader.increment_reuse_count(pattern_path) == 3
    assert "reuse_count: 3" in pattern_path.read_text(encoding="utf-8")
