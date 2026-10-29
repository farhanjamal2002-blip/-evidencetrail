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
                res=await page.goto("http://127.0.0.1:8016/demo20",wait_until="domcontentloaded")
                assert res.status==200
                await page.locator("#total").get_by_text("20",exact=True).wait_for()
                assert await page.locator("#list .item").count()==20
                assert await page.locator("#criteria input").count()==4
                assert await page.locator("#ready").inner_text()=="0"
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
                if width==1440:
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
                    await page.locator("#filter").select_option("all_direct")
                    assert 0 < await page.locator("#list .item").count() < 20
                    await page.locator("#filter").select_option("direct")
                    assert 0 < await page.locator("#list .item").count() <= 20
                    await page.locator("#filter").select_option("related")
                    assert 0 < await page.locator("#list .item").count() <= 20
                    assert not calls, "Viewing recorded evidence must not make paid API calls"
                    await page.screenshot(path=str(OUT/"real-muse-recorded-evidence.png"),full_page=True)
                assert not errors,errors
                await page.close()
        finally:
            await browser.close()
    print("PASS: 20-candidate intake, original PDF, search, 4 rubric fields, explicit consent, real mock API, human Hold action, mobile layout and JS console.")

if __name__=="__main__":asyncio.run(main())
