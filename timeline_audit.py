"""Conservative, quote-anchored date math for CV employment timelines.

Local code finds clear date ranges first; Muse may add role scope and propose
other spans. This module verifies each source quote and performs interval
arithmetic locally. Flags prompt review and never assert fraud or qualification.
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
DATE_RANGE_CONNECTOR = re.compile(r"\s*(?:-|–|—|to|through|until)\s*", re.IGNORECASE)
EMPLOYMENT_STATUS = re.compile(
    r"\b(?:full[ -]time|part[ -]time|permanent|fixed[ -]term|internship|intern|"
    r"apprentice|freelance|self[ -]employed|employed)\b",
    re.IGNORECASE,
)
ROLE_CUE = re.compile(
    r"\b(?:manager|director|engineer|analyst|specialist|associate|coordinator|"
    r"officer|consultant|executive|lead|head|supervisor|technician|administrator|"
    r"developer|nurse|teacher|buyer|procurement|sourcing|accountant|architect|"
    r"scientist|representative|president|founder|owner|partner|operator|designer|"
    r"recruiter|counsel|attorney|lawyer|sales|assistant|controller|inspector|"
    r"planner|strategist|advisor|adviser|specialist|principal|chief)\b",
    re.IGNORECASE,
)
NON_WORK_CONTEXT = re.compile(
    r"\b(?:education|bachelor(?:'s)?(?:\s+degree)?|master(?:'s)?\s+(?:degree|of|in)|"
    r"doctorate|ph\.?d|diploma|graduat(?:ed|ion)|coursework|certification|"
    r"certificate|academic)\b",
    re.IGNORECASE,
)
WORK_SECTION_HEADINGS = {
    "experience", "work experience", "professional experience", "employment",
    "employment history", "work history", "career history", "professional history",
}
NON_WORK_SECTION_HEADINGS = {
    "education", "education history", "certifications", "certificates", "projects",
    "selected projects", "publications", "skills", "awards", "training",
}
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
# Month-level CV dates can produce a short handoff overlap. Escalate only
# overlaps longer than two months; all spans are still unioned for tenure math.
MIN_OVERLAP_REVIEW_MONTHS = 3


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


def _explicit_date_range(text: str) -> tuple[list[str] | None, str | None]:
    """Return two date anchors only when their source has an explicit range connector."""
    matches = list(DATE_TOKEN.finditer(text))
    if len(matches) < 2:
        return None, "date_quote_lacks_two_anchors"
    if len(matches) > 2:
        return None, "date_quote_has_extra_date_anchors"
    connector = text[matches[0].end():matches[1].start()]
    if not DATE_RANGE_CONNECTOR.fullmatch(connector):
        return None, "date_quote_has_ambiguous_range_separator"
    return [match.group(0).strip() for match in matches], None


def extract_explicit_employment_episodes(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find clear employment date lines locally so timeline math doesn't depend on Muse.

    The extractor is deliberately conservative: a range must appear on a line
    that is in a work-history section, has an explicit employment marker, or
    has a recognizable role cue. Education and profile-duration lines are
    excluded. The returned quote is still passed through the normal local
    quote/page verifier before it can affect a review flag.
    """
    episodes: list[dict[str, Any]] = []
    for page in pages:
        page_number = page.get("number")
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            continue
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in str(page.get("text", "")).splitlines()
            if line.strip()
        ]
        in_work_section = False
        for index, line in enumerate(lines):
            heading = re.sub(r"[^a-z ]+", " ", line.casefold()).strip()
            heading = re.sub(r"\s+", " ", heading)
            if heading in WORK_SECTION_HEADINGS:
                in_work_section = True
                continue
            if heading in NON_WORK_SECTION_HEADINGS:
                in_work_section = False
                continue

            date_parts, range_error = _explicit_date_range(line)
            if range_error or not date_parts:
                continue
            if re.search(r"\b(?:profile|summary|experience covers|years of experience)\b", line, re.I):
                continue

            first_date = DATE_TOKEN.search(line)
            if not first_date:
                continue
            role = line[:first_date.start()].strip(" |·:,-")
            date_quote = line
            if not role and index:
                previous = lines[index - 1]
                previous_heading = re.sub(r"[^a-z ]+", " ", previous.casefold()).strip()
                previous_heading = re.sub(r"\s+", " ", previous_heading)
                if (
                    previous_heading not in WORK_SECTION_HEADINGS
                    and previous_heading not in NON_WORK_SECTION_HEADINGS
                    and len(previous.split()) <= 14
                    and not DATE_TOKEN.search(previous)
                ):
                    role = previous.strip(" |·:,-")
                    date_quote = f"{previous} {line}"

            if not role or len(role.split()) > 14:
                continue
            if (
                NON_WORK_CONTEXT.search(line)
                and not EMPLOYMENT_STATUS.search(line)
                and not ROLE_CUE.search(role)
            ):
                continue
            has_work_cue = (
                in_work_section
                or bool(EMPLOYMENT_STATUS.search(line))
                or bool(ROLE_CUE.search(role))
            )
            if not has_work_cue:
                continue

            # Remove employment labels from the display role while preserving
            # the complete source line for exact anchoring.
            display_role = EMPLOYMENT_STATUS.sub("", role)
            display_role = re.sub(r"\s+", " ", display_role).strip(" |·:,-")
            if not display_role:
                continue
            episodes.append({
                "role": display_role[:160],
                "company": "",
                "start_date": date_parts[0],
                "end_date": date_parts[1],
                "date_quote": date_quote[:1200],
                "scope_quote": None,
                "experience_areas": [],
                "page_hint": page_number,
                "_source": "local_date_extraction",
            })
            if len(episodes) >= MAX_EPISODES:
                return episodes
    return episodes


def _role_identity(value: Any) -> set[str]:
    role = EMPLOYMENT_STATUS.sub("", str(value or "").casefold())
    return {
        token for token in re.findall(r"[a-z0-9]+", role)
        if token not in {"role", "not", "confirmed", "full", "time", "part"}
    }


def _same_episode_proposal(
    left: dict[str, Any], right: dict[str, Any], *, as_of: date
) -> bool:
    left_start = parse_date_bound(left.get("start_date"), end=False, as_of=as_of)
    left_end = parse_date_bound(left.get("end_date"), end=True, as_of=as_of)
    right_start = parse_date_bound(right.get("start_date"), end=False, as_of=as_of)
    right_end = parse_date_bound(right.get("end_date"), end=True, as_of=as_of)
    if not left_start or not left_end or not right_start or not right_end:
        return False
    if (left_start[0], left_end[0]) != (right_start[0], right_end[0]):
        return False
    left_quote = " ".join(re.findall(r"[a-z0-9]+", str(left.get("date_quote", "")).casefold()))
    right_quote = " ".join(re.findall(r"[a-z0-9]+", str(right.get("date_quote", "")).casefold()))
    if left_quote and left_quote == right_quote:
        return True
    left_role = _role_identity(left.get("role"))
    right_role = _role_identity(right.get("role"))
    if not left_role or not right_role:
        return False
    overlap = len(left_role & right_role) / max(1, len(left_role | right_role))
    return overlap >= 0.6


def _unverified_date_range_flag(date_quote: str, page: int, reason: str) -> dict[str, Any]:
    return {
        "type": "employment_date_range_unverified",
        "date_page": max(0, int(page or 0)),
        "date_quote": date_quote[:500],
        "reason": reason,
        "review_note": (
            "The cited employment dates could not be verified as one explicit, matching range. "
            "No duration was counted; confirm the dates against the CV before relying on total experience."
        ),
    }


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
    model_episodes = episodes if isinstance(episodes, list) else []
    raw_episodes = extract_explicit_employment_episodes(pages)[:MAX_EPISODES]
    for model_episode in model_episodes:
        if len(raw_episodes) >= MAX_EPISODES:
            break
        if not isinstance(model_episode, dict):
            raw_episodes.append(model_episode)
            continue
        duplicate = next(
            (
                existing for existing in raw_episodes
                if isinstance(existing, dict)
                and _same_episode_proposal(existing, model_episode, as_of=today)
            ),
            None,
        )
        if duplicate is not None:
            # Keep locally parsed dates and source quote authoritative, while
            # retaining Muse's optional, separately quote-verified work scope.
            if not duplicate.get("scope_quote") and model_episode.get("scope_quote"):
                duplicate["scope_quote"] = model_episode["scope_quote"]
            if not duplicate.get("experience_areas") and isinstance(
                model_episode.get("experience_areas"), list
            ):
                duplicate["experience_areas"] = model_episode["experience_areas"]
            continue
        raw_episodes.append(model_episode)
    raw_claims = experience_claims if isinstance(experience_claims, list) else []
    exclusions: list[dict[str, str]] = []
    date_range_flags: list[dict[str, Any]] = []
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

        source_dates, range_error = _explicit_date_range(date_quote)
        if range_error:
            exclusions.append({"item": f"episode_{index}", "reason": range_error})
            date_range_flags.append(
                _unverified_date_range_flag(
                    date_quote, int(location.get("page", 0)), range_error
                )
            )
            continue

        start_raw = str(item.get("start_date", "")).strip()
        end_raw = str(item.get("end_date", "")).strip()
        start = parse_date_bound(start_raw, end=False, as_of=today)
        end = parse_date_bound(end_raw, end=True, as_of=today)
        if not start or not end or start[0] >= end[0]:
            reason = "invalid_or_inverted_dates"
            exclusions.append({"item": f"episode_{index}", "reason": reason})
            date_range_flags.append(
                _unverified_date_range_flag(
                    date_quote, int(location.get("page", 0)), reason
                )
            )
            continue
        source_start = parse_date_bound(source_dates[0], end=False, as_of=today)
        source_end = parse_date_bound(source_dates[1], end=True, as_of=today)
        # The exact CV quote must anchor the dates Muse supplied; page checks
        # and matching tokens alone are not enough without a range connector.
        if not source_start or not source_end or source_start[0] != start[0] or source_end[0] != end[0]:
            reason = "dates_do_not_match_quote"
            exclusions.append({"item": f"episode_{index}", "reason": reason})
            date_range_flags.append(
                _unverified_date_range_flag(
                    date_quote, int(location.get("page", 0)), reason
                )
            )
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
            "source": (
                "local_date_extraction"
                if item.get("_source") == "local_date_extraction"
                else "muse_proposal"
            ),
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
            if overlap >= MIN_OVERLAP_REVIEW_MONTHS:
                overlaps.append({
                    "type": "employment_date_overlap",
                    "episodes": [left["id"], right["id"]],
                    "roles": [left["role"], right["role"]],
                    "overlap_months": overlap,
                    "review_note": (
                        "These dated roles overlap by at least three months. Confirm "
                        "whether they were concurrent, part-time, or a date-entry issue."
                    ),
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
    flags: list[dict[str, Any]] = [*date_range_flags, *overlaps]
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
