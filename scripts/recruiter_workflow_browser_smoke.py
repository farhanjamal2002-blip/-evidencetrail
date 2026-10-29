"""Headless end-to-end proof that human recruiter workflow adds no Muse calls."""
from __future__ import annotations

import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import pymupdf as fitz
from demo20_workflow import make_cv_pdf

BASE = os.getenv("EVIDENCETRAIL_SMOKE_URL","http://127.0.0.1:8017")
OUT = Path("artifacts/recruiter-workflow-browser")
OUT.mkdir(parents=True,exist_ok=True)

with sync_playwright() as engine:
    browser = engine.chromium.launch(headless=True)
    page = browser.new_page(accept_downloads=True, viewport={"width":1440,"height":1000})
    calls = []
    page.on("request", lambda req: calls.append(req.url) if "/api/analyze" in req.url else None)
    response = page.goto(BASE+"/demo20", wait_until="domcontentloaded")
    assert response and response.status == 200
    page.wait_for_function("document.getElementById('ready').textContent === '20'", timeout=30000)
    assert page.locator("#visual-consent").is_disabled()
    page.locator('#list [data-id="ET-005"]').click()
    page.locator("#generate-followup").click()
    question = page.locator("#followup-question")
    assert "contract" in question.input_value().casefold()
    question.fill("Which supplier contracts did you personally negotiate and sign?")
    page.locator("#followup-comment").fill("Clarification request based on R2.")
    page.locator("#save-followup").click()
    assert "draft" in page.locator(".workflow-status").inner_text().lower()
    page.locator("#followup-status").select_option("waiting_external")
    page.locator("#save-followup").click()
    assert "waiting" in page.locator(".workflow-status").inner_text().lower()
    assert "did NOT send" in page.locator("#apistatus").inner_text()
    page.locator("#filter").select_option("waiting_external")
    assert page.locator('#list [data-id="ET-005"]').count() == 1
    with page.expect_download() as download:
        page.locator("#export-workflow").click()
    d = download.value
    assert d.suggested_filename == "evidencetrail-fictional-workflow.csv"
    target = OUT/"workflow.csv"
    d.save_as(target)
    body = target.read_text()
    assert "waiting_external" in body and "ET-005" in body
    assert not calls, "Review/export should never call the Muse analysis endpoint"
    page.screenshot(path=str(OUT/"review-workflow.png"),full_page=True)
    # Main application uploader must accept scanned images, not only PDFs.
    main = browser.new_page()
    main.goto(BASE+"/",wait_until="domcontentloaded")
    with fitz.open(stream=make_cv_pdf("ET-001"),filetype="pdf") as source_pdf:
        png = source_pdf[0].get_pixmap(dpi=135).tobytes("png")
    main.locator("#cv").set_input_files({
        "name":"fictional-scanned-cv.png","mimeType":"image/png","buffer":png,
    })
    assert "fictional-scanned-cv.png" in main.locator("#file-name").inner_text()
    main.screenshot(path=str(OUT/"image-upload.png"),full_page=True)
    main.close()
    browser.close()
print("PASS: Recorded Muse replay, manual clarification, stage, CSV, zero new model calls")
