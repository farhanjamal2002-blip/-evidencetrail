"""Local validation for the OpenAI-compatible Muse chat-completions boundary.

This module deliberately has no provider SDK dependency. It can be exercised with
an in-process fake response object and never performs network requests itself.
"""

from __future__ import annotations

import json
from typing import Any


MAX_RESPONSE_CHARS = 128_000
MAX_REQUIREMENTS = 80
MAX_FIRST_PASS_EVIDENCE_PER_REQUIREMENT = 12
MAX_FIRST_PASS_EVIDENCE_TOTAL = 400
MAX_VERIFIER_EVIDENCE_PER_ITEM = 16
MAX_VERIFIER_EVIDENCE_TOTAL = 800
MAX_REQUIREMENT_CHARS = 1_000
MAX_QUOTE_CHARS = 1_600
MAX_REASON_CHARS = 2_000
MAX_APPLICATION_CLAIM_CHARS = 700
MAX_TRANSFER_EXPLANATION_CHARS = 1_200
MAX_FOLLOW_UP_QUESTION_CHARS = 600
MAX_UNPROVEN_ASPECTS = 12
MAX_UNPROVEN_ASPECT_CHARS = 300
MAX_EMPLOYMENT_EPISODES = 40
MAX_EXPERIENCE_CLAIMS = 20
MAX_TIMELINE_TEXT_CHARS = 1_200


class MuseProtocolError(ValueError):
    """The provider response did not satisfy the local contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MuseProtocolError("Muse returned duplicate JSON object keys.")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise MuseProtocolError(f"Muse returned a non-JSON numeric value ({value}).")


def _token_count(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def decode_chat_json_response(
    response: Any,
    *,
    response_name: str,
    max_chars: int = MAX_RESPONSE_CHARS,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Decode a single completed JSON response and normalize optional usage.

    Refusals, truncation, ambiguous multi-choice responses, content blocks, and
    invalid JSON are rejected. Provider exception text and raw response content
    are intentionally omitted from errors returned to the application.
    """
    choices = getattr(response, "choices", None)
    if not isinstance(choices, (list, tuple)) or len(choices) != 1:
        raise MuseProtocolError(f"Muse returned an invalid {response_name} response.")

    choice = choices[0]
    finish_reason = getattr(choice, "finish_reason", None)
    if finish_reason not in (None, "", "stop", "end_turn", "completed"):
        raise MuseProtocolError(
            f"Muse did not complete the {response_name} response."
        )

    message = getattr(choice, "message", None)
    if message is None:
        raise MuseProtocolError(f"Muse returned an invalid {response_name} response.")
    refusal = getattr(message, "refusal", None)
    if refusal:
        raise MuseProtocolError(f"Muse refused the {response_name} request.")

    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise MuseProtocolError(f"Muse returned an empty {response_name} response.")
    if len(content) > max_chars:
        raise MuseProtocolError(f"Muse returned an oversized {response_name} response.")

    try:
        result = json.loads(
            content,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except MuseProtocolError:
        raise
    except (json.JSONDecodeError, RecursionError, TypeError, ValueError) as exc:
        raise MuseProtocolError(f"Muse returned invalid JSON for {response_name}.") from exc
    if not isinstance(result, dict):
        raise MuseProtocolError(f"Muse returned an invalid {response_name} object.")

    usage = getattr(response, "usage", None)
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    completion_details = getattr(usage, "completion_tokens_details", None)
    usage_summary = {
        "input_tokens": _token_count(getattr(usage, "prompt_tokens", None)),
        "output_tokens": _token_count(getattr(usage, "completion_tokens", None)),
        "cached_input_tokens": _token_count(
            getattr(prompt_details, "cached_tokens", None)
        ),
        "reasoning_tokens": _token_count(
            getattr(completion_details, "reasoning_tokens", None)
        ),
    }
    return result, usage_summary


def _require_exact_keys(
    value: dict[str, Any], required: set[str], *, context: str
) -> None:
    if set(value) != required:
        raise MuseProtocolError(f"Muse returned an invalid {context} shape.")


def _require_list(value: Any, *, context: str, maximum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise MuseProtocolError(f"Muse returned an invalid {context} list.")
    return value


def validate_mapping_result(
    result: dict[str, Any], *, max_application_claims: int
) -> dict[str, Any]:
    """Enforce the first-pass schema and resource bounds locally."""
    _require_exact_keys(
        result,
        {"requirements", "application_claims", "employment_episodes", "experience_claims"},
        context="mapping",
    )
    requirements = _require_list(
        result["requirements"], context="requirements", maximum=MAX_REQUIREMENTS
    )
    claims = _require_list(
        result["application_claims"],
        context="application claims",
        maximum=max_application_claims,
    )
    episodes = _require_list(
        result["employment_episodes"],
        context="employment episodes",
        maximum=MAX_EMPLOYMENT_EPISODES,
    )
    experience_claims = _require_list(
        result["experience_claims"],
        context="experience claims",
        maximum=MAX_EXPERIENCE_CLAIMS,
    )
    evidence_total = 0
    for item in requirements:
        if not isinstance(item, dict):
            raise MuseProtocolError("Muse returned an invalid requirement item.")
        _require_exact_keys(item, {"requirement", "evidence"}, context="requirement")
        requirement = item["requirement"]
        if (
            not isinstance(requirement, str)
            or not requirement.strip()
            or len(requirement) > MAX_REQUIREMENT_CHARS
        ):
            raise MuseProtocolError("Muse returned an invalid requirement text.")
        citations = _require_list(
            item["evidence"],
            context="first-pass evidence",
            maximum=MAX_FIRST_PASS_EVIDENCE_PER_REQUIREMENT,
        )
        evidence_total += len(citations)
        if evidence_total > MAX_FIRST_PASS_EVIDENCE_TOTAL:
            raise MuseProtocolError("Muse returned too many first-pass citations.")
        for citation in citations:
            if not isinstance(citation, dict):
                raise MuseProtocolError("Muse returned an invalid first-pass citation.")
            _require_exact_keys(
                citation, {"quote", "role", "page_hint"}, context="first-pass citation"
            )
            quote = citation["quote"]
            role = citation["role"]
            page_hint = citation["page_hint"]
            if (
                not isinstance(quote, str)
                or not quote.strip()
                or len(quote) > MAX_QUOTE_CHARS
            ):
                raise MuseProtocolError("Muse returned an invalid evidence quote.")
            if not isinstance(role, str) or role not in {"supports", "contradicts"}:
                raise MuseProtocolError("Muse returned an invalid evidence role.")
            if page_hint is not None and (
                isinstance(page_hint, bool)
                or not isinstance(page_hint, int)
                or page_hint < 1
            ):
                raise MuseProtocolError("Muse returned an invalid page hint.")

    for claim in claims:
        if not isinstance(claim, dict):
            raise MuseProtocolError("Muse returned an invalid application claim.")
        _require_exact_keys(claim, {"claim"}, context="application claim")
        text = claim["claim"]
        if (
            not isinstance(text, str)
            or not text.strip()
            or len(text) > MAX_APPLICATION_CLAIM_CHARS
        ):
            raise MuseProtocolError("Muse returned invalid application claim text.")

    for episode in episodes:
        if not isinstance(episode, dict):
            raise MuseProtocolError("Muse returned an invalid employment episode.")
        _require_exact_keys(
            episode,
            {
                "role", "company", "start_date", "end_date", "date_quote",
                "scope_quote", "experience_areas", "page_hint",
            },
            context="employment episode",
        )
        for field in ("role", "start_date", "end_date", "date_quote"):
            value = episode[field]
            if not isinstance(value, str) or not value.strip() or len(value) > MAX_TIMELINE_TEXT_CHARS:
                raise MuseProtocolError("Muse returned invalid employment episode text.")
        company = episode["company"]
        if not isinstance(company, str) or len(company) > MAX_TIMELINE_TEXT_CHARS:
            raise MuseProtocolError("Muse returned invalid employment company text.")
        scope_quote = episode["scope_quote"]
        if scope_quote is not None and (
            not isinstance(scope_quote, str) or len(scope_quote) > MAX_TIMELINE_TEXT_CHARS
        ):
            raise MuseProtocolError("Muse returned an invalid employment scope quote.")
        areas = _require_list(
            episode["experience_areas"], context="employment experience areas", maximum=8
        )
        if any(not isinstance(area, str) or not area.strip() or len(area) > 100 for area in areas):
            raise MuseProtocolError("Muse returned an invalid employment experience area.")
        page_hint = episode["page_hint"]
        if page_hint is not None and (
            isinstance(page_hint, bool) or not isinstance(page_hint, int) or page_hint < 1
        ):
            raise MuseProtocolError("Muse returned an invalid employment page hint.")

    for claim in experience_claims:
        if not isinstance(claim, dict):
            raise MuseProtocolError("Muse returned an invalid experience duration claim.")
        _require_exact_keys(
            claim, {"topic", "claim_quote", "page_hint"}, context="experience duration claim"
        )
        if (
            not isinstance(claim["topic"], str)
            or not claim["topic"].strip()
            or len(claim["topic"]) > 120
            or not isinstance(claim["claim_quote"], str)
            or not claim["claim_quote"].strip()
            or len(claim["claim_quote"]) > MAX_TIMELINE_TEXT_CHARS
        ):
            raise MuseProtocolError("Muse returned invalid experience duration claim text.")
        page_hint = claim["page_hint"]
        if page_hint is not None and (
            isinstance(page_hint, bool) or not isinstance(page_hint, int) or page_hint < 1
        ):
            raise MuseProtocolError("Muse returned an invalid experience claim page hint.")
    return result


def validate_single_pass_result(
    result: dict[str, Any], *, max_application_claims: int
) -> dict[str, Any]:
    """Validate the combined semantic and citation proposal in one model reply.

    Citation text and page hints still require local PDF verification. This
    validator only checks that the response is bounded and structurally usable.
    """
    if not isinstance(result, dict):
        raise MuseProtocolError("Muse returned an invalid single-pass analysis object.")
    _require_exact_keys(
        result,
        {"requirements", "application_claims", "employment_episodes", "experience_claims"},
        context="single-pass analysis",
    )

    requirements = result.get("requirements")
    claims = result.get("application_claims")
    if not isinstance(requirements, list) or not isinstance(claims, list):
        raise MuseProtocolError("Muse returned invalid single-pass analysis lists.")

    # Reuse the established strict limits for quotes, employment timelines,
    # experience claims, and application-claim text.
    mapping_shape = {
        "requirements": [
            {"requirement": item.get("requirement"), "evidence": item.get("evidence")}
            if isinstance(item, dict) else item
            for item in requirements
        ],
        "application_claims": [
            {"claim": item.get("claim")}
            if isinstance(item, dict) else item
            for item in claims
        ],
        "employment_episodes": result.get("employment_episodes"),
        "experience_claims": result.get("experience_claims"),
    }
    validate_mapping_result(
        mapping_shape, max_application_claims=max_application_claims
    )

    semantic_fields = {
        "requirement", "status", "evidence_type", "evidence_strength",
        "transfer_explanation", "unproven_aspects", "follow_up_question",
        "certainty", "reason", "evidence",
    }
    for item in requirements:
        if not isinstance(item, dict) or set(item) != semantic_fields:
            raise MuseProtocolError("Muse returned an invalid single-pass requirement shape.")
        if not isinstance(item["status"], str) or item["status"] not in {"supported", "not_found", "conflicting"}:
            raise MuseProtocolError("Muse returned an invalid requirement status.")
        if not isinstance(item["evidence_type"], str) or item["evidence_type"] not in {"direct", "related", "unsupported", "conflicting"}:
            raise MuseProtocolError("Muse returned an invalid requirement evidence type.")
        if not isinstance(item["evidence_strength"], str) or item["evidence_strength"] not in {"specific", "stated", "keyword_only", "none"}:
            raise MuseProtocolError("Muse returned an invalid requirement evidence strength.")
        if not isinstance(item["certainty"], str) or item["certainty"] not in {"clear", "ambiguous"}:
            raise MuseProtocolError("Muse returned invalid requirement certainty.")
        if len(item["evidence"]) > 2:
            raise MuseProtocolError("Muse returned too many citations for one requirement.")
        if not isinstance(item["reason"], str) or len(item["reason"]) > MAX_REASON_CHARS:
            raise MuseProtocolError("Muse returned an invalid requirement reason.")
        transfer = item["transfer_explanation"]
        if transfer is not None and (
            not isinstance(transfer, str)
            or len(transfer) > MAX_TRANSFER_EXPLANATION_CHARS
        ):
            raise MuseProtocolError("Muse returned an invalid transfer explanation.")
        question = item["follow_up_question"]
        if question is not None and (
            not isinstance(question, str)
            or len(question) > MAX_FOLLOW_UP_QUESTION_CHARS
        ):
            raise MuseProtocolError("Muse returned an invalid follow-up question.")
        aspects = _require_list(
            item["unproven_aspects"],
            context="requirement unproven aspects",
            maximum=MAX_UNPROVEN_ASPECTS,
        )
        if any(
            not isinstance(aspect, str)
            or not aspect.strip()
            or len(aspect) > MAX_UNPROVEN_ASPECT_CHARS
            for aspect in aspects
        ):
            raise MuseProtocolError("Muse returned invalid unproven aspects.")

    claim_fields = {"claim", "status", "certainty", "reason", "evidence"}
    for item in claims:
        if not isinstance(item, dict) or set(item) != claim_fields:
            raise MuseProtocolError("Muse returned an invalid single-pass application claim shape.")
        if not isinstance(item["status"], str) or item["status"] not in {"supported", "not_found", "conflicting"}:
            raise MuseProtocolError("Muse returned an invalid application-claim status.")
        if not isinstance(item["certainty"], str) or item["certainty"] not in {"clear", "ambiguous"}:
            raise MuseProtocolError("Muse returned invalid application-claim certainty.")
        if not isinstance(item["reason"], str) or len(item["reason"]) > MAX_REASON_CHARS:
            raise MuseProtocolError("Muse returned an invalid application-claim reason.")
        citations = _require_list(
            item["evidence"],
            context="application-claim evidence",
            maximum=2,
        )
        for citation in citations:
            if not isinstance(citation, dict):
                raise MuseProtocolError("Muse returned invalid application-claim evidence.")
            _require_exact_keys(
                citation,
                {"quote", "role", "page_hint"},
                context="application-claim citation",
            )
            quote = citation["quote"]
            role = citation["role"]
            page_hint = citation["page_hint"]
            if not isinstance(quote, str) or not quote.strip() or len(quote) > MAX_QUOTE_CHARS:
                raise MuseProtocolError("Muse returned an invalid application-claim quote.")
            if not isinstance(role, str) or role not in {"supports", "contradicts"}:
                raise MuseProtocolError("Muse returned an invalid application-claim evidence role.")
            if page_hint is not None and (
                isinstance(page_hint, bool)
                or not isinstance(page_hint, int)
                or page_hint < 1
            ):
                raise MuseProtocolError("Muse returned an invalid application-claim page hint.")
    return result


def validate_verification_result(
    result: dict[str, Any],
    verification_payload: dict[str, Any],
    *,
    max_application_claims: int,
) -> dict[str, Any]:
    """Validate verifier shape, enums, count bounds, and one-to-one item IDs."""
    _require_exact_keys(
        result, {"reviews", "application_reviews"}, context="verification"
    )
    expected_requirements = verification_payload.get("requirements")
    expected_claims = verification_payload.get("application_claims")
    if not isinstance(expected_requirements, list) or not isinstance(expected_claims, list):
        raise MuseProtocolError("The local verification request is invalid.")
    if len(expected_requirements) > MAX_REQUIREMENTS or len(expected_claims) > max_application_claims:
        raise MuseProtocolError("The local verification request exceeds its limit.")

    reviews = _require_list(
        result["reviews"], context="verification reviews", maximum=MAX_REQUIREMENTS
    )
    application_reviews = _require_list(
        result["application_reviews"],
        context="application reviews",
        maximum=max_application_claims,
    )
    citation_total = 0

    def validate_reviews(
        items: list[Any],
        *,
        id_key: str,
        expected_items: list[Any],
        context: str,
        semantic_fields: bool = False,
    ) -> None:
        nonlocal citation_total
        expected_ids: list[str] = []
        for expected in expected_items:
            if not isinstance(expected, dict) or not isinstance(expected.get("id"), str):
                raise MuseProtocolError("The local verification request is invalid.")
            expected_ids.append(expected["id"])
        seen_ids: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                raise MuseProtocolError(f"Muse returned an invalid {context} item.")
            required_fields = {id_key, "status", "certainty", "reason", "evidence"}
            if semantic_fields:
                required_fields.update(
                    {
                        "evidence_type",
                        "evidence_strength",
                        "transfer_explanation",
                        "unproven_aspects",
                        "follow_up_question",
                    }
                )
            _require_exact_keys(item, required_fields, context=context)
            item_id = item[id_key]
            if not isinstance(item_id, str) or item_id in seen_ids:
                raise MuseProtocolError(f"Muse returned duplicate or invalid {context} IDs.")
            seen_ids.add(item_id)
            status = item["status"]
            if not isinstance(status, str) or status not in {
                "supported", "not_found", "conflicting"
            }:
                raise MuseProtocolError(f"Muse returned an invalid {context} status.")
            if semantic_fields:
                evidence_type = item["evidence_type"]
                if not isinstance(evidence_type, str) or evidence_type not in {
                    "direct", "related", "unsupported", "conflicting"
                }:
                    raise MuseProtocolError(f"Muse returned an invalid {context} evidence type.")
                evidence_strength = item["evidence_strength"]
                if not isinstance(evidence_strength, str) or evidence_strength not in {
                    "specific", "stated", "keyword_only", "none"
                }:
                    raise MuseProtocolError(f"Muse returned an invalid {context} evidence strength.")
                transfer = item["transfer_explanation"]
                if transfer is not None and (
                    not isinstance(transfer, str)
                    or len(transfer) > MAX_TRANSFER_EXPLANATION_CHARS
                ):
                    raise MuseProtocolError(f"Muse returned an invalid {context} transfer explanation.")
                question = item["follow_up_question"]
                if question is not None and (
                    not isinstance(question, str)
                    or len(question) > MAX_FOLLOW_UP_QUESTION_CHARS
                ):
                    raise MuseProtocolError(f"Muse returned an invalid {context} follow-up question.")
                aspects = _require_list(
                    item["unproven_aspects"],
                    context=f"{context} unproven aspects",
                    maximum=MAX_UNPROVEN_ASPECTS,
                )
                if any(
                    not isinstance(aspect, str)
                    or not aspect.strip()
                    or len(aspect) > MAX_UNPROVEN_ASPECT_CHARS
                    for aspect in aspects
                ):
                    raise MuseProtocolError(f"Muse returned invalid {context} unproven aspects.")
            certainty = item["certainty"]
            if not isinstance(certainty, str) or certainty not in {"clear", "ambiguous"}:
                raise MuseProtocolError(f"Muse returned invalid {context} certainty.")
            reason = item["reason"]
            if not isinstance(reason, str) or len(reason) > MAX_REASON_CHARS:
                raise MuseProtocolError(f"Muse returned an invalid {context} reason.")
            citations = _require_list(
                item["evidence"],
                context=f"{context} evidence",
                maximum=MAX_VERIFIER_EVIDENCE_PER_ITEM,
            )
            citation_total += len(citations)
            if citation_total > MAX_VERIFIER_EVIDENCE_TOTAL:
                raise MuseProtocolError("Muse returned too many verification citations.")
            for citation in citations:
                if not isinstance(citation, dict):
                    raise MuseProtocolError("Muse returned an invalid verification citation.")
                _require_exact_keys(
                    citation, {"source_id", "quote", "role"}, context="verification citation"
                )
                source_id = citation["source_id"]
                if (
                    not isinstance(source_id, str)
                    or not source_id
                    or len(source_id) > 100
                ):
                    raise MuseProtocolError("Muse returned an invalid source ID.")
                quote = citation["quote"]
                if (
                    not isinstance(quote, str)
                    or not quote.strip()
                    or len(quote) > MAX_QUOTE_CHARS
                ):
                    raise MuseProtocolError("Muse returned an invalid verification quote.")
                role = citation["role"]
                if not isinstance(role, str) or role not in {"supports", "contradicts"}:
                    raise MuseProtocolError("Muse returned an invalid verification role.")
        if len(items) != len(expected_ids) or seen_ids != set(expected_ids):
            raise MuseProtocolError(f"Muse did not return one {context} per input item.")

    validate_reviews(
        reviews,
        id_key="requirement_id",
        expected_items=expected_requirements,
        context="requirement review",
        semantic_fields=True,
    )
    validate_reviews(
        application_reviews,
        id_key="claim_id",
        expected_items=expected_claims,
        context="application review",
    )
    return result
