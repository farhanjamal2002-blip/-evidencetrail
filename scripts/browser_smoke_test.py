"""Verify EvidenceTrail replay and consent flows in a real headless browser."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

READY_URL = os.getenv("EVIDENCETRAIL_READY_URL", "http://127.0.0.1:8000").rstrip("/")
NO_KEY_URL = os.getenv("EVIDENCETRAIL_NO_KEY_URL", "http://127.0.0.1:8001").rstrip("/")
ARTIFACT_DIR = Path("artifacts/browser-smoke")


def format_run_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


async def install_network_guards(page, analysis_attempts: list[dict], meta_attempts: list[str]) -> None:
    async def block_analysis(route) -> None:
        analysis_attempts.append(
            {"method": route.request.method, "url": route.request.url}
        )
        await route.abort()

    async def block_meta(route) -> None:
        meta_attempts.append(route.request.url)
        await route.abort()

    await page.route("**/api/analyze", block_analysis)
    await page.route("https://api.meta.ai/**", block_meta)


async def capture_page(page, name: str) -> str:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(ARTIFACT_DIR / f"{name}.png"), full_page=False)
    body = await page.locator("body").inner_text()
    (ARTIFACT_DIR / f"{name}.txt").write_text(body, encoding="utf-8")
    return body


async def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    analysis_attempts: list[dict] = []
    meta_attempts: list[str] = []
    evidence: dict = {}
    current_page = None

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000}
            )
            page = await context.new_page()
            current_page = page
            page.set_default_timeout(10_000)
            await install_network_guards(page, analysis_attempts, meta_attempts)

            manifest_response = await page.request.get(f"{READY_URL}/demo/unified-replay")
            assert manifest_response.status == 200, "Saved Muse replay endpoint failed."
            replay = await manifest_response.json()
            assert replay.get("replay_mode") == "frozen_live_muse_results"
            assert replay.get("makes_model_request") is False
            assert replay.get("model") == "muse-spark-1.3"
            assert len(replay.get("results", [])) == 5

            proposed = 0
            verified = 0
            for entry in replay["results"]:
                result = entry.get("result", {})
                assert result.get("provider_mode") == "muse"
                assert result.get("model") == replay["model"]
                audit = result.get("verification_audit", {})
                proposed += int(audit.get("proposed", 0))
                verified += int(audit.get("verified", 0))
            assert proposed > 0 and verified == proposed, (
                f"Replay source audit mismatch: {verified}/{proposed} citations verified."
            )
            replay_stamp = format_run_timestamp(replay["run_at_utc"])
            expected_run_detail = (
                f"{replay['model']} · run {replay_stamp} · "
                f"{replay['analysis_calls']} Muse calls"
            )

            response = await page.goto(READY_URL, wait_until="domcontentloaded")
            assert response and response.status == 200
            assert await page.locator("#model-status-title").inner_text() == "MUSE READY"
            assert await page.locator("#analyze-button").is_enabled()

            # Start from Analyze, then choose the saved result. Replay is consent-free.
            await page.locator("#analyze-button").click()
            dialog = page.locator("#analysis-mode-dialog")
            await dialog.wait_for(state="visible")
            assert await page.locator("#choose-live-analysis").is_enabled()
            assert await page.locator("#choose-verified-replay").is_enabled()
            await page.screenshot(
                path=str(ARTIFACT_DIR / "ready-mode-chooser.png"),
                full_page=False,
            )
            await page.locator("#choose-verified-replay").click()

            results = page.locator("#results")
            await results.wait_for(state="visible")
            assert await page.locator("#model-status-title").inner_text() == "SAVED META AI REPLAY"
            assert await page.locator("#model-status-detail").inner_text() == (
                expected_run_detail + " · no new API request"
            )
            assert await page.locator("#batch-review-items .batch-candidate").count() == 5
            assert await page.locator("#consent").is_checked() is False

            disclosure = page.locator("#preview-notice")
            assert await disclosure.is_visible()
            disclosure_text = await disclosure.inner_text()
            assert replay.get("disclosure", "") in disclosure_text
            assert "Recorded run: " + expected_run_detail + "." in disclosure_text

            verifier_chip = page.locator("#verifier-chip")
            assert await verifier_chip.is_visible()
            verifier_text = await verifier_chip.inner_text()
            assert "Source check" in verifier_text

            await page.locator("#results .results-top").scroll_into_view_if_needed()
            replay_body = await capture_page(page, "saved-muse-replay")
            assert "SAVED META AI REPLAY" in replay_body
            assert "no new API request" in replay_body

            # The replay has valid fictional inputs; consent is the only invalid field.
            invalid_controls = await page.locator("#analysis-form").evaluate(
                """form => Array.from(form.elements)
                    .filter(element => element.willValidate && !element.validity.valid)
                    .map(element => element.id || element.name)"""
            )
            assert invalid_controls == ["consent"], (
                f"Expected consent to be the sole invalid control, got {invalid_controls!r}"
            )
            consent = page.locator("#consent")
            assert await consent.is_visible()
            assert await consent.get_attribute("required") is not None
            assert await consent.is_checked() is False

            await page.locator("#analyze-button").click()
            await dialog.wait_for(state="visible")
            await page.locator("#choose-live-analysis").click()
            await dialog.wait_for(state="hidden")
            assert await consent.is_checked() is False
            invalid_after_live_choice = await page.locator("#analysis-form").evaluate(
                """form => Array.from(form.elements)
                    .filter(element => element.willValidate && !element.validity.valid)
                    .map(element => element.id || element.name)"""
            )
            assert invalid_after_live_choice == ["consent"]
            assert analysis_attempts == [], (
                f"Live request reached the local analysis endpoint without consent: {analysis_attempts!r}"
            )
            assert meta_attempts == [], (
                f"Unexpected browser request to Meta: {meta_attempts!r}"
            )

            await consent.scroll_into_view_if_needed()
            await capture_page(page, "live-consent-blocked")

            no_key_page = await context.new_page()
            current_page = no_key_page
            no_key_page.set_default_timeout(10_000)
            await install_network_guards(no_key_page, analysis_attempts, meta_attempts)
            no_key_response = await no_key_page.goto(NO_KEY_URL, wait_until="domcontentloaded")
            assert no_key_response and no_key_response.status == 200
            assert await no_key_page.locator("#model-status-title").inner_text() == "MUSE NOT CONFIGURED"
            assert await no_key_page.locator("#analyze-button").is_disabled()

            replay_button = no_key_page.locator("#load-unified-replay")
            assert await replay_button.is_visible()
            replay_classes = await replay_button.get_attribute("class") or ""
            assert "primary-button" in replay_classes, (
                f"Saved replay is not the primary no-key action: {replay_classes!r}"
            )
            assert await no_key_page.locator("#preview-demo-results").is_visible() is False

            await replay_button.click()
            await no_key_page.locator("#results").wait_for(state="visible")
            assert await no_key_page.locator("#model-status-title").inner_text() == "SAVED META AI REPLAY"
            no_key_detail = await no_key_page.locator("#model-status-detail").inner_text()
            assert expected_run_detail in no_key_detail
            no_key_body = await capture_page(no_key_page, "no-key-saved-replay")
            assert "SAVED META AI REPLAY" in no_key_body
            assert analysis_attempts == []
            assert meta_attempts == []

            evidence = {
                "result": "pass",
                "replay": {
                    "model": replay["model"],
                    "run_at_utc": replay["run_at_utc"],
                    "analysis_calls": replay["analysis_calls"],
                    "candidate_count": len(replay["results"]),
                    "verified_citations": verified,
                    "proposed_citations": proposed,
                    "ui_badge": "SAVED META AI REPLAY",
                },
                "live_consent_gate": {
                    "required": True,
                    "unchecked": True,
                    "blocked_before_api_request": True,
                    "analysis_requests": len(analysis_attempts),
                    "meta_requests": len(meta_attempts),
                },
                "no_key_state": {
                    "badge": "MUSE NOT CONFIGURED",
                    "analyze_disabled": True,
                    "saved_replay_primary": True,
                    "saved_replay_loads": True,
                },
            }
        except Exception:
            if current_page is not None:
                try:
                    await capture_page(current_page, "failure-state")
                except Exception:
                    pass
            raise
        finally:
            await browser.close()

    (ARTIFACT_DIR / "evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
