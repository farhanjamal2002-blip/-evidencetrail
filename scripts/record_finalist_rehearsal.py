"""Record an honest, reproducible judge-demo rehearsal from the PUBLIC frozen build.

No paid calls, no synthetic provider responses, no falsified proof, no external
messages, and no writes to production. This is a SILENT rehearsal clip with
clearly marked captions, not the narrated hackathon submission itself.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import time
from playwright.sync_api import sync_playwright

BASE = os.getenv("EVIDENCETRAIL_DEMO_URL",
                 "https://evidencetrail-judge-rc1-2026.onrender.com").rstrip("/")
EXPECTED_SHA = "8489e45ae0f87d8421562618bda556c31911372b"
OUT = Path("artifacts/submission-rehearsal")
OUT.mkdir(parents=True, exist_ok=True)
TIMELINE: list[dict] = []
START = time.monotonic()

def elapsed():
    return round(time.monotonic() - START, 2)

def caption(page, headline: str, detail: str, seconds: float = 5):
    if len(headline) > 105 or len(detail) > 190:
        raise ValueError("Caption exceeds approved length")
    page.evaluate("""([h,d]) => {
      let el = document.getElementById('evidencetrail-rehearsal-overlay');
      if (!el) {
        el = document.createElement('div');
        el.id = 'evidencetrail-rehearsal-overlay';
        el.setAttribute('aria-label','Video caption; not application UI');
        Object.assign(el.style, {
          position:'fixed',left:'14px',right:'14px',bottom:'14px',
          zIndex:'2147483647',pointerEvents:'none',
          background:'rgba(10,22,26,.94)',border:'1px solid #7c9e91',
          borderLeft:'6px solid #36c49c',borderRadius:'8px',
          color:'#fff',padding:'12px 18px',
          font:'500 17px/1.4 Arial,sans-serif',
          boxShadow:'0 8px 30px rgba(0,0,0,.3)'
        });
        document.body.appendChild(el);
      }
      el.textContent = '';
      const a=document.createElement('div');
      a.style.fontWeight='bold';a.style.fontSize='20px';a.textContent=h;
      const b=document.createElement('div');
      b.style.fontSize='15px';b.style.marginTop='3px';
      b.style.color='#d5eee3';b.textContent=d;
      const c=document.createElement('div');
      c.style.fontSize='10px';c.style.marginTop='4px';
      c.style.color='#b4c6bc';
      c.textContent='REHEARSAL · REAL SAVED MUSE REPLAY · FICTIONAL CVS · NO LIVE MODEL REQUESTS';
      el.append(a,b,c);
    }""", [headline,detail])
    TIMELINE.append({"at_seconds":elapsed(),"headline":headline,
                     "detail":detail,"duration_seconds":seconds})
    page.wait_for_timeout(int(seconds * 1000))

def show(page, selector: str):
    loc = page.locator(selector).first
    loc.scroll_into_view_if_needed(timeout=10000)
    return loc

with sync_playwright() as engine:
    browser = engine.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width":1440,"height":900},
        record_video_dir=str(OUT),
        record_video_size={"width":1280,"height":800},
        accept_downloads=True,
        reduced_motion="reduce",
    )
    context.grant_permissions(["clipboard-read","clipboard-write"],origin=BASE)
    page = context.new_page()
    calls = []
    page.on("request", lambda req: calls.append(req.url) if "/api/analyze" in req.url else None)

    info = context.request.get(BASE+"/build-info",timeout=45000)
    if info.status != 200:
        raise RuntimeError("Public build fingerprint endpoint inaccessible")
    data=info.json()
    if (data.get("source_commit") != EXPECTED_SHA or
        data.get("judge_demo_mode") != "mock_only"):
        raise RuntimeError("Public judge build is stale or not confirmed mock-only")

    response = page.goto(BASE+"/demo20",wait_until="domcontentloaded",timeout=65000)
    assert response and response.status == 200, "Public demo cannot load anonymously"
    page.wait_for_function(
        "document.getElementById('ready').textContent === '20'",
        timeout=40000)
    assert page.locator("#visual-consent").is_disabled()

    caption(page,"What if AI misreads a candidate's CV?",
            "An inspectable evidence review — not an automatic hiring decision.",6)

    show(page,'#list [data-id="ET-003"]').click()
    assert page.locator("#verification-banner").is_visible()
    caption(page,"One fictional applicant. Real recorded Meta Muse analysis.",
            "The saved response has an authentic receipt. Opening it makes zero new model calls.",7)

    show(page,"#verification-banner").click()
    corrections=page.locator(".audit-change")
    assert corrections.count() >= 1, "Must visibly show a genuine status correction"
    first=corrections.first.inner_text()
    assert "supported" in first.lower(), "No real supported-to-uncertain correction found"
    show(page,".audit-change")
    caption(page,"The key moment: EvidenceTrail checks Muse's interpretation.",
            "Actual raw-versus-final status change from the saved genuine Meta response.",12)

    show(page,'#list [data-id="ET-008"]').click()
    snap=page.locator(".source-snap").first
    assert snap.count() >= 1, "No verified source navigation"
    show(page,".source-snap")
    caption(page,"A citation is an original PDF location, not an AI assertion.",
            "Open a source-verified quotation on the fictional CV page.",6)
    snap.click()
    page.locator("#pdf-evidence-viewer").wait_for(state="visible",timeout=20000)
    page.wait_for_function(
        "document.getElementById('pdf-geometry-badge').textContent.includes('Source located')",
        timeout=20000)
    show(page,"#pdf-evidence-viewer")
    caption(page,"Verified source geometry: show the original page.",
            "Page location is checked locally. Presence of text does not prove a claim is true.",8)

    show(page,'#list [data-id="ET-015"]').click()
    assert page.locator(".conflict-pair").count() > 0
    assert "Claim A" in page.locator(".conflict-pair").first.inner_text()
    assert "Claim B" in page.locator(".conflict-pair").first.inner_text()
    show(page,".conflict-pair")
    caption(page,"Contradictions remain visible for a human to resolve.",
            "Two opposing CV statements. No silent guess and no automatic rejection.",9)

    show(page,'#list [data-id="ET-005"]').click()
    show(page,"#generate-followup").click()
    assert "contract" in page.locator("#followup-question").input_value().lower()
    caption(page,"When CV evidence is unclear, ask a precise follow-up.",
            "The question comes from the unresolved job requirement; no extra Muse call.",8)

    show(page,"#copy-selected").click()
    caption(page,"One-click clarification outreach — copied, not sent.",
            "The app does not email applicants automatically.",4)

    page.locator("#followup-question").fill(
        "Which supplier contract terms did you personally negotiate?"
    )
    page.locator("#candidate-reply").fill(
        "FICTIONAL REPLY: I prepared comparisons; my director negotiated the contracts."
    )
    page.locator("#followup-status").select_option("resolved")
    show(page,"#save-followup").click()
    assert "self-attested" in page.locator(".reply-attestation").inner_text().lower()
    show(page,".reply-attestation")
    caption(page,"A candidate's reply is recorded — never magically verified.",
            "Human-entered, timestamped, self-attested. Original CV evidence is unchanged.",10)

    with page.expect_download(timeout=12000) as download:
        show(page,"#export-report").click()
    path=OUT/"fictional-ET-005-evidence.html"
    download.value.save_as(path)
    html=path.read_text(encoding="utf-8")
    assert "Candidate reply — self-attested" in html
    assert "my director negotiated the contracts" in html
    caption(page,"The result: an inspectable export for a human reviewer.",
            "Muse interprets. EvidenceTrail checks the source. The recruiter decides.",8)

    assert not calls, "This rehearsal must not call any paid Muse endpoint"
    (OUT/"video-shotlog.json").write_text(json.dumps({
        "public_url":BASE,"exact_release_sha":EXPECTED_SHA,
        "mode":"saved genuine Muse replay, not fresh inference",
        "public_mock_only":True,
        "all_applicants_fictional":True,
        "candidate_reply_fictional":True,
        "new_meta_model_requests":0,
        "total_capture_seconds":elapsed(),
        "captions":TIMELINE,
        "known_limitation":"SILENT REHEARSAL: not a narrated or submitted final video",
    },indent=2)+"\n",encoding="utf-8")
    video_path=page.video.path()
    page.close()
    context.close()
    browser.close()

mp4=OUT/"evidencetrail-judge-rehearsal-silent.mp4"
subprocess.run([
    "ffmpeg","-y","-hide_banner","-loglevel","error",
    "-i",str(video_path),"-c:v","libx264",
    "-preset","veryfast","-crf","25","-pix_fmt","yuv420p",
    "-movflags","+faststart","-an",str(mp4),
],check=True,timeout=110)
if not mp4.exists() or mp4.stat().st_size < 40_000:
    raise RuntimeError("Recorded MP4 missing or implausibly empty")
print("REHEARSAL_PASS="+json.dumps({
    "sha":EXPECTED_SHA,"new_model_calls":0,
    "duration_seconds":elapsed(),"mp4_bytes":mp4.stat().st_size,
    "source":"anonymous real public judge app",
}))
