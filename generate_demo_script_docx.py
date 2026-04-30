"""Generate a professional DOCX version of the Demo Script."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = Path(__file__).parent

BRAND      = RGBColor(0x03, 0x68, 0x68)
BRAND_DARK = RGBColor(0x02, 0x4F, 0x4F)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
TEAL_LIGHT = RGBColor(0xE6, 0xF4, 0xF4)
TEAL_MID   = RGBColor(0xA7, 0xD4, 0xD4)
TEXT_DARK  = RGBColor(0x1F, 0x2D, 0x2D)
TEXT_MID   = RGBColor(0x4A, 0x68, 0x68)
QUOTE_BG   = RGBColor(0xF0, 0xFA, 0xFA)
STEP_BG    = RGBColor(0xF7, 0xFC, 0xFC)
AMBER      = RGBColor(0xD9, 0x77, 0x06)
GREEN      = RGBColor(0x16, 0xA3, 0x4A)
GREY       = RGBColor(0x6B, 0x72, 0x80)


def set_cell_bg(cell, rgb):
    hex_color = str(rgb) if not isinstance(rgb, str) else rgb
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)


def cell_para(cell, text, bold=False, size=9, color=None,
              align=WD_ALIGN_PARAGRAPH.LEFT, italic=False):
    cell.paragraphs[0].clear()
    run = cell.paragraphs[0].add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    cell.paragraphs[0].alignment = align
    return cell.paragraphs[0]


def add_run(para, text, bold=False, italic=False, size=None, color=None):
    run = para.add_run(text)
    run.bold   = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return run


# ── Cover / header banner ─────────────────────────────────────────────

def add_cover(doc):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_bg(cell, BRAND_DARK)

    p1 = cell.paragraphs[0]
    p1.clear()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p1.add_run("METAFORE")
    r.font.color.rgb = TEAL_MID
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.letter_spacing = Pt(2)  # may not render in all viewers

    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Discovery Engine")
    r2.font.color.rgb = WHITE
    r2.font.size = Pt(22)
    r2.font.bold = True

    p3 = cell.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Demo Script")
    r3.font.color.rgb = TEAL_MID
    r3.font.size = Pt(13)
    r3.font.bold = False

    p4 = cell.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = p4.add_run("Approx. 12 – 15 minutes   |   http://localhost:8083")
    r4.font.color.rgb = TEAL_MID
    r4.font.size = Pt(8.5)

    doc.add_paragraph()  # spacer


# ── Quick-info box at the top ─────────────────────────────────────────

def add_info_box(doc):
    table = doc.add_table(rows=3, cols=2)
    table.style = 'Table Grid'
    rows_data = [
        ("URL",               "http://localhost:8083"),
        ("SOP Document",      "sample_docs/commercial_banking_loan_sop.docx"),
        ("Audit Document",    "sample_docs/loan_audit_report.docx"),
    ]
    for i, (lbl, val) in enumerate(rows_data):
        set_cell_bg(table.rows[i].cells[0], TEAL_LIGHT)
        cell_para(table.rows[i].cells[0], lbl, bold=True, size=9, color=BRAND_DARK)
        cell_para(table.rows[i].cells[1], val, size=9)
    doc.add_paragraph()


# ── Section heading ───────────────────────────────────────────────────

def section_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(8)
    run.font.color.rgb = BRAND
    # top border via paragraph XML
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    top = OxmlElement('w:top')
    top.set(qn('w:val'),   'single')
    top.set(qn('w:sz'),    '4')
    top.set(qn('w:space'), '4')
    top.set(qn('w:color'), str(BRAND))
    pBdr.append(top)
    pPr.append(pBdr)
    return p


# ── Opening quote box ─────────────────────────────────────────────────

def add_quote_box(doc, text):
    table = doc.add_table(rows=1, cols=1)
    cell = table.cell(0, 0)
    set_cell_bg(cell, QUOTE_BG)
    # left border accent via tcBorders
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left = OxmlElement('w:left')
    left.set(qn('w:val'),   'single')
    left.set(qn('w:sz'),    '12')
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), str(BRAND))
    tcBorders.append(left)
    tcPr.append(tcBorders)
    p = cell.paragraphs[0]
    p.clear()
    run = p.add_run(f'"{text}"')
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = BRAND_DARK
    doc.add_paragraph()


# ── Step card ─────────────────────────────────────────────────────────

def add_step_card(doc, step_num, title, duration, actions, narrations,
                  callouts=None, tips=None):
    """
    actions   : list of str (numbered action items)
    narrations: list of (after_action_idx, narration_text)  — 0-based index
    callouts  : optional list of (bullet_label, bullet_text) highlighted points
    tips      : optional list of str tip lines
    """
    # ── Header row ──
    header_table = doc.add_table(rows=1, cols=2)
    lc = header_table.cell(0, 0)
    rc = header_table.cell(0, 1)
    set_cell_bg(lc, BRAND)
    set_cell_bg(rc, BRAND)
    lc.width = Inches(4.5)
    rc.width = Inches(2.0)

    p_l = lc.paragraphs[0]
    p_l.clear()
    add_run(p_l, f"Step {step_num}  ", bold=True, size=10, color=WHITE)
    add_run(p_l, title, bold=False, size=10, color=TEAL_MID)

    p_r = rc.paragraphs[0]
    p_r.clear()
    p_r.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_run(p_r, duration, bold=False, size=9, color=TEAL_MID)

    # ── Body ──
    narr_map = {idx: text for idx, text in narrations}

    for i, action in enumerate(actions):
        # action row
        body_table = doc.add_table(rows=1, cols=2)
        body_table.style = 'Table Grid'
        nc = body_table.cell(0, 0)
        ac = body_table.cell(0, 1)
        set_cell_bg(nc, TEAL_LIGHT)
        set_cell_bg(ac, STEP_BG)
        nc.width = Inches(0.35)
        ac.width = Inches(6.15)
        cell_para(nc, str(i + 1), bold=True, size=9, color=BRAND,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
        cell_para(ac, action, size=9)

        # narration after this action?
        if i in narr_map:
            nq_table = doc.add_table(rows=1, cols=1)
            nc2 = nq_table.cell(0, 0)
            set_cell_bg(nc2, QUOTE_BG)
            _add_left_border(nc2, str(BRAND))
            p = nc2.paragraphs[0]
            p.clear()
            add_run(p, f'Say:  "{narr_map[i]}"', italic=True, size=9,
                    color=BRAND_DARK)

    # callouts
    if callouts:
        co_table = doc.add_table(rows=len(callouts), cols=2)
        co_table.style = 'Table Grid'
        for i, (lbl, txt) in enumerate(callouts):
            set_cell_bg(co_table.rows[i].cells[0], TEAL_LIGHT)
            set_cell_bg(co_table.rows[i].cells[1], STEP_BG)
            cell_para(co_table.rows[i].cells[0], lbl, bold=True, size=8.5,
                      color=BRAND_DARK)
            cell_para(co_table.rows[i].cells[1], txt, size=8.5)

    # tips
    if tips:
        tip_table = doc.add_table(rows=1, cols=1)
        tc2 = tip_table.cell(0, 0)
        set_cell_bg(tc2, RGBColor(0xFF, 0xFB, 0xEB))
        _add_left_border(tc2, str(AMBER))
        p = tc2.paragraphs[0]
        p.clear()
        add_run(p, "Tips:  ", bold=True, size=8.5, color=AMBER)
        add_run(p, "  |  ".join(tips), size=8.5, color=RGBColor(0x78, 0x35, 0x00))

    doc.add_paragraph()


def _add_left_border(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left = OxmlElement('w:left')
    left.set(qn('w:val'),   'single')
    left.set(qn('w:sz'),    '12')
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), hex_color)
    tcBorders.append(left)
    tcPr.append(tcBorders)


# ── Quick reference table ─────────────────────────────────────────────

def add_quick_ref(doc):
    section_heading(doc, "Quick Reference — What Each Feature Shows")
    doc.add_paragraph()

    rows = [
        ("Graph Extraction",   "Turns documents into structured knowledge",    "Yes — Sonnet", "~40s"),
        ("Gap Analysis",       "Structural audit — no AI needed",               "No",           "Instant"),
        ("Blueprint",          "Actionable improvement plan",                   "Yes — Haiku",  "~7s"),
        ("Pulse",              "Prioritised action queue",                      "No (rule-based)","Instant"),
        ("NLQ",                "Plain English queries, grounded answers",       "Yes — Haiku",  "~5s"),
        ("Workflow Generation","AS-IS vs TO-BE automation roadmap",             "Yes — Sonnet", "~2 min"),
        ("Conformance Checker","Audit report vs SOP — automated gap finding",   "Yes — Sonnet", "~35s"),
        ("Object Model",       "Schema for applications built on this domain",  "Yes — Sonnet", "~40s"),
    ]
    table = doc.add_table(rows=1 + len(rows), cols=4)
    table.style = 'Table Grid'
    headers = ("Feature", "Key Message", "AI Call?", "Wait Time")
    for c, h in enumerate(headers):
        set_cell_bg(table.rows[0].cells[c], BRAND)
        cell_para(table.rows[0].cells[c], h, bold=True, color=WHITE, size=9)

    for i, (feat, msg, ai, wait) in enumerate(rows):
        r = table.rows[i + 1]
        bg = TEAL_LIGHT if i % 2 == 0 else WHITE
        set_cell_bg(r.cells[0], bg)
        set_cell_bg(r.cells[1], bg)
        set_cell_bg(r.cells[2], bg)
        set_cell_bg(r.cells[3], bg)
        cell_para(r.cells[0], feat, bold=True, size=9, color=BRAND_DARK)
        cell_para(r.cells[1], msg,  size=9)
        ai_color = GREEN if ai.startswith("Yes") else GREY
        cell_para(r.cells[2], ai,   size=9, color=ai_color)
        cell_para(r.cells[3], wait, size=9)
    doc.add_paragraph()


# ══════════════════════════════════════════════════════════════════════
# BUILD
# ══════════════════════════════════════════════════════════════════════

def build():
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(9.5)
    for section in doc.sections:
        section.top_margin    = Cm(1.8)
        section.bottom_margin = Cm(1.8)
        section.left_margin   = Cm(2.2)
        section.right_margin  = Cm(2.2)

    add_cover(doc)
    add_info_box(doc)

    # Opening
    section_heading(doc, "Opening Line  (30 seconds)")
    doc.add_paragraph()
    add_quote_box(doc,
        "Before you can build or evolve an enterprise application, you need to understand "
        "the organisation. The Discovery Engine is how Metafore does that — it reads your "
        "existing documents and turns them into a living knowledge graph. Let me show you."
    )

    # ── Steps ──────────────────────────────────────────────────────────
    section_heading(doc, "Demo Steps")
    doc.add_paragraph()

    add_step_card(doc,
        step_num=1,
        title="Multi-Document Upload",
        duration="≈ 3 min",
        actions=[
            "Open http://localhost:8083",
            "Click Choose Files → select FOUR documents together: "
            "commercial_banking_loan_sop.docx, compliance_policy.docx, "
            "role_descriptions.docx, it_systems_register.docx",
            "Watch the file list build up; observe the green 'Combined size: ~13,000 chars' counter",
            "Click Extract Knowledge Graph",
            "While loading (~50s) — narrate (see right →)",
            "When the graph renders, look top-left of the graph area for: "
            "'Knowledge Graph — 4 documents' + 4 colored 📄 chips, plus a Cross-Document Insights panel",
            "Click each 📄 chip → graph filters to that document's nodes",
            "Click any node that came from 2+ documents → detail panel shows Sources: file1, file2",
        ],
        narrations=[
            (3, "Most enterprises don't have ONE document describing a process — they have an SOP, a separate compliance policy, "
                "a role description from HR, and an IT systems register. The Discovery Engine reads them all together "
                "and produces ONE unified graph that links the entities across documents."),
            (5, "Top-left: a chip per source document. The Cross-Document Insights panel below it is the most valuable thing here — "
                "the engine has compared the four documents and surfaced gaps you'd otherwise need a senior consultant to find. "
                "Read out one or two of the insights — they typically include compliance gaps, role inconsistencies, and orphan systems."),
            (6, "Click a chip and the graph filters to nodes from just that document. This is how you trace which document is the source of truth for any entity."),
            (7, "Sources field on a node tells you it appeared in multiple documents — that means HIGHER confidence. "
                "If something is in three out of four documents, you can trust it; if it's in one alone, you might want to verify."),
        ],
        callouts=[
            ("Teal circles",   "Processes — AML screening, credit bureau pull, sanctioning"),
            ("Orange circles", "Roles — Loan Processing Officer, Credit Analyst, Quality Assurance Officer"),
            ("Blue circles",   "Systems — LoanIQ (LOS), Compliance Tracker, Document Management Portal"),
            ("Red circles",    "Policies — AML Policy, Sanctioning Timeline Policy, Fair Lending"),
            ("📄 chips",       "One per uploaded document — colored, clickable, filter the graph"),
            ("Cross-Doc panel","3 cross-document findings — gap / inconsistency / missing / contradiction"),
        ],
    )

    add_step_card(doc,
        step_num=2,
        title="Dashboard — Health Score and Live Operational Data",
        duration="≈ 2 min",
        actions=[
            "Click the Dashboard nav (after Conformance in the sidebar)",
            "Point to the SVG ring at the top — Overall Health Score (weighted: Coverage 40% / SLA 35% / Conformance 25%)",
            "Walk through: 3 metric cards · Graph composition bar chart · Top issues · Live Operational Data section · Completeness checklist",
            "Click a metric card → it navigates to the source tab",
            "Click a 'Top issue' item → graph highlights the affected nodes and the relevant tab opens",
        ],
        narrations=[
            (1, "The Dashboard is the executive view. It aggregates everything the engine has discovered into one health score "
                "and a handful of cards. None of this is a new AI call — it all comes from data the engine has already produced."),
            (2, "The Live Operational Data section is critical. The engine ships with a local SQLite store of real banking-loan operations data — "
                "13 sample applications, 71 step executions across 7 process steps. We use that to ground every other feature in actual numbers, "
                "not just what the SOP says should happen."),
            (3, "Every issue, every quick win, every metric card is click-through — you can drill from this single screen into any feature."),
        ],
    )

    add_step_card(doc,
        step_num=4,
        title="Gap Analysis",
        duration="≈ 1 min",
        actions=[
            "Click the Gap Analysis tab (bar chart icon in sidebar)",
            "Results appear instantly — no AI call",
            "Point to coverage score — narrate",
            "Click a failing check → click View in Graph",
        ],
        narrations=[
            (1, "This is a structural audit of the knowledge graph. It checks: does every process have an owner? "
                "Is every policy enforced? Are there orphaned nodes? This runs in milliseconds — no Claude call."),
            (2, "The score tells us how complete this process model is. A low score means real gaps — "
                "processes without assigned roles, policies not linked to any process."),
            (3, "The graph highlights exactly which nodes are the problem. No hunting through the document."),
        ],
    )

    add_step_card(doc,
        step_num=5,
        title="Blueprint",
        duration="≈ 1 min",
        actions=[
            "Still in Gap Analysis — click Generate Blueprint",
            "Wait ~7 seconds (Haiku model)",
            "Read out one of the next steps",
        ],
        narrations=[
            (1, "The Blueprint turns the gap analysis into an actionable improvement plan. "
                "This is the output you'd hand to a process owner or a consulting team."),
            (2, "It even recommends which documents to upload next to fill the gaps — feeding the Knowledge Fabric."),
        ],
    )

    add_step_card(doc,
        step_num=6,
        title="Pulse Recommendations",
        duration="≈ 1 min",
        actions=[
            "Click the bell icon in the top-right header",
            "Drawer slides in — NOW / THIS_WEEK / BACKLOG items shown",
            "Click View in Graph on a critical item",
        ],
        narrations=[
            (1, "Pulse is how the Discovery Engine surfaces what needs attention — prioritised by urgency. "
                "NOW means act today. It's not a report, it's a recommended action queue."),
            (2, "Clicking View in Graph jumps you directly to the affected nodes — "
                "so whoever is responsible can see exactly what's missing."),
        ],
    )

    add_step_card(doc,
        step_num=7,
        title="Natural Language Query (with live operational context)",
        duration="≈ 1 min",
        actions=[
            "Click the search icon (NLQ tab) in sidebar",
            "Try a process question: 'Who is responsible for AML screening and what system do they use?'",
            "Wait ~5 seconds (Haiku model)",
            "Then try a reality question: 'Which steps have the most SLA breaches and who is performing them?'",
            "Point to the answer — it cites real numbers (e.g. KYC 15.4% breach, Underwriting 51.8h vs 48h SLA, role mismatches on Credit Check)",
            "Click one of the follow-up questions it suggests",
        ],
        narrations=[
            (2, "Plain-English questions about the organisation's processes — no SQL, no dashboard config."),
            (4, "The first question pulls from the SOP and graph. The second question is the trick — "
                "the engine doesn't just answer from documents, it grounds the response in live operational data "
                "from our SQLite store. So instead of saying 'KYC should be done by a Compliance Analyst', "
                "the answer can say 'KYC has a 15% breach rate across 13 applications and is sometimes done by a Loan Officer'."),
            (5, "The answer references specific graph nodes AND specific operational facts — it's grounded, not hallucinated."),
        ],
    )

    add_step_card(doc,
        step_num=8,
        title="Workflows — ROI, Automation Scoring, Process Variants, Actual vs SOP",
        duration="≈ 4 min",
        actions=[
            "Click Workflows nav → click Generate (Sonnet model, ~60–90s — narrate while loading)",
            "When cards appear, expand one (e.g. AML & Compliance Pre-Screening Automation)",
            "Walk down a single card top-to-bottom:",
            "  · AS-IS / TO-BE columns — point to a step's 'Actual' sub-block (avg duration / breach % / role mismatches from SQLite)",
            "  · Estimated annual value (teal headline) — read out the number",
            "  · Click 'Assumptions used' → show 4–7 banking-grade assumptions (loaded staff cost, NIM, FTE hours)",
            "  · Benefits strip (4 boxes)",
            "  · Automation Scoring table — point to the 0–10 colored bars and one row's suggested approach (Rule-based RPA / AI-assisted / Human required)",
            "  · Process Variants — point to Variant A frequency, then a non-A variant card",
            "  · Click any step chip in a variant → graph highlights that node",
            "  · Click anywhere on the variant card → all variant nodes highlight + banner",
            "  · Read out the Variant Summary card (standard path %, exception rate, biggest TAT driver)",
        ],
        narrations=[
            (1, "ONE Sonnet call returns four things at once for every workflow we propose: "
                "the AS-IS/TO-BE comparison, an annual ROI estimate, an automation score per step, "
                "and 2–4 process variants showing how the workflow actually executes across exception paths. "
                "Going from seven calls to one is what makes this tab usable."),
            (4, "The 'Actual' sub-block on each AS-IS step is overlaid from our SQLite operational data. "
                "What the SOP says SHOULD happen, vs what's actually happening across recent applications. "
                "If a step has a 15% breach rate, you see it RIGHT THERE in the workflow card — you don't have to switch screens."),
            (5, "ROI: an annual dollar figure with 4–7 banking-industry assumptions you can defend in a steering committee. "
                "Loaded staff cost, NIM, FTE hours, transaction volume — all stated explicitly. "
                "No black-box 'Claude said it's $2M.'"),
            (8, "Automation scoring: 0–10 per step. Green is rule-based RPA, amber is AI-assisted, red is human-required. "
                "The 'Avg score' and '% automatable' summary tell you whether this whole workflow is even a candidate for automation."),
            (9, "Process Variants is what process mining gets you — the standard happy path is rarely 100% of cases. "
                "Variant A is the happy path, then 2–4 exception paths (AML flag, threshold breach, manual override). "
                "The frequencies sum to 100. When the divergence point matches a known SQLite step, the variant gets a 'Live data' badge — "
                "we cross-check the AI estimate against actual breach rates."),
            (12, "Hovering and clicking step chips highlights the underlying graph node. "
                "Everything in this card is connected to the source graph — nothing is detached."),
        ],
        tips=[
            "Second click on the same upload returns workflows instantly (cached per document hash)",
            "If you only have a few minutes, demo Workflows AFTER Dashboard — the customer arrives at this card already understanding the bigger picture"
        ],
    )

    add_step_card(doc,
        step_num=9,
        title="Conformance Checker (file upload OR live operational data)",
        duration="≈ 3 min",
        actions=[
            "Click the shield icon in sidebar (Conformance tab)",
            "OPTION A — file upload (the classic flow):",
            "  · Click Choose File → select loan_audit_report.docx",
            "  · Click Run Conformance Check (~35 seconds)",
            "OPTION B — live operational data (the new flow):",
            "  · Below the drop zone, click 'Use live operational data instead'",
            "  · The engine builds a synthetic evidence document from the SQLite operational store and runs analysis",
            "Either way: point to conformance rate (~47% on the audit doc, similar on live data)",
            "Click Show All Overlays → colour-coded graph visible",
            "Click a red deviation card → graph highlight + evidence excerpt in detail panel",
        ],
        narrations=[
            (0, "Conformance is where the engine moves from understanding to auditing. "
                "We have the SOP as our source of truth. Now we ask: did reality match it?"),
            (1, "Two ways to feed in 'reality': drop in an audit report, or use the live operational data we already have in SQLite."),
            (5, "Both paths run through the SAME conformance pipeline — Sonnet checks every node against the evidence and tags it Confirmed, Deviated, or Not Found. "
                "The live-data path is the demo killer for stakeholders who don't have an audit report to upload."),
            (8, "47% conformance on the audit doc — more than half the process wasn't followed correctly. "
                "The engine found that automatically; no human had to read both documents and cross-reference."),
            (9, "Every deviation links to a specific node and quotes the exact evidence."),
        ],
    )

    add_step_card(doc,
        step_num=10,
        title="Object Model  (optional)",
        duration="≈ 1 min",
        actions=[
            "Click Object Model nav",
            "Wait ~40s for first generation (cached after that)",
            "Show Pydantic tab, JSON Schema tab, then Entity Diagram tab",
            "Click Copy on the Pydantic tab",
        ],
        narrations=[
            (1, "The object model is the bridge from understanding to building. The Discovery Engine "
                "generates the data schema — Pydantic models, JSON Schema, and a visual entity diagram — "
                "that an application built on this process would need. This is an early signal of what the ALM will produce."),
        ],
    )

    add_step_card(doc,
        step_num=11,
        title="Generate Executive Report  (the finale)",
        duration="≈ 1 min",
        actions=[
            "Click 'Generate Report' in the top-right of the header",
            "A new tab opens with a brand-styled HTML page",
            "Scroll the recipient through the sections quickly: hero, source documents, executive summary, top issues, "
            "cross-document insights, workflow opportunities (with a total annual ROI roll-up), gap analysis, conformance, live data",
            "Click the floating 'Save as PDF / Print' button (or Ctrl+P) → save",
        ],
        narrations=[
            (1, "Everything we've shown for the last fifteen minutes — the graph, the workflows, the ROI numbers, the cross-document gaps, "
                "the conformance rate, the operational data — gets bundled into a single executive report you can email to a CIO or steering committee."),
            (2, "No new AI calls were made to compose this report. It's pure aggregation of state we already produced. "
                "That's the discipline — every fact in this document already lives somewhere in the engine."),
            (3, "The report is print-styled — Ctrl+P saves it as a PDF. Customers walk out of the room with the engine's findings in their inbox before the demo's even over."),
        ],
        tips=[
            "If you only have one slide to leave behind, this PDF is it",
            "The button is disabled until a graph has been extracted — extract first"
        ],
    )

    # Closing
    section_heading(doc, "Closing Line")
    doc.add_paragraph()
    add_quote_box(doc,
        "In about fifteen minutes we went from four Word documents to a unified knowledge graph, "
        "a cross-document gap analysis, an executive dashboard, automation workflows with defensible ROI numbers, "
        "process variants validated against real operational data, a conformance audit, a data model, "
        "and a printable executive report — all from documents the customer already has. "
        "That's the Discovery Engine. Understand your organisation before building anything. "
        "It's the foundation everything else in Metafore sits on."
    )

    # Tips
    section_heading(doc, "Presenter Tips")
    doc.add_paragraph()
    tips_data = [
        ("If a Claude call fails",  "Skip to the next feature — Gap Analysis and Pulse work instantly with no API calls."),
        ("Graph zoom",              "The graph looks more impressive zoomed into dense clusters — use the scroll wheel."),
        ("Conformance deviations",  "The banking documents surface real named deviations — let the red cards do the talking."),
        ("Reset between demos",     "Click the Reset button — it clears all state cleanly in one click."),
        ("Workflow cache",          "Second upload of the same file returns workflows instantly — no wait time."),
    ]
    table = doc.add_table(rows=len(tips_data), cols=2)
    table.style = 'Table Grid'
    for i, (lbl, tip) in enumerate(tips_data):
        bg = TEAL_LIGHT if i % 2 == 0 else WHITE
        set_cell_bg(table.rows[i].cells[0], bg)
        set_cell_bg(table.rows[i].cells[1], bg)
        cell_para(table.rows[i].cells[0], lbl, bold=True, size=9, color=BRAND_DARK)
        cell_para(table.rows[i].cells[1], tip, size=9)
    doc.add_paragraph()

    # Quick ref
    add_quick_ref(doc)

    path = OUT / "DEMO_SCRIPT.docx"
    doc.save(path)
    print(f"Saved: {path}")


if __name__ == "__main__":
    build()
