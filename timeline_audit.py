"""Conservative date math for CV employment timelines.

Muse proposes episodes and duration claims. This module verifies the cited text,
parses only explicit dates, and performs interval arithmetic locally. Flags are
review prompts, not claims of fraud or qualification.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Callable


MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3,
    "march": 3, "apr": 4, "april": 4, "may": 5, "jun": 6,
    "june": 6, "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}
MONTH_PATTERN = "|".join(sorted(MONTHS, key=len, reverse=True))
DATE_TOKEN = re.compile(
    rf"(?<![A-Za-z0-9])(?:({MONTH_PATTERN})\.?\s+\d{{4}}|\d{{4}}(?:[-/]\d{{1,2}})?|present|current|ongoing|now)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
DURATION = re.compile(
    r"\b(?P<number>\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty)\s*(?:\+\s*)?(?P<unit>years?|yrs?|months?|mos?)\b",
    re.IGNORECASE,
)
DURATION_RANGE = re.compile(
    r"\b(?:between\s+(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s+and\s+"
    r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)|"
    r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:-|–|—|to|through)\s*"
    r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten))\s*"
    r"(?:years?|yrs?|months?|mos?)\b",
    re.IGNORECASE,
)
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
}
TOPIC_STOP_WORDS = {
    "a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or",
    "the", "to", "with", "experience", "experienced", "work", "working",
    "years", "year", "yrs", "yr", "months", "month", "mos", "mo",
}
WORK_ACTION = re.compile(
    r"\b(?:manage[sd]?|lead|led|build|built|negotiate[sd]?|draft(?:ed)?|"
    r"process(?:ed)?|maintain(?:ed)?|coordinate[sd]?|support(?:ed)?|"
    r"implement(?:ed)?|create[sd]?|develop(?:ed)?|conduct(?:ed)?|"
    r"oversee|oversaw|own(?:ed)?|analy[sz](?:e|ed|ing)|prepare[sd]?|"
    r"track(?:ed)?|review(?:ed)?|operate[sd]?|deliver(?:ed)?|"
    r"administer(?:ed)?|execute[sd]?|handle[sd]?|manage|work(?:ed|ing)?)\b",
    re.IGNORECASE,
)
MAX_EPISODES = 40
MAX_EXPERIENCE_CLAIMS = 20


def _month_index(year: int, month: int) -> int:
    return year * 12 + month - 1


def parse_date_bound(value: Any, *, end: bool, as_of: date) -> tuple[int, str] | None:
    """Return a half-open month index and precision for one explicit endpoint."""
    text = str(value or "").strip().casefold().replace(".", "")
    if not text:
        return None
    if text in {"present", "current", "now", "ongoing", "today"}:
        return (_month_index(as_of.year, as_of.month) + 1, "current_month") if end else None

    month_year = re.fullmatch(rf"({MONTH_PATTERN})\s+(\d{{4}})", text, re.IGNORECASE)
    if month_year:
        month = MONTHS[month_year.group(1).casefold()]
        year = int(month_year.group(2))
        start = _month_index(year, month)
        return (start + 1 if end else start, "month")

    numeric = re.fullmatch(r"(\d{4})(?:[-/](\d{1,2}))?", text)
    if not numeric:
        return None
    year = int(numeric.group(1))
    if year < 1900 or year > as_of.year + 5:
        return None
    month_text = numeric.group(2)
    if not month_text:
        # Year-only endpoints use January as a boundary, avoiding invented
        # inclusive months (e.g. 2018–2024 is six years, not seven).
        return (_month_index(year, 1), "year")
    month = int(month_text)
    if month < 1 or month > 12:
        return None
    start = _month_index(year, month)
    return (start + 1 if end else start, "month")


def _date_tokens(text: str) -> list[str]:
    return [match.group(0).strip() for match in DATE_TOKEN.finditer(text)]


def _duration_months(text: str) -> int | None:
    if DURATION_RANGE.search(text):
        return None
    matches = list(DURATION.finditer(text))
    if len(matches) != 1:
        return None
    match = matches[0]
    raw = match.group("number").casefold()
    try:
        number = float(raw) if raw[0].isdigit() else float(NUMBER_WORDS[raw])
    except (ValueError, KeyError):
        return None
    unit = match.group("unit").casefold()
    months = number * (12 if unit.startswith(("year", "yr")) else 1)
    if months <= 0 or months > 1200:
        return None
    return int(round(months))


def _topic_tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"[^\W_]+", str(text), flags=re.UNICODE)
        if token.casefold() not in TOPIC_STOP_WORDS
    }


def _union_months(intervals: list[tuple[int, int]]) -> int:
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def audit_employment_timeline(
    episodes: Any,
    experience_claims: Any,
    pages: list[dict[str, Any]],
    quote_locator: Callable[[str, list[dict[str, Any]], Any], dict[str, Any] | None],
    *,
    as_of: date | None = None,
) -> dict[str, Any]:
    """Verify Muse-proposed timeline spans, then calculate durations and overlaps."""
    today = as_of or date.today()
    raw_episodes = episodes if isinstance(episodes, list) else []
    raw_claims = experience_claims if isinstance(experience_claims, list) else []
    exclusions: list[dict[str, str]] = []
    verified: list[dict[str, Any]] = []

    for index, item in enumerate(raw_episodes[:MAX_EPISODES], start=1):
        if not isinstance(item, dict):
            exclusions.append({"item": f"episode_{index}", "reason": "invalid_shape"})
            continue
        date_quote = str(item.get("date_quote", "")).strip()
        hint = item.get("page_hint")
        location = quote_locator(date_quote, pages, hint) if date_quote else None
        if not location:
            exclusions.append({"item": f"episode_{index}", "reason": "date_quote_not_verified"})
            continue

        start_raw = str(item.get("start_date", "")).strip()
        end_raw = str(item.get("end_date", "")).strip()
        start = parse_date_bound(start_raw, end=False, as_of=today)
        end = parse_date_bound(end_raw, end=True, as_of=today)
        source_dates = _date_tokens(date_quote)
        if not start or not end or start[0] >= end[0]:
            exclusions.append({"item": f"episode_{index}", "reason": "invalid_or_inverted_dates"})
            continue
        if len(source_dates) < 2:
            exclusions.append({"item": f"episode_{index}", "reason": "date_quote_lacks_two_anchors"})
            continue
        source_start = parse_date_bound(source_dates[0], end=False, as_of=today)
        source_end = parse_date_bound(source_dates[-1], end=True, as_of=today)
        # The exact CV quote must anchor the dates Muse supplied; page checks
        # alone are not enough if the model normalized the wrong dates.
        if not source_start or not source_end or source_start[0] != start[0] or source_end[0] != end[0]:
            exclusions.append({"item": f"episode_{index}", "reason": "dates_do_not_match_quote"})
            continue

        scope_quote = str(item.get("scope_quote") or "").strip()
        scope_location = quote_locator(scope_quote, pages, location.get("page")) if scope_quote else None
        role_label = str(item.get("role", "")).strip()[:160]
        role_terms = set(re.findall(r"[^\W_]+", role_label.casefold(), flags=re.UNICODE))
        date_quote_terms = set(re.findall(r"[^\W_]+", date_quote.casefold(), flags=re.UNICODE))
        if not role_terms or not role_terms.issubset(date_quote_terms):
            role_label = "Role not confirmed"
        areas = item.get("experience_areas", [])
        if not isinstance(areas, list):
            areas = []
        grounded_areas: list[str] = []
        if (
            scope_location
            and int(scope_location.get("page", 0)) == int(location.get("page", 0))
            and len(_topic_tokens(scope_quote)) >= 4
            and WORK_ACTION.search(scope_quote)
        ):
            scope_terms = _topic_tokens(scope_quote)
            for area in areas[:8]:
                label = str(area).strip()[:100]
                terms = _topic_tokens(label)
                if label and terms and len(terms & scope_terms) / len(terms) >= 0.5:
                    grounded_areas.append(label)

        verified.append({
            "id": f"E{index}",
            "role": role_label or "Role not confirmed",
            "company": str(item.get("company", ""))[:160],
            "start_date": start_raw,
            "end_date": end_raw,
            "start_month": start[0],
            "end_month": end[0],
            "precision": "year_only" if start[1] == "year" and end[1] == "year" else "month_or_better",
            "date_quote": date_quote[:500],
            "date_page": int(location.get("page", 0)),
            "scope_quote": scope_quote[:700] if scope_location else "",
            "scope_page": int(scope_location.get("page", 0)) if scope_location else None,
            "experience_areas": grounded_areas,
            "duration_months": end[0] - start[0],
        })

    overlaps: list[dict[str, Any]] = []
    for left_index, left in enumerate(verified):
        for right in verified[left_index + 1:]:
            overlap = min(left["end_month"], right["end_month"]) - max(left["start_month"], right["start_month"])
            if overlap > 0:
                overlaps.append({
                    "type": "employment_date_overlap",
                    "episodes": [left["id"], right["id"]],
                    "roles": [left["role"], right["role"]],
                    "overlap_months": overlap,
                    "review_note": "These dated roles overlap. Confirm whether they were concurrent, part-time, or a date-entry issue.",
                })

    all_intervals = [(item["start_month"], item["end_month"]) for item in verified]
    dated_months = _union_months(all_intervals)
    area_intervals: dict[str, list[tuple[int, int]]] = {}
    for item in verified:
        interval = (item["start_month"], item["end_month"])
        for area in item["experience_areas"]:
            area_intervals.setdefault(area, []).append(interval)
    tenure_by_area = [
        {"area": area, "months": _union_months(intervals)}
        for area, intervals in sorted(area_intervals.items(), key=lambda pair: pair[0].casefold())
    ]

    claims: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = list(overlaps)
    for index, item in enumerate(raw_claims[:MAX_EXPERIENCE_CLAIMS], start=1):
        if not isinstance(item, dict):
            exclusions.append({"item": f"claim_{index}", "reason": "invalid_shape"})
            continue
        quote = str(item.get("claim_quote", "")).strip()
        location = quote_locator(quote, pages, item.get("page_hint")) if quote else None
        if not location:
            exclusions.append({"item": f"claim_{index}", "reason": "claim_quote_not_verified"})
            continue
        claimed_months = _duration_months(quote)
        topic = str(item.get("topic", "")).strip()[:120]
        if claimed_months is None or not topic:
            exclusions.append({"item": f"claim_{index}", "reason": "claim_duration_or_topic_missing"})
            continue
        topic_terms = _topic_tokens(topic)
        matched_areas = [
            row["area"] for row in tenure_by_area
            if topic_terms and len(topic_terms & _topic_tokens(row["area"])) / len(topic_terms) >= 0.5
        ]
        matching_intervals: list[tuple[int, int]] = []
        for episode in verified:
            if any(area in matched_areas for area in episode["experience_areas"]):
                matching_intervals.append((episode["start_month"], episode["end_month"]))
        comparison_basis = "topic_scoped" if matching_intervals else "all_dated_roles" if all_intervals else None
        # The full dated career span is a conservative upper bound: a claimed
        # topic duration beyond that span cannot be reconciled without omitted
        # or undated work, which the recruiter can ask about.
        if not matching_intervals and all_intervals:
            matching_intervals = all_intervals
        documented_months = _union_months(matching_intervals) if matching_intervals else None
        claim_status = "review" if documented_months is not None and claimed_months > documented_months else "not_comparable" if documented_months is None else "no_excess_detected"
        claim_record = {
            "topic": topic,
            "claim_quote": quote[:500],
            "claim_page": int(location.get("page", 0)),
            "claimed_months": claimed_months,
            "documented_months": documented_months,
            "matched_areas": matched_areas,
            "comparison_basis": comparison_basis,
            "status": claim_status,
        }
        claims.append(claim_record)
        if claim_status == "review":
            flags.append({
                "type": "claimed_tenure_exceeds_dated_evidence",
                "topic": topic,
                "claimed_months": claimed_months,
                "documented_months": documented_months,
                "comparison_basis": comparison_basis,
                "claim_page": claim_record["claim_page"],
                "review_note": (
                    "The stated duration is longer than the dated roles found for this topic. The CV may omit earlier roles; ask the candidate to clarify."
                    if comparison_basis == "topic_scoped"
                    else "The stated duration is longer than the full dated work history shown in this CV. The CV may omit earlier roles; ask the candidate to clarify."
                ),
            })

    for index in range(MAX_EPISODES, len(raw_episodes)):
        exclusions.append({"item": f"episode_{index + 1}", "reason": "episode_limit"})
    for index in range(MAX_EXPERIENCE_CLAIMS, len(raw_claims)):
        exclusions.append({"item": f"claim_{index + 1}", "reason": "claim_limit"})

    # Internal month indices and raw date quotes are useful to auditors, while
    # the API only needs the concise fields below.
    public_episodes = [
        {key: value for key, value in episode.items() if key not in {"start_month", "end_month"}}
        for episode in verified
    ]
    return {
        "status": "review_required" if flags else "calculated" if verified else "insufficient_data",
        "precision_note": "Year-only endpoints use January boundaries; month-level dates count the stated endpoint month. Day-level precision is not inferred.",
        "dated_employment_months": dated_months,
        "dated_employment_years_approx": round(dated_months / 12, 1),
        "episodes": public_episodes,
        "tenure_by_area": tenure_by_area,
        "experience_claims": claims,
        "overlaps": overlaps,
        "flags": flags,
        "excluded_proposals": exclusions,
    }
