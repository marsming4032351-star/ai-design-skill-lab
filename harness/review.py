"""Human review primitives for the Design Harness M1 skeleton."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewDecision:
    """Decision returned by a harness review gate."""

    approved: bool
    reason: str = ""
    reviewer: str = "human"

    @classmethod
    def approve(cls, *, reason: str = "", reviewer: str = "human") -> "ReviewDecision":
        return cls(approved=True, reason=reason, reviewer=reviewer)

    @classmethod
    def reject(cls, *, reason: str, reviewer: str = "human") -> "ReviewDecision":
        return cls(approved=False, reason=reason, reviewer=reviewer)
