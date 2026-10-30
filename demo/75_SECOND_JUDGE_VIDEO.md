# EvidenceTrail — 75-second judge demo (draft cut)

**Record against the reviewed branch only after the browser smoke passes and the public `/build-info` SHA matches the build being recorded.** All documents and applicants are fictional. The M02 and 20-applicant views use saved Muse responses; they make no new model calls.

| Time | What to show | Narration |
|---|---|---|
| 0:00–0:08 | Recruiter inbox and one job requirement | “A quote can be real and still credit the wrong person. EvidenceTrail makes the source check and the applicant-attribution check visible separately.” |
| 0:08–0:20 | Open **Replay benchmark** and show the two M02 cards | “These are two fictional passages with the same requirement and action. In the second, the director negotiated; the applicant only prepared comparison notes.” |
| 0:20–0:38 | Point to **Quote on the page?** and **Does it credit the applicant?** on both cards; then raw-to-final labels and reasons | “Both quotations are verified on the source page. Only the first credits the applicant. Muse’s raw `conflicting` label remains visible while the pipeline records `not_found` for applicant support.” |
| 0:38–0:48 | Show M02 audit link and replay statistics/caveat | “The saved receipts are inspectable. The 25/25 citation result is for the full 12-pair fictional replay—not an M02 score or real-CV accuracy estimate.” |
| 0:48–1:04 | Click the dark ET-018 next card; open ET-018 and choose **View outlined source instruction** | “This instruction-like text is part of the supplied CV. The source page outlines both exact lines and labels them ‘Treated as content.’ EvidenceTrail does not follow them.” |
| 1:04–1:15 | Show reviewer panel and saved-replay badge | “The reviewer’s state and note sit apart from the evidence labels. The badge marks this as a saved replay, with no new Muse call.” |

## Capture checklist

- Keep the M02 caveat and full-replay denominator legible.
- Do not call 24/24 general accuracy or 25/25 an M02-specific result.
- Do not describe the saved replay as live inference or the ET-018 instruction as a detected attack.
- Keep the final capture on the same SHA shown by the public `/build-info`; the branch changes are not deployed yet.
