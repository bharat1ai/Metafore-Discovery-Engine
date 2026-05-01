# Metafore Discovery Engine — Demo Script

**URL:** http://localhost:8083
**Demo documents:**
- SOP (extraction + audit check): `discovery-engine/sample_docs/commercial_banking_loan_sop.docx`
- Audit (audit check): `discovery-engine/sample_docs/loan_audit_report.docx`

**Total time:** ~12–15 minutes

---

## Positioning — say this in your head before the demo

Discovery Engine is the **wedge** into Metafore's broader Enterprise General Intelligence platform. The story is *"first step is understanding the enterprise — done at low cost, from your existing documents — before you commit to any platform build."* That's slide 8 of the corporate deck. Don't oversell the demo as the whole platform; sell it as the on-ramp.

---

## Opening line (30 seconds)

> *"Before you can build, automate, or evolve an enterprise application, you have to understand the organisation. Today, that takes consultants months and tools like Celonis cost half a million in integration before you see a single insight. The Discovery Engine reads your documents and gives you a living knowledge graph in minutes. Let me show you on a real banking SOP."*

---

## Step 1 — Upload the Banking SOP & Knowledge Graph (2 min)

1. Open http://localhost:8083 — you land on the Knowledge Graph tab
2. Click **Choose Files** in the upload zone → select `commercial_banking_loan_sop.docx`
3. Click **Extract Knowledge Graph**
4. While it loads (~30–40s), narrate:
   > *"This is a Loan Origination SOP — the kind of document that sits in a SharePoint and never gets read. The Discovery Engine is extracting every process, role, system, policy, and data entity from it automatically. This is the first AI moment — it's actually reading."*
5. When the graph renders, point out:
   - **Teal circles** = Processes (KYC Verification, Credit Check, Underwriting Review)
   - **Orange circles** = Roles (Loan Officer, Credit Analyst, Credit Officer)
   - **Blue circles** = Systems (KYC Platform, Credit Bureau Gateway, Core Banking)
   - **Red circles** = Policies (AML Policy, DTI threshold, sanctioning timeline)
   > *"Every circle is an entity. Every line is a relationship. This is the bank's lending process — extracted in under a minute."*
6. Click any node → show the **source-text quote** in the inspector on the right
   > *"Click any node, and the inspector shows you exactly where it came from in the original document. Nothing hallucinated, everything traceable."*

---

## Step 2 — Gap Analysis (1 min)

1. Click the **Gap Analysis** nav button (sidebar)
2. Click **Analyse Graph** — runs in milliseconds (no AI call)
3. Narrate:
   > *"This is a structural audit of the graph. Does every process have an owner? Is every policy enforced? Are there orphans? It runs instantly — no Claude call, just rules."*
4. Point to the **coverage score** and the breakdown
   > *"The score tells us how complete the SOP itself is. Anything below 70 means the document has real gaps — processes without assigned roles, policies floating in space."*
5. Click any failing check → click **View in Graph**
   > *"View in Graph jumps you to the affected nodes. The graph becomes a heatmap of where the SOP is weak."*

---

## Step 3 — Generate Blueprint (45 sec)

1. Back in Gap Analysis, click **Generate Blueprint**
2. Wait ~7s (Haiku)
3. Narrate:
   > *"The Blueprint turns the gaps into an actionable improvement plan — what to fix, what to add, what documents to upload next. This is the output you hand to the process owner."*

---

## Step 4 — Process Mining (the headline) (3 min)

1. Click **Workflows** in the sidebar — you land on Process Mining (full screen, graph hidden)
2. **Live-data caveat — say this clearly:**
   > *"Quick context — what you're about to see uses operational event-log data. For this demo we've pre-seeded a representative loan-origination dataset (13 cases) so you can see the mining surface live. In production this is wired from your event logs in days, not the six months Celonis takes."*
3. Narrate the KPI strip:
   > *"13 cases mined, 7 activities, 8 days median TAT, 9% SLA breach rate, 46% conformance fitness. Every number is real, derived from the operational data you can see in the variants tab."*
4. **Process Map tab** — point to the bottleneck:
   > *"KYC Verification is flagged as the bottleneck — 2 SLA breaches across the runs. Edge thickness shows case volume; red edges are SLA-breaching transitions; amber dashed edges are rework loops."*
5. Click the bottleneck node — inspector populates on the right:
   > *"The right pane gives the per-execution wait-time chart, top causes, breach counts. This is what an analyst would dig into."*
6. **Variants tab** — click a variant card:
   > *"Seven distinct execution paths through this process. Variant 1 is the happy path. Some are deviations — Sunita Iyer's case actually skipped Underwriting Review entirely. We caught it from the data, not the SOP."*
7. **Execution Conformance tab**:
   > *"This is conformance against operational reality — not against an audit document. Fitness 0.46 means 6 of 13 cases conform. The deviation patterns are listed by severity — skipped Underwriting (critical), wrong-role Credit Check (high), SLA-breached KYC (medium)."*
8. **Filter cases** — click the Filter Cases button → check `Commercial` only → Apply:
   > *"You can slice by loan type. Commercial-only — 5 cases, fitness jumps to 60%. Retail loans are where most deviations live."*
   Click Clear to reset.
9. **Optimise** — click the Optimise button → modal opens:
   > *"And here's the Haiku call. Given the bottleneck and the deviation patterns, the AI proposes specific re-routing rules and SLA targets — auto-route low-risk KYC, enforce mandatory Underwriting gates. Each suggestion has effort and impact estimates."*

---

## Step 5 — Audit Check (was Conformance) (2 min)

1. Click **Audit Check** in the sidebar (was "Conformance" — renamed for clarity)
2. Narrate:
   > *"Process Mining compared the SOP to your **operational data**. Audit Check compares the SOP to an **audit document** — a different question, answered by Claude reading prose."*
3. Click **Choose File** → select `loan_audit_report.docx`
4. Click **Run Audit Check →**
5. Wait ~30–40s (Sonnet — second AI moment, narrate while it runs):
   > *"This is a Q3 2024 audit report from the same bank. Claude is reading every node in the SOP graph and asking: did the audit confirm this happened? deviate? not mention it?"*
6. When results appear:
   > *"30% audit match. Three nodes confirmed, six deviated, one no-evidence. The audit found that AML screening was performed AFTER credit pull — a critical sequencing breach the SOP forbids."*
7. Click a red **deviated** card → click **View in Graph**:
   > *"Every deviation links to the specific node and quotes the exact evidence from the audit. The graph becomes a colour-coded audit dashboard."*
8. Toggle **All / Deviated / Confirmed** overlays:
   > *"Different views for different audiences. Compliance team sees deviated. Process owner sees confirmed."*

---

## Step 6 — Object Model (1 min)

1. Click **Object Model** in the sidebar — full-screen, Entity Diagram tab default
2. Narrate while it loads (Sonnet, ~30s):
   > *"The Object Model is the bridge from understanding to building. The same knowledge graph, expressed as a BRD-compliant entity model — Pydantic, JSON Schema, ERD. This is what the Application Language Model consumes upstream."*
3. Point to the diagram — entities laid out by FK depth (customer → loan_application → credit_assessment / sanction)
   > *"Layered by foreign-key depth. Brand-teal arrows are relationships. Click Pydantic or JSON Schema for the generated code."*
4. Click **Regenerate** — busts the cache, re-runs Sonnet:
   > *"Regenerate forces a fresh run if the graph has changed."*

---

## Step 7 — Dashboard — the bird's-eye view (1 min)

1. Click **Dashboard** in the sidebar — full-screen
2. Narrate:
   > *"This is the operational health of the discovery, in one view. Health score, four KPI tiles, top hotspots from Process Mining, top deviating cases by name, graph composition, live ops, completeness checklist."*
3. Click the **Bottleneck** tile or a **Top Hotspot** row:
   > *"Every tile and row drills through to the source tab. The dashboard isn't a report — it's the hub."*

---

## Step 8 — Pulse (45 sec)

1. Click the **bell icon** at the bottom of the sidebar
2. Drawer slides in
3. Narrate:
   > *"Pulse surfaces what needs attention now. Critical / Warning / Info filter at the top. Each card has the issue, source, and two actions — View in Graph or Dismiss."*
4. Click **View in Graph** on a critical item:
   > *"Closes the drawer, jumps to the graph, highlights the affected nodes, banners the source. The agent's recommendation lands at the exact spot it applies."*

---

## Step 9 — Generate Executive Report (1 min)

1. Click **Generate Report** in the header
2. Opens a new tab with the printable HTML report
3. Narrate:
   > *"Cover page, Executive Summary with health score, Top Issues, Process Mining findings, Audit Check results, Object Model summary, AI Optimisation Suggestions. Self-contained HTML — they can save to PDF from the browser print dialog. No new AI calls — it's composed from what we already produced."*
4. Show the print preview (`Ctrl+P`):
   > *"Each major section starts on its own page. The Metafore wordmark is on the cover. Ready for the boardroom."*

---

## Closing line

> *"Twelve minutes. From a Word document to a knowledge graph, an operational process model with named deviations, an audit comparison, a generated data model, and a printable executive report. Today this is reading documents. Tomorrow — once you wire your event logs and systems of record — it's the same engine, the same graph, the same insights, but now living and self-evolving. That's the Metafore Discovery Engine. Slide 8 of our deck. The wedge into the EGI platform."*

---

## Tips & risks

- **Live-data question is the #1 risk.** If asked *"can it read our SAP/Salesforce live?"* — answer: *"Today's demo is document-driven. Connecting to live systems is a connector job — days, not the months Celonis takes. We've pre-seeded operational data here to show you what mining looks like once that's wired."* Don't dodge the question; pre-empt it.
- If a Sonnet call (graph extraction, audit check, object model) is slow, narrate the fact that it's actively reading. The wait is the proof.
- If a Claude call fails mid-demo, skip — Gap Analysis, Process Mining, Pulse, and Dashboard all work without LLM calls.
- Reset between demos via the Reset button — clears all state cleanly.
- Banking SOP + audit doc were designed so the audit finds **named** deviations (Sunita skipped Underwriting, James wrong-role on approval, BlueRiver's wrong-role Credit Check). Let those names land.

---

## Quick reference — what each feature shows

| Feature | Surface | AI call | Wait | Talking point |
|---|---|---|---|---|
| Graph extraction | Knowledge Graph tab | Sonnet | ~30–40s | "First AI moment — it's reading" |
| Gap analysis | Gap Analysis tab | None | Instant | "Structural audit — no AI needed" |
| Blueprint | Gap Analysis tab | Haiku | ~7s | "Actionable improvement plan" |
| Process Mining (Map / Variants / Execution Conformance) | Workflows tab | None (pure SQL) | Instant | "Celonis-class mining at $0" |
| Optimise | Workflows tab → Optimise modal | Haiku | ~6s | "AI re-routing suggestions" |
| Audit Check | Audit Check tab | Sonnet | ~30–40s | "Claude reads the audit doc" |
| Object Model | Object Model tab | Sonnet | ~30s | "Bridge to the ALM" |
| Pulse | Bell-icon drawer | None / Haiku (Strategic Insights) | Instant | "Action queue, not a report" |
| Dashboard | Dashboard tab | None | Instant | "Bird's-eye hub" |
| Executive Report | Header → Generate Report | None | Instant | "Print-ready PDF" |

---

## What's NOT in this demo (and how to handle it)

| Question | Honest answer |
|---|---|
| *"Can you read our SAP / Salesforce live?"* | "Document-driven today; connector layer is week-2 work in deployment." |
| *"What about telco / healthcare / insurance?"* | "Banking is the loaded vertical for this demo. Adding a vertical is a seed-data + ontology pack — days." |
| *"Does it learn from our corrections?"* | "HITL feedback loop is on the platform roadmap — slide 9 of our deck. Discovery today is read-only." |
| *"How does this integrate with code?"* | "It doesn't — that's the point. Discovery produces a graph; the Application Language Model consumes it. No code repository." |
