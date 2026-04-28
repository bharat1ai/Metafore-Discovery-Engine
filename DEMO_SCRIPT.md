# Metafore Discovery Engine — Demo Script

**URL:** http://localhost:8083
**Demo documents:**
- Extraction: `discovery-engine/sample_docs/commercial_banking_loan_sop.docx`
- Conformance: `discovery-engine/sample_docs/loan_audit_report.docx`

**Total time:** ~12–15 minutes

---

## Opening line (30 seconds)

> *"Before you can build or evolve an enterprise application, you need to understand the organisation. The Discovery Engine is how Metafore does that — it reads your existing documents and turns them into a living knowledge graph. Let me show you."*

---

## Step 1 — Upload the Banking SOP (2 min)

1. Open http://localhost:8083
2. Click **Choose Files** → select `commercial_banking_loan_sop.txt`
3. Click **Extract Graph**
4. While it loads (~40s), narrate:
   > *"We're uploading a Loan Origination SOP — the kind of document that sits in a SharePoint and never gets read. The Discovery Engine is extracting every process, role, system, and policy from it automatically."*
5. When the graph renders, say:
   > *"What you're seeing is the institutional knowledge of this bank's lending process — extracted in under a minute. Every circle is an entity. Every line is a relationship."*

**Point out on the graph:**
- **Teal circles** = Processes (AML screening, credit bureau pull, sanctioning)
- **Orange circles** = Roles (Loan Processing Officer, Credit Analyst, Credit Committee)
- **Blue circles** = Systems (LoanIQ, Compliance Tracker, Document Management System)
- **Red circles** = Policies (AML Policy, Sanctioning Timeline Policy, DTI Certification Policy)

> *"Click any node to see where it came from in the original document."*

Click a node → show the **source text quote** in the detail panel on the right.

---

## Step 2 — Gap Analysis (1 min)

1. Click the **Gap Analysis** tab (bar chart icon in sidebar)
2. Results appear instantly — no AI call needed
3. Narrate:
   > *"This is a structural audit of the knowledge graph. It checks: does every process have an owner? Is every policy enforced? Are there orphaned nodes? This runs in milliseconds — no Claude call."*
4. Point to the **coverage score** (e.g. 44/Needs Work)
   > *"The score tells us how complete this process model is. A 44 means there are real gaps — processes without assigned roles, policies not linked to any process."*
5. Click a failing check → click **View in Graph**
   > *"The graph highlights exactly which nodes are the problem. No hunting through the document."*

---

## Step 3 — Blueprint (1 min)

1. Still in Gap Analysis, click **Generate Blueprint**
2. Wait ~7 seconds (fast Haiku model)
3. Narrate:
   > *"The Blueprint turns the gap analysis into an actionable improvement plan. This is the output you'd hand to a process owner or a consulting team."*
4. Read out one of the next steps
   > *"It even recommends which documents to upload next to fill the gaps — feeding the Knowledge Fabric."*

---

## Step 4 — Pulse Recommendations (1 min)

1. Click the **bell icon** in the top-right header
2. The drawer slides in showing NOW / THIS_WEEK / BACKLOG items
3. Narrate:
   > *"Pulse is how the Discovery Engine surfaces what needs attention — prioritised by urgency. NOW means act today. It's not a report, it's a recommended action queue."*
4. Click **View in Graph** on a critical item
   > *"Clicking View in Graph jumps you directly to the affected nodes — so whoever is responsible can see exactly what's missing."*

---

## Step 5 — Natural Language Query (1 min)

1. Click the **search icon** (NLQ tab) in sidebar
2. Type: `Who is responsible for AML screening and what system do they use?`
3. Wait ~5 seconds (fast Haiku model)
4. Narrate:
   > *"You can now interrogate this organisation's processes in plain English. No SQL, no dashboard config — just a question."*
5. Point to the **highlighted nodes** in the graph
   > *"The answer references specific nodes from the graph — it's grounded, not hallucinated."*
6. Click one of the **follow-up questions** it suggests

---

## Step 6 — Workflow Generation (2 min)

1. Click **Generate Workflows** button in the header
2. Wait ~2 minutes (complex Sonnet call)
3. While loading, narrate:
   > *"The workflow generator takes the knowledge graph and asks: where could automation add value? It produces AS-IS versus TO-BE comparisons — what the process looks like today versus what it could look like with automation."*
4. When cards appear, expand one (e.g. **AML & Compliance Pre-Screening Automation**)
5. Narrate:
   > *"Each workflow shows the current steps, who does them, what system they use, and the SLA status — breach, warning, or OK. Then the TO-BE view shows which steps get automated and what the improvement looks like."*
6. Hover over a step with a role → watch the **node highlight** in the graph
   > *"Hovering a step highlights the actual node in the knowledge graph. Everything stays connected to the source."*

---

## Step 7 — Conformance Checker (3 min)

1. Click the **shield icon** in sidebar (Conformance tab)
2. Narrate:
   > *"This is where the Discovery Engine moves from understanding to auditing. We have the SOP as our source of truth — the knowledge graph. Now we upload an audit report and ask: did reality match the process?"*
3. The main document (SOP) is already shown at the top
4. Under **Evidence Document**, click **Choose File** → select `loan_audit_report.txt`
5. Click **Analyse Conformance**
6. Wait ~35 seconds
7. When results appear, narrate:
   > *"The Q3 2024 audit report has been assessed against every node in the knowledge graph. Green is confirmed — the audit says this was followed. Red is deviated — a specific breach was found."*
8. Point to the **conformance rate** (~47%)
   > *"47% conformance. More than half the process wasn't followed correctly. The Discovery Engine found that automatically — it didn't need a human to read both documents and cross-reference them."*
9. Click **Show All Overlays** → show the colour-coded graph
   > *"Now the knowledge graph becomes an audit dashboard. You can see at a glance where the organisation is compliant and where it isn't."*
10. Click a **red deviation card** → click **View in Graph**
    > *"Every deviation links to a specific node and quotes the exact evidence from the audit report."*

---

## Step 8 — Object Model (1 min, optional)

1. Click **Generate Object Model** button (top of upload panel)
2. Wait ~40s
3. Narrate:
   > *"The object model is the bridge from understanding to building. The Discovery Engine takes the knowledge graph and generates the data schema — Pydantic models and JSON Schema — that an application built on this process would need. This is an early signal of what the ALM will produce."*

---

## Closing line

> *"In 12 minutes we went from a PDF document to a knowledge graph, a gap analysis, a conformance audit, automation workflows, and a data model. That's the Discovery Engine — understanding your organisation before building anything. It's the foundation everything else in Metafore sits on."*

---

## Tips

- If a Claude call fails or takes too long, skip to the next feature — gap analysis and pulse work instantly with no API calls
- The graph looks more impressive if you zoom in on dense clusters — use scroll wheel
- The banking documents were designed so the conformance audit finds real, named deviations — let the red deviation cards do the talking
- Reset between demos using the **Reset** button — it clears all state cleanly

---

## Quick Reference — What Each Feature Shows

| Feature | Key message | AI call? | Wait time |
|---------|------------|---------|-----------|
| Graph extraction | Turns documents into structured knowledge | Yes — Sonnet | ~40s |
| Gap analysis | Structural audit — no AI needed | No | Instant |
| Blueprint | Actionable improvement plan | Yes — Haiku | ~7s |
| Pulse | Prioritised action queue | No (rule-based) | Instant |
| NLQ | Plain English queries, grounded answers | Yes — Haiku | ~5s |
| Workflow generation | AS-IS vs TO-BE automation roadmap | Yes — Sonnet | ~2 min |
| Conformance checker | Audit report vs SOP — automated gap finding | Yes — Sonnet | ~35s |
| Object model | Schema for applications built on this domain | Yes — Sonnet | ~40s |
