"""Chromium E2E smoke for the 20 fictional CV recruiter inbox (mock only)."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright

OUT=Path("artifacts/demo20-browser")
OUT.mkdir(parents=True,exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        try:
            for width,height in ((1440,940),(375,812)):
                page=await browser.new_page(viewport={"width":width,"height":height})
                errors=[]
                page.on("pageerror",lambda err: errors.append(str(err)))
                paid_calls=[]
                page.on("request",lambda req: paid_calls.append(req.url) if "/api/analyze" in req.url else None)
                res=await page.goto("http://127.0.0.1:8016/demo20",wait_until="domcontentloaded")
                assert res.status==200
                await page.locator("#total").get_by_text("20",exact=True).wait_for()
                await page.wait_for_function("document.querySelector('#ready').textContent==='20'",timeout=25000)
                assert await page.locator("#list .item").count()==20
                assert await page.locator("#list").get_by_text("Recorded Muse").count()==20
                # Three explanatory documentation groups: no opaque score or automatic rejection.
                counts=[int(await page.locator("#coverage-"+kind+"-count").inner_text())
                        for kind in ("complete","partial","attention")]
                assert sum(counts)==20,counts
                assert await page.locator("#list .coverage-dot").count()==80
                assert 1<=await page.locator("#list .coverage-group").count()<=3
                assert not await page.locator("#list").get_by_text("92% match").count()
                await page.locator("#coverage-summary [data-coverage='coverage_complete']").click()
                assert 0<await page.locator("#list .item").count()<20
                assert await page.locator("#filter").input_value()=="coverage_complete"
                await page.locator("#coverage-summary [data-coverage='coverage_complete']").click()
                assert await page.locator("#filter").input_value()=="all"
                assert await page.locator("#list .item").count()==20
                # Four signals per CV are accessible even without distinguishing colors.
                legend=await page.locator("#list .coverage-dots").first.get_attribute("aria-label")
                assert "Requirement 1:" in legend and "Requirement 4:" in legend,legend
                assert not paid_calls,"Instant evidence replay must incur zero new Muse calls"
                await page.locator("#quickviews [data-view='all_direct']").click()
                count=await page.locator("#list .item").count()
                assert 0<count<20
                await page.locator("#quickviews [data-view='awaiting_decision']").click()
                assert await page.locator("#list .item").count()==20
                # Keyboard stepping through the currently visible human review queue.
                first_id=await page.locator("#review .eyebrow").inner_text()
                await page.keyboard.press("j")
                assert await page.locator("#review .eyebrow").inner_text()!=first_id
                await page.keyboard.press("k")
                assert await page.locator("#review .eyebrow").inner_text()==first_id
                await page.locator("#load").click()
                await page.wait_for_function("document.querySelector('#ready').textContent==='0'",timeout=15000)
                assert await page.locator("#list .item").count()==20
                assert await page.locator("#criteria input").count()==4
                assert await page.locator("#ready").inner_text()=="0"
                reset_counts=[int(await page.locator("#coverage-"+k+"-count").inner_text()) for k in ("complete","partial","attention")]
                assert sum(reset_counts)==0,reset_counts
                assert await page.locator("#analyze-one").is_disabled()
                # Editing a criterion must survive a control refresh or candidate selection.
                first=page.locator("#criteria input").first
                original=await first.input_value()
                await first.fill("Five years managing cross-border supplier operations.")
                await page.locator('#list [data-id="ET-005"]').click()
                assert await first.input_value()=="Five years managing cross-border supplier operations."
                await page.locator("#consent").check()
                assert await first.input_value()=="Five years managing cross-border supplier operations."
                await first.fill(original)
                await page.locator("#consent").uncheck()
                assert "NOT Muse" in await page.locator("#consent-copy").inner_text()
                # A custom JD must produce genuinely editable criteria, not merely a count.
                await page.locator("#job").fill(chr(10).join(["Role: Supply Analyst","Requirements:","1. Five years purchasing experience.","2. Managed supplier contracts."]))
                await page.locator("#prepare").click()
                await page.wait_for_function("document.querySelector('#jobstatus').textContent.includes('Extracted')",timeout=10000)
                assert await page.locator("#criteria input").count()>=1
                await page.locator("#load").click()
                await page.wait_for_function("document.querySelectorAll('#criteria input').length===4 && document.querySelector('#job').value.includes('Cedar Gate Supply')",timeout=12000)
                assert await page.locator("#criteria input").count()==4
                # No fabricated 'Muse done' cards on initial load
                assert await page.locator("#list").get_by_text("Not analyzed").count()==20
                small=await page.evaluate("({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})")
                assert small["scroll"]<=small["client"]+3,small
                await page.screenshot(path=str(OUT/f"inbox-{width}.png"),full_page=True)
                if width==375:
                    # The replay's receipt links must wrap cleanly on a phone viewport.
                    await page.locator("#open-benchmark").click()
                    await page.locator("#benchmark-panel").wait_for(state="visible")
                    mobile_replay=await page.evaluate("({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})")
                    assert mobile_replay["scroll"]<=mobile_replay["client"]+3,mobile_replay
                    await page.locator("#back-to-inbox").click()
                    await page.locator("#benchmark-panel").wait_for(state="hidden")
                if width==1440:
                    # The saved replay tab must be self-contained and must not make a paid call.
                    await page.locator("#open-benchmark").click()
                    await page.locator("#benchmark-panel").wait_for(state="visible")
                    desktop_replay=await page.evaluate("({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})")
                    assert desktop_replay["scroll"]<=desktop_replay["client"]+3,desktop_replay
                    assert await page.locator("#benchmark-panel .split-card").count()==2
                    replay_text=await page.locator("#benchmark-panel").inner_text()
                    assert "19/24" in replay_text and "24/24" in replay_text and "25/25" in replay_text
                    assert "conflicting" in replay_text and "not_found" in replay_text
                    assert await page.locator("#inbox-layout").is_hidden()
                    await page.screenshot(path=str(OUT/"actor-swap-replay.png"),full_page=True)
                    # Run pages and full archive listing resolve; the compact case audit is public JSON.
                    audit_response=await page.request.get("http://127.0.0.1:8016/static/replay-artifacts/m02-case-audit.json")
                    assert audit_response.status==200,audit_response.status
                    audit=await audit_response.json()
                    assert audit["schema"]=="evidencetrail/public-m02-case-audit/v1"
                    assert audit["source"]["workflow_run_id"]==41030259074
                    assert audit["source"]["successful_authentic_receipts"]==4
                    assert audit["source"]["automatic_retries"]==0
                    cases={case["case_id"]:case for case in audit["cases"]}
                    assert cases["M02-baseline"]["verification_receipt"]["quote_grounding"]["verified"]==1
                    assert cases["M02-variant"]["finding_summary"][0]["raw_status"]=="conflicting"
                    assert cases["M02-variant"]["finding_summary"][0]["final_status"]=="not_found"
                    assert await page.locator("#m02-audit-json").get_attribute("href")=="/static/replay-artifacts/m02-case-audit.json"
                    for selector in (
                        "#benchmark-panel a[href*='/actions/runs/41030259074']",
                        "#benchmark-panel a[href*='/actions/runs/41031352414']",
                        "#m02-audit-artifact",
                    ):
                        link=page.locator(selector)
                        href=await link.get_attribute("href")
                        assert href and href.startswith("https://github.com/")
                        response=await page.request.get(href)
                        assert response.status==200,(href,response.status)
                    # Encore returns to the same inbox and selects ET-018 without reload.
                    await page.locator("#injection-encore").click()
                    await page.locator("#benchmark-panel").wait_for(state="hidden")
                    assert await page.locator("#inbox-layout").is_visible()
                    assert await page.locator("#search").input_value()=="ET-018"
                    assert await page.locator("#list .item").count()==1
                    assert "selected" in (await page.locator('#list [data-id="ET-018"]').get_attribute("class") or "")
                    assert not paid_calls,"Replay and ET-018 encore must not call the analysis API"
                    # Reopen M02, return again, and ensure the inbox filter/selection survive.
                    await page.locator("#open-benchmark").click()
                    await page.locator("#benchmark-panel").wait_for(state="visible")
                    await page.locator("#back-to-inbox").click()
                    assert await page.locator("#search").input_value()=="ET-018"
                    assert "selected" in (await page.locator('#list [data-id="ET-018"]').get_attribute("class") or "")
                    await page.locator('#search').fill("ET-018")
                    assert await page.locator("#list .item").count()==1
                    await page.locator('#search').fill("")
                    await page.locator('#list [data-id="ET-019"]').click()
                    assert "Image-only" in await page.locator("#review").inner_text() or "Scanned" in await page.locator("#review").inner_text()
                    source=await page.request.get("http://127.0.0.1:8016/demo20/cv/ET-019")
                    assert source.status==200 and (await source.body()).startswith(b"%PDF-")
                    await page.locator("#lock").click()
                    await page.locator("#consent").check()
                    assert await page.locator("#analyze-one").is_enabled()
                    await page.locator("#analyze-one").click()
                    await page.wait_for_function("document.querySelector('#ready').textContent==='1'",timeout=40000)
                    assert "simulation" in (await page.locator("#review").inner_text()).lower()
                    await page.locator("#decision").select_option(label="Hold")
                    await page.locator("#review-note").fill("Clarify source scope with the applicant.")
                    await page.locator("#save-decision").click()
                    assert "Hold" in await page.locator("#review").inner_text()
                    await page.locator("#filter").select_option("reviewed")
                    assert await page.locator("#list .item").count()==1
                    await page.locator("#filter").select_option("all")
                    assert await page.locator("#reviewed").inner_text()=="1"
                    assert await page.locator("#next-review").is_disabled(), "No more analyzed applicants awaiting a human decision"
                    # Return to reviewed CV before testing rubric invalidation.
                    await page.locator('#list [data-id="ET-019"]').click()
                    await page.screenshot(path=str(OUT/"review-selected.png"),full_page=True)
                    # Editing an approved rubric must invalidate old findings and decisions.
                    page.once("dialog",lambda dialog: asyncio.create_task(dialog.accept()))
                    await page.locator("#unlock").click()
                    assert await page.locator("#ready").inner_text()=="0"
                    assert "No decision" in await page.locator("#decision").inner_text()
                    # Competition demo: instant authentic Muse results, with ZERO new model calls.
                    calls=[]
                    page.on("request",lambda req: calls.append(req.url) if "/api/analyze" in req.url else None)
                    await page.locator("#recorded").click()
                    await page.wait_for_function("document.querySelector('#ready').textContent==='20'",timeout=30000)
                    assert await page.locator("#list").get_by_text("Recorded Muse").count()==20
                    assert "Recorded genuine Muse response" in await page.locator("#review").inner_text()
                    assert "Authentic Meta response" in await page.locator("#review").inner_text()
                    start_id=await page.locator("#review .eyebrow").inner_text()
                    await page.locator("#next-review").click()
                    assert await page.locator("#review .eyebrow").inner_text()!=start_id, "Next pending reviewer action must navigate"
                    await page.locator('#list [data-id="ET-005"]').click()
                    assert await page.locator("#review .quote a[href*='#page=']").count()>=1
                    async with page.expect_download() as download_info:
                        await page.locator("#export-report").click()
                    received=await download_info.value
                    assert received.suggested_filename.endswith("-evidence.html")
                    exported=await received.path()
                    report=Path(exported).read_text(encoding="utf-8")
                    assert "Original Muse status" in report
                    assert "Original PDF page" in report
                    assert "<script" not in report.lower()
                    await page.locator("#consent").check()
                    page.once("dialog",lambda dialog: asyncio.create_task(dialog.dismiss()))
                    await page.locator("#analyze-one").click()
                    assert await page.locator("#ready").inner_text()=="20"
                    assert "Recorded genuine Muse response" in await page.locator("#review").inner_text()
                    # Critical semantic acceptance: a scope limitation is NOT a CV self-contradiction.
                    await page.locator("#filter").select_option("scope_limit")
                    assert 0 < await page.locator("#list .item").count() <= 20
                    await page.locator("#filter").select_option("all")
                    await page.locator('#list [data-id="ET-008"]').click()
                    review=await page.locator("#review").inner_text()
                    assert "Scope not established" in review
                    assert "Model: conflicting" in review
                    assert "status override" in await page.locator("#inspect-audit").inner_text()
                    assert await page.locator("#review .matrix .source-snap").count()>0
                    await page.locator("#review .matrix .source-snap").first.click()
                    await page.wait_for_function("document.querySelector('#pdf-page-img')?.naturalWidth>0",timeout=20000)
                    assert await page.locator("#pdf-evidence-viewer").is_visible()
                    assert await page.locator("#pdf-highlight-layer .pdf-bbox-highlight").count()>=1
                    assert "Source located" in await page.locator("#pdf-geometry-badge").inner_text()
                    raw=await page.locator("#pdf-raw-link").get_attribute("href")
                    assert raw.startswith("/demo20/cv/ET-008#page="),raw
                    await page.screenshot(path=str(OUT/"precise-pdf-quote-snap.png"),full_page=True)
                    await page.locator("#pdf-close").click()
                    assert await page.locator("#pdf-evidence-viewer").is_hidden()
                    assert await page.locator("#inspect-audit").get_attribute("aria-expanded")=="false"
                    await page.locator("#inspect-audit").click()
                    assert await page.locator("#inspect-audit").get_attribute("aria-expanded")=="true"
                    receipt=await page.locator("#audit-drawer").inner_text()
                    assert "Meta Muse proposal" in receipt
                    assert "EvidenceTrail verifier" in receipt
                    assert "conflicting → not_found" in receipt
                    assert "explicit_scope_limit_not_contradiction" in receipt
                    assert "Source quotation verified" in receipt
                    assert "not recorded" in receipt.lower()
                    assert "not a hiring recommendation" in receipt.lower() or "no candidate score" in receipt.lower()
                    await page.keyboard.press("a")
                    assert await page.locator("#inspect-audit").get_attribute("aria-expanded")=="false"
                    assert await page.locator("#audit-drawer").count()==0
                    # Image-only CV must identify the actual OCR path, not a guessed mode.
                    await page.locator('#list [data-id="ET-019"]').click()
                    assert "OCR" in await page.locator("#inspect-audit").inner_text()
                    await page.keyboard.press("a")
                    assert "Tesseract OCR" in await page.locator("#audit-drawer").inner_text()
                    assert await page.locator("#review .matrix .source-snap").count()>0
                    await page.locator("#review .matrix .source-snap").first.click()
                    await page.wait_for_function("document.querySelector('#pdf-page-img')?.naturalWidth>0",timeout=20000)
                    assert "scanned OCR" in (await page.locator("#pdf-geometry-badge").inner_text())
                    assert await page.locator("#pdf-highlight-layer .pdf-bbox-highlight").count()==0
                    await page.screenshot(path=str(OUT/"honest-scanned-page-only.png"),full_page=True)
                    await page.locator('#list [data-id="ET-018"]').click()
                    text=await page.locator("#audit-drawer").inner_text()
                    assert "prompt injection scan" in text.lower() and "not_recorded" in text.lower()
                    assert "not establish that a detector fired" in text.lower()
                    await page.keyboard.press("a")
                    assert "Used a warehouse management system, not SAP procurement." in review
                    await page.locator('#list [data-id="ET-015"]').click()
                    review=await page.locator("#review").inner_text()
                    assert "Discrepancy to clarify" in review
                    assert "I never led contract negotiations" in review
                    await page.locator('#list [data-id="ET-005"]').click()
                    await page.locator("#filter").select_option("all_direct")
                    assert 0 < await page.locator("#list .item").count() < 20
                    await page.locator("#filter").select_option("direct")
                    assert 0 < await page.locator("#list .item").count() <= 20
                    await page.locator("#filter").select_option("related")
                    assert 0 < await page.locator("#list .item").count() <= 20
                    assert not calls, "Viewing recorded evidence must not make paid API calls"
                    assert len(paid_calls)==1, "Only the one deliberately triggered mock analysis may call /api/analyze; saved Muse replays must not"
                    await page.screenshot(path=str(OUT/"real-muse-recorded-evidence.png"),full_page=True)
                assert not errors,errors
                await page.close()
        finally:
            await browser.close()
    print("PASS: 20-candidate intake, original PDF, search, 4 rubric fields, explicit consent, real mock API, human Hold action, mobile layout and JS console.")

if __name__=="__main__":asyncio.run(main())
