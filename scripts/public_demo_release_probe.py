"""Anonymous, zero-provider-call Render demo release parity check.

Only GETs fixed public paths. It never submits a CV, requests model inference,
authenticates, mutates cloud services or guesses deployed source versions.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PUBLIC_URL = "https://evidencetrail-meta-hackathon-demo.onrender.com"
EXPECTED_SHA = (os.getenv("EVIDENCETRAIL_EXPECTED_SHA") or "").strip().lower()
OUT = Path("artifacts/public-smoke/report.json")


def fetch_json(path: str, timeout: int = 22) -> tuple[int | None, object | None, str | None]:
    url = PUBLIC_URL + path
    req = Request(url, headers={"User-Agent": "EvidenceTrail-judge-release-smoke/1.0",
                                "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as r:
            status = r.status
            body = r.read(2_200_000)
    except HTTPError as error:
        return error.code, None, "HTTP " + str(error.code)
    except (URLError, TimeoutError, OSError) as error:
        return None, None, type(error).__name__
    try:
        return status, json.loads(body), None
    except (ValueError, UnicodeError):
        return status, None, "invalid JSON"


def run() -> dict:
    if len(EXPECTED_SHA) != 40 or any(c not in "0123456789abcdef" for c in EXPECTED_SHA):
        return {"passed": False, "error": "expected deployment SHA missing or malformed",
                "requests": [], "model_calls": 0}
    requests = []
    health_ok = False
    # Cold-start grace window without hammering the free public host.
    for attempt in range(1, 7):
        status, body, err = fetch_json("/health")
        requests.append({"path": "/health", "attempt": attempt, "status": status, "error": err})
        if status == 200 and isinstance(body, dict) and body.get("status") == "ok":
            health_ok = True
            break
        if attempt < 6:
            time.sleep(15)
    result = {"passed": False, "expected_sha": EXPECTED_SHA,
              "public_url": PUBLIC_URL, "health_ok": health_ok,
              "requests": requests, "model_calls": 0, "blockers": []}
    if not health_ok:
        result["blockers"].append("Public /health still failed after cold-start grace.")
        return result

    status, build, err = fetch_json("/build-info")
    requests.append({"path": "/build-info", "status": status, "error": err})
    if status != 200 or not isinstance(build, dict) or not build.get("source_provenance_available"):
        result["blockers"].append("Public service has no valid source SHA proof.")
    else:
        result["deployed_sha"] = build.get("source_commit")
        result["deployed_branch"] = build.get("source_branch")
        if build.get("source_commit") != EXPECTED_SHA:
            result["blockers"].append("Stale deployed commit does not equal release candidate.")
        if build.get("judge_demo_mode") != "mock_only":
            result["blockers"].append("Judge host is not confirmed mock-only.")

    status, manifest, err = fetch_json("/demo20/manifest")
    requests.append({"path": "/demo20/manifest", "status": status, "error": err})
    if status != 200 or not isinstance(manifest, dict) or manifest.get("total") != 20:
        result["blockers"].append("The fictional 20-applicant manifest was not accessible.")
    else:
        result["manifest_candidates"] = manifest["total"]
        if manifest.get("live_muse_configured") is True:
            result["blockers"].append("Public host unexpectedly has live paid Muse enabled.")

    status, recording, err = fetch_json("/demo20/recorded-muse")
    requests.append({"path": "/demo20/recorded-muse", "status": status, "error": err})
    if status != 200 or not isinstance(recording, dict):
        result["blockers"].append("Authentic saved Muse replay not anonymously accessible.")
    else:
        rows = recording.get("results", [])
        result["saved_genuine_model_responses"] = len(rows) if isinstance(rows, list) else 0
        if not isinstance(rows, list) or len(rows) != 20 or not all(
            isinstance(row, dict) and row.get("provider_mode") == "muse" and
            row.get("receipt") and row.get("analysis_calls") == 1 for row in rows
        ):
            result["blockers"].append("Recorded responses missing authentic Meta receipt coverage.")

    result["passed"] = not result["blockers"]
    return result


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = run()
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        sys.exit(1)


if __name__ == "__main__":
    main()
