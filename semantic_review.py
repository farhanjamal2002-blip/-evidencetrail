"""Deterministic, fail-closed interpretation of *verified* CV evidence.

A CV's explicit task limitation does not by itself mean the CV contains
internally contradictory claims. This stage NEVER creates or deletes citations,
never changes the raw Muse label, and never establishes positive qualifications.

The function consumes already locally verified quote roles and retains the
underlying audit. Only evidence that has survived PDF-source grounding may be
supplied here. Empty/malformed citations are not treated as verified evidence.
"""
from __future__ import annotations

import re
from typing import Any

ABSENCE_ONLY = re.compile(
    r"\b(?:no|not|without|none)\b.{0,100}"
    r"\b(?:evidence|listed|mentioned|documented|shown|described|reported)\b"
    r"|\b(?:not|never)\s+(?:listed|mentioned|documented|shown|described|reported)\b",
    re.IGNORECASE,
)


# Minimal, auditable polarity check. A *job* criterion and a CV sentence
# disagreeing do not by themselves constitute two incompatible CV claims.
# This is intentionally conservative and never promotes a candidate to
# 'supported'. Ambiguous examples remain visible for human clarification.
REQUIREMENT_ACTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("negotiat", ("negotiat",)),
    ("led", ("led", "lead", "command")),
    ("lead", ("led", "lead", "command")),
    ("develop", ("develop", "deplo", "built", "wrote")),
    ("deploy", ("deplo", "shipp", "released")),
    ("configur", ("configur", "set up")),
    ("author", ("author", "wrote")),
    ("perform", ("perform", "conduct")),
    ("optimiz", ("optimiz", "tuned")),
    ("created", ("creat", "built", "entered")),
    ("approv", ("approv", "signed", "sign")),
    ("sign", ("sign", "approv")),
    ("coordinat", ("coordinat", "clear")),
    ("manag", ("manag", "owned", "chaired")),
    ("review", ("review", "audited")),
    ("delivered", ("deliver", "facilitat")),
    ("built", ("built", "designed", "creat")),
)
SCOPE_NEGATIVE = re.compile(
    r"\b(?:never|did not|didn't|not personally|not directly|"
    r"no (?:permission|authority|responsibility)|without|"
    r"director (?:led|approved)|manager (?:led|approved)|"
    r"a different team|another (?:colleague|person|team))\b",
    re.IGNORECASE,
)
FIRST_PERSON = re.compile(r"\b(?:I|my|personally)\b", re.IGNORECASE)
EXPLICIT_SELF_DENIAL = re.compile(
    r"\b(?:I (?:did not|never|have never|had never|was not)|"
    r"my (?:role|duties) did not|"
    r"no (?:direct|personal) (?:responsibility|authority|experience)|"
    r"never|did not|not the (?:negotiator|owner|lead)|"
    r"without (?:direct|personal) (?:responsibility|authority))\b",
    re.IGNORECASE,
)


def _first_action_synonyms(requirement: str) -> tuple[str, ...]:
    # The first action in the requirement is usually the required ownership.
    # "Personally LED supplier price NEGOTIATIONS" tests leadership, not just
    # proximity to a later noun containing the negotiation root.
    words = requirement.casefold()
    hits = [(words.index(stem),equivalents)
            for stem,equivalents in REQUIREMENT_ACTIONS if stem in words]
    return min(hits,key=lambda x:x[0])[1] if hits else ()


# Use complete verbal forms when interpreting personal ownership. Substring
# matching incorrectly treated "negotiation notes" as "negotiated" and the
# word "handled" as "led". Neither establishes the applicant's requested act.
VERB_FORM_PATTERNS = {
    "negotiat": r"\b(?:negotiat(?:e|ed|es|ing)|negotiator)\b",
    "led": r"\b(?:led|lead|leads|leading|leader)\b",
    "lead": r"\b(?:led|lead|leads|leading|leader)\b",
    "command": r"\b(?:command|commanded|commanding)\b",
    "author": r"\b(?:author|authored|authoring)\b",
    "wrote": r"\bwrote\b",
    "configur": r"\b(?:configure|configured|configures|configuring)\b",
    "perform": r"\b(?:perform|performed|performing)\b",
    "review": r"\b(?:review|reviewed|reviewing)\b",
    "approv": r"\b(?:approve|approved|approving)\b",
    "sign": r"\b(?:sign|signed|signing)\b",
    "deplo": r"\b(?:deploy|deployed|deploying)\b",
    "develop": r"\b(?:develop|developed|developing)\b",
    "creat": r"\b(?:create|created|creating)\b",
    "built": r"\b(?:built|build|building)\b",
    "enter": r"\b(?:entered|enter|entering)\b",
    "clear": r"\b(?:cleared|clearing|clear)\b",
    "optimiz": r"\b(?:optimize|optimized|optimizing)\b",
    "tuned": r"\b(?:tune|tuned|tuning)\b",
    "coordinat": r"\b(?:coordinate|coordinated|coordinating)\b",
    "manag": r"\b(?:manage|managed|managing)\b",
    "owned": r"\b(?:owned|owning|own)\b",
    "chaired": r"\b(?:chaired|chairing|chair)\b",
    "facilitat": r"\b(?:facilitate|facilitated|facilitating)\b",
    "deliver": r"\b(?:deliver|delivered|delivering)\b",
    "designed": r"\b(?:design|designed|designing)\b",
}
def _contains_applicant_action(clause: str, stem: str) -> bool:
    pattern = VERB_FORM_PATTERNS.get(stem)
    if pattern is None:
        # An unknown action alias is *not* sufficient to certify two
        # opposing personally owned claims. Keep source evidence available.
        return False
    if not re.search(pattern, clause, flags=re.IGNORECASE):
        return False
    if stem == "wrote":
        # "Wrote incident notes" does not establish authorship of SIEM
        # detections or production code; insist on a named technical object.
        return bool(re.search(r"\bwrote\b.{0,70}\b(?:rules?|detections?|pipelines?|python|etl|applications?|software|code)\b", clause, flags=re.IGNORECASE))
    return True


def _asserts_requested_personal_action(quote: str, action_words: tuple[str, ...]) -> bool:
    """Require a candidate-owned verb, not the same verb in a manager clause."""
    if not action_words:
        return False
    # Split clauses so 'I assembled notes; the director negotiated' cannot
    # turn into the applicant saying they personally negotiated.
    clauses = re.split(r"[;.!?]|\b(?:but|whereas|while)\b", quote, flags=re.IGNORECASE)
    for clause in clauses:
        if SCOPE_NEGATIVE.search(clause):
            continue
        cleaned = clause.strip().casefold()
        # Real CV bullet points often omit "I": "led all negotiations".
        first_person = bool(FIRST_PERSON.search(clause))
        verb_led_bullet = any(
            re.match(VERB_FORM_PATTERNS[stem], cleaned, flags=re.IGNORECASE)
            for stem in action_words if stem in VERB_FORM_PATTERNS
        )
        if not first_person and not verb_led_bullet:
            continue
        if any(_contains_applicant_action(cleaned, stem) for stem in action_words):
            return True
    return False


def _clear_internal_opposition(finding: dict[str, Any],
                               support: list[dict[str, Any]],
                               limiting: list[dict[str, Any]]) -> bool:
    actions = _first_action_synonyms(str(finding.get("requirement") or ""))
    if not actions:
        # Absence of a parsed criterion is not evidence it is safe to clear an
        # existing discrepancy; keep for human attention.
        return bool(support and limiting)
    affirmative = any(_asserts_requested_personal_action(str(q["quote"]), actions)
                      for q in support)
    denial = any(EXPLICIT_SELF_DENIAL.search(str(q["quote"])) for q in limiting)
    return bool(affirmative and denial)


def clarify_verified_findings(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Separate one-sided scope limitations from multiple documented claims.

    A *single* citation labeled contradicts is evidence against satisfying a
    specific requirement, not proof that the person's CV contradicts itself.
    Even two citations can be an ambiguous difference rather than a verified
    logical contradiction. Keep the original Muse proposal in raw_status,
    mark only possible multi-claim discrepancies for human clarification, and
    fail closed (no positive status can be created).

    Mutates findings in-place only after local quote verification and timeline
    adjudication. Safe to run again; results are idempotent.
    """
    counters = {
        "single_scope_limits_clarified": 0,
        "document_absences_clarified": 0,
        "multi_quote_discrepancies_retained": 0,
        "multi_quote_scope_clarifications": 0,
        "related_context_labeled": 0,
        "unchanged": 0,
    }
    for finding in findings:
        if not isinstance(finding, dict):
            counters["unchanged"] += 1
            continue
        status = str(finding.get("status", "not_found"))
        evidence_type = str(finding.get("evidence_type", "unsupported"))
        citations = [
            quote for quote in (finding.get("evidence") or [])
            if isinstance(quote, dict) and str(quote.get("quote", "")).strip()
            and isinstance(quote.get("page"), int)
            and not isinstance(quote.get("page"), bool) and quote["page"] >= 1
            and quote.get("role") in {"supports", "contradicts"}
        ]
        support = [q for q in citations if q["role"] == "supports"]
        limiting = [q for q in citations if q["role"] == "contradicts"]
        has_timeline_issue = bool(finding.get("timeline_review_flags"))

        if status == "conflicting" and len(limiting) == 1 and not support and not has_timeline_issue and len(citations) == 1:
            quote = limiting[0]
            document_absence = bool(ABSENCE_ONLY.search(str(quote["quote"])))
            code = "document_absence_not_contradiction" if document_absence else "explicit_scope_limit_not_contradiction"
            finding["status"] = "not_found"
            finding["effective_status"] = "not_found"
            finding["evidence_type"] = "unsupported"
            finding["certainty"] = "ambiguous"
            finding["review_reason_code"] = code
            finding["review_label"] = (
                "Not documented in this CV" if document_absence
                else "Scope not established"
            )
            finding["review_explanation"] = (
                "The CV reports that evidence is absent; no incompatible second CV claim was verified."
                if document_absence else
                "The cited statement limits the documented role or task; no incompatible second CV claim was verified."
            )
            finding["note"] = (
                str(finding.get("note", "")).strip()
                + " Local clarification: this source is a limitation on the requirement, "
                "not verified proof of self-contradictory CV claims."
            ).strip()
            finding["status_policy"] = "unpaired_limiting_quote_cannot_establish_cv_self_contradiction"
            for item in limiting:
                item["display_role"] = "scope_context"
                item["evidence_type"] = "unsupported"
            scope = finding.get("scope_boundary_review")
            if isinstance(scope, dict):
                scope["final_status"] = "not_found"
            counters[
                "document_absences_clarified" if document_absence
                else "single_scope_limits_clarified"
            ] += 1
        elif status == "conflicting" and not has_timeline_issue and len(citations) > 1 and not _clear_internal_opposition(finding, support, limiting):
            # Multiple notes describing someone's boundaries do not establish
            # two incompatible CV claims. Preserve both original quotes and
            # the raw Meta label; do not manufacture a positive qualification.
            finding["status"] = "not_found"
            finding["effective_status"] = "not_found"
            finding["evidence_type"] = "related" if support else "unsupported"
            finding["certainty"] = "ambiguous"
            finding["review_reason_code"] = "multi_quote_scope_not_internal_contradiction"
            finding["review_label"] = "Scope or responsibility to clarify"
            finding["review_explanation"] = (
                "Multiple citations describe adjacent or limited work; no clear "
                "opposing claims by the applicant were verified."
            )
            finding["status_policy"] = "require_two_explicit_opposing_personal_claims"
            scope = finding.get("scope_boundary_review")
            if isinstance(scope, dict):
                scope["final_status"] = "not_found"
            counters["multi_quote_scope_clarifications"] += 1
        elif status == "conflicting":
            finding["review_reason_code"] = "multi_claim_or_timeline_discrepancy"
            finding["review_label"] = "Discrepancy to clarify"
            finding["review_explanation"] = (
                "Multiple cited statements or an independently checked timeline flag require human clarification. "
                "This does not establish that the CV claim is false."
            )
            counters["multi_quote_discrepancies_retained"] += 1
        elif status == "not_found" and evidence_type == "related" and not finding.get("review_reason_code"):
            finding["review_reason_code"] = "related_evidence_exact_criterion_unproven"
            finding["review_label"] = "Related evidence — exact requirement unproven"
            finding["review_explanation"] = (
                "Concrete transferable work is quoted, but the specific qualification has not been established."
            )
            counters["related_context_labeled"] += 1
        else:
            counters["unchanged"] += 1
    return counters
