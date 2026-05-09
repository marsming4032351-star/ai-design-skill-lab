"""Skill registry for the Design Harness M1 skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


@dataclass(frozen=True)
class SkillSpec:
    """Registered callable capability.

    M1 records entrypoints only; it does not execute them.
    """

    id: str
    entrypoint: Path
    description: str = ""
    risk_level: str = "low"

    def __post_init__(self) -> None:
        object.__setattr__(self, "entrypoint", Path(self.entrypoint))
        if self.risk_level not in VALID_RISK_LEVELS:
            raise ValueError(
                f"risk_level must be one of {sorted(VALID_RISK_LEVELS)}, got {self.risk_level!r}"
            )


class SkillRegistry:
    """In-memory registry of harness skills."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillSpec] = {}

    def register(
        self,
        skill_id: str,
        entrypoint: str | Path,
        *,
        description: str = "",
        risk_level: str = "low",
    ) -> SkillSpec:
        skill = SkillSpec(
            id=skill_id,
            entrypoint=Path(entrypoint),
            description=description,
            risk_level=risk_level,
        )
        self._skills[skill.id] = skill
        return skill

    def get(self, skill_id: str) -> SkillSpec | None:
        return self._skills.get(skill_id)

    def require(self, skill_id: str) -> SkillSpec:
        skill = self.get(skill_id)
        if skill is None:
            raise KeyError(f"skill {skill_id!r} is not registered")
        return skill

    def ids(self) -> list[str]:
        return sorted(self._skills)
