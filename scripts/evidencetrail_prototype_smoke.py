"""Browser smoke for the standalone EvidenceTrail redesign prototype (offline only)."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("artifacts/evidencetrail-prototype-browser")
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:8016/static/evidencetrail-redesign-preview.html"
SCREENS = ("start", "setup", "upload", "run", "inbox", "review", "source", "benchmark")


async def assert_accessible_controls(page):
    controls = await page.locator("button:visible, a[href]:visible").all()
    for control in controls:
        box = await control.bounding_box()
        assert box and box["width"] >= 44 and box["height"] >= 44, ("touch target", box)
    ratios = await page.evaluate("""() => {
      const luminance = color => {
        const values = color.match(/[\\d.]+/g).map(Number).slice(0, 3).map(v => {
          v /= 255;
          return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
        });
        return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
      };
      const opaqueBackground = el => {
        for (let node = el; node; node = node.parentElement) {
          const c = getComputedStyle(node).backgroundColor;
          const values = c.match(/[\\d.]+/g).map(Number);
          if (values.length < 4 || values[3] >= .98) return c;
        }
        return "rgb(255,255,255)";
      };
      const ratio = el => {
        const a = luminance(getComputedStyle(el).color);
        const b = luminance(opaqueBackground(el));
        return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      };
      const selectors = [".muted", ".status.supported", ".status.notfound",
        ".status.conflicting", ".status.ambiguous", ".status.related",
        ".status.unknown", ".nav-label", ".nav button", ".btn.primary",
        ".content-label", ".untrusted-block p", ".next-card strong"];
      const values = {};
      for (const selector of selectors) {
        const el = [...document.querySelectorAll(selector)].find(node =>
          node.getClientRects().length && getComputedStyle(node).visibility !== "hidden");
        if (el) values[selector] = ratio(el);
      }
      return values;
    }""")
    assert ratios and all(value >= 4.5 for value in ratios.values()), ("text contrast", ratios)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            for width, height in ((1440, 940), (390, 844)):
                page = await browser.new_page(viewport={"width": width, "height": height})
                errors = []
                analysis_calls = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.on("request", lambda req: analysis_calls.append(req.url)
                        if "/api/analyze" in req.url else None)

                response = await page.goto(URL, wait_until="domcontentloaded")
                assert response and response.status == 200
                assert await page.locator(".screen").count() == 8

                for screen_id in SCREENS:
                    await page.locator(f'[data-screen-link="{screen_id}"]').first.click()
                    screen = page.locator("#screen-" + screen_id)
                    assert await screen.is_visible(), screen_id
                    assert "Saved replay" in await page.locator("#saved-replay-indicator").inner_text()
                    await assert_accessible_controls(page)
                    if screen_id == "inbox":
                        rows = page.locator("#candidate-list .candidate")
                        assert await rows.count() == 5
                        assert await page.locator("#candidate-list button").count() == 1
                        await page.locator("#state-filter").select_option("conflicting")
                        assert await page.locator("#candidate-list .candidate:visible").count() == 1
                        assert "ET-018" in await page.locator("#candidate-list").inner_text()
                        await page.locator("#state-filter").select_option("supported")
                        assert await page.locator("#candidate-list .candidate:visible").count() == 1
                        assert "ET-019" in await page.locator("#candidate-list").inner_text()
                        await page.locator("#applicant-search").fill("ET-018")
                        assert await page.locator("#candidate-list .candidate:visible").count() == 0
                        assert await page.locator("#candidate-empty").is_visible()
                        await page.locator("#applicant-search").fill("")
                        await page.locator("#state-filter").select_option("all")
                        await page.locator("#candidate-list button[data-screen-link='review']").click()
                        assert await page.locator("#screen-review").is_visible()
                        await page.locator(".nav [data-screen-link='inbox']").click()
                        assert await page.locator("#screen-inbox").is_visible()
                    if screen_id == "review":
                        finding = page.locator("#screen-review")
                        assert await finding.locator(".verification-checks .axis-card").count() == 2
                        assert "Quote on the page?" in await finding.inner_text()
                        assert "Does it credit the applicant?" in await finding.inner_text()
                        assert await finding.locator(".pipeline-outcome del").inner_text() == "conflicting"
                        assert "→" in await finding.locator(".pipeline-outcome").inner_text()
                        assert "not_found" in await finding.locator(".pipeline-outcome").inner_text()
                        assert "Why it changed:" in await finding.locator(".why-line").inner_text()
                        assert await finding.locator(".decision-panel").is_visible()
                        assert await page.locator("#decision-status").inner_text() == "Not reviewed"
                        await page.locator("[data-review-state='Follow-up']").click()
                        await page.locator("#review-note").fill("Ask who led the negotiations.")
                        await page.locator("[data-action='save-decision']").click()
                        assert await page.locator("#decision-status").inner_text() == "Follow-up"
                        assert "Ask who led the negotiations." in await page.locator("#decision-saved-note").inner_text()
                        assert "Compare with M02 replay" in await finding.inner_text()
                        await page.reload(wait_until="domcontentloaded")
                        assert await page.locator("#screen-review").is_visible()
                        assert await page.locator("#decision-status").inner_text() == "Follow-up"
                        assert "Ask who led the negotiations." in await page.locator("#review-note").input_value()
                        await page.locator(".nav [data-screen-link='inbox']").click()
                        assert "1 recruiter decision recorded" in await page.locator("#decision-count").inner_text()
                        await page.locator(".nav [data-screen-link='review']").click()
                    if screen_id == "source":
                        block = page.locator("#screen-source .untrusted-block")
                        assert "treated as content" in (await block.inner_text()).lower()
                        assert await block.evaluate("(el)=>getComputedStyle(el).borderStyle") == "dashed"
                    if screen_id == "benchmark":
                        cards = page.locator("#screen-benchmark .case-card")
                        assert await cards.count() == 2
                        for i in range(2):
                            card = cards.nth(i)
                            assert await card.locator(".verification-checks .axis-card").count() == 2
                            assert "Quote on the page?" in await card.inner_text()
                            assert "Does it credit the applicant?" in await card.inner_text()
                            assert await card.locator(".pipeline-outcome del").count() == 1
                            assert "→" in await card.locator(".pipeline-outcome").inner_text()
                            assert "Why it changed:" in await card.locator(".why-line").inner_text()
                        next_card = page.locator("[data-next-card]")
                        assert "ET-018" in await next_card.inner_text()
                        assert await next_card.evaluate("(el)=>getComputedStyle(el).backgroundColor") == "rgb(32, 38, 35)"
                        assert "not an accuracy estimate for real CVs" in await page.locator(".benchmark-caveat").inner_text()
                        await next_card.click()
                        assert await page.locator("#screen-source").is_visible()
                        await page.locator('[data-screen-link="benchmark"]').first.click()
                    dims = await page.evaluate(
                        "({scroll:document.documentElement.scrollWidth,"
                        "client:document.documentElement.clientWidth})"
                    )
                    assert dims["scroll"] <= dims["client"] + 3, (screen_id, width, dims)
                    if width == 1440:
                        await page.screenshot(
                            path=str(OUT / f"screen-{screen_id}.png"), full_page=True
                        )

                await page.locator("[data-action='open-audit']:visible").first.click()
                audit = page.locator("#audit-overlay")
                assert await audit.get_attribute("aria-hidden") == "false"
                text = await audit.inner_text()
                assert "chatcmpl-01a18c0a-a8e5-7533-88ec-b02a7d8f7c9d" in text
                assert "chatcmpl-01a18c0a-b026-7153-9dfa-ac9fb569b9a4" in text
                assert "1 proposed · 1 verified · 0 excluded" in text
                dims = await page.evaluate(
                    "({scroll:document.documentElement.scrollWidth,"
                    "client:document.documentElement.clientWidth})"
                )
                assert dims["scroll"] <= dims["client"] + 3, ("audit overlay", width, dims)
                if width == 1440:
                    await page.screenshot(path=str(OUT / "audit-overlay.png"), full_page=True)
                await page.keyboard.press("Escape")
                assert await audit.get_attribute("aria-hidden") == "true"
                await page.locator("[data-action='open-audit']:visible").first.click()
                assert await audit.get_attribute("aria-hidden") == "false"
                await page.locator("#audit-overlay").click(position={"x": 10, "y": 10})
                assert await audit.get_attribute("aria-hidden") == "true"
                await page.locator("[data-action='open-audit']:visible").first.click()
                await page.locator("#audit-overlay [data-action='close-audit']").first.click()
                assert await audit.get_attribute("aria-hidden") == "true"

                await page.locator("[data-action='open-export']").click()
                export = page.locator("#export-overlay")
                assert await export.get_attribute("aria-hidden") == "false"
                assert "The downloadable report remains generated by the existing application." in await export.inner_text()
                if width == 1440:
                    await page.screenshot(path=str(OUT / "export-preview.png"), full_page=True)
                await page.locator("[data-action='export-ready']").click()
                assert await export.get_attribute("aria-hidden") == "true"
                assert "Prototype only" in await page.locator("#toast").inner_text()
                assert not analysis_calls, analysis_calls
                assert not errors, errors
                await page.close()
        finally:
            await browser.close()

    print("PASS: eight prototype screens and both overlays at desktop and phone widths; no overflow, JS errors, or analysis calls.")


if __name__ == "__main__":
    asyncio.run(main())
