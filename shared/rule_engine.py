"""Rule engine for Design Data Factory.

Runs keyword/regex rules and the hybrid router. The router implementation
mirrors the 8-step flow declared in rul_class_router.md, but only the steps
the engine can execute today (steps 1-7). LLM fallback (step 8) is opt-in
and currently a no-op.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .rule_loader import Rule, filter_rules


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class AssetCandidate:
    """Subject of classification — a single file."""
    path: str            # absolute path string
    extension: str       # ".pdf" etc, lowercase, with dot

    @property
    def parts_lower(self) -> str:
        return self.path.lower().replace("\\", "/")


@dataclass
class RuleHit:
    """Single rule's verdict on a file."""
    rule_id: str
    rule_version: str
    category: str | None
    confidence: str | None              # high | medium | low | None
    evidence: list[str] = field(default_factory=list)
    precedence: int = 0


@dataclass
class Classification:
    """Final classification produced by the router."""
    category: str
    confidence: str
    evidence: list[str]
    needs_review: bool
    family_role: str | None = None
    conflicts: dict[str, Any] | None = None
    rules_used: list[tuple[str, str]] = field(default_factory=list)  # (id, version)


# ---------------------------------------------------------------------------
# Engine: run a single keyword rule
# ---------------------------------------------------------------------------

def run_keyword_rule(rule: Rule, candidate: AssetCandidate) -> RuleHit:
    """Execute a keyword rule against a candidate. Returns a hit (possibly empty)."""
    body = rule.body
    haystack = candidate.parts_lower
    case_sensitive = bool(body.get("case_sensitive", False))
    if not case_sensitive:
        haystack = haystack.lower()

    keywords = list(body.get("keywords") or [])
    keyword_hits: list[str] = []
    for kw in keywords:
        needle = kw if case_sensitive else kw.lower()
        if needle in haystack:
            keyword_hits.append(kw)

    # Extension hints
    ext_hints = body.get("extension_hints") or {}
    high_exts = set(ext_hints.get("high_signal") or [])
    medium_exts = set(ext_hints.get("medium_signal") or [])
    ext_high = candidate.extension in high_exts
    ext_medium = candidate.extension in medium_exts

    # Filename pattern hints (regex) — used by process rule
    pattern_hits: list[str] = []
    pattern_hint_strength = 0  # 0 none, 1 medium, 2 high
    pattern_hints = body.get("filename_pattern_hints") or []
    if pattern_hints:
        filename = candidate.path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        for ph in pattern_hints:
            if not isinstance(ph, dict):
                continue
            pat = ph.get("pattern")
            if not pat:
                continue
            try:
                if re.search(pat, filename):
                    pattern_hits.append(pat)
                    weight = (ph.get("weight") or "").lower()
                    if weight == "high" and pattern_hint_strength < 2:
                        pattern_hint_strength = 2
                    elif weight == "medium" and pattern_hint_strength < 1:
                        pattern_hint_strength = 1
            except re.error:
                continue

    # Path / folder boost (used by reference rule)
    path_hint_high = False
    path_hints = body.get("path_signal_hints") or {}
    folder_keywords = list(path_hints.get("folder_keywords") or [])
    if folder_keywords:
        # Match any folder segment
        segments = candidate.parts_lower.split("/")
        for seg in segments:
            for fk in folder_keywords:
                if fk.lower() in seg:
                    path_hint_high = True
                    break
            if path_hint_high:
                break

    # Decide outcome
    scoring = body.get("scoring") or {}
    output = body.get("output") or {}
    base_category = output.get("category")
    base_confidence = output.get("base_confidence", "medium")

    high_threshold = int(scoring.get("keyword_hits_required_for_high", 2))
    medium_threshold = int(scoring.get("keyword_hits_required_for_medium", 1))
    extension_only_conf = scoring.get("extension_only_confidence")

    n_hits = len(keyword_hits)
    evidence: list[str] = []
    confidence: str | None = None

    if path_hint_high:
        confidence = "high"
        evidence.append(f"folder match: {','.join(folder_keywords[:3])}...")
    elif n_hits >= high_threshold:
        confidence = "high"
    elif n_hits >= max(medium_threshold, 1):
        confidence = "medium"
    elif n_hits == 0 and ext_high and extension_only_conf:
        confidence = extension_only_conf
        evidence.append(f"extension: {candidate.extension} (high signal, no keyword)")
    elif n_hits == 0 and ext_medium and extension_only_conf == "low":
        confidence = "low"
        evidence.append(f"extension: {candidate.extension}")

    # Pattern bonus (process rule)
    if confidence is None and pattern_hint_strength > 0:
        confidence = "medium" if pattern_hint_strength == 2 else "low"
    elif confidence == "medium" and pattern_hint_strength == 2:
        confidence = "high"

    # Combine extension boost when keywords also hit
    if confidence == "medium" and (ext_high or ext_medium) and n_hits >= 1:
        confidence = "high" if (ext_high and n_hits >= 1) else confidence

    # Evidence assembly
    if keyword_hits:
        evidence.append(f"{base_category}: {', '.join(keyword_hits[:5])}")
    if ext_high or ext_medium:
        evidence.append(f"extension: {candidate.extension}")
    if pattern_hits:
        evidence.append(f"filename pattern: {pattern_hits[0]}")

    if confidence is None:
        return RuleHit(
            rule_id=rule.id,
            rule_version=rule.version,
            category=None,
            confidence=None,
            evidence=[],
            precedence=rule.precedence,
        )

    # Apply base_confidence cap ONLY when the rule explicitly opts in.
    # process rule sets cap_at_base=true to prevent its inherent ambiguity from
    # producing high confidence; other rules with base_confidence=medium (like
    # reference, where folder-match is genuinely strong) should not be capped.
    if scoring.get("cap_at_base", False) and base_confidence == "medium" and confidence == "high":
        confidence = "medium"

    return RuleHit(
        rule_id=rule.id,
        rule_version=rule.version,
        category=base_category,
        confidence=confidence,
        evidence=evidence,
        precedence=rule.precedence,
    )


# ---------------------------------------------------------------------------
# Router: implement rul_class_router logic in Python
# ---------------------------------------------------------------------------

CONFIDENCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}
CLOSE_TIE_DELTA = 50


def classify(
    candidate: AssetCandidate,
    registry: dict[str, Rule],
) -> Classification:
    """Run the classification pipeline on a candidate.

    Mirrors rul_class_router steps 1-7. Step 8 (LLM fallback) is opt-in and
    currently disabled.
    """
    # Step 1: collect candidates from all classification rules (excluding router itself)
    classification_rules = [
        r for r in filter_rules(registry, domain="classification")
        if r.engine == "keyword"
    ]
    rules_used: list[tuple[str, str]] = []
    hits_all: list[RuleHit] = []
    for rule in classification_rules:
        hit = run_keyword_rule(rule, candidate)
        rules_used.append((rule.id, rule.version))
        hits_all.append(hit)

    # Step 2: filter
    hits = [h for h in hits_all if h.category is not None]

    # Step 3: path context boost — bump candidates whose category appears in
    # the file's parent path. Both directions matter:
    #   /软装/moodboard/foo.jpg  → boost soft-decoration over reference
    #   /参考/some_logo.png      → boost reference over brand
    # Reference gets a slightly larger boost because folder names in CJK
    # ("参考", "案例", "竞品") are unambiguous "this is reference material".
    CATEGORY_FOLDER_KEYWORDS = {
        "reference": ["reference", "refs", "参考", "案例", "竞品", "调研",
                      "灵感", "inspiration", "research"],
        "brand": ["brand", "品牌", "vi", "logo"],
        "poster": ["poster", "海报", "kv", "活动", "campaign"],
        "space": ["space", "interior", "空间", "展厅", "展陈", "门店"],
        "soft-decoration": ["soft", "软装", "家具", "moodboard"],
        "proposal": ["proposal", "方案", "提案", "汇报"],
        "process": ["process", "draft", "迭代", "草稿"],
    }
    path_lower = candidate.parts_lower
    segments = path_lower.split("/")
    parent_segments = segments[:-1]  # exclude the file's own name
    boost_log: list[str] = []
    for h in hits:
        kws = CATEGORY_FOLDER_KEYWORDS.get(h.category, [])
        for seg in parent_segments:
            if any(kw.lower() in seg for kw in kws):
                bonus = 25 if h.category == "reference" else 20
                h.precedence += bonus
                boost_log.append(f"{h.category}:+{bonus} (folder)")
                break

    # Step 4: process is a co-category, not main
    family_role: str | None = None
    process_evidence: list[str] = []
    if any(h.category == "process" for h in hits) and len([h for h in hits if h.category != "process"]) >= 1:
        process_hits = [h for h in hits if h.category == "process"]
        for ph in process_hits:
            process_evidence.extend(ph.evidence)
        hits = [h for h in hits if h.category != "process"]
        family_role = "variant"

    # Step 7: no hits → unknown
    if not hits:
        return Classification(
            category="unknown",
            confidence="low",
            evidence=["no rule matched"],
            needs_review=True,
            family_role=family_role,
            conflicts=None,
            rules_used=rules_used,
        )

    # Step 5: single hit
    if len(hits) == 1:
        top = hits[0]
        evidence = list(top.evidence)
        if process_evidence:
            evidence.append(f"process signals: {'; '.join(process_evidence[:2])}")
        confidence = top.confidence or "low"
        needs_review = confidence != "high"
        return Classification(
            category=top.category,
            confidence=confidence,
            evidence=evidence,
            needs_review=needs_review,
            family_role=family_role,
            conflicts=None,
            rules_used=rules_used,
        )

    # Step 6: multi-hit ranking
    def score(h: RuleHit) -> float:
        return h.precedence + CONFIDENCE_WEIGHT.get(h.confidence or "low", 0) * 100

    ranked = sorted(hits, key=score, reverse=True)
    top, second = ranked[0], ranked[1]
    delta = score(top) - score(second)

    final_conf = top.confidence or "low"
    if delta < CLOSE_TIE_DELTA:
        # Downgrade by one level
        if final_conf == "high":
            final_conf = "medium"
        elif final_conf == "medium":
            final_conf = "low"

    evidence: list[str] = []
    for h in ranked:
        evidence.extend(h.evidence)
    if process_evidence:
        evidence.append(f"process signals: {'; '.join(process_evidence[:2])}")

    conflicts = {
        "candidates": [h.category for h in ranked],
        "scores": {h.category: round(score(h), 2) for h in ranked},
        "delta": round(delta, 2),
    }
    needs_review = (delta < CLOSE_TIE_DELTA) or (final_conf != "high")

    return Classification(
        category=top.category,
        confidence=final_conf,
        evidence=evidence,
        needs_review=needs_review,
        family_role=family_role,
        conflicts=conflicts,
        rules_used=rules_used,
    )
