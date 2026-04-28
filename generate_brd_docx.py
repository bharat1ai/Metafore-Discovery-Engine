"""Generate a professional DOCX version of the Discovery Engine BRD."""
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
GREY       = RGBColor(0x6B, 0x72, 0x80)
AMBER      = RGBColor(0xD9, 0x77, 0x06)
GREEN      = RGBColor(0x16, 0xA3, 0x4A)
RED        = RGBColor(0xDC, 0x26, 0x26)
GOLD       = RGBColor(0xB4, 0x5A, 0x00)


# ── Helpers ───────────────────────────────────────────────────────────

def set_cell_bg(cell, rgb):
    hex_color = format(rgb[0], '02X') + format(rgb[1], '02X') + format(rgb[2], '02X') \
        if isinstance(rgb, tuple) else str(rgb)
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


def section_heading(doc, number, title):
    """Numbered section heading with teal top border."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(4)
    add_run(p, f"{number}  ", bold=True, size=13, color=BRAND)
    add_run(p, title.upper(), bold=True, size=11, color=BRAND_DARK)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    top  = OxmlElement('w:top')
    top.set(qn('w:val'),   'single')
    top.set(qn('w:sz'),    '6')
    top.set(qn('w:space'), '4')
    top.set(qn('w:color'), '036868')
    pBdr.append(top)
    pPr.append(pBdr)


def sub_heading(doc, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(2)
    add_run(p, title, bold=True, size=10, color=BRAND_DARK)


def body_text(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(4)
    for run in p.runs:
        run.font.size = Pt(9.5)
        run.font.color.rgb = TEXT_DARK


def bullet(doc, text, indent=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Inches(0.3 + indent * 0.2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.font.size = Pt(9)
    run.font.color.rgb = TEXT_DARK


def add_table(doc, headers, rows, col_widths=None, alt_rows=True):
    """Generic branded table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    for c, h in enumerate(headers):
        set_cell_bg(table.rows[0].cells[c], BRAND)
        cell_para(table.rows[0].cells[c], h, bold=True, color=WHITE, size=9)
    for i, row in enumerate(rows):
        bg = TEAL_LIGHT if (alt_rows and i % 2 == 0) else WHITE
        for c, val in enumerate(row):
            set_cell_bg(table.rows[i + 1].cells[c], bg)
            cell_para(table.rows[i + 1].cells[c], str(val), size=9)
    if col_widths:
        for r in table.rows:
            for c, w in enumerate(col_widths):
                r.cells[c].width = Inches(w)
    doc.add_paragraph()
    return table


def add_note_box(doc, text, color=TEAL_LIGHT, border_color='036868'):
    tbl  = doc.add_table(rows=1, cols=1)
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, color)
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left = OxmlElement('w:left')
    left.set(qn('w:val'),   'single')
    left.set(qn('w:sz'),    '12')
    left.set(qn('w:space'), '0')
    left.set(qn('w:color'), border_color)
    tcBorders.append(left)
    tcPr.append(tcBorders)
    p = cell.paragraphs[0]
    p.clear()
    run = p.add_run(text)
    run.font.size = Pt(9)
    run.font.color.rgb = BRAND_DARK
    doc.add_paragraph()


# ══════════════════════════════════════════════════════════════════════
# SECTIONS
# ══════════════════════════════════════════════════════════════════════

def add_cover(doc):
    tbl  = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, BRAND_DARK)

    p1 = cell.paragraphs[0]; p1.clear(); p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p1.add_run("METAFORE WORKS")
    r.font.color.rgb = TEAL_MID; r.font.size = Pt(9); r.font.bold = True

    p2 = cell.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Discovery Engine")
    r2.font.color.rgb = WHITE; r2.font.size = Pt(24); r2.font.bold = True

    p3 = cell.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Business Requirements Document")
    r3.font.color.rgb = TEAL_MID; r3.font.size = Pt(13)

    p4 = cell.add_paragraph(); p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = p4.add_run("Version 1.0   |   April 2026   |   CONFIDENTIAL")
    r4.font.color.rgb = TEAL_MID; r4.font.size = Pt(8.5)

    doc.add_paragraph()


def add_meta_table(doc):
    rows = [
        ("Document Title",  "Metafore Works Discovery Engine — Business Requirements Document"),
        ("Version",         "1.0"),
        ("Date",            "April 2026"),
        ("Status",          "Active"),
        ("Author",          "Metafore Works"),
        ("Classification",  "Confidential"),
    ]
    add_table(doc, ["Field", "Detail"], rows, col_widths=[1.5, 5.0])


def add_s1_summary(doc):
    section_heading(doc, "1", "Executive Summary")
    body_text(doc,
        "The Metafore Works Discovery Engine is an AI-powered document intelligence platform "
        "that transforms unstructured business documents — SOPs, policies, audit reports — into "
        "structured knowledge graphs. It enables organisations to visualise process flows, identify "
        "compliance gaps, generate domain object models, and assess conformance against operating "
        "standards, all through a browser-based interface with no installation required beyond Python."
    )
    add_note_box(doc,
        "The Discovery Engine is the foundational layer of the Metafore Works platform. "
        "It is designed to be the first step before any application build — understanding "
        "the organisation before designing for it."
    )


def add_s2_context(doc):
    section_heading(doc, "2", "Business Context and Problem Statement")
    body_text(doc,
        "Organisations accumulate large volumes of operational documentation containing rich process "
        "and governance knowledge locked in unstructured text. Extracting, relating, and acting on "
        "this knowledge currently requires significant manual analyst effort."
    )
    add_table(doc,
        ["Problem", "Impact"],
        [
            ("Process knowledge buried in long-form documents",      "Analysts spend days manually mapping workflows"),
            ("Gap analysis done manually and inconsistently",        "Critical compliance gaps are missed or under-reported"),
            ("Object models created from scratch each time",         "Data model rework delays system design phases"),
            ("No automated conformance checking against SOPs",       "Audit findings remain disconnected from source procedures"),
        ],
        col_widths=[3.0, 3.5]
    )


def add_s3_objectives(doc):
    section_heading(doc, "3", "Objectives")
    objectives = [
        "Extract a structured knowledge graph from any uploaded business document in under 60 seconds.",
        "Surface workflow AS-IS and TO-BE suggestions from extracted graph data.",
        "Automatically generate a BRD §4-compliant domain object model (Pydantic + JSON Schema).",
        "Calculate gap analysis and provide actionable remediation blueprints.",
        "Score conformance between evidence documents and the source process graph.",
        "Provide natural language querying over the knowledge graph.",
    ]
    for i, obj in enumerate(objectives, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        add_run(p, f"{i}.  ", bold=True, size=9.5, color=BRAND)
        add_run(p, obj, size=9.5, color=TEXT_DARK)


def add_s4_stakeholders(doc):
    section_heading(doc, "4", "Stakeholders")
    add_table(doc,
        ["Role", "Interest"],
        [
            ("Product Owner — Metafore Works",  "Feature prioritisation and roadmap"),
            ("Business Analyst",                "Gap analysis, conformance, object model output"),
            ("Data Architect",                  "BRD §4 object model export and ERD review"),
            ("Process Owner",                   "Workflow suggestions and pulse recommendations"),
            ("IT / Infrastructure",             "Deployment and API key management"),
        ],
        col_widths=[2.5, 4.0]
    )


def add_s5_scope(doc):
    section_heading(doc, "5", "Scope")
    sub_heading(doc, "5.1  In Scope")
    in_scope = [
        "Document upload: PDF, DOCX, TXT",
        "AI-driven knowledge graph extraction (nodes and edges)",
        "Interactive graph visualisation via vis-network",
        "Workflow generation (AS-IS and TO-BE)",
        "Gap analysis with remediation blueprint",
        "Pulse health recommendations",
        "Conformance checking with evidence document",
        "Object model generation: Pydantic v2, JSON Schema, ERD",
        "Natural language querying over the graph",
        "Single-user, local deployment on Windows",
    ]
    for item in in_scope:
        bullet(doc, item)
    doc.add_paragraph()

    sub_heading(doc, "5.2  Out of Scope")
    out_scope = [
        "Multi-user or multi-tenant access",
        "Persistent database storage (all data is in-memory, reset on server restart)",
        "Authentication or authorisation",
        "Real-time collaboration",
        "Mobile application",
        "Neo4j integration (available but disabled by default)",
    ]
    for item in out_scope:
        bullet(doc, item)
    doc.add_paragraph()


def add_s6_functional(doc):
    section_heading(doc, "6", "Functional Requirements")

    def fr_table(sub, title, rows):
        sub_heading(doc, f"{sub}  {title}")
        add_table(doc, ["ID", "Requirement"], rows, col_widths=[0.7, 5.8])

    fr_table("6.1", "Document Upload and Graph Extraction", [
        ("FR-01", "System shall accept PDF, DOCX, and TXT documents"),
        ("FR-02", "System shall extract 15–20 nodes and 15–20 edges per document using Claude Sonnet"),
        ("FR-03", "Nodes shall be classified as: Process, Role, System, Policy, DataEntity, Event"),
        ("FR-04", "Extracted graph shall be rendered as an interactive force-directed network"),
        ("FR-05", "Each upload shall produce an independent graph with a unique graph_id (UUID)"),
        ("FR-06", "Document text stored in memory shall be capped at 15,000 characters"),
    ])
    fr_table("6.2", "Workflow Generation", [
        ("FR-07", "System shall generate AS-IS and TO-BE workflows from the knowledge graph"),
        ("FR-08", "Each workflow shall include ordered steps with responsible roles and linked systems"),
        ("FR-09", "Hovering a workflow step shall highlight the corresponding node in the graph"),
        ("FR-10", "Workflows shall be cached per graph_id and not regenerated on repeated navigation"),
    ])
    fr_table("6.3", "Gap Analysis", [
        ("FR-11", "System shall identify gaps: missing roles, policies, and systems in the process graph"),
        ("FR-12", "Each gap item shall have a severity: Critical / High / Medium / Low"),
        ("FR-13", "View in Graph shall highlight affected nodes on the knowledge graph"),
        ("FR-14", "System shall generate a remediation blueprint using Claude Haiku"),
    ])
    fr_table("6.4", "Pulse Recommendations", [
        ("FR-15", "System shall calculate rule-based health metrics from the knowledge graph"),
        ("FR-16", "System shall generate AI recommendations (up to 5) using Claude Haiku"),
        ("FR-17", "Pulse panel shall be accessible via a slide-in drawer from the sidebar"),
    ])
    fr_table("6.5", "Conformance Checking", [
        ("FR-18", "User shall upload a secondary evidence document (audit report, review log)"),
        ("FR-19", "System shall score each eligible node as: Confirmed / Deviated / Not Found"),
        ("FR-20", "System shall display a conformance percentage and evidence quotes"),
        ("FR-21", "Overlay modes shall allow filtering to confirmed, deviated, or all nodes"),
        ("FR-22", "Event and Objective nodes shall be excluded from conformance assessment"),
    ])
    fr_table("6.6", "Object Model Generation", [
        ("FR-23", "System shall generate a domain object model using BRD Authoring Standard §4"),
        ("FR-24", "Output shall include: Pydantic v2 Python code, JSON Schema, and an ERD"),
        ("FR-25", "Object model shall be cached per graph_id and not regenerated on repeated navigation"),
        ("FR-26", "System shall show a loading spinner while the model is being generated"),
        ("FR-27", "If no graph has been extracted, system shall show an empty-state prompt"),
    ])
    fr_table("6.7", "Natural Language Querying", [
        ("FR-28", "User shall be able to type a plain-English question about the graph"),
        ("FR-29", "System shall return a direct answer plus highlighted relevant nodes"),
        ("FR-30", "Query history shall be maintained per graph_id for the session"),
    ])


def add_s7_nfr(doc):
    section_heading(doc, "7", "Non-Functional Requirements")
    add_table(doc,
        ["ID", "Category", "Requirement"],
        [
            ("NFR-01", "Performance",    "Graph extraction shall complete within 60 seconds for documents up to 20,000 characters"),
            ("NFR-02", "Performance",    "Natural language queries shall respond within 10 seconds"),
            ("NFR-03", "Usability",      "All features shall be accessible from a single-page browser UI with no page reloads"),
            ("NFR-04", "Reliability",    "Server shall auto-restart on code changes during development (uvicorn --reload)"),
            ("NFR-05", "Security",       "API key shall be stored in a local .env file and never committed to version control"),
            ("NFR-06", "Compatibility",  "Frontend shall work in Microsoft Edge without CDN dependency"),
            ("NFR-07", "Portability",    "Application shall run on any Windows machine with Python 3.11+ via double-click START.bat"),
            ("NFR-08", "Data isolation", "All session data is in-memory; restart clears all state"),
        ],
        col_widths=[0.7, 1.3, 4.5]
    )


def add_s8_object_model(doc):
    section_heading(doc, "8", "Object Model Standard — BRD Authoring Standard §4")
    body_text(doc,
        "All domain object models generated by the Discovery Engine must conform to the following rules. "
        "These rules apply to both the Pydantic code output and the JSON Schema output."
    )

    sub_heading(doc, "8.1  Field Naming")
    add_table(doc,
        ["Rule", "Specification"],
        [
            ("Case",    "snake_case only — no spaces, no camelCase"),
            ("Length",  "Maximum 63 characters per field name"),
            ("FK naming", "<parent_table>_id format — e.g. customer_id, account_id"),
        ],
        col_widths=[1.5, 5.0]
    )

    sub_heading(doc, "8.2  Mandatory Fields — Every Entity")
    body_text(doc, "Every entity must include these fields in this order:")
    add_table(doc,
        ["Position", "Field", "Type", "Constraint"],
        [
            ("1st", "id",         "UUID",     "Primary Key"),
            ("2nd", "created_at", "datetime", "Not Null — audit trail"),
        ],
        col_widths=[0.8, 1.5, 1.5, 2.7]
    )

    sub_heading(doc, "8.3  Audit Fields — Every Entity")
    body_text(doc, "Every entity must include these audit-only fields. They carry no FK constraint and must not appear in ERD relationship lines.")
    add_table(doc,
        ["Field", "Type", "Description"],
        [
            ("created_by",       "UUID", "AUDIT ONLY – no relationship"),
            ("last_changed_by",  "UUID", "AUDIT ONLY – no relationship"),
        ],
        col_widths=[2.0, 1.5, 3.0]
    )

    sub_heading(doc, "8.4  Enum Values")
    body_text(doc, "All enum values must be UPPERCASE: OPEN, IN_PROGRESS, APPROVED, REJECTED, CLOSED. Never lowercase.")

    sub_heading(doc, "8.5  Relationship Declaration Format")
    body_text(doc, "Relationships must use this exact string format:")
    add_note_box(doc, "entity_a (parent) → entity_b (child) via entity_b.fk_column = entity_a.id\n\n"
                      "Example: Customer (parent) → LoanApplication (child) via loan_application.customer_id = customer.id")

    sub_heading(doc, "8.6  JSON Schema Requirements")
    body_text(doc, 'The JSON Schema output must include an "entities" array (each with name and fields) '
                   'and a "relationships" array using the arrow format above.')


def add_s9_architecture(doc):
    section_heading(doc, "9", "System Architecture")

    sub_heading(doc, "9.1  Tech Stack")
    add_table(doc,
        ["Layer", "Technology", "Notes"],
        [
            ("AI",                "Anthropic Claude Sonnet 4.6 + Haiku 4.5",  "Tool-use API — structured output guaranteed"),
            ("Backend",           "Python 3.11 · FastAPI 0.115 · Uvicorn 0.32", "Port 8083, launched via --app-dir"),
            ("Document parsing",  "PyMuPDF (PDF) · python-docx (DOCX)",         "Built-in for TXT"),
            ("Graph DB",          "Neo4j 5",                                     "Optional — disabled by default"),
            ("Frontend",          "Vanilla JS · vis-network 9.1.9",              "Self-hosted; no build step required"),
            ("Fonts",             "GT America · IBM Plex Mono · Inter",           "Self-hosted OTF/TTF"),
        ],
        col_widths=[1.5, 2.5, 2.5]
    )

    sub_heading(doc, "9.2  API Endpoints")
    add_table(doc,
        ["Endpoint", "Method", "Feature"],
        [
            ("/api/upload",                     "POST", "Document upload and graph extraction"),
            ("/api/workflows/generate",          "POST", "Workflow generation"),
            ("/api/workflows/{id}",              "GET",  "Retrieve cached workflows"),
            ("/api/generate-object-model",       "POST", "Object model generation"),
            ("/api/query/natural-language",      "POST", "Natural language query"),
            ("/api/query/history/{id}",          "GET",  "NLQ history"),
            ("/api/gap-analysis/calculate",      "POST", "Gap analysis"),
            ("/api/gap-analysis/blueprint",      "POST", "Remediation blueprint"),
            ("/api/pulse/calculate",             "POST", "Pulse health metrics"),
            ("/api/pulse/ai-recommendations",    "POST", "AI pulse recommendations"),
            ("/conformance/upload",              "POST", "Evidence document upload"),
            ("/conformance/analyse",             "POST", "Conformance analysis"),
            ("/conformance/{id}/latest",         "GET",  "Latest conformance result"),
        ],
        col_widths=[2.8, 0.7, 3.0]
    )

    sub_heading(doc, "9.3  AI Model Routing")
    add_table(doc,
        ["Feature", "Model", "Max Tokens", "Reason"],
        [
            ("Graph extraction",         "Claude Sonnet 4.6", "8,096",  "Highest accuracy required"),
            ("Workflow generation",       "Claude Sonnet 4.6", "16,000", "Complex nested schema"),
            ("Object model",             "Claude Sonnet 4.6", "4,096",  "Code generation quality"),
            ("Conformance analysis",     "Claude Sonnet 4.6", "6,000",  "Precise evidence matching"),
            ("Natural language query",   "Claude Haiku 4.5",  "800",    "Simple Q&A"),
            ("Blueprint",                "Claude Haiku 4.5",  "800",    "Short summary"),
            ("Pulse AI recommendations", "Claude Haiku 4.5",  "2,048",  "Structured list"),
        ],
        col_widths=[2.2, 1.8, 1.0, 1.5]
    )


def add_s10_data_model(doc):
    section_heading(doc, "10", "Data Model")

    sub_heading(doc, "10.1  In-Memory Stores")
    body_text(doc, "All stores are keyed by graph_id (UUID) and reset on server restart. There is no persistent storage.")
    add_table(doc,
        ["Store", "Key", "Value"],
        [
            ("_graph_store",         "graph_id",    "Nodes, edges, graph_id"),
            ("_doc_store",           "graph_id",    "Combined document text (max 15,000 chars)"),
            ("_workflow_store",      "graph_id",    "Workflows list"),
            ("_object_model_store",  "graph_id",    "Object model result"),
            ("_query_history",       "graph_id",    "NLQ history entries"),
            ("_gap_store",           "graph_id",    "Gap analysis result"),
            ("_blueprint_store",     "graph_id",    "Blueprint result"),
            ("_pulse_store",         "graph_id",    "Pulse items"),
            ("_pulse_ai_store",      "graph_id",    "AI recommendations"),
            ("_evidence_store",      "evidence_id", "Evidence document"),
            ("_conformance_store",   "evidence_id", "Conformance result"),
            ("_conformance_latest",  "graph_id",    "Latest evidence_id"),
        ],
        col_widths=[2.2, 1.3, 3.0]
    )

    sub_heading(doc, "10.2  Node Types")
    add_table(doc,
        ["Type", "Colour", "Represents"],
        [
            ("Process",    "Teal",   "Business processes and activities"),
            ("Role",       "Orange", "People, teams, job functions"),
            ("System",     "Blue",   "Applications, platforms, databases"),
            ("Policy",     "Red",    "Rules, regulations, compliance requirements"),
            ("DataEntity", "Purple", "Data objects, records, documents"),
            ("Event",      "Yellow", "Triggers, milestones, notifications"),
        ],
        col_widths=[1.3, 1.2, 4.0]
    )


def add_s11_ui(doc):
    section_heading(doc, "11", "User Interface Requirements")
    add_table(doc,
        ["ID", "Requirement"],
        [
            ("UI-01", "Navigation via a 200px labeled sidebar with five items: Graph, Workflows, Gap Analysis, Conformance, Object Model"),
            ("UI-02", "Left panel width varies per view: Graph 35%, Workflows 60%, Gap 50%, Conformance 50%, Object Model 55%"),
            ("UI-03", "Right graph canvas shall always be visible regardless of the active left panel"),
            ("UI-04", "Sidebar top shows Metafore Works logo and text; header shows DISCOVERY ENGINE only"),
            ("UI-05", "Colour palette follows the Metafore Works design system (primary #036868)"),
            ("UI-06", "All node types in the graph shall use circle shapes only — no mixed shapes"),
            ("UI-07", "Object model panel shall show a loading spinner during API calls and empty-state when no graph is loaded"),
        ],
        col_widths=[0.7, 5.8]
    )


def add_s12_samples(doc):
    section_heading(doc, "12", "Sample Demo Documents")
    add_table(doc,
        ["Document", "Purpose", "Expected Output"],
        [
            ("commercial_banking_loan_sop.docx", "Source SOP for extraction",       "~25 nodes: 8 processes, 6 roles, 4 systems, 3+ policies"),
            ("loan_audit_report.docx",           "Evidence for conformance check",  "~47% conformance: 9 confirmed, 10 deviated, 2 not found"),
        ],
        col_widths=[2.2, 1.8, 2.5]
    )
    body_text(doc,
        "Key conformance deviations surfaced by the audit report: AML check sequencing (Critical), "
        "property appraisal before completeness check, sanctioning timeline breach, "
        "DTI calculation assigned to incorrect role."
    )


def add_s13_constraints(doc):
    section_heading(doc, "13", "Constraints and Assumptions")
    add_table(doc,
        ["Type", "Detail"],
        [
            ("Constraint", "Requires a valid Anthropic API key with sufficient credits"),
            ("Constraint", "Windows only — batch scripts use .bat syntax"),
            ("Constraint", "Python 3.11+ must be installed with PATH configured"),
            ("Constraint", "All data is session-scoped; no persistence between server restarts"),
            ("Assumption", "Single user at a time — no concurrent session isolation"),
            ("Assumption", "Documents are in English"),
            ("Assumption", "Network access is available for initial pip install"),
        ],
        col_widths=[1.3, 5.2]
    )


def add_s14_glossary(doc):
    section_heading(doc, "14", "Glossary")
    add_table(doc,
        ["Term", "Definition"],
        [
            ("BRD",          "Business Requirements Document"),
            ("ERD",          "Entity Relationship Diagram"),
            ("SOP",          "Standard Operating Procedure"),
            ("NLQ",          "Natural Language Query"),
            ("graph_id",     "UUID assigned to each extracted knowledge graph"),
            ("evidence_id",  "UUID assigned to each uploaded conformance evidence document"),
            ("Pulse",        "Health score and recommendations derived from the knowledge graph"),
            ("Blueprint",    "AI-generated remediation plan for identified gaps"),
            ("Conformance",  "Assessment of how closely an evidence document matches the source process graph"),
            ("AS-IS",        "Current state of a business process as documented"),
            ("TO-BE",        "Target future state of a process with recommended improvements"),
        ],
        col_widths=[1.5, 5.0]
    )


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
    add_meta_table(doc)
    add_s1_summary(doc)
    add_s2_context(doc)
    add_s3_objectives(doc)
    add_s4_stakeholders(doc)
    add_s5_scope(doc)
    add_s6_functional(doc)
    add_s7_nfr(doc)
    add_s8_object_model(doc)
    add_s9_architecture(doc)
    add_s10_data_model(doc)
    add_s11_ui(doc)
    add_s12_samples(doc)
    add_s13_constraints(doc)
    add_s14_glossary(doc)

    path = OUT / "BRD_Discovery_Engine.docx"
    doc.save(path)
    print(f"Saved: {path}")


if __name__ == "__main__":
    build()
