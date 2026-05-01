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
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filename(s) of source documents this entity appeared in. Single-doc: [filename]. Multi-doc: list ALL filenames where the entity is mentioned (an entity in 2+ docs has higher confidence).",
                        },
                    },
                    "required": ["id", "label", "type", "description", "source_text", "sources"],
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

_ROI_SCHEMA = {
    "type": "object",
    "description": "Estimated annual ROI of automating this workflow, with banking-industry assumptions.",
    "properties": {
        "headline_value_usd":     {"type": "integer", "description": "Estimated annual value in whole USD (e.g. 2400000 for $2.4M)."},
        "headline_value_display": {"type": "string", "description": "Formatted figure with units, e.g. '$2.4M / year'."},
        "headline_basis":         {"type": "string", "description": "One sentence: what primarily drives this number."},
        "assumptions": {
            "type": "array",
            "description": "4-7 banking-industry assumptions used to derive the headline value.",
            "items": {
                "type": "object",
                "properties": {
                    "label":     {"type": "string", "description": "Short name, e.g. 'Loaded staff cost'."},
                    "value":     {"type": "string", "description": "The figure used, e.g. '$85/hr fully loaded'."},
                    "rationale": {"type": "string", "description": "One sentence on why this is realistic for retail/commercial banking."},
                },
                "required": ["label", "value", "rationale"],
            },
        },
        "methodology_note": {"type": "string", "description": "1-2 sentences on how the headline figure was derived from the assumptions."},
    },
    "required": ["headline_value_usd", "headline_value_display", "headline_basis", "assumptions", "methodology_note"],
}

_AUTOMATION_SCHEMA = {
    "type": "object",
    "description": "Per-step automation potential scoring plus an overall recommendation.",
    "properties": {
        "step_scores": {
            "type": "array",
            "description": "One scoring entry per AS-IS step. step_number must match the as_is_steps.step_number on the same workflow.",
            "items": {
                "type": "object",
                "properties": {
                    "step_number":        {"type": "integer"},
                    "automation_score":   {"type": "integer", "description": "0-10. 8-10 fully automatable, 5-7 AI-assistable, 0-4 needs a human."},
                    "automation_level":   {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "reason":             {"type": "string", "description": "One sentence explaining the score."},
                    "suggested_approach": {"type": "string", "description": "e.g. 'Rule-based RPA', 'AI-assisted', 'Full automation', 'Human required'."},
                },
                "required": ["step_number", "automation_score", "automation_level", "reason", "suggested_approach"],
            },
        },
        "overall_recommendation": {"type": "string", "description": "One sentence overall guidance for automating this workflow."},
    },
    "required": ["step_scores", "overall_recommendation"],
}

_VARIANTS_SCHEMA = {
    "type": "array",
    "description": (
        "Process variants — how this workflow actually executes across the standard "
        "happy path and exception/escalation scenarios. Always include a Variant A "
        "(standard path) and 2-4 additional variants for exceptions described in the "
        "document. frequency_pct across all variants MUST sum to exactly 100. "
        "Return an EMPTY array if as_is_steps has fewer than 3 steps."
    ),
    "items": {
        "type": "object",
        "properties": {
            "id":                {"type": "string", "description": "variant_a, variant_b, variant_c, ..."},
            "name":              {"type": "string", "description": "Short label (≤4 words), e.g. 'Standard Path' or 'AML Flag Path'."},
            "description":       {"type": "string", "description": "One short sentence (≤16 words)."},
            "frequency_pct":     {"type": "integer", "description": "Estimated 0-100 of cases. ALL variants sum to 100. Variant A is highest."},
            "steps":             {"type": "array", "items": {"type": "string"}, "description": "Ordered step name strings — match document or as_is_steps names."},
            "divergence_point":  {"type": ["string", "null"], "description": "Step name where this variant splits from Variant A. null for Variant A."},
            "divergence_reason": {"type": ["string", "null"], "description": "Trigger for this variant (≤16 words). null for Variant A."},
            "avg_tat":           {"type": "string", "description": "Avg turnaround, e.g. '5.2 days', '4 hrs'."},
            "sla_status":        {"type": "string", "enum": ["ok", "breach"]},
            "node_ids":          {"type": "array", "items": {"type": "string"}, "description": "Graph node ids involved (must match actual extracted node ids)."},
        },
        "required": ["id", "name", "description", "frequency_pct", "steps", "divergence_point", "divergence_reason", "avg_tat", "sla_status", "node_ids"],
    },
}

WORKFLOW_BUNDLE_TOOL = {
    "name": "generate_workflow_bundle",
    "description": "Generate AS-IS/TO-BE workflows together with ROI estimate and per-step automation scoring in a single response.",
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
                        "roi":             _ROI_SCHEMA,
                        "automation":      _AUTOMATION_SCHEMA,
                        "variants":        _VARIANTS_SCHEMA,
                    },
                    "required": ["id", "title", "description", "trigger", "sla_target", "current_avg", "sla_compliance_rate", "complexity", "as_is_steps", "to_be_steps", "benefits", "source_node_ids", "roi", "automation", "variants"],
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
    "description": "Generate Pydantic v2 models and a structured BRD-format JSON Schema from a knowledge graph.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pydantic_code": {"type": "string", "description": "Complete Python file with Pydantic v2 models"},
            "json_schema": {
                "type": "object",
                "description": "BRD-format JSON Schema with entities and relationships arrays — used to render the ERD.",
                "properties": {
                    "entities": {
                        "type": "array",
                        "description": "Every domain entity, in the same order as the Pydantic classes.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name":   {"type": "string", "description": "Entity name in snake_case (e.g. loan_application)"},
                                "fields": {
                                    "type": "array",
                                    "description": "All fields of this entity. Must start with id (UUID, Primary Key) and include created_at.",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name":        {"type": "string", "description": "Field name, snake_case"},
                                            "type":        {"type": "string", "description": "Pydantic-style type (e.g. UUID, datetime, str, int, MyEnum)"},
                                            "constraints": {"type": "string", "description": "Constraint hint: 'Primary Key', 'Foreign Key → other_entity', 'Not Null', 'AUDIT ONLY – no relationship', or empty"},
                                        },
                                        "required": ["name", "type"],
                                    },
                                },
                            },
                            "required": ["name", "fields"],
                        },
                    },
                    "relationships": {
                        "type": "array",
                        "description": "Each relationship as a string in EXACT format: 'parent_entity (parent) → child_entity (child) via child_entity.fk_col = parent_entity.id'",
                        "items": {"type": "string"},
                    },
                },
                "required": ["entities", "relationships"],
            },
            "summary": {"type": "string", "description": "2-3 sentence explanation of the model"},
        },
        "required": ["pydantic_code", "json_schema", "summary"],
    },
}

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


PM_OPTIMISE_TOOL = {
    "name": "suggest_process_optimisations",
    "description": "Given a process-mining snapshot (KPIs, activities, deviation patterns), produce 3-5 specific re-routing or SLA-target suggestions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1-2 sentence diagnosis: name the bottleneck and the single most impactful change.",
            },
            "recommendations": {
                "type": "array",
                "minItems": 3,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "title":            {"type": "string", "description": "Short imperative — e.g. 'Auto-route low-value loans to Junior Underwriter'"},
                        "rationale":        {"type": "string", "description": "1 sentence: which deviation/bottleneck this addresses."},
                        "expected_impact":  {"type": "string", "description": "Quantitative or qualitative — e.g. '−1.4d median TAT' or 'eliminate wrong-role events'"},
                        "effort":           {"type": "string", "enum": ["low", "medium", "high"]},
                        "target_step":      {"type": "string", "description": "Which process step (activity) this targets, if any. Empty string if cross-cutting."},
                    },
                    "required": ["title", "rationale", "expected_impact", "effort", "target_step"],
                },
            },
        },
        "required": ["summary", "recommendations"],
    },
}

PM_OPTIMISE_SYSTEM = (
    "You are a process-mining expert advising a mid-size bank on loan-origination operations. "
    "Given the SOP-vs-execution data below, propose specific, actionable optimisations. "
    "Be concrete (mention real step names, role swaps, threshold rules). "
    "Always call the suggest_process_optimisations tool."
)


def generate_pm_optimise(pm_data: dict) -> dict:
    """Take the process-mining JSON shape and ask Haiku for 3-5 optimisations."""
    k = pm_data.get("kpis", {})
    activities = pm_data.get("activities", [])
    patterns   = pm_data.get("conformance", {}).get("deviation_patterns", [])
    bottleneck = k.get("bottleneck_step") or "(none flagged)"

    act_lines = []
    for a in activities:
        bits = [f"{a['id']}: {a['case_count']} cases, dwell {a.get('median_dwell_hours')}h vs SLA {a.get('sla_hours')}h"]
        if a.get("breach_count"):       bits.append(f"{a['breach_count']} breaches")
        if a.get("role_mismatch_count"): bits.append(f"{a['role_mismatch_count']} wrong-role")
        act_lines.append("- " + "; ".join(bits))

    pat_lines = [f"- [{p['severity']}] {p['label']} ({p['case_count']} cases)" for p in patterns]

    prompt = (
        f"Process-mining snapshot — {k.get('total_cases')} cases, {k.get('total_activities')} activities.\n"
        f"Median TAT {k.get('median_tat_days')}d. SLA breach rate {k.get('breach_rate_pct')}%. "
        f"Conformance fitness {k.get('fitness')}. Bottleneck: {bottleneck}.\n\n"
        f"Activities:\n" + "\n".join(act_lines) + "\n\n"
        f"Deviation patterns:\n" + ("\n".join(pat_lines) if pat_lines else "(none)") + "\n\n"
        "Propose 3-5 concrete optimisations. Prioritise the bottleneck and the highest-severity deviation patterns."
    )
    return _call_tool(PM_OPTIMISE_SYSTEM, prompt, PM_OPTIMISE_TOOL, model=HAIKU, max_tokens=1500)


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
    "Always populate the 'sources' field on every node with the filename(s) of the document(s) "
    "that entity appeared in. "
    "Always call the extract_knowledge_graph tool with the full graph."
)

EXTRACTION_MULTI_DOC_RULES = (
    "Multi-document rules:\n"
    "- This is ONE unified graph that connects entities across all the documents above.\n"
    "- Where the same entity appears in multiple documents, MERGE it into ONE node and "
    "list ALL filenames in its sources field — this signals higher confidence.\n"
    "- Where documents contradict on the same entity, note BOTH views in the node description.\n"
    "- Tag every node with which document(s) it came from using the sources field."
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

WORKFLOW_BUNDLE_SYSTEM = (
    "You are an enterprise process automation expert and banking ROI analyst. "
    "Given a Knowledge Graph and the source document text, generate 3-5 practical workflows "
    "as AS-IS vs TO-BE comparisons AND, for each workflow, also produce:\n"
    "  (a) ROI estimate — the realistic ANNUAL USD VALUE of automating it, with banking-industry "
    "assumptions used to derive the figure.\n"
    "  (b) Automation score per AS-IS step — score 0-10 with level, reason, and suggested approach.\n"
    "  (c) Process variants — how this workflow actually executes across the standard happy "
    "path and exception/escalation scenarios.\n\n"
    "── WORKFLOW RULES ──\n"
    "- as_is_steps reflect what the document describes today, using any SLA and performance data "
    "found in the text. Set sla_status to 'breach' if current_avg exceeds sla_target, 'warn' if "
    "within 20% of breaching, 'ok' otherwise.\n"
    "- to_be_steps are the same steps with automation improvements on breaching/at-risk steps. "
    "Unchanged steps use changed: false and empty improvement_note.\n"
    "- benefits: use actual numbers from the document where present.\n"
    "- Provide a non-empty string for every numeric field (sla_target, current_avg, "
    "sla_compliance_rate, estimated_time, and all benefits fields). If the document does not state "
    "exact figures, estimate from typical industry benchmarks. Never leave a field blank or return '—'.\n"
    "- Never invent steps not grounded in the extracted graph nodes.\n"
    "- Every responsible_role and system_used must reference actual node IDs from the graph, or null.\n\n"
    "── ROI RULES (mid-2020s banking benchmarks) ──\n"
    "- Loaded staff cost: $60-95/hr ops & back-office; $120-180/hr credit, risk, compliance.\n"
    "- Avg loan value: commercial $250K-$2M; retail $25K-$80K; SME $50K-$500K.\n"
    "- Net Interest Margin (NIM): 2.5-3.5% for US/EU commercial banks.\n"
    "- FTE productive hours: ~1,800/yr.\n"
    "- KYC/onboarding volume: 5K-50K applications/yr for a mid-size commercial bank.\n"
    "- Be concrete and conservative. The headline figure must reconcile with the assumptions.\n"
    "- List 4-7 assumptions (label / value / rationale). State your transaction-volume assumption explicitly.\n"
    "- Prefer FTE-time-freed valuation when SLA breaches drive value; prefer NIM-based revenue capture "
    "when faster cycle time unlocks more lending.\n"
    "- A single workflow rarely yields >$10M/yr in one bank — flag if your number exceeds that.\n\n"
    "── AUTOMATION SCORE RULES ──\n"
    "- 8-10 (High):   Deterministic, rule-driven, structured I/O. Suggest 'Rule-based RPA' or 'Full automation'.\n"
    "- 5-7  (Medium): Semi-structured, judgement-light, pattern-based. Suggest 'AI-assisted'.\n"
    "- 0-4  (Low):    Requires human judgement, negotiation, ambiguity, or relationship management. "
    "Suggest 'Human required' or 'Human-in-the-loop'.\n"
    "- Map automation_level from the score: 8-10 → 'High', 5-7 → 'Medium', 0-4 → 'Low'.\n"
    "- Each reason is ONE sentence. Each automation.step_scores entry's step_number MUST match a "
    "step_number that exists on the same workflow's as_is_steps.\n\n"
    "── PROCESS VARIANTS RULES ──\n"
    "- Variant A is the standard happy path with no exceptions or escalations: id='variant_a', "
    "divergence_point=null, divergence_reason=null. Variant A is ALWAYS the most frequent.\n"
    "- Generate 2-4 additional variants based on exceptions, escalations, and edge cases described "
    "in the document (e.g. AML flag raised, loan amount exceeds threshold, missing documents, "
    "manual override, committee escalation).\n"
    "- frequency_pct values across ALL variants MUST sum to exactly 100.\n"
    "- Estimate frequency from document language: 'in most cases' → 60-70%, 'occasionally' → 10-20%, "
    "'rarely' → 1-5%. Variant A typically 55-80%.\n"
    "- 'steps' is an ordered list of step name strings — should match step names from the document "
    "or the workflow's own as_is_steps names where applicable.\n"
    "- 'node_ids' lists the graph node ids involved in this variant — must reference actual node "
    "ids from the extracted graph. Empty list is acceptable only when no specific nodes apply.\n"
    "- Set sla_status='breach' if the variant's avg_tat clearly exceeds the workflow's sla_target; "
    "'ok' otherwise.\n"
    "- IF the workflow has fewer than 3 as_is_steps, return an EMPTY variants array.\n\n"
    "── BREVITY RULES (output length matters — long outputs slow the response) ──\n"
    "- workflow.description: 1-2 short sentences (≤ 30 words total).\n"
    "- as_is_steps[].description and to_be_steps[].description: ≤ 18 words each.\n"
    "- improvement_note: ≤ 12 words. Empty string when changed=false.\n"
    "- benefits.* fields: short phrases, not sentences (e.g. '4 hrs/loan', '+150 loans/yr').\n"
    "- roi.headline_basis: ≤ 16 words.\n"
    "- roi.assumptions[].rationale: ≤ 18 words each.\n"
    "- roi.methodology_note: ≤ 30 words total.\n"
    "- automation.step_scores[].reason: ≤ 16 words each.\n"
    "- automation.step_scores[].suggested_approach: ≤ 6 words (e.g. 'Rule-based RPA', 'AI-assisted review', 'Human required').\n"
    "- automation.overall_recommendation: 1 short sentence (≤ 22 words).\n"
    "- variants[].name: ≤ 4 words.\n"
    "- variants[].description: ≤ 16 words.\n"
    "- variants[].divergence_reason: ≤ 16 words. null for Variant A.\n"
    "- variants[].avg_tat: short phrase (e.g. '5.2 days', '4 hrs').\n\n"
    "Always call the generate_workflow_bundle tool."
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

def _call_tool(system: str, prompt: str, tool: dict, model: str = "claude-sonnet-4-6", max_tokens: int = 8096, cache: bool = False) -> dict:
    """Call Claude with tool_choice forced to `tool`, return the tool input dict.

    When cache=True, the system prompt and tool schema are marked as ephemeral
    cache breakpoints — repeat calls within ~5 min reuse the cached prefix
    (faster TTFT + cheaper input tokens).
    """
    client = _get_client()
    if cache:
        system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        tools_param  = [{**tool, "cache_control": {"type": "ephemeral"}}]
    else:
        system_param = system
        tools_param  = [tool]
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_param,
        tools=tools_param,
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    # Find the tool_use block — Claude is forced to produce exactly one
    for block in response.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input
    raise RuntimeError("Claude did not return a tool_use block")


# ── Public API ────────────────────────────────────────────────────────────────

EXTRACTION_TOTAL_LIMIT = 15_000   # combined doc text cap before sending to Claude


def _proportional_truncate(documents: list[tuple[str, str]], total_limit: int = EXTRACTION_TOTAL_LIMIT) -> list[tuple[str, str]]:
    """Trim each document proportionally so total combined text length ≤ limit.

    Reserves a small overhead per document for the "=== DOCUMENT: name ===" headers.
    Each document is guaranteed at least 100 chars so very small docs are not zeroed.
    """
    header_overhead = 60 * len(documents)
    text_budget = max(0, total_limit - header_overhead)
    total_len = sum(len(t) for _, t in documents)
    if total_len <= text_budget or total_len == 0:
        return documents
    out: list[tuple[str, str]] = []
    for name, text in documents:
        ratio = len(text) / total_len
        new_len = max(100, int(ratio * text_budget))
        out.append((name, text[:new_len]))
    return out


def extract_graph_from_text(text: str, filename: str = "document") -> dict:
    """Single-document extraction (kept for backwards compatibility — delegates
    to the unified multi-doc path with one entry)."""
    return extract_graphs([(filename, text)])


def extract_graphs(documents: list[tuple[str, str]]) -> dict:
    """One Claude call against combined text → ONE unified knowledge graph.

    For multi-doc uploads, entities that appear in more than one document are
    merged into a single node whose 'sources' lists every filename it appeared
    in (signalling higher confidence). For single-doc, this is identical to
    the previous extract_graph_from_text behaviour.
    """
    if not documents:
        raise ValueError("extract_graphs called with no documents")

    truncated = _proportional_truncate(documents, EXTRACTION_TOTAL_LIMIT)
    parts = [
        f"=== DOCUMENT: {name} ===\n{text}\n=== END DOCUMENT ==="
        for name, text in truncated
    ]
    combined = "\n\n".join(parts)

    is_multi = len(documents) > 1
    rules_block = f"\n\n{EXTRACTION_MULTI_DOC_RULES}" if is_multi else ""
    filenames_csv = ", ".join(name for name, _ in documents)
    node_target = "20-30" if is_multi else "15-20"

    prompt = (
        f"Analyse the following document{'s' if is_multi else ''} and call "
        f"extract_knowledge_graph with a complete graph.\n\n"
        f"{combined}{rules_block}\n\n"
        "Node types to extract:\n"
        "- Process   — workflows, procedures, process steps\n"
        "- Role      — job titles, teams, departments, actors\n"
        "- System    — software, platforms, tools, databases\n"
        "- Policy    — rules, regulations, compliance requirements, SLAs\n"
        "- DataEntity — documents, records, forms, data types\n"
        "- Event     — triggers, milestones, notifications, deadlines\n\n"
        "Relationship labels (use these or create precise alternatives):\n"
        "triggers | executed_by | governed_by | uses_system | produces |\n"
        "escalates_to | approves | reports_to | manages | depends_on |\n"
        "notifies | owned_by | submits | validates | stores_in | assigned_to\n\n"
        f"Extract {node_target} nodes and {node_target} edges covering the most important entities.\n"
        "Every node ID referenced in an edge must exist in the nodes array.\n"
        f"Every node MUST set the 'sources' field listing the document filename(s) it came from. "
        f"Possible filenames: [{filenames_csv}].\n"
    )
    return _call_tool(EXTRACTION_SYSTEM, prompt, GRAPH_TOOL, model=SONNET, max_tokens=8096)


# ── Cross-document insights (Haiku) ──────────────────────────────────────────

CROSS_DOC_TOOL = {
    "name": "cross_document_insights",
    "description": "Identify the most valuable cross-document gaps, inconsistencies, or contradictions in a multi-source knowledge graph.",
    "input_schema": {
        "type": "object",
        "properties": {
            "insights": {
                "type": "array",
                "description": "Up to 3 most valuable cross-document findings.",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "ONE evidence-based sentence (≤ 30 words)."},
                        "category": {
                            "type": "string",
                            "enum": ["gap", "inconsistency", "missing", "contradiction"],
                            "description": "gap = policy/standard not enforced anywhere; missing = entity expected but absent; inconsistency = same entity defined differently; contradiction = explicit disagreement.",
                        },
                    },
                    "required": ["text", "category"],
                },
            },
        },
        "required": ["insights"],
    },
}

CROSS_DOC_SYSTEM = (
    "You are an enterprise process compliance analyst. Given a knowledge graph "
    "extracted from MULTIPLE documents (each node tagged with its source document(s) "
    "in 'sources'), identify the 3 MOST valuable cross-document connections, gaps, or "
    "inconsistencies. Look for:\n"
    "- gap          : a Policy in one doc not referenced by any process in others\n"
    "- missing      : a System/Role mentioned in one doc but not registered in another that should reference it\n"
    "- inconsistency: same role/system with different scope or governance across docs\n"
    "- contradiction: documents that explicitly disagree about the same entity\n"
    "Each insight must be ONE short evidence-based sentence (≤30 words) that names the "
    "specific entities and document(s). Always call cross_document_insights."
)


def generate_cross_doc_insights(graph: dict, source_filenames: list[str]) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_lines = "\n".join(
        f"{n['id']} | {n.get('label','')} | {n.get('type','')} | sources: {','.join(n.get('sources') or [])}"
        for n in nodes
    )
    edge_lines = "\n".join(
        f"{e.get('source','')} --[{e.get('label','')}]--> {e.get('target','')}"
        for e in edges
    )
    prompt = (
        f"Documents: {', '.join(source_filenames)}\n\n"
        f"Nodes (with source documents):\n{node_lines}\n\n"
        f"Edges:\n{edge_lines}\n\n"
        "Identify the 3 MOST valuable cross-document insights — gaps, inconsistencies, "
        "or contradictions — that the customer should act on."
    )
    return _call_tool(CROSS_DOC_SYSTEM, prompt, CROSS_DOC_TOOL, model=HAIKU, max_tokens=1500)


def _build_workflow_prompt(graph: dict, doc_text: str = "") -> str:
    nodes = graph.get("nodes", [])
    node_lines = "\n".join(
        f"{n['id']} | {n['label']} | {n.get('type', '')} | {n.get('description', '')}"
        for n in nodes
    )
    edge_lines = "\n".join(
        f"{e.get('source', '')} --[{e.get('label', '')}]--> {e.get('target', '')}"
        for e in graph.get("edges", [])
    )
    policies = [n for n in nodes if n.get("type") == "Policy"]
    roles    = [n for n in nodes if n.get("type") == "Role"]
    policy_lines = "\n".join(f"- {p['label']}: {p.get('description','')[:120]}" for p in policies[:8]) or "(none)"
    role_lines   = ", ".join(r["label"] for r in roles[:8]) or "(none)"

    doc_section = f"\n\n=== SOURCE DOCUMENT (use for SLA data and timings) ===\n{doc_text[:8000]}\n===" if doc_text else ""
    return (
        f"NODES:\n{node_lines}\n\nEDGES:\n{edge_lines}{doc_section}\n\n"
        f"POLICIES (use SLAs from these for ROI): \n{policy_lines}\n\n"
        f"ROLES INVOLVED (cost basis for ROI): {role_lines}\n\n"
        "Generate 3-5 practical automation workflows. For each workflow, populate:\n"
        "  - the workflow itself (AS-IS / TO-BE / benefits)\n"
        "  - roi: headline annual USD value with 4-7 banking assumptions\n"
        "  - automation: 0-10 score for every AS-IS step plus a one-sentence overall recommendation\n"
        "All numeric fields MUST be non-empty — extract from the document or estimate from "
        "industry benchmarks. Each automation.step_scores entry must reference a step_number "
        "that exists on the same workflow's as_is_steps."
    )


def _post_process_workflow_bundle(workflows: list[dict]) -> list[dict]:
    """Validate and enrich each workflow with computed automation aggregates."""
    for wf in workflows:
        as_is_steps = wf.get("as_is_steps", []) or []
        valid_step_numbers = {s.get("step_number") for s in as_is_steps}

        automation = wf.get("automation") or {}
        scores = [s for s in (automation.get("step_scores") or []) if s.get("step_number") in valid_step_numbers]

        if scores:
            avg = sum(s.get("automation_score", 0) for s in scores) / len(scores)
            automatable = sum(1 for s in scores if s.get("automation_score", 0) >= 5)
            pct = round(automatable / len(scores) * 100)
        else:
            avg, pct = 0.0, 0

        wf["automation"] = {
            "step_scores":            scores,
            "average_score":          round(avg, 1),
            "automatable_percentage": pct,
            "overall_recommendation": automation.get("overall_recommendation", ""),
            "step_count":             len(scores),
        }
    return workflows


def generate_workflows(graph: dict, doc_text: str = "") -> list[dict]:
    """Single Sonnet call: returns workflows with embedded ROI and automation scoring.

    System prompt + tool schema are cached (ephemeral) — second 'Generate'
    within ~5 min skips re-encoding the static prefix.
    """
    prompt = _build_workflow_prompt(graph, doc_text)
    result = _call_tool(
        WORKFLOW_BUNDLE_SYSTEM,
        prompt,
        WORKFLOW_BUNDLE_TOOL,
        model=SONNET,
        max_tokens=32000,
        cache=True,
    )
    return _post_process_workflow_bundle(result.get("workflows", []))


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


def query_graph(graph: dict, question: str, doc_text: str = "", live_data_text: str = "") -> dict:
    node_lines = "\n".join(
        f"{n['id']} | {n['label']} | {n.get('type', '')}"
        for n in graph.get("nodes", [])
    )
    edge_lines = "\n".join(
        f"{e['id']} | {e.get('source', '')} --[{e.get('label', '')}]--> {e.get('target', '')}"
        for e in graph.get("edges", [])
    )
    doc_section = f"\n\n=== SOURCE DOCUMENT ===\n{doc_text[:3000]}\n===" if doc_text else ""
    live_section = (
        f"\n\n=== OPERATIONAL DATA (live, from production logs — use to ground answers about reality, "
        f"breach rates, who actually performed steps) ===\n{live_data_text[:3000]}\n==="
        if live_data_text else ""
    )
    prompt = (
        f"KNOWLEDGE GRAPH:\n\nNODES:\n{node_lines}\n\nEDGES:\n{edge_lines}"
        f"{doc_section}{live_section}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer based on the graph, document, and operational data when relevant. "
        "List the IDs of the most relevant nodes in relevant_node_ids and edges in relevant_edge_ids."
    )
    return _call_tool(NLQ_SYSTEM, prompt, NLQ_TOOL, model=HAIKU, max_tokens=800)
