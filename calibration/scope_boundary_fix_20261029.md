# Scope-boundary fix and live check — 2026-10-29

## Failure addressed

In the saved five-CV Muse batch, the career-switcher CV was labeled Direct for
supplier negotiations even though the CV said: “I did not own supplier
negotiations or contract sign-off.” The page and quote verifier had correctly
confirmed the cited text, but that alone could not catch the semantic overclaim.

## Change

The local review layer now checks for a narrow class of explicit first-person
responsibility limits. If a finding is Direct, the requirement asks for that
same action, and the verified supporting passages do not document the action,
the final label becomes Related and ambiguous. The result preserves the
original proposed label, anchors the limiting statement to its CV page, adds a
neutral follow-up question, and recolors the evidence highlight to match the
Related label. Documented participation remains Direct when only final approval
or sign-off is denied. The evaluator scores Muse's proposed label separately
from the final label and records when the scope gate changed it.

## Evidence

- Four regression tests cover the saved failure shape, the full one-pass
  verification path, documented negotiation participation, and an unrelated
  scope limit.
- An offline replay of the saved five-CV result preserved the old Muse output
  and applied the new rule locally. With the timeline gate already applied,
  expected-label matches moved from **7/10 to 8/10**; one C3 Direct finding was
  routed to Related. This is a derived replay, not a new Muse run.
- A separate live run on the fictional C3 CV used **one Muse Spark 1.3 request**
  at medium reasoning effort and made no retry. Both requirements returned as
  Related, all **4/4** proposed quotes matched their source pages, and the
  request completed in **25.156 seconds**. The local scope override did not
  need to fire in that live result. This single CV is not a broad accuracy
  claim.

## Latency finding

Muse took **25.058 seconds** of the live request. PDF extraction took 9 ms,
local quote checks 3 ms, and page-preview rendering took 24 ms; the full local
pipeline outside the model call was roughly 73 ms. The wait is still in model
generation; no local-stage optimization would materially reduce this request.
The existing five-CV client runs analyses concurrently and displays completed
candidates as they arrive. The lower-reasoning setting was faster in earlier
runs but had weaker label results, so this change does not switch the default
away from medium.

## Validation

- 110 Python tests passed.
- 9 frontend Node tests passed.
- `app.py` compilation, JavaScript syntax, and `git diff --check` passed.

Live request details and the offline replay are saved separately in
`scope_boundary_live_c3_20261029.json` and
`scope_boundary_gate_replay_20261029.json`.
