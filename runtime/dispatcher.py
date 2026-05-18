"""Agent dispatcher for the lightweight file-driven runtime."""

from __future__ import annotations

from typing import Any

from agents.design_critic.executor import execute_design_critic


def dispatch_agent(run: dict[str, Any]) -> bool:
    """Dispatch the current run to a real local executor when one exists.

    Returns True when a real executor handled the run, otherwise False so the
    runtime can continue using its generic mock behavior.
    """

    if run.get("current_agent") == "design_critic":
        execute_design_critic(run)
        return True
    return False
