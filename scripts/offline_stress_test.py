#!/usr/bin/env python3
"""Run EvidenceTrail's analysis path against local fixtures and a fake Muse API.

This intentionally bypasses FastAPI's ASGI/multipart layer. Tiny import shims let
the production analysis function run in a minimal checkout; all provider calls
are intercepted by FakeMuse and never leave this process. It needs PyMuPDF and
Pillow, but no FastAPI, OpenAI SDK, Tesseract install, API key, or network.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


os.environ["EVIDENCETRAIL_PROVIDER"] = "mock"
os.environ["MODEL_API_KEY"] = "local-fake-key-never-sent"
os.environ["MAX_ANALYSES_PER_HOUR_PER_IP"] = "2000"
os.environ["MAX_ANALYSES_PER_PROCESS"] = "2000"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class LocalHTTPException(Exception):
    def __init__(self, status_code: int = 500, detail: str | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def install_import_shims() -> None:
    """Stand in for runtime plumbing that this direct-call harness doesn't use."""
    fastapi = types.ModuleType("fastapi")
    fastapi.__path__ = []

    class FastAPI:
        def __init__(self, **_kwargs: Any):
            pass

        def mount(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def add_middleware(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def include_router(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def get(self, *_args: Any, **_kwargs: Any):
            return lambda function: function

        def post(self, *_args: Any, **_kwargs: Any):
            return lambda function: function

    fastapi.FastAPI = FastAPI
    fastapi.APIRouter = FastAPI
    fastapi.File = lambda default=None, **_kwargs: default
    fastapi.Form = lambda default=None, **_kwargs: default
    fastapi.HTTPException = LocalHTTPException
    fastapi.Request = type("Request", (), {})
    fastapi.UploadFile = type("UploadFile", (), {})

    response_module = types.ModuleType("fastapi.responses")
    response_module.HTMLResponse = type("HTMLResponse", (), {})
    response_module.Response = type("Response", (), {})
    response_module.FileResponse = type("FileResponse", (), {})
    response_module.JSONResponse = type("JSONResponse", (), {})
    static_module = types.ModuleType("fastapi.staticfiles")
    static_module.StaticFiles = type(
        "StaticFiles", (), {"__init__": lambda self, *_a, **_k: None}
    )
    template_module = types.ModuleType("fastapi.templating")
    template_module.Jinja2Templates = type(
        "Jinja2Templates", (), {"__init__": lambda self, *_a, **_k: None}
    )
    middleware_module = types.ModuleType("fastapi.middleware")
    middleware_module.__path__ = []
    gzip_module = types.ModuleType("fastapi.middleware.gzip")
    gzip_module.GZipMiddleware = type("GZipMiddleware", (), {})
    fastapi.middleware = middleware_module
    middleware_module.gzip = gzip_module
    sys.modules.update(
        {
            "fastapi": fastapi,
            "fastapi.middleware": middleware_module,
            "fastapi.middleware.gzip": gzip_module,
            "fastapi.responses": response_module,
            "fastapi.staticfiles": static_module,
            "fastapi.templating": template_module,
        }
    )

    starlette = types.ModuleType("starlette")
    concurrency = types.ModuleType("starlette.concurrency")

    async def run_in_threadpool(function, *args, **kwargs):
        return function(*args, **kwargs)

    concurrency.run_in_threadpool = run_in_threadpool
    sys.modules["starlette"] = starlette
    sys.modules["starlette.concurrency"] = concurrency

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *_args, **_kwargs: None
    sys.modules["dotenv"] = dotenv

    openai = types.ModuleType("openai")
    openai.APIConnectionError = type("APIConnectionError", (Exception,), {})
    openai.OpenAI = lambda **_kwargs: (_ for _ in ()).throw(
        AssertionError("The fake API client must be installed before provider use.")
    )
    sys.modules["openai"] = openai

    # These tests use native-text PDFs. OCR stays unavailable by design.
    pytesseract = types.ModuleType("pytesseract")
    pytesseract.get_languages = lambda **_kwargs: []
    pytesseract.image_to_data = lambda *_args, **_kwargs: {}
    pytesseract.Output = types.SimpleNamespace(DICT="dict")
    sys.modules["pytesseract"] = pytesseract


install_import_shims()

import pymupdf as fitz  # noqa: E402
import app  # noqa: E402


JOB = (
    "Requirements:\n"
    "- At least 5 years of Python experience\n"
    "- Current AWS certification\n"
    "- Bachelor's degree"
)
PYTHON_QUOTE = "Python experience: 8 years"
AWS_QUOTE = "AWS certification expired"
TIMELINE_DATE_QUOTE = "Procurement Analyst | 2020–2025"
TIMELINE_SCOPE_QUOTE = "Managed procurement contracts and vendor bids."
TIMELINE_CLAIM_QUOTE = "Profile: 8 years in procurement."


def make_pdf(*pages: list[str]) -> bytes:
    document = fitz.open()
    for blocks in pages:
        page = document.new_page()
        for index, block in enumerate(blocks):
            page.insert_text((72, 72 + 24 * index), block)
    output = document.tobytes()
    document.close()
    return output


PDF = make_pdf(
    [
        PYTHON_QUOTE,
        AWS_QUOTE,
        "Built reporting workflows and documented operational controls.",
        TIMELINE_DATE_QUOTE,
        TIMELINE_SCOPE_QUOTE,
        TIMELINE_CLAIM_QUOTE,
    ]
)


@dataclass
class LocalRequest:
    client: Any = field(
        default_factory=lambda: types.SimpleNamespace(host="offline-stress-test")
    )
    state: Any = field(default_factory=types.SimpleNamespace)


class LocalUpload:
    def __init__(self, content: bytes, filename: str = "fictional-cv.pdf"):
        self.content = content
        self.filename = filename

    async def read(self, size: int = -1) -> bytes:
        return self.content if size < 0 else self.content[:size]

    async def seek(self, _offset: int) -> None:
        return None


async def analyze(pdf: bytes = PDF, job: str = JOB) -> dict[str, Any]:
    return await app.analyze(
        LocalRequest(),
        LocalUpload(pdf),
        job,
        True,
        "",
    )


def expect_http_error(awaitable, status_code: int) -> LocalHTTPException:
    try:
        asyncio.run(awaitable)
    except LocalHTTPException as exc:
        assert exc.status_code == status_code, (exc.status_code, exc.detail)
        return exc
    raise AssertionError(f"Expected HTTP {status_code}, analysis returned a report.")


class FakeMuseCompletions:
    scenario = "clean"
    calls: list[dict[str, Any]] = []

    def create(self, **request: Any) -> types.SimpleNamespace:
        self.calls.append(request)
        if self.scenario in {"invalid_json", "truncated"}:
            reason = "length" if self.scenario == "truncated" else "stop"
            return self.response("{\"requirements\":", finish_reason=reason)
        if self.scenario == "refusal":
            return self.response("", refusal="local refusal fixture")

        python_quote = (
            "I have 20 years in quantum procurement"
            if self.scenario == "forged_quote"
            else PYTHON_QUOTE
        )
        result: dict[str, Any] = {
            "requirements": [
                {
                    "requirement": "At least 5 years of Python experience",
                    "status": "supported",
                    "evidence_type": "direct",
                    "evidence_strength": "specific",
                    "transfer_explanation": None,
                    "unproven_aspects": [],
                    "follow_up_question": None,
                    "certainty": "clear",
                    "reason": "The CV provides a direct duration statement.",
                    "evidence": [{
                        "quote": python_quote, "role": "supports", "page_hint": 1,
                    }],
                },
                {
                    "requirement": "Current AWS certification",
                    "status": "conflicting",
                    "evidence_type": "conflicting",
                    "evidence_strength": "stated",
                    "transfer_explanation": None,
                    "unproven_aspects": [],
                    "follow_up_question": "Can you clarify the credential's current status?",
                    "certainty": "clear",
                    "reason": "The CV explicitly describes an incompatible credential status.",
                    "evidence": [{
                        "quote": AWS_QUOTE, "role": "contradicts", "page_hint": 1,
                    }],
                },
                {
                    "requirement": "Bachelor's degree",
                    "status": "not_found",
                    "evidence_type": "unsupported",
                    "evidence_strength": "none",
                    "transfer_explanation": None,
                    "unproven_aspects": [],
                    "follow_up_question": "Can you describe your relevant education?",
                    "certainty": "clear",
                    "reason": "No degree passage is shown in this CV.",
                    "evidence": [],
                },
            ],
            "employment_episodes": [{
                "role": "Procurement Analyst",
                "company": "SampleCo",
                "start_date": "2020",
                "end_date": "2025",
                "date_quote": TIMELINE_DATE_QUOTE,
                "scope_quote": TIMELINE_SCOPE_QUOTE,
                "experience_areas": ["procurement"],
                "page_hint": 1,
            }],
            "experience_claims": [{
                "topic": "procurement",
                "claim_quote": TIMELINE_CLAIM_QUOTE,
                "page_hint": 1,
            }],
        }
        if self.scenario == "extra_first_field":
            result["unrequested_field"] = "reject this"
        if self.scenario == "invalid_semantic_enum":
            result["requirements"][0]["evidence_type"] = "invented"
        if self.scenario == "missing_semantic_field":
            del result["requirements"][0]["certainty"]
        return self.response(json.dumps(result))

    @staticmethod
    def response(
        content: str,
        *,
        finish_reason: str = "stop",
        refusal: str | None = None,
    ) -> types.SimpleNamespace:
        return types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content=content, refusal=refusal),
                    finish_reason=finish_reason,
                )
            ],
            usage=types.SimpleNamespace(prompt_tokens=23, completion_tokens=11),
        )


class FakeMuseClient:
    def __init__(self, **config: Any):
        assert config["base_url"] == app.API_BASE_URL
        assert config["api_key"] == "local-fake-key-never-sent"
        assert config["max_retries"] == 0
        self.chat = types.SimpleNamespace(completions=FakeMuseCompletions())


def run_mock_pipeline() -> None:
    app.MOCK_PROVIDER_ENABLED = True
    app.ANALYSIS_PROVIDER = "mock"
    FakeMuseCompletions.calls.clear()
    result = asyncio.run(analyze())
    assert result["provider_mode"] == "mock"
    assert result["analysis_calls"] == 0
    assert result["usage"] == {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "reasoning_tokens": 0,
        "analysis_pass": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_tokens": 0,
        },
        "local_verification": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_tokens": 0,
            "mode": "local_mock",
        },
    }
    assert [item["status"] for item in result["requirements"]] == [
        "supported",
        "conflicting",
        "not_found",
    ]
    assert [item["job_source"]["line"] for item in result["requirements"]] == [2, 3, 4]
    assert all(item["job_source"]["verified"] for item in result["requirements"])
    assert all(
        {"from": f"JD-{item['id']}", "to": item["id"], "relation": "defines"}
        in result["evidence_graph"]["edges"]
        for item in result["requirements"]
    )
    wrapped_jd = (
        "Role: Automation Lead\n\nRequirements:\n"
        "- At least five years of\n"
        "  Python experience, including automation and integrations."
    )
    wrapped_source = app.locate_job_requirement_source(
        wrapped_jd, "At least five years of Python experience"
    )
    assert wrapped_source["line"] == 4
    assert "automation and integrations" in wrapped_source["text"]
    assert not FakeMuseCompletions.calls
    print("PASS mock: 3 outcomes, JD+CV provenance, page grounding, zero API calls")

    hostile_jd = "Requirements:\n- Python experience <script>alert('xss')</script>"
    hostile_source = app.locate_job_requirement_source(hostile_jd, "Python experience")
    hostile_finding = {
        "id": "R1",
        "requirement": "Python experience",
        "job_source": hostile_source,
        "status": "not_found",
        "note": "No direct evidence in the CV.",
        "evidence": [],
    }
    hostile_report = app.build_report(
        findings=[hostile_finding],
        previews={},
        cv_hash="synthetic-cv",
        job_hash="synthetic-job",
        omitted_requirement_audit=[],
        proposed_quotes=0,
        excluded_quotes=0,
        verification_audit={"proposed": 0, "verified": 0, "excluded": 0},
        evidence_graph=app.build_evidence_graph([hostile_finding]),
        created_at="2026-10-28T00:00:00+00:00",
    )
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in hostile_report
    assert "<script>alert('xss')</script>" not in hostile_report
    print("PASS JD provenance: wrapped criteria and hostile markup remain safe")


def run_batch_pipeline() -> None:
    app.MOCK_PROVIDER_ENABLED = True
    app.ANALYSIS_PROVIDER = "mock"
    count_before = app.analysis_count
    request = LocalRequest()
    results = asyncio.run(
        app.analyze_batch(
            request,
            [
                LocalUpload(PDF, "fictional-candidate-a.pdf"),
                LocalUpload(PDF, "fictional-candidate-b.pdf"),
            ],
            JOB,
            True,
        )
    )
    assert results["candidate_count"] == 2
    assert results["completed_count"] == 2
    assert results["failed_count"] == 0
    assert results["analysis_calls"] == 0
    assert results["automated_ranking"] is False
    assert app.analysis_count == count_before + 2
    assert [item["filename"] for item in results["results"]] == [
        "fictional-candidate-a.pdf",
        "fictional-candidate-b.pdf",
    ]
    assert all(item["result"]["provider_mode"] == "mock" for item in results["results"])
    print("PASS batch: two CVs processed in upload order, isolated reports, no ranking")


def run_fake_muse_pipeline() -> None:
    app.MOCK_PROVIDER_ENABLED = False
    app.ANALYSIS_PROVIDER = "muse"
    app.MUSE_PROVIDER_ENABLED = True
    app.OpenAI = FakeMuseClient
    FakeMuseCompletions.scenario = "clean"
    FakeMuseCompletions.calls.clear()
    result = asyncio.run(analyze())
    assert result["provider_mode"] == "muse"
    assert result["analysis_calls"] == 1
    assert result["timeline_audit"]["dated_employment_months"] == 60
    assert result["timeline_audit"]["tenure_by_area"] == [
        {"area": "procurement", "months": 60}
    ]
    assert result["timeline_audit"]["flags"][0]["type"] == "claimed_tenure_exceeds_dated_evidence"
    assert "Timeline and tenure review" in result["report_html"]
    assert len(FakeMuseCompletions.calls) == 1
    assert [item["status"] for item in result["requirements"]] == [
        "supported",
        "conflicting",
        "not_found",
    ]
    assert "application_claim_audit" not in result
    assert all(request["store"] is False for request in FakeMuseCompletions.calls)
    assert FakeMuseCompletions.calls[0]["model"] == app.MODEL_ID
    muse_input = FakeMuseCompletions.calls[0]["messages"][1]["content"]
    assert isinstance(muse_input, str)
    assert "[Page 1]" in muse_input
    assert PYTHON_QUOTE in muse_input
    print("PASS fake Muse: one-pass semantic response, local quote checks, timeline math, strict schema")

    for scenario, expected_calls in (
        ("invalid_json", 1),
        ("truncated", 1),
        ("refusal", 1),
        ("extra_first_field", 1),
        ("invalid_semantic_enum", 1),
        ("missing_semantic_field", 1),
    ):
        FakeMuseCompletions.scenario = scenario
        FakeMuseCompletions.calls.clear()
        failure = expect_http_error(analyze(), 502)
        assert len(FakeMuseCompletions.calls) == expected_calls, scenario
        assert failure.detail and "Muse" in failure.detail
    print("PASS fake Muse attacks: six broken replies fail closed with no report")

    FakeMuseCompletions.scenario = "forged_quote"
    FakeMuseCompletions.calls.clear()
    result = asyncio.run(analyze())
    finding = result["requirements"][0]
    assert finding["status"] == "not_found"
    assert finding["certainty"] == "ambiguous"
    assert finding["evidence"] == []
    assert result["verification_audit"]["rejected_citations"][0]["reason"] == "quote_not_found_on_cited_page"
    print("PASS citation attack: forged quote is rejected by the local page verifier")


def run_input_attacks() -> None:
    app.MOCK_PROVIDER_ENABLED = True
    app.ANALYSIS_PROVIDER = "mock"
    before = len(FakeMuseCompletions.calls)

    for size in range(1, 129):
        malformed = b"%PDF-" + bytes((index * 37 + size) % 256 for index in range(size))
        expect_http_error(analyze(pdf=malformed), 422)
    assert len(FakeMuseCompletions.calls) == before
    print("PASS file attacks: 128 malformed PDFs rejected before any provider call")

    oversized_page_doc = fitz.open()
    for _ in range(app.MAX_PDF_PAGES + 1):
        oversized_page_doc.new_page()
    too_many_pages = oversized_page_doc.tobytes()
    oversized_page_doc.close()
    expect_http_error(analyze(pdf=too_many_pages), 422)

    expect_http_error(analyze(job="x" * (app.MAX_JOB_CHARS + 1)), 400)
    print("PASS boundary attacks: page count and job length caps hold")


def main() -> None:
    run_mock_pipeline()
    run_batch_pipeline()
    run_fake_muse_pipeline()
    run_input_attacks()
    print("All offline stress scenarios passed. No live API requests or model credits used.")


if __name__ == "__main__":
    main()
