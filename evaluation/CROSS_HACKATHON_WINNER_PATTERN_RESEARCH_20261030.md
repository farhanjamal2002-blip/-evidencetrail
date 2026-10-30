# Cross-hackathon winner patterns for EvidenceTrail
## Research note — 30 October 2026

### Purpose and limits

Study prior AI hackathon winners, especially Meta/Llama events, to identify transferable product and demo patterns for EvidenceTrail. These are retrospective descriptions published by organizers and project teams. They are selected examples, not controlled evidence that any one feature caused a win, and they do not predict this event's outcome.

### Primary-source cases

| Hackathon project | What the project actually demonstrated | Transferable pattern |
| --- | --- | --- |
| **OrgLens — 1st place, LlamaCon Hackathon 2025** | Connected GitHub tasks, repositories, issues, internal documents, and resumes into contributor profiles and expert search; offered questions against a contributor's work history. Meta reports a working web demo with GitHub and Llama API integrations. | Make the user's end goal visible: retrieve evidence from real sources, organize it into a useful representation, and let the user act on it. For EvidenceTrail, this means an evidence map that ties each requirement to exact CV spans and leaves the reviewer able to inspect the source. |
| **Compliance Wizards — 2nd place, LlamaCon 2025** | Analyzes transactions, alerts a user, supports acknowledgement/reporting through voice, and uses multimodal inputs plus news lookup for context. | Show a complete short workflow with a clear handoff, not a model response in isolation. EvidenceTrail can show analysis → source check → unresolved issue → recruiter clarification/export. |
| **Llama CCTV Operator — 3rd place, LlamaCon 2025** | Lets an operator describe video events in ordinary language and checks a video stream for those events without fine-tuning. | Demonstrate a capability that feels newly enabled by the model in one immediate interaction. EvidenceTrail's equivalent is surfacing that a genuine quote names a manager/director and does not establish the applicant's own responsibility. |
| **Geo-ML — Best Llama API Usage, LlamaCon 2025** | Processes long geological reports and maps, consolidates content into a domain-specific structured language, then feeds it to GemPy to produce a 3D geological model. | Use the model as the semantic transformation core, then let ordinary software validate and render a structured artifact. EvidenceTrail can transform a job criterion and CV into actor/action/scope claims linked to source spans, run deterministic source checks, and render a reviewable evidence pack. This is a particularly close architecture analogy. |
| **OpenGlass — 1st place, Meta Llama 3 Hackathon 2024** | Built low-cost smart glasses that identify what the wearer is looking at and provide contextual information. | Keep the value legible in seconds: show input, useful model interpretation, and output in one continuous demo. Avoid a long architecture tour before the audience sees the result. |
| **Deb8 — 2nd place, Meta Llama 3 Hackathon 2024** | Built a debate arena with multiple models and a separate evaluator. | Multi-model orchestration can be a compelling visible interaction, but “models debate” alone is not enough evidence of truth. EvidenceTrail should show a blind challenger identifying a concrete actor/scope error, then open the original page; do not present agreement as verification. |
| **CurePharma AI — 1st place, Meta Llama Hackathon India 2024** | Helps users interpret prescription information in regional languages through WhatsApp, with an access path suited to its target users. | Fit the solution to a real user's constraints and familiar workflow. EvidenceTrail's user should be able to follow a single requirement and source page without understanding the model pipeline. |
| **CivicFix — 2nd place, India Llama Hackathon 2024** | Accepts voice, photos, or text reports, classifies local problems, and routes useful summaries to authorities. | Intake is only useful when the output reaches a next action. EvidenceTrail should make “what needs human clarification?” obvious and provide the evidence needed to ask that question. |
| **Evalssment — 3rd place, India Llama Hackathon 2024** | Lets teachers set grading criteria and returns individualized feedback against those criteria. | Make the rubric explicit and preserve the connection between criterion and output. EvidenceTrail should keep the job requirement visible beside the exact CV passage and the model's bounded interpretation. |

### What these cases suggest for EvidenceTrail

1. **Lead with a concrete, consequential problem.** “A CV quote can be real but still fail to prove the applicant personally did the work” is more specific than “AI-powered recruiting.” Demonstrate it with a fictional CV where a director negotiated a contract and the applicant's role is distinct.
2. **Make the intelligence visible as a transformation.** Show the requirement decomposed into actor, action, scope, and time; show the source passages; then show what the pipeline can and cannot conclude. The model should be clearly doing semantic work, while local code checks quote/page anchoring.
3. **Give the audience one complete story.** One uploaded fictional CV and JD should travel through Muse analysis, deterministic quote/page verification, a targeted challenge or correction when justified, and a final inspectable report. Include a second case only if it adds a distinct failure mode (for example, contradictory dates).
4. **Show a visible next step.** End with an evidence-bounded finding and a recruiter clarification question when responsibility or scope remains unclear. Keep the reviewer in control; no ranking or auto-rejection.
5. **Use each Meta capability only where its role is obvious.** Spark interprets; Glimmer can independently challenge; Wonder is a rare escalation; Spark image input addresses a scan/layout failure; SAM locates a visual region when required. Do not spend demo time listing models or imply that using more models proves correctness.
6. **Make robustness part of the demo, not a slide of claims.** Show the source quote on its original page, a verified passage, and one concrete failure caught or unresolved. Present the stored replay as a replay, and distinguish it from a fresh live model run.
7. **Optimize demo reliability.** Have a deterministic prepared fixture and offline evidence pack ready; rehearse a no-network path. The main story should complete even if a live API is slow. Label any precomputed output honestly.

### Priority experiment and demo revision

**Experiment:** use the existing frozen fictional actor-swap pair as the flagship case. Prepare two matching one-page CVs: one says the director negotiated the contract; the other explicitly assigns negotiation to the applicant. Run the frozen pipeline on both and preserve raw Muse output, final pipeline output, source-check result, and provider receipts. Present them side by side so the audience sees whether the conclusion changes with the actor while the quote/page check stays correct.

**Why this is the right first showcase:** it communicates the product's core distinction in seconds, makes Muse's role substantive (interpreting who did what), makes deterministic verification independently visible, and supports a practical recruiter action. The existing 12-pair results are a small fictional replay, not a broad accuracy claim; this new demonstration should not be described as general performance evidence.

**Demo sequence (target ~90 seconds within the full video):**

- State the problem: “A true quote can still support the wrong conclusion about who did the work.”
- Show the requirement: “Personally negotiated a supplier contract.”
- Show CV page 1: “The director negotiated the supplier contract; I prepared the comparison table.”
- Show Muse's initial proposal and the source verifier's result separately. If the actual saved result does not expose the intended distinction, do not edit or stage it; select a predeclared successful fixture only after replay and preserve all results.
- Show the actor/scope challenge, then the original page and the bounded finding: director's negotiation is not evidence of applicant negotiation; comparison-table work may be related but does not prove negotiation.
- End with a recruiter clarification question tied to the missing responsibility detail.

### Application to hackathon judging

Meta's event page frames the indie track around creativity, technical ambition, and whether the project works; the startup track around technical execution and production readiness. It also asks builders to bring a problem they know firsthand or to push a technical frontier. EvidenceTrail should therefore make its concrete hiring-document workflow and the working source-verification loop the center of the entry. If presenting as a startup, emphasize reliability, repeatability, privacy boundaries, and stage-wise auditability. If presenting as an indie project, emphasize the novel distinction between citation existence and justified attribution, and show the complete interaction working.

### Sources

- Meta, “Meet the winners of our first-ever LlamaCon Hackathon” (2025): https://ai.meta.com/blog/llamacon-hackathon/
- Meta, “Event Recap: First-Ever Meta Llama 3 Hackathon” (2024): https://ai.meta.com/blog/llama-3-hackathon-recap-cerebral-valley/
- Meta, “Highlights from the first-ever Llama hackathon in India” (2024): https://ai.meta.com/blog/llama-hackathon-india/
- Meta, “Meta’s Llama Impact Hackathon: Pioneering AI Solutions for Public Good” (2024): https://about.fb.com/news/2024/11/metas-llama-impact-hackathon-pioneering-ai-solutions-for-public-good/
- OrgLens source repository: https://github.com/TheCl3m/llama-hack
- Geo-ML source repository: https://github.com/williamjsdavis/geo-lm
- Current Meta Global AI Developer Hackathon official page: https://dev.meta.ai/events/global-hackathon

**Conclusion:** the strongest borrowing is not “add more features.” It is to demonstrate a tight model-to-structured-evidence-to-action loop, with the Meta capability visibly essential and the source evidence still inspectable.
