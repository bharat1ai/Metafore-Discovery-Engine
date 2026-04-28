import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

import anthropic

_client = None

SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


# ── Tool schemas ────────────────────────────────────────────────────────────

GRAPH_TOOL = {
    "name": "extract_knowledge_graph",
    "description": (
        "Extract a structured knowledge graph from an enterprise document. "
        "Identify processes, roles, systems, policies, data entities, and events "
        "as nodes, and the relationships between them as edges."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "description": "All significant entities found in the document",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":          {"type": "string", "description": "Unique ID: n1, n2, …"},
                        "label":       {"type": "string", "description": "Short readable name (≤ 40 chars)"},
                        "type":        {"type": "string", "enum": ["Process", "Role", "System", "Policy", "DataEntity", "Event"]},
                        "description": {"type": "string", "description": "One-sentence description (≤ 90 chars)"},
                        "source_text": {"type": "string", "description": "Verbatim quote from the document (≤ 120 chars)"},
                    },
                    "required": ["id", "label", "type", "description", "source_text"],
                },
            },
            "edges": {
                "type": "array",
                "description": "Relationships between nodes",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":          {"type": "string", "description": "Unique ID: e1, e2, …"},
                        "source":      {"type": "string", "description": "Source node ID"},
                        "target":      {"type": "string", "description": "Target node ID"},
                        "label":       {"type": "string", "description": "Relationship verb (e.g. triggers, governed_by)"},
                        "description": {"type": "string", "description": "What this relationship means (≤ 90 chars)"},
                        "source_text": {"type": "string", "description": "Verbatim quote supporting the relationship (≤ 120 chars)"},
                    },
                    "required": ["id", "source", "target", "label", "description", "source_text"],
                },
            },
        },
        "required": ["nodes", "edges"],
    },
}

_ROLE_SYS_SCHEMA = {
    "type": "object",
    "properties": {
        "node_id":    {"type": ["string", "null"]},
        "node_label": {"type": ["string", "null"]},
    },
    "required": ["node_id", "node_label"],
}

WORKFLOW_TOOL = {
    "name": "suggest_workflows",
    "description": "Suggest practical as-is / to-be automation workflows grounded in the knowledge graph.",
    "input_schema": {
        "type": "object",
        "properties": {
            "workflows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":                  {"type": "string"},
                        "title":               {"type": "string"},
                        "description":         {"type": "string"},
                        "trigger": {
                            "type": "object",
                            "properties": {
                                "node_id":    {"type": "string"},
                                "node_label": {"type": "string"},
                                "condition":  {"type": "string"},
                            },
                            "required": ["node_id", "node_label", "condition"],
                        },
                        "sla_target":           {"type": "string"},
                        "current_avg":          {"type": "string"},
                        "sla_compliance_rate":  {"type": "string"},
                        "complexity":           {"type": "string", "enum": ["low", "medium", "high"]},
                        "as_is_steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step_number":      {"type": "integer"},
                                    "name":             {"type": "string"},
                                    "description":      {"type": "string"},
                                    "responsible_role": _ROLE_SYS_SCHEMA,
                                    "system_used":      _ROLE_SYS_SCHEMA,
                                    "sla_target":       {"type": "string"},
                                    "current_avg":      {"type": "string"},
                                    "sla_status":       {"type": "string", "enum": ["ok", "warn", "breach"]},
                                },
                                "required": ["step_number", "name", "description", "responsible_role", "system_used", "sla_target", "current_avg", "sla_status"],
                            },
                        },
                        "to_be_steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step_number":      {"type": "integer"},
                                    "name":             {"type": "string"},
                                    "description":      {"type": "string"},
                                    "responsible_role": _ROLE_SYS_SCHEMA,
                                    "system_used":      _ROLE_SYS_SCHEMA,
                                    "estimated_time":   {"type": "string"},
                                    "changed":          {"type": "boolean"},
                                    "improvement_note": {"type": "string"},
                                },
                                "required": ["step_number", "name", "description", "responsible_role", "system_used", "estimated_time", "changed", "improvement_note"],
                            },
                        },
                        "benefits": {
                            "type": "object",
                            "properties": {
                                "time_saved_per_transaction": {"type": "string"},
                                "extra_capacity":             {"type": "string"},
                                "revenue_or_cost_impact":     {"type": "string"},
                                "implementation_effort":      {"type": "string", "enum": ["low", "medium", "high"]},
                            },
                            "required": ["time_saved_per_transaction", "extra_capacity", "revenue_or_cost_impact", "implementation_effort"],
                        },
                        "source_node_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "title", "description", "trigger", "sla_target", "current_avg", "sla_compliance_rate", "complexity", "as_is_steps", "to_be_steps", "benefits", "source_node_ids"],
                },
            },
        },
        "required": ["workflows"],
    },
}

NLQ_TOOL = {
    "name": "answer_graph_query",
    "description": "Answer a natural language question about a knowledge graph and source document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "Concise, factual answer (2-4 sentences). Reference specific entity labels.",
            },
            "relevant_node_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs of nodes most relevant to answering the question",
            },
            "relevant_edge_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs of edges most relevant to answering the question",
            },
            "follow_up_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2-3 natural follow-up questions the user might ask next",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Confidence level based on evidence in the graph/document",
            },
        },
        "required": ["answer", "relevant_node_ids", "relevant_edge_ids", "follow_up_questions", "confidence"],
    },
}

OBJECT_MODEL_TOOL = {
    "name": "generate_object_model",
    "description": "Generate Pydantic v2 models and JSON Schema from a knowledge graph.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pydantic_code": {"type": "string", "description": "Complete Python file with Pydantic v2 models"},
            "json_schema":   {"type": "object", "description": "JSON Schema object for the domain model"},
            "summary":       {"type": "string", "description": "2-3 sentence explanation of the model"},
        },
        "required": ["pydantic_code", "json_schema", "summary"],
    },
}

ROI_TOOL = {
    "name": "calculate_workflow_roi",
    "description": "Calculate the estimated annual USD value of automating a banking workflow, with explicit assumptions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "headline_value_usd": {
                "type": "integer",
                "description": "Estimated annual value in whole USD (e.g. 2400000 for $2.4M).",
            },
            "headline_value_display": {
                "type": "string",
                "description": "Formatted headline figure with units, e.g. '$2.4M / year' or '$845K / year'.",
            },
            "headline_basis": {
                "type": "string",
                "description": "One sentence stating what primarily drives this number (e.g. 'FTE time freed on credit underwriting').",
            },
            "assumptions": {
                "type": "array",
                "description": "4-7 banking-industry assumptions used to derive the headline value.",
                "items": {
                    "type": "object",
                    "properties": {
                        "label":     {"type": "string", "description": "Short name, e.g. 'Loaded staff cost' or 'Annual transaction volume'."},
                        "value":     {"type": "string", "description": "The figure used, e.g. '$85/hr fully loaded' or '12,000 loan applications/yr'."},
                        "rationale": {"type": "string", "description": "One sentence on why this is realistic for retail/commercial banking."},
                    },
                    "required": ["label", "value", "rationale"],
                },
            },
            "methodology_note": {
                "type": "string",
                "description": "1-2 sentences describing how the headline figure was calculated from the assumptions.",
            },
        },
        "required": ["headline_value_usd", "headline_value_display", "headline_basis", "assumptions", "methodology_note"],
    },
}

ROI_SYSTEM = (
    "You are a banking automation ROI analyst. "
    "Given an automation workflow and its supporting graph context, estimate the realistic ANNUAL "
    "DOLLAR VALUE the bank would capture by automating it, and state the banking-industry "
    "assumptions you used to get there.\n\n"
    "Use realistic mid-2020s benchmarks for retail / commercial banking:\n"
    "- Loaded staff cost: $60-95/hr for ops & back-office, $120-180/hr for credit, risk, compliance roles\n"
    "- Average commercial loan value: $250K-$2M; retail loan: $25K-$80K; SME loan: $50K-$500K\n"
    "- Net Interest Margin (NIM): 2.5-3.5% for US/EU commercial banks\n"
    "- FTE productive hours: ~1,800/year per FTE\n"
    "- KYC/onboarding volume: a mid-size commercial bank processes 5K-50K applications/yr\n"
    "- Cost of regulatory breaches, opportunity cost on capital — only mention if material\n\n"
    "Rules:\n"
    "- Be concrete, conservative, and explainable. The headline figure must reconcile with the assumptions.\n"
    "- If transaction volume is uncertain, state your volume assumption explicitly as one of the assumptions.\n"
    "- Prefer FTE-time-freed valuations when SLA breaches are the main driver; prefer NIM-based revenue capture when faster cycle time unlocks more lending.\n"
    "- Do not over-claim. A single workflow rarely yields >$10M/yr in a single bank — flag if your number exceeds that.\n"
    "Always call the calculate_workflow_roi tool."
)


def calculate_workflow_roi(workflow: dict, graph: dict) -> dict:
    nodes = graph.get("nodes", [])
    policies = [n for n in nodes if n.get("type") == "Policy"]
    roles    = [n for n in nodes if n.get("type") == "Role"]

    policy_lines = "\n".join(
        f"- {p['label']}: {p.get('description','')[:120]}" for p in policies[:8]
    ) or "(none extracted)"
    role_lines = ", ".join(r["label"] for r in roles[:8]) or "(none extracted)"

    benefits = workflow.get("benefits", {}) or {}
    as_is_n  = len(workflow.get("as_is_steps", []))
    to_be_n  = len(workflow.get("to_be_steps", []))

    prompt = (
        f"WORKFLOW: {workflow.get('title','')}\n"
        f"Description: {workflow.get('description','')}\n"
        f"Complexity: {workflow.get('complexity','')} | "
        f"Current avg: {workflow.get('current_avg','')} | "
        f"SLA target: {workflow.get('sla_target','')} | "
        f"Compliance: {workflow.get('sla_compliance_rate','')}\n"
        f"Steps: {as_is_n} as-is, {to_be_n} to-be\n\n"
        f"DERIVED BENEFITS (already estimated upstream):\n"
        f"- Time saved per transaction: {benefits.get('time_saved_per_transaction','—')}\n"
        f"- Extra capacity unlocked: {benefits.get('extra_capacity','—')}\n"
        f"- Revenue / cost impact note: {benefits.get('revenue_or_cost_impact','—')}\n"
        f"- Implementation effort: {benefits.get('implementation_effort','—')}\n\n"
        f"GOVERNING POLICIES (use SLAs from these):\n{policy_lines}\n\n"
        f"ROLES INVOLVED: {role_lines}\n\n"
        "Calculate the headline annual USD value of automating this workflow, "
        "and list 4-7 banking assumptions you used to derive it."
    )
    return _call_tool(ROI_SYSTEM, prompt, ROI_TOOL, model=HAIKU, max_tokens=1500)


PULSE_AI_TOOL = {
    "name": "generate_pulse_recommendations",
    "description": "Generate strategic AI-powered recommendations based on knowledge graph structure and gaps.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":              {"type": "string"},
                        "title":           {"type": "string"},
                        "detail":          {"type": "string"},
                        "category":        {"type": "string", "enum": ["NOW", "THIS_WEEK", "BACKLOG"]},
                        "severity":        {"type": "string", "enum": ["critical", "warning", "info"]},
                        "business_impact": {"type": "string"},
                    },
                    "required": ["id", "title", "detail", "category", "severity", "business_impact"],
                },
            },
        },
        "required": ["recommendations"],
    },
}

PULSE_AI_SYSTEM = (
    "You are an enterprise process improvement expert. "
    "Given a Knowledge Graph and its detected gaps, generate 5–8 strategic "
    "AI-powered recommendations the organisation should act on. "
    "Categorise each as NOW (urgent — days), THIS_WEEK (important — this week), "
    "or BACKLOG (valuable — no rush). Be specific, business-friendly, and actionable. "
    "Always call the generate_pulse_recommendations tool."
)


def generate_pulse_ai(graph: dict, pulse_items: list) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    type_counts: dict[str, int] = {}
    for n in nodes:
        t = n.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    item_lines = "\n".join(
        f"- [{item['severity'].upper()}] {item['title']}: {item['description']}"
        for item in pulse_items[:20]
    )

    prompt = (
        f"Knowledge graph: {len(nodes)} nodes "
        f"({', '.join(f'{v} {k}' for k, v in type_counts.items())}), "
        f"{len(edges)} edges\n\n"
        f"Detected issues:\n{item_lines or 'No significant gaps detected.'}\n\n"
        "Generate 5–8 strategic recommendations for this organisation."
    )
    return _call_tool(PULSE_AI_SYSTEM, prompt, PULSE_AI_TOOL, model=HAIKU, max_tokens=2048)


BLUEPRINT_TOOL = {
    "name": "generate_blueprint",
    "description": "Generate an enterprise blueprint summary and improvement roadmap from a knowledge graph and gap analysis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "3-4 sentences describing what the document covers, what is well-defined, and what the main gaps are",
            },
            "next_steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3 specific actionable improvement recommendations",
            },
            "documents_to_upload": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Types of documents that would resolve the identified gaps",
            },
        },
        "required": ["summary", "next_steps", "documents_to_upload"],
    },
}

# ── Prompts ──────────────────────────────────────────────────────────────────

EXTRACTION_SYSTEM = (
    "You are an expert enterprise knowledge graph extractor. "
    "You extract comprehensive, accurate knowledge graphs from business documents. "
    "Always call the extract_knowledge_graph tool with the full graph."
)

EXTRACTION_PROMPT = """\
Analyse this enterprise document and call extract_knowledge_graph with a complete graph.

=== DOCUMENT: {filename} ===
{text}
=== END DOCUMENT ===

Node types to extract:
- Process   — workflows, procedures, process steps
- Role      — job titles, teams, departments, actors
- System    — software, platforms, tools, databases
- Policy    — rules, regulations, compliance requirements, SLAs
- DataEntity — documents, records, forms, data types
- Event     — triggers, milestones, notifications, deadlines

Relationship labels (use these or create precise alternatives):
triggers | executed_by | governed_by | uses_system | produces |
escalates_to | approves | reports_to | manages | depends_on |
notifies | owned_by | submits | validates | stores_in | assigned_to

Extract 15–20 nodes and 15–20 edges covering the most important entities and relationships.
Every node ID referenced in an edge must exist in the nodes array.
"""

WORKFLOW_SYSTEM = (
    "You are an enterprise process automation expert. Given a Knowledge Graph and the source "
    "document text, suggest 3–5 practical workflows as AS-IS vs TO-BE comparisons. "
    "Rules:\n"
    "- as_is_steps: reflect what the document describes today, using any SLA and performance data "
    "found in the text. Set sla_status to 'breach' if current_avg exceeds sla_target, 'warn' if "
    "within 20% of breaching, 'ok' otherwise.\n"
    "- to_be_steps: same steps with automation improvements on breaching/at-risk steps. "
    "Unchanged steps use changed: false and empty improvement_note.\n"
    "- benefits: use actual numbers from the document where present.\n"
    "- IMPORTANT: You MUST provide a non-empty string for every field — sla_target, current_avg, "
    "sla_compliance_rate, estimated_time, and all benefits fields. If the document does not state "
    "exact figures, estimate realistic values based on typical industry benchmarks for this process "
    "type. Never leave a field blank or return '—'.\n"
    "- Never invent steps not grounded in the extracted graph nodes.\n"
    "- Every responsible_role and system_used must reference actual node IDs from the graph, or null.\n"
    "Always call the suggest_workflows tool."
)

NLQ_SYSTEM = (
    "You are a knowledge graph analyst. Answer questions about the provided knowledge graph "
    "and source document concisely and accurately. "
    "Reference specific graph node labels in your answer where relevant. "
    "Always call the answer_graph_query tool."
)

OBJECT_MODEL_SYSTEM = (
    "You are a senior software architect following the BRD Authoring Standard. "
    "Given a knowledge graph, generate Pydantic v2 models and a JSON Schema that "
    "conform strictly to the entity rules below. Always call the generate_object_model tool.\n\n"
    "NON-NEGOTIABLE ENTITY RULES (BRD §4):\n"
    "1. Field names: snake_case only — no spaces, no camelCase, under 63 chars\n"
    "2. First field on every entity: id: UUID  (Primary Key)\n"
    "3. Every entity must include: created_at: datetime  (Not Null)\n"
    "4. Audit fields: created_by: UUID and last_changed_by: UUID — mark description as 'AUDIT ONLY – no relationship'\n"
    "5. FK columns named <parent_table>_id: UUID (e.g. customer_id, account_id)\n"
    "6. Enum values: UPPERCASE only (OPEN, IN_PROGRESS, BLOCKED — never lowercase)\n"
    "7. Relationships must use format: entity_a (parent) → entity_b (child) via entity_b.fk_column = entity_a.id"
)

BLUEPRINT_SYSTEM = (
    "You are an enterprise architect reviewing a Knowledge Graph "
    "extracted from an enterprise document by the Metafore Discovery Engine. "
    "Based on the graph summary and gaps identified, write a concise Blueprint Summary. "
    "Be specific and business-friendly. "
    "Always call the generate_blueprint tool."
)

OBJECT_MODEL_PROMPT = """\
Generate a domain object model for this knowledge graph by calling generate_object_model.

GRAPH:
{graph_json}

PYDANTIC CODE — follow BRD Authoring Standard §4 exactly:
- Imports: `from pydantic import BaseModel, Field`, `from uuid import UUID`, `from datetime import datetime`, `from typing import Optional, List`, `import enum`
- One class per major domain entity (group related node types into entities)
- Every entity MUST have as its first two fields:
    id: UUID = Field(description="Primary Key")
    created_at: datetime = Field(description="Not Null — audit trail")
- Every entity MUST include audit fields:
    created_by: UUID = Field(description="AUDIT ONLY – no relationship")
    last_changed_by: UUID = Field(description="AUDIT ONLY – no relationship")
- FK fields: <parent_table>_id: UUID = Field(description="Foreign Key → ParentEntity")
- Enums: `class MyStatusEnum(str, enum.Enum)` with UPPERCASE values only
- snake_case field names throughout
- Add `__all__` at the bottom listing all model class names
- Keep under 200 lines total

JSON SCHEMA — include:
- "entities": array of objects, each with "name", "fields" (array of {{name, type, constraints}})
- "relationships": array of relationship strings using EXACT format:
  "entity_a (parent) → entity_b (child) via entity_b.fk_column = entity_a.id"
- Enum values UPPERCASE in the schema

SUMMARY: 2–3 sentences describing the domain model and its key entities.
"""


# ── Core call ────────────────────────────────────────────────────────────────

def _call_tool(system: str, prompt: str, tool: dict, model: str = "claude-sonnet-4-6", max_tokens: int = 8096) -> dict:
    """Call Claude with tool_choice forced to `tool`, return the tool input dict."""
    client = _get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    # Find the tool_use block — Claude is forced to produce exactly one
    for block in response.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input
    raise RuntimeError("Claude did not return a tool_use block")


# ── Graph helpers ─────────────────────────────────────────────────────────────

def _merge_graphs(graphs: list[dict]) -> dict:
    merged = {"nodes": [], "edges": []}
    node_counter = 1
    edge_counter = 1

    for g in graphs:
        id_remap: dict[str, str] = {}
        for node in g.get("nodes", []):
            new_id = f"n{node_counter}"
            node_counter += 1
            id_remap[node["id"]] = new_id
            merged["nodes"].append({**node, "id": new_id})

        for edge in g.get("edges", []):
            src = id_remap.get(edge["source"], edge["source"])
            tgt = id_remap.get(edge["target"], edge["target"])
            merged["edges"].append(
                {**edge, "id": f"e{edge_counter}", "source": src, "target": tgt}
            )
            edge_counter += 1

    return merged


# ── Public API ────────────────────────────────────────────────────────────────

def extract_graph_from_text(text: str, filename: str = "document") -> dict:
    prompt = EXTRACTION_PROMPT.format(filename=filename, text=text[:20_000])
    return _call_tool(EXTRACTION_SYSTEM, prompt, GRAPH_TOOL, model=SONNET, max_tokens=8096)


def extract_graphs(documents: list[tuple[str, str]]) -> dict:
    graphs = [extract_graph_from_text(text, name) for name, text in documents]
    return _merge_graphs(graphs)


def _build_workflow_prompt(graph: dict, doc_text: str = "") -> str:
    node_lines = "\n".join(
        f"{n['id']} | {n['label']} | {n.get('type', '')} | {n.get('description', '')}"
        for n in graph.get("nodes", [])
    )
    edge_lines = "\n".join(
        f"{e.get('source', '')} --[{e.get('label', '')}]--> {e.get('target', '')}"
        for e in graph.get("edges", [])
    )
    doc_section = f"\n\n=== SOURCE DOCUMENT (use for SLA data and timings) ===\n{doc_text[:8000]}\n===" if doc_text else ""
    return (
        f"NODES:\n{node_lines}\n\nEDGES:\n{edge_lines}{doc_section}\n\n"
        "Suggest 3–5 practical automation workflows. "
        "All numeric fields (sla_target, current_avg, sla_compliance_rate, estimated_time, "
        "benefits) MUST be non-empty — extract from the document or estimate from industry benchmarks."
    )


def generate_workflows(graph: dict, doc_text: str = "") -> list[dict]:
    prompt = _build_workflow_prompt(graph, doc_text)
    result = _call_tool(WORKFLOW_SYSTEM, prompt, WORKFLOW_TOOL, max_tokens=16000)
    return result.get("workflows", [])


def generate_object_model(graph: dict) -> dict:
    node_lines = "\n".join(
        f"{n['id']} | {n.get('type','')} | {n['label']}"
        for n in graph.get("nodes", [])
    )
    edge_lines = "\n".join(
        f"{e.get('source','')} --[{e.get('label','')}]--> {e.get('target','')}"
        for e in graph.get("edges", [])
    )
    compact = f"NODES:\n{node_lines}\n\nEDGES:\n{edge_lines}"
    prompt = OBJECT_MODEL_PROMPT.format(graph_json=compact)
    return _call_tool(OBJECT_MODEL_SYSTEM, prompt, OBJECT_MODEL_TOOL, model=SONNET, max_tokens=4096)


def generate_blueprint(graph: dict, gap_analysis: dict) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    type_counts: dict[str, int] = {}
    for n in nodes:
        t = n.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    edge_label_counts: dict[str, int] = {}
    for e in edges:
        lbl = e.get("label", "unknown")
        edge_label_counts[lbl] = edge_label_counts.get(lbl, 0) + 1

    node_summary = ", ".join(f"{v} {k}" for k, v in type_counts.items())
    edge_summary = ", ".join(f"{v} {lbl}" for lbl, v in list(edge_label_counts.items())[:8])

    gap_lines = []
    for check in gap_analysis.get("checks", []):
        if check.get("count", 0) > 0:
            labels = ", ".join(check.get("affected_node_labels", [])[:5])
            gap_lines.append(f"- {check['title']}: {check['count']} affected ({labels})")

    gap_text = "\n".join(gap_lines) if gap_lines else "No significant gaps found."

    prompt = (
        f"Graph summary: {len(nodes)} nodes ({node_summary}), {len(edges)} edges ({edge_summary})\n\n"
        f"Gaps identified:\n{gap_text}\n\n"
        f"Coverage score: {gap_analysis.get('coverage_score', 0)} ({gap_analysis.get('score_label', '')})"
    )
    return _call_tool(BLUEPRINT_SYSTEM, prompt, BLUEPRINT_TOOL, model=HAIKU, max_tokens=800)


CONFORMANCE_TOOL = {
    "name": "assess_conformance",
    "description": "Assess each knowledge graph node against an evidence document for process conformance.",
    "input_schema": {
        "type": "object",
        "properties": {
            "conformance_results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "node_id":          {"type": "string"},
                        "node_label":       {"type": "string"},
                        "node_type":        {"type": "string"},
                        "status":           {"type": "string", "enum": ["confirmed", "deviated", "not_found"]},
                        "confidence":       {"type": "number"},
                        "evidence_excerpt": {"type": ["string", "null"]},
                        "deviation_detail": {"type": ["string", "null"]},
                    },
                    "required": ["node_id", "node_label", "node_type", "status", "confidence",
                                 "evidence_excerpt", "deviation_detail"],
                },
            },
            "overall_conformance_rate": {"type": "integer"},
            "summary":                  {"type": "string"},
        },
        "required": ["conformance_results", "overall_conformance_rate", "summary"],
    },
}

CONFORMANCE_SYSTEM = (
    "You are a process conformance analyst. You have two inputs:\n\n"
    "1. A Knowledge Graph showing how a business process SHOULD work — extracted from an SOP.\n\n"
    "2. An evidence document showing what ACTUALLY happened — an audit report, incident log, "
    "email thread, or operational record.\n\n"
    "Assess each node in the Knowledge Graph against the evidence document and return one of three statuses:\n\n"
    "CONFIRMED — evidence clearly shows this step, role, or policy was followed as described in the SOP.\n\n"
    "DEVIATED — evidence shows this was NOT followed, was skipped, done by the wrong person, or "
    "contradicts the SOP in a specific way.\n\n"
    "NOT_FOUND — evidence does not mention this node at all. This is neutral — absence is not deviation.\n\n"
    "Rules:\n"
    "- Only use what the evidence document explicitly states — do not assume conformance\n"
    "- Only mark DEVIATED when there is clear contradictory evidence, not just absence\n"
    "- For CONFIRMED and DEVIATED always include a short verbatim excerpt from the evidence document\n"
    "- For DEVIATED always explain specifically what differs from the SOP description\n"
    "Always call the assess_conformance tool."
)


def run_conformance_analysis(graph: dict, evidence_text: str) -> dict:
    ELIGIBLE_TYPES = {"Process", "Role", "Policy", "DataEntity"}
    nodes = [n for n in graph.get("nodes", []) if n.get("type") in ELIGIBLE_TYPES]

    node_lines = "\n".join(
        f"{n['id']} | {n.get('type', '')} | {n['label']}"
        for n in nodes
    )
    prompt = (
        f"KNOWLEDGE GRAPH NODES:\n{node_lines}\n\n"
        f"EVIDENCE DOCUMENT:\n{evidence_text[:8000]}\n\n"
        "Assess each node."
    )
    return _call_tool(CONFORMANCE_SYSTEM, prompt, CONFORMANCE_TOOL, model=SONNET, max_tokens=6000)


def query_graph(graph: dict, question: str, doc_text: str = "") -> dict:
    node_lines = "\n".join(
        f"{n['id']} | {n['label']} | {n.get('type', '')}"
        for n in graph.get("nodes", [])
    )
    edge_lines = "\n".join(
        f"{e['id']} | {e.get('source', '')} --[{e.get('label', '')}]--> {e.get('target', '')}"
        for e in graph.get("edges", [])
    )
    doc_section = f"\n\n=== SOURCE DOCUMENT ===\n{doc_text[:3000]}\n===" if doc_text else ""
    prompt = (
        f"KNOWLEDGE GRAPH:\n\nNODES:\n{node_lines}\n\nEDGES:\n{edge_lines}"
        f"{doc_section}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer based on the graph and document. "
        "List the IDs of the most relevant nodes in relevant_node_ids and edges in relevant_edge_ids."
    )
    return _call_tool(NLQ_SYSTEM, prompt, NLQ_TOOL, model=HAIKU, max_tokens=800)
