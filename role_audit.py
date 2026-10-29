"""Local, explainable checks for vague wording in job descriptions.

The gender-language cue lists below are adapted from Gender Decoder's
MIT-licensed lists. They are shown as human-review prompts only. EvidenceTrail
does not calculate a gender-bias score or determine that wording is unlawful.
"""

from __future__ import annotations

import re
from typing import Any


# Adapted from lovedaybrooke/gender-decoder (MIT), genderdecoder 0.3.
# The upstream package's prefix lists are preserved in THIRD_PARTY_NOTICES.md.
FEMININE_CODED_PREFIXES = (
    "agree", "affectionate", "child", "cheer", "collab", "commit",
    "communal", "compassion", "connect", "considerate", "cooperat",
    "co-operat", "depend", "emotiona", "empath", "feel", "flatterable",
    "gentle", "honest", "interpersonal", "interdependen", "interpersona",
    "inter-personal", "inter-dependen", "inter-persona", "kind", "kinship",
    "loyal", "modesty", "nag", "nurtur", "pleasant", "polite", "quiet",
    "respon", "sensitiv", "submissive", "support", "sympath", "tender",
    "together", "trust", "understand", "warm", "whin", "enthusias",
    "inclusive", "yield", "shar",
)

MASCULINE_CODED_PREFIXES = (
    "active", "adventurous", "aggress", "ambitio", "analy", "assert",
    "athlet", "autonom", "battle", "boast", "challeng", "champion",
    "compet", "confident", "courag", "decid", "decision", "decisive",
    "defend", "determin", "domina", "dominant", "driven", "fearless",
    "fight", "force", "greedy", "head-strong", "headstrong", "hierarch",
    "hostil", "implusive", "independen", "individual", "intellect",
    "logic", "objective", "opinion", "outspoken", "persist", "principle",
    "reckless", "self-confiden", "self-relian", "self-sufficien",
    "selfconfiden", "selfrelian", "selfsufficien", "stubborn", "superior",
    "unreasonab",
)

VAGUE_PHRASES = (
    "culture fit",
    "fast-paced",
    "fast paced",
    "strong communication skills",
    "excellent communication skills",
    "strong communicator",
    "good communicator",
    "proven track record",
    "self-starter",
    "self starter",
    "rockstar",
    "ninja",
    "wear many hats",
    "highly motivated",
    "work hard play hard",
)

_GENDER_PATTERN = re.compile(
    r"\b(?P<cue>" + "|".join(
        re.escape(prefix)
        for prefix in sorted(
            set(FEMININE_CODED_PREFIXES + MASCULINE_CODED_PREFIXES),
            key=len,
            reverse=True,
        )
    ) + r")\w*\b",
    re.IGNORECASE,
)
_VAGUE_PATTERN = re.compile(
    r"\b(?P<cue>" + "|".join(
        re.escape(phrase)
        for phrase in sorted(VAGUE_PHRASES, key=len, reverse=True)
    ) + r")\b",
    re.IGNORECASE,
)
_LIST_ITEM_PATTERN = re.compile(r"^\s*(?:\d+[.)]\s+|[-*•‣]\s+)(.+?)\s*$")
_CREDENTIAL_PATTERN = re.compile(
    r"\b(certifications?|certificates?|licenses?|licences?|credentials?)\b", re.IGNORECASE
)
_EDUCATION_PATTERN = re.compile(
    r"\b(degree|bachelor'?s?|master'?s?|ph\.?d\.?|doctorate|diploma|education)\b",
    re.IGNORECASE,
)
_EXPERIENCE_PATTERN = re.compile(
    r"\b\d+\s*\+?\s*years?\b|\b(?:experience|experienced|seniority|senior|junior|entry.level)\b",
    re.IGNORECASE,
)
_BEHAVIOR_PATTERN = re.compile(
    r"\b(communicat\w*|leadership|collaborat\w*|teamwork|interpersonal|"
    r"problem.solv\w*|stakeholder|organized|organisation|organization|initiative)\b",
    re.IGNORECASE,
)
_REQUIRED_PRIORITY_PATTERN = re.compile(
    r"\b(?:required|must|mandatory|essential|minimum|at\s+least|need\s+to)\b",
    re.IGNORECASE,
)
_PREFERRED_PRIORITY_PATTERN = re.compile(
    r"\b(?:preferred|desirable|nice[ -]to[ -]have|bonus|a\s+plus)\b",
    re.IGNORECASE,
)
_OPTIONAL_PRIORITY_PATTERN = re.compile(
    r"\b(?:not\s+required|not\s+mandatory|not\s+essential|optional|"
    r"no\s+(?:[\w'-]+\s+){0,3}required)\b",
    re.IGNORECASE,
)
_PREFERRED_BUT_NOT_REQUIRED_PATTERN = re.compile(
    r"\bpreferred\s+but\s+not\s+required\b", re.IGNORECASE
)
_REQUIRED_SECTION_PATTERN = re.compile(
    r"^(?:(?:minimum|required|mandatory|essential|basic)\s+(?:job\s+)?"
    r"(?:qualifications?|requirements?|criteria|skills?|experience)|"
    r"(?:qualifications?|requirements?|criteria|skills?|experience)\s+(?:required|minimum))$",
    re.IGNORECASE,
)
_PREFERRED_SECTION_PATTERN = re.compile(
    r"^(?:(?:preferred|desirable|desired)\s+(?:job\s+)?"
    r"(?:qualifications?|requirements?|criteria|skills?|experience)|"
    r"nice\s+to\s+have|bonus(?:\s+(?:qualifications?|requirements?|skills?))?)$",
    re.IGNORECASE,
)
_OPTIONAL_SECTION_PATTERN = re.compile(
    r"^(?:optional(?:\s+(?:qualifications?|requirements?|skills?))?|"
    r"not\s+required(?:\s+(?:qualifications?|requirements?|skills?))?)$",
    re.IGNORECASE,
)
_COMMON_UNPRIORITIZED_HEADINGS = {
    "responsibilities",
    "key responsibilities",
    "what youll do",
    "what you ll do",
    "what you will do",
    "who you are",
    "about the role",
    "about this role",
    "about the job",
    "role overview",
    "position summary",
    "what youll bring",
    "what you ll bring",
    "what you will bring",
    "your role",
    "day to day",
    "benefits",
    "about us",
    "company overview",
    "qualifications",
    "requirements",
    "skills",
    "experience",
}
_COMPENSATION_CONTEXT_PATTERN = re.compile(
    r"(?:\bcompetitive\b.{0,28}\b(?:salary|pay|compensation|benefits?|bonus|wages?|remuneration)\b|"
    r"\b(?:salary|pay|compensation|benefits?|bonus|wages?|remuneration)\b.{0,28}\bcompetitive\b)",
    re.IGNORECASE,
)
_NEUTRAL_COMPETENCE_WORDS = {"competence", "competences", "competency", "competencies", "competent"}


def _sentence_excerpt(text: str, start: int, end: int, radius: int = 100) -> str:
    """Return a compact, source-exact excerpt around one flagged phrase."""
    left = max(text.rfind("\n", 0, start), text.rfind(".", 0, start), 0)
    right_candidates = [
        position
        for position in (text.find("\n", end), text.find(".", end))
        if position >= 0
    ]
    right = min(right_candidates) + 1 if right_candidates else len(text)
    if right - left > radius * 2:
        left = max(left, start - radius)
        right = min(right, end + radius)
    return " ".join(text[left:right].split())


def _criterion_plan(requirement: str) -> tuple[str, str, str, str, str]:
    """Return a transparent keyword bucket and prompts, never a quality rating."""
    if _CREDENTIAL_PATTERN.search(requirement):
        return (
            "Credential or license",
            "Is an exact credential required? Specify its title, issuer or level, whether it must be current, and what equivalents count.",
            "Can I point to the exact credential and its current status, if the role requires that?",
            "Name the credential and required level or status; state accepted equivalents.",
            "Which exact credential do you hold that meets this requirement? Please name the issuer, level, and current status.",
        )
    if _EDUCATION_PATTERN.search(requirement):
        return (
            "Education",
            "What qualification or field is essential? State whether equivalent experience or alternate qualifications count.",
            "Which qualification or equivalent route can I accurately document?",
            "State the required level and field, then list acceptable equivalent routes.",
            "What qualification or equivalent experience meets this requirement? Please describe the relevant field and route.",
        )
    if _EXPERIENCE_PATTERN.search(requirement):
        return (
            "Experience or duration",
            "What work or outcome qualifies, and is the duration essential or a proxy for demonstrated capability?",
            "What specific work example, role, and timeframe can I truthfully point to?",
            "Define the relevant work and outcome; include a duration only if it is necessary.",
            "Describe a relevant role or project, your responsibilities, the timeframe, and the outcome.",
        )
    if _BEHAVIOR_PATTERN.search(requirement):
        return (
            "Work behavior",
            "Which observable behavior or work outcome demonstrates this, and what consistent example should reviewers accept?",
            "What real situation shows this behavior, what did I do, and what happened?",
            "Replace the trait label with an observable action, context, and expected outcome.",
            "Describe a specific work situation related to this requirement, what you did, and the result.",
        )
    return (
        "Other requirement",
        "What observable work result, example, credential, or standard would satisfy this requirement?",
        "Which truthful example, result, or document can I point to for this requirement?",
        "State the task or capability, the expected result, and acceptable evidence.",
        "Describe one specific work example that meets this requirement, including your role and the outcome.",
    )


def _priority_plan(
    requirement: str,
    section_priority: str = "",
    section_basis: str = "",
) -> tuple[str, str]:
    """Report only explicit priority wording; do not infer job importance."""
    preferred_but_optional = _PREFERRED_BUT_NOT_REQUIRED_PATTERN.search(requirement)
    if preferred_but_optional:
        explicit_priority = "preferred"
        explicit_basis = preferred_but_optional.group(0)
        explicit_label = "Preferred · explicitly not required"
    else:
        optional_match = _OPTIONAL_PRIORITY_PATTERN.search(requirement)
        required_text = _OPTIONAL_PRIORITY_PATTERN.sub(" ", requirement)
        required_match = _REQUIRED_PRIORITY_PATTERN.search(required_text)
        preferred_match = _PREFERRED_PRIORITY_PATTERN.search(requirement)

        if optional_match and required_match:
            return "Mixed priority wording", optional_match.group(0)
        if optional_match and preferred_match:
            explicit_priority = "preferred"
            explicit_basis = f"{preferred_match.group(0)} / {optional_match.group(0)}"
            explicit_label = "Preferred · explicitly not required"
        elif optional_match:
            explicit_priority = "optional"
            explicit_basis = optional_match.group(0)
            explicit_label = "Explicitly not required"
        elif required_match and preferred_match:
            return "Mixed priority wording", f"{required_match.group(0)} / {preferred_match.group(0)}"
        elif required_match:
            explicit_priority = "required"
            explicit_basis = required_match.group(0)
            explicit_label = "Explicitly required"
        elif preferred_match:
            explicit_priority = "preferred"
            explicit_basis = preferred_match.group(0)
            explicit_label = "Preferred"
        else:
            explicit_priority = ""
            explicit_basis = ""
            explicit_label = ""

    if section_priority and explicit_priority:
        if section_priority != explicit_priority:
            return "Mixed priority wording", f"{section_basis} / {explicit_basis}"
    if explicit_priority:
        return explicit_label, explicit_basis
    if section_priority:
        section_label = {
            "required": "Explicitly required",
            "preferred": "Preferred",
            "optional": "Explicitly not required",
        }[section_priority]
        return section_label, section_basis
    return "Not stated", "No explicit priority wording found"


def _extract_criteria(text: str, limit: int) -> tuple[list[dict[str, Any]], int]:
    criteria: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    total = 0
    section_priority = ""
    section_basis = ""
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = _LIST_ITEM_PATTERN.match(line)
        if not match:
            heading = " ".join(line.strip().rstrip(":").split())
            if not heading:
                continue
            heading_key = re.sub(r"[^a-z0-9]+", " ", heading.casefold()).strip()
            if _REQUIRED_SECTION_PATTERN.fullmatch(heading):
                section_priority, section_basis = "required", heading
            elif _PREFERRED_SECTION_PATTERN.fullmatch(heading):
                section_priority, section_basis = "preferred", heading
            elif _OPTIONAL_SECTION_PATTERN.fullmatch(heading):
                section_priority, section_basis = "optional", heading
            elif heading_key in _COMMON_UNPRIORITIZED_HEADINGS or line.strip().endswith(":"):
                section_priority, section_basis = "", ""
            continue
        requirement = " ".join(match.group(1).split())[:700]
        if not requirement:
            continue
        total += 1
        (
            kind,
            reviewer_prompt,
            candidate_prompt,
            rewrite_prompt,
            interview_question,
        ) = _criterion_plan(requirement)
        priority, priority_basis = _priority_plan(requirement, section_priority, section_basis)
        normalized = re.sub(r"[^\w]+", " ", requirement.casefold()).strip()
        duplicate_of = seen.get(normalized, "")
        item_id = f"C{total}"
        if normalized and not duplicate_of:
            seen[normalized] = item_id
        if len(criteria) >= max(0, limit):
            continue
        criteria.append(
            {
                "id": item_id,
                "line": line_number,
                "text": requirement,
                "kind": kind,
                "priority": priority,
                "priority_basis": priority_basis,
                "reviewer_prompt": reviewer_prompt,
                "candidate_prompt": candidate_prompt,
                "rewrite_prompt": rewrite_prompt,
                "interview_question": interview_question,
                "possible_exact_duplicate_of": duplicate_of,
            }
        )
    return criteria, max(0, total - len(criteria))


def audit_role_description(text: str, limit: int = 40) -> dict[str, Any]:
    """Flag exact job-ad phrases that may merit human clarification.

    This deterministic scan never scores a role or labels an employer. Each
    item points to source wording and asks a reviewer to define an observable
    task, outcome, or standard.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "items": [],
            "count": 0,
            "criteria": [],
            "criteria_count": 0,
            "truncated": 0,
            "criteria_truncated": 0,
            "disclosure": (
                "This free role-text check offers drafting prompts. It does not score the role, "
                "assess applicants, or make a legal finding."
            ),
        }

    criteria, criteria_truncated = _extract_criteria(text, limit)
    candidates: list[dict[str, Any]] = []
    for pattern, category, question in (
        (
            _VAGUE_PATTERN,
            "Vague or personality-based wording",
            "What observable responsibility, output, or standard would satisfy this phrase?",
        ),
        (
            _GENDER_PATTERN,
            "Historical language-review lexicon cue",
            "Does this word describe a necessary job task, and can the requirement be stated as observable work?",
        ),
    ):
        for match in pattern.finditer(text):
            start, end = match.span()
            if category == "Historical language-review lexicon cue":
                matched_word = match.group(0).casefold()
                if matched_word in _NEUTRAL_COMPETENCE_WORDS:
                    continue
                if matched_word.startswith("competitive") and _COMPENSATION_CONTEXT_PATTERN.search(
                    _sentence_excerpt(text, start, end, radius=50)
                ):
                    continue
            candidates.append(
                {
                    "start": start,
                    "end": end,
                    "cue": match.group("cue"),
                    "category": category,
                    "excerpt": _sentence_excerpt(text, start, end),
                    "review_question": question,
                    "rewrite_prompt": (
                        "If essential, describe the observable task or outcome and the "
                        "standard or timeframe a reviewer can use to assess it."
                    ),
                    "source": (
                        "Gender Decoder word list (MIT)"
                        if category == "Historical language-review lexicon cue"
                        else "EvidenceTrail local clarity phrase list"
                    ),
                }
            )

    candidates.sort(key=lambda item: (item["start"], item["end"], item["category"]))
    # Merge duplicate hits at the same location while keeping each category
    # explicit, and prefer the phrase-level clarity prompt for that location.
    unique: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for item in candidates:
        key = (item["start"], item["end"], item["category"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    displayed = unique[: max(0, limit)]
    for index, item in enumerate(displayed, start=1):
        item["id"] = f"L{index}"
        item.pop("start", None)
        item.pop("end", None)

    return {
        "items": displayed,
        "count": len(unique),
        "criteria": criteria,
        "criteria_count": len(criteria) + criteria_truncated,
        "truncated": max(0, len(unique) - len(displayed)),
        "criteria_truncated": criteria_truncated,
        "disclosure": (
            "This free preflight sends only job text to the EvidenceTrail app server and makes no Meta request. "
            "Numbered or bulleted requirements get keyword-based evidence-planning prompts and draft interview questions, not a clarity rating. "
            "Review draft questions with a job expert and, if used, apply the same relevant question and documented standard consistently. "
            "Priority labels reflect explicit wording in a requirement or its list heading only; they do not infer importance. Phrase matches are review prompts, "
            "not a bias score or legal conclusion. The Gender Decoder list is based on older, binary-framed research; "
            "later replication found effects varied by context. Matches may be harmless or context-dependent, and the "
            "list cannot cover all identities, cultures, or forms of unfairness."
        ),
    }
