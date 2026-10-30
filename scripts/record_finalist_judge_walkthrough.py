"""Record an honest, captioned, silent judge walkthrough from the frozen public app.

This is an EDITABLE VIDEO ASSET, not the official submitted video.
It uses previously saved authentic Meta results, no paid model requests,
and only fictional CV data. Fails if the public host serves a different SHA.
Captions are recorder overlays, not native UI or evidence claims.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

BASE=(os.getenv("EVIDENCETRAIL_JUDGE_URL") or
      "https://evidencetrail-judge-rc1-2026.onrender.com").rstrip("/")
EXPECTED=(os.getenv("EVIDENCETRAIL_EXPECTED_RELEASE_SHA") or
          "8489e45ae0f87d8421562618bda556c31911372b").lower()
OUT=Path("artifacts/finalist-judge-video")
OUT.mkdir(parents=True,exist_ok=True)


def stage(page, heading: str, caption: str, seconds: float):
    """Put an explicitly labelled *video caption* above unaltered app pixels."""
    page.evaluate("""({heading,caption}) => {
      let div=document.getElementById('recording-caption-not-product-ui');
      if(!div){
        div=document.createElement('aside');
        div.id='recording-caption-not-product-ui';
        div.setAttribute('aria-label','Video narration caption, not product UI');
        Object.assign(div.style,{
          position:'fixed',bottom:'12px',left:'calc(50% - 500px)',
          width:'1000px',zIndex:'2147483000',pointerEvents:'none',
          padding:'12px 22px',boxSizing:'border-box',color:'#fff',
          background:'rgba(6,31,37,0.94)',border:'1px solid #56bfa6',
          borderRadius:'14px',font:'500 19px Arial, sans-serif',
          boxShadow:'0 8px 30px rgba(0,0,0,.25)'
        });
        document.body.appendChild(div);
      }
      div.innerHTML='';
      const a=document.createElement('div');
      a.textContent='VIDEO CAPTION · '+heading;
      a.style.cssText='color:#7ce5bb;font-weight:700;font-size:13px;margin-bottom:6px;letter-spacing:.06em';
      const b=document.createElement('div');
      b.textContent=caption;
      div.append(a,b);
    }""",{"heading":heading,"caption":caption})
    page.wait_for_timeout(round(seconds*1000))


def main():
    with urlopen(BASE+"/build-info",timeout=45) as response:
        info=json.load(response)
    if info.get("source_commit")!=EXPECTED or info.get("judge_demo_mode")!="mock_only":
        raise SystemExit("Cannot record: public release SHA or mock-only gate failed")
    errors=[]
    analysis_requests=[]
    screenshots=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(
            viewport={"width":1365,"height":768},
            record_video_dir=str(OUT),
            record_video_size={"width":1365,"height":768},
            accept_downloads=True,
            reduced_motion="reduce",
            color_scheme="light",
        )
        page=context.new_page()
        page.on("request",lambda req: analysis_requests.append(req.url)
                if "/api/analyze" in req.url else None)
        page.on("pageerror",lambda error: errors.append(str(error)))
        response=page.goto(BASE+"/demo20",wait_until="domcontentloaded",timeout=70000)
        if not response or response.status!=200:
            raise AssertionError("Judge demo page was not reachable")
        page.wait_for_function(
            "document.getElementById('ready')?.textContent === '20'",
            timeout=45000
        )
        page.locator('#list [data-id="ET-003"]').click()
        banner=page.locator("#verification-banner")
        assert banner.is_visible()
        assert "proposed quotes" in banner.inner_text()
        assert "2" in page.locator("#inspect-audit").inner_text(), (
            "The real ET-003 correction should be present in the saved replay"
        )
        stage(page,"THE PROBLEM",
              "Muse proposed supported labels. Can the original CV actually establish each requirement?",7)
        banner.click()
        page.locator("#audit-drawer").wait_for(state="visible")
        page.locator("#audit-drawer").scroll_into_view_if_needed()
        stage(page,"THE PROOF",
              "Two real ET-003 status corrections. Original Muse labels and source checks remain inspectable.",12)
        screenshots.append("01-verified-audit.png")
        page.screenshot(path=str(OUT/screenshots[-1]),full_page=False)

        page.locator(".source-snap").first.click()
        page.locator("#pdf-evidence-viewer").wait_for(state="visible")
        page.locator("#pdf-page-img").wait_for(state="visible")
        page.wait_for_function("""() => {
          const t=document.getElementById('pdf-geometry-badge')?.textContent||'';
          return t.includes('Source located')||t.includes('Verified page')
        }""",timeout=25000)
        stage(page,"EVIDENCE, NOT A BLACK BOX",
              "The verified passage is located on the original fictional CV page.",12)
        screenshots.append("02-pdf-source.png")
        page.screenshot(path=str(OUT/screenshots[-1]),full_page=False)

        page.locator('#list [data-id="ET-015"]').click()
        pairs=page.locator(".conflict-pair")
        assert pairs.count()>0
        pairs.first.scroll_into_view_if_needed()
        assert "Claim A" in pairs.first.inner_text()
        assert "Claim B" in pairs.first.inner_text()
        stage(page,"WHEN TWO CLAIMS DISAGREE",
              "Two source-checked CV statements are shown side by side; EvidenceTrail does not choose which is true.",12)
        screenshots.append("03-two-sided-conflict.png")
        page.screenshot(path=str(OUT/screenshots[-1]),full_page=False)

        page.locator('#list [data-id="ET-005"]').click()
        page.locator("#generate-followup").click()
        q=page.locator("#followup-question")
        assert q.input_value().strip()
        q.scroll_into_view_if_needed()
        stage(page,"THE RECRUITER LOOP",
              "A job-specific clarification is drafted locally. No automatic rejection or message is sent.",9)
        page.locator("#candidate-reply").fill(
            "FICTIONAL DEMO REPLY: I prepared the supplier comparisons; the director negotiated and signed the terms."
        )
        page.locator("#followup-status").select_option("resolved")
        page.locator("#save-followup").click()
        assert "self-attested" in page.locator(".reply-attestation").inner_text().lower()
        page.locator(".reply-attestation").scroll_into_view_if_needed()
        stage(page,"RESOLUTION WITHOUT FALSE VERIFICATION",
              "A fictional pasted reply is marked SELF-ATTESTED, not verified. The original source status is unchanged.",12)
        screenshots.append("04-self-attested-reply.png")
        page.screenshot(path=str(OUT/screenshots[-1]),full_page=False)
        with page.expect_download(timeout=18000) as item:
            page.locator("#export-report").click()
        doc=item.value
        doc.save_as(OUT/"ET-005-fictional-evidence-pack.html")
        text=(OUT/"ET-005-fictional-evidence-pack.html").read_text()
        assert "Candidate reply — self-attested" in text
        assert "FICTIONAL DEMO REPLY" in text
        stage(page,"HUMAN REVIEW, AUDITABLE EXPORT",
              "Muse proposes. EvidenceTrail verifies the document. Recruiters decide. A complete report is exported.",11)
        screenshots.append("05-handoff.png")
        page.screenshot(path=str(OUT/screenshots[-1]),full_page=False)
        if errors:
            raise AssertionError("Browser errors: "+str(errors[:6]))
        if analysis_requests:
            raise AssertionError("This recording must not invoke new Muse requests")
        saved=page.video
        context.close()
        saved.save_as(str(OUT/"judge-walkthrough-raw.webm"))
        browser.close()

    if shutil.which("ffmpeg"):
        subprocess.run([
            "ffmpeg","-hide_banner","-loglevel","error","-y",
            "-i",str(OUT/"judge-walkthrough-raw.webm"),
            "-an","-c:v","libx264","-preset","medium","-crf","23",
            "-pix_fmt","yuv420p","-movflags","+faststart",
            str(OUT/"judge-walkthrough-silent.mp4"),
        ],check=True,timeout=120)
    else:
        raise RuntimeError("ffmpeg is required for the judge MP4 asset")
    meta={
        "kind":"silent captioned draft video, NOT the submitted final narration",
        "public_demo_url":BASE+"/demo20",
        "recorded_release_sha":EXPECTED,
        "candidate_fictional":True,
        "meta_model_calls_during_capture":0,
        "genuine_meta_recording":"historical saved 20 CV Muse replay",
        "story_cases":["ET-003","ET-015","ET-005"],
        "screenshots":screenshots,
        "mp4":"judge-walkthrough-silent.mp4",
        "source_original_unchanged":True,
        "voiceover_recorded":False,
        "external_candidacy_outreach_sent":False,
        "limitations":[
            "Do not describe saved model responses as live inference",
            "Self-attested reply is fictional and not externally verified",
            "This artifact does not prove recruiter time savings",
            "Recording narration and final organizer upload are still pending",
        ],
    }
    (OUT/"video-provenance.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))


if __name__=="__main__":
    main()
