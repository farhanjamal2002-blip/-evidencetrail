"""Run one real Muse analysis on EvidenceTrail's fictional sample documents.

This script makes two Meta Model API requests when a server-side key is
configured. It never prints the key, CV text, model quotes, or the full report.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def main() -> int:
    if app.ANALYSIS_PROVIDER != "muse":
        print(
            "Set EVIDENCETRAIL_PROVIDER=muse in the server environment. "
            "No Meta request was made.",
            file=sys.stderr,
        )
        return 2
    if not os.getenv("MODEL_API_KEY", "").strip():
        print(
            "MODEL_API_KEY is not configured in the server environment. "
            "No Meta request was made.",
            file=sys.stderr,
        )
        return 2

    job_description = "\n".join(
        [
            "Role: Procurement Automation Lead",
            "Requirements:",
            "1. At least five years of Python experience.",
            "2. Current AWS Solutions Architect Professional certification.",
            "3. At least seven years of procurement experience.",
            "4. At least three years of team leadership experience.",
        ]
    )
    pdf_bytes = app.make_demo_pdf()
    with TestClient(app.app) as client:
        response = client.post(
            "/api/analyze",
            files={"cv": ("evidencetrail-synthetic-cv.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": job_description, "consent": "true"},
        )

    if response.status_code != 200:
        detail = response.json().get("detail", "Analysis failed.")
        print(
            json.dumps(
                {"status": "failed", "http_status": response.status_code, "detail": detail},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    result = response.json()
    summary = {
        "status": "completed",
        "provider": result.get("provider_mode"),
        "model": result.get("model"),
        "analysis_calls": result.get("analysis_calls"),
        "requirements": [
            {"id": item.get("id"), "status": item.get("status"), "certainty": item.get("certainty")}
            for item in result.get("requirements", [])
        ],
        "job_item_coverage": {
            "matched": result.get("job_item_coverage", {}).get("matched", 0),
            "needs_review": result.get("job_item_coverage", {}).get("needs_review", 0),
        },
        "quote_audit": result.get("quote_audit", {}),
        "input_tokens": result.get("usage", {}).get("input_tokens", 0),
        "output_tokens": result.get("usage", {}).get("output_tokens", 0),
        "ocr_pages": result.get("ocr_pages", []),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
