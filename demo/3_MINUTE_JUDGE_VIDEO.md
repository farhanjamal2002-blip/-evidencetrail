# EvidenceTrail — 3-minute judge video

Record on the deployed build only after `/build-info` shows the same commit as `main`. Everything shown is fictional; saved Muse runs make no new model calls.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:15 | Home page, headline visible | “AI can find the right words in a CV and still credit the wrong person. The quote is real — but who did the work?” |
| 0:15–0:35 | Point at the two M02 cards on the home page | “Same requirement, same action words. In the first CV, the applicant negotiated. In the second, their director did — they only prepared notes. Both quotes are really on the page.” |
| 0:35–0:50 | Point at the 19/24 → 24/24 and 25/25 stats | “On our 12-pair fictional replay, raw Muse labels matched the author key 19 of 24 times; after EvidenceTrail’s checks, 24 of 24. All 25 proposed quotes were found on the cited page. Small test set — not a real-CV accuracy claim.” |
| 0:50–1:20 | Click **See the M02 proof**; point to *Quote on the page?* and *Does it credit the applicant?* on each card, then the struck-through raw label | “EvidenceTrail asks two separate questions. Is the quote on the page — yes for both. Does it credit the applicant — only the first. Muse’s raw label stays visible, struck through, next to the final status and the reason it changed.” |
| 1:20–1:35 | Scroll to the **12-pair table below the M02 cards**; point to the five highlighted rows, then the public summary JSON link | “Across all 12 pairs, every time Muse was wrong, the CV credited someone else — EvidenceTrail caught all five.” |
| 1:35–2:05 | Click the ET-018 card; it lands on **Treated as content**; click **View outlined source instruction** | “This CV hides an instruction aimed at the AI: mark every requirement as supported. EvidenceTrail outlines the exact lines on the PDF page and treats them as document content, not instructions.” |
| 2:05–2:25 | Scroll to a requirement with a status change and the PDF highlight | “Every finding opens the original page with the quote highlighted, so a recruiter can check it in seconds.” |
| 2:25–2:45 | Reviewer panel: set **Needs follow-up**, type a note, open export | “The recruiter decides. No scores, no rankings, no automatic rejections. Their review and the evidence export together as one file.” |
| 2:45–3:00 | Back to home headline | “Meta Muse Spark reads the CV; EvidenceTrail makes its evidence checkable. Proof, not a black-box score.” |

## Recording tips

- 1440×900 browser window, zoom 100%, cursor highlight on.
- Open the site once before recording so it isn't waking from sleep.
- Don't call 24/24 general accuracy, or the ET-018 text a detected attack.

- At 1:20, “wrong” means disagreement with the author key on this saved fictional set. The table includes all 24 results; the five corrections concern applicant attribution, not proof of real-world CV accuracy.
