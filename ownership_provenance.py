"""Conservative evidence-provenance shadow audit: WHO did the described work?

This standalone diagnostic has no model access and never changes candidate
status or scores. It flags explicit attributions to *another* actor and
contrasts a CV's own claims with the job action required. It must be treated
as a human-review prompt, not as an employment qualification check.

A verified quote may exist on a PDF page yet attribute work to a colleague.
Use only quotes already source-verified by EvidenceTrail when integrating.
"""
from __future__ import annotations

import re
from typing import Any

# Action families are general work-activity concepts, not an exact string match
# to any particular benchmark CV, employer or applicant.
ACTIONS: dict[str, re.Pattern[str]] = {
    "contract": re.compile(r"\b(?:negotiat\w*|contract\s+terms|agreement\s+terms)\b", re.I),
    "operate": re.compile(r"\b(?:operat\w*|administrat\w*|run|ran|manag\w*\s+(?:production|clusters?))\b", re.I),
    "build": re.compile(r"\b(?:built|build\w*|develop\w*|author\w*|creat\w*)\b", re.I),
    "lead": re.compile(r"\b(?:lead|led|direct\w*|command\w*|head\w*)\b", re.I),
    "perform": re.compile(r"\b(?:perform\w*|ran|run|execut\w*|conduct\w*)\b", re.I),
    "prepare": re.compile(r"\b(?:prepar\w*|consolidat\w*|maintain\w*\s+forecast)\b", re.I),
    "control": re.compile(r"\b(?:control\w*|allocat\w*|approv\w*|authori[sz]\w*|own\w*\s+budget)\b", re.I),
    "manage": re.compile(r"\b(?:manag\w*|own\w*|renew\w*|sign\w*)\b", re.I),
    "coordinate": re.compile(r"\b(?:coordinat\w*|supervis\w*|assign\w*|manag\w*)\b", re.I),
    "design": re.compile(r"\b(?:design\w*|plan\w*|creat\w*)\b", re.I),
}
ACTOR = re.compile(
    r"\b(?:the|my|our|a|an)\s+(?:external\s+|different\s+|district\s+|"
    r"platform\s+|molecular\s+|project\s+|controls\s+|account\s+|"
    r"procurement\s+|operations\s+|ground\s+|senior\s+|"
    r"team\s+|department\s+|group\s+){0,3}"
    r"(?:director|manager|managers|supervisor|supervisors|officer|officers|"
    r"agency|team|colleague|colleagues|engineer|engineers|controller|"
    r"department|specialist|specialists|lead|group|soc|vendor|contractor)s?\b",
    re.I,
)
SELF = re.compile(r"\b(?:I|personally|myself)\b", re.I)
HANDOFF = re.compile(
    r"\bI\s+(?:received|reviewed|viewed|reported|observed|distributed|uploaded|"
    r"prepared|assembled|wrote|accessioned)\b.{0,150}"
    r"\b(?:from|after|while|but|who|alone|only|instead)\b",
    re.I | re.S,
)
SEPARATE_ROLE = re.compile(
    r"\b(?:alone|exclusively|only|different\s+department|"
    r"rather\s+than|instead\s+of|while|but|who|after)\b",
    re.I,
)
SELF_DENIAL = re.compile(
    r"\bI\s+(?:never|did\s+not|didn't|was\s+not|wasn't)\b.{0,80}"
    r"\b(?:negotiat\w*|operat\w*|lead|led|direct\w*|perform\w*|"
    r"prepar\w*|consolidat\w*|design\w*|own\w*|control\w*|manage\w*|"
    r"coordinat\w*|develop\w*|build\w*|sign\w*)\b",
    re.I,
)
# First-person action only counts if it matches the REQUIRED action.
# Preparing a comparison sheet is not personal contract negotiation.
SELF_ACTIONS: dict[str,re.Pattern[str]] = {
    "contract":re.compile(r"\bI\s+(?:personally\s+)?negotiat\w*\b",re.I),
    "operate":re.compile(r"\bI\s+(?:personally\s+)?(?:operat\w*|administrat\w*|ran|managed)\b",re.I),
    "build":re.compile(r"\bI\s+(?:personally\s+)?(?:built|developed|authored|created)\b",re.I),
    "lead":re.compile(r"\bI\s+(?:personally\s+)?(?:led|directed|commanded|headed)\b",re.I),
    "perform":re.compile(r"\bI\s+(?:personally\s+)?(?:performed|ran|conducted|executed)\b",re.I),
    "prepare":re.compile(r"\bI\s+(?:personally\s+)?(?:prepared|consolidated|maintained)\b",re.I),
    "control":re.compile(r"\bI\s+(?:personally\s+)?(?:controlled|allocated|approved|authorized|owned)\b",re.I),
    "manage":re.compile(r"\bI\s+(?:personally\s+)?(?:managed|owned|renewed|signed|led)\b",re.I),
    "coordinate":re.compile(r"\bI\s+(?:personally\s+)?(?:coordinated|supervised|assigned|managed)\b",re.I),
    "design":re.compile(r"\bI\s+(?:personally\s+)?(?:designed|planned|created)\b",re.I),
}

def ownership_warning(requirement: str, quote: str) -> dict[str, Any] | None:
    """Advisory warning for an *already verified* CV quote; never a label."""
    requirement = str(requirement or "")[:800]
    quote = str(quote or "")[:1800]
    if not requirement.strip() or not quote.strip():
        return None
    action_names = [
        name for name, pattern in ACTIONS.items() if pattern.search(requirement)
    ]
    if not action_names:
        return None
    if not SELF.search(quote) and not ACTOR.search(quote):
        return None
    other_actor = ACTOR.search(quote)
    denial = SELF_DENIAL.search(quote)
    handoff = HANDOFF.search(quote)
    split = SEPARATE_ROLE.search(quote)
    # A warning needs explicit provenance ambiguity, not just a third-party
    # employer name or the existence of a team.
    # A clearly named other actor doing the *required* action is relevant
    # even when the sentence does not contain "but", "after", or "alone".
    third_party_action = bool(other_actor) and any(
        ACTIONS[name].search(quote) for name in action_names
    )
    if not denial and not (third_party_action or (other_actor and (handoff or split))):
        return None
    if any(SELF_ACTIONS[name].search(quote) for name in action_names) and not denial:
        # Both applicant and third party might genuinely share work. A future
        # semantic/human review can assess that, not this deterministic rule.
        return None
    return {
        "kind": "third_party_or_denied_task_ownership",
        "human_review_required": True,
        "source_text": quote,
        "requirement": requirement,
        "other_actor_explicitly_named": bool(other_actor),
        "applicant_denial": bool(denial),
        "asserted_qualification": None,
        "suggested_question": (
            "Which parts of this requirement did you personally perform, "
            "and which were handled by colleagues or another team?"
        ),
    }


def audit_verified_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only cited, page-labelled source passages are eligible for warnings.

    The caller must have independently verified them against actual source PDF
    pages. No quote, page or candidate status is changed. Avoids repeating the
    same advisory on duplicate citations.
    """
    out=[]
    for finding in findings:
        if not isinstance(finding,dict):
            continue
        requirement=str(finding.get("requirement",""))
        seen=set()
        for ev in finding.get("evidence") or []:
            if not isinstance(ev,dict):
                continue
            quote=ev.get("quote")
            page=ev.get("page")
            if not isinstance(page,int) or isinstance(page,bool) or page<1:
                continue
            if ev.get("role") not in ("supports","contradicts"):
                continue
            key=(page,str(quote).casefold())
            if key in seen:
                continue
            seen.add(key)
            warn=ownership_warning(requirement,str(quote))
            if warn:
                out.append({
                    "requirement_id":finding.get("id"),
                    "page":page,
                    "source_id":ev.get("source_id"),
                    "role_recorded_unchanged":ev.get("role"),
                    **warn,
                })
    return out
