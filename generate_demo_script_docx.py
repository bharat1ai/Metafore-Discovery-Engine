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
        title="Upload the Banking SOP",
        duration="≈ 2 min",
        actions=[
            "Open http://localhost:8083",
            "Click Choose Files → select commercial_banking_loan_sop.docx",
            "Click Extract Graph",
            "While loading (~40s) — narrate (see right →)",
            "When graph renders — narrate (see right →)",
            "Click any node → show source text quote in detail panel",
        ],
        narrations=[
            (3, "We're uploading a Loan Origination SOP — the kind of document that sits in a SharePoint and never gets read. "
                "The Discovery Engine is extracting every process, role, system, and policy from it automatically."),
            (4, "What you're seeing is the institutional knowledge of this bank's lending process — extracted in under a minute. "
                "Every circle is an entity. Every line is a relationship."),
            (5, "Click any node to see where it came from in the original document."),
        ],
        callouts=[
            ("Teal circles",   "Processes — AML screening, credit bureau pull, sanctioning"),
            ("Orange circles", "Roles — Loan Processing Officer, Credit Analyst, Credit Committee"),
            ("Blue circles",   "Systems — LoanIQ, Compliance Tracker, Document Management System"),
            ("Red circles",    "Policies — AML Policy, Sanctioning Timeline Policy, DTI Certification Policy"),
        ],
    )

    add_step_card(doc,
        step_num=2,
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
        step_num=3,
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
        step_num=4,
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
        step_num=5,
        title="Natural Language Query",
        duration="≈ 1 min",
        actions=[
            "Click the search icon (NLQ tab) in sidebar",
            "Type: Who is responsible for AML screening and what system do they use?",
            "Wait ~5 seconds (Haiku model)",
            "Point to highlighted nodes in the graph",
            "Click one of the follow-up questions it suggests",
        ],
        narrations=[
            (2, "You can now interrogate this organisation's processes in plain English. "
                "No SQL, no dashboard config — just a question."),
            (3, "The answer references specific nodes from the graph — it's grounded, not hallucinated."),
        ],
    )

    add_step_card(doc,
        step_num=6,
        title="Workflow Generation",
        duration="≈ 2 min",
        actions=[
            "Click Generate Workflows button in the header",
            "Wait ~2 minutes (Sonnet model) — narrate while loading",
            "When cards appear, expand one (e.g. AML & Compliance Pre-Screening Automation)",
            "Hover over a step with a role → watch node highlight in the graph",
        ],
        narrations=[
            (1, "The workflow generator takes the knowledge graph and asks: where could automation add value? "
                "It produces AS-IS versus TO-BE comparisons — what the process looks like today "
                "versus what it could look like with automation."),
            (2, "Each workflow shows the current steps, who does them, what system they use, and the SLA status — "
                "breach, warning, or OK. The TO-BE view shows which steps get automated and the improvement."),
            (3, "Hovering a step highlights the actual node in the knowledge graph. "
                "Everything stays connected to the source."),
        ],
        tips=["Second click on same file returns workflows instantly (cached)"],
    )

    add_step_card(doc,
        step_num=7,
        title="Conformance Checker",
        duration="≈ 3 min",
        actions=[
            "Click the shield icon in sidebar (Conformance tab)",
            "Main document (SOP) already shown at the top",
            "Under Evidence Document — click Choose File → select loan_audit_report.docx",
            "Click Analyse Conformance",
            "Wait ~35 seconds",
            "Point to conformance rate (~47%)",
            "Click Show All Overlays → colour-coded graph visible",
            "Click a red deviation card → click View in Graph",
        ],
        narrations=[
            (0, "This is where the Discovery Engine moves from understanding to auditing. "
                "We have the SOP as our source of truth — the knowledge graph. "
                "Now we upload an audit report and ask: did reality match the process?"),
            (5, "47% conformance. More than half the process wasn't followed correctly. "
                "The Discovery Engine found that automatically — it didn't need a human "
                "to read both documents and cross-reference them."),
            (6, "Now the knowledge graph becomes an audit dashboard. "
                "You can see at a glance where the organisation is compliant and where it isn't."),
            (7, "Every deviation links to a specific node and quotes the exact evidence from the audit report."),
        ],
    )

    add_step_card(doc,
        step_num=8,
        title="Object Model  (optional)",
        duration="≈ 1 min",
        actions=[
            "Click Generate Object Model button (top of upload panel)",
            "Wait ~40s",
            "Show Pydantic tab, JSON Schema tab, then Entity Diagram tab",
        ],
        narrations=[
            (1, "The object model is the bridge from understanding to building. The Discovery Engine "
                "generates the data schema — Pydantic models, JSON Schema, and a visual entity diagram — "
                "that an application built on this process would need. This is an early signal of what the ALM will produce."),
        ],
    )

    # Closing
    section_heading(doc, "Closing Line")
    doc.add_paragraph()
    add_quote_box(doc,
        "In 12 minutes we went from a Word document to a knowledge graph, a gap analysis, "
        "a conformance audit, automation workflows, and a data model. That's the Discovery Engine — "
        "understanding your organisation before building anything. "
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
