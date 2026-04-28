import hashlib
import os
import uuid
from pathlib import Path
from typing import List

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# find_dotenv() walks up from backend/ until it finds .env in discovery-engine/
_env_file = find_dotenv(usecwd=True) or str(Path(__file__).parent.parent / ".env")
load_dotenv(_env_file, override=True)

from document_parser import parse_document  # noqa: E402
from graph_extractor import extract_graphs, generate_object_model, generate_workflows, query_graph, generate_blueprint, generate_pulse_ai, run_conformance_analysis  # noqa: E402

ENABLE_NEO4J = os.getenv("ENABLE_NEO4J", "false").lower() == "true"

_graph_store: dict[str, dict] = {}
_doc_store:   dict[str, str]  = {}
_workflow_store: dict[str, list] = {}
_query_history: dict[str, list] = {}
_gap_store: dict[str, dict] = {}
_blueprint_store:     dict[str, dict] = {}
_object_model_store: dict[str, dict] = {}
_pulse_store:        dict[str, dict] = {}
_pulse_ai_store:     dict[str, dict] = {}
_evidence_store:     dict[str, dict] = {}  # evidence_id -> {text, filename, word_count, graph_id}
_conformance_store:  dict[str, dict] = {}  # evidence_id -> full result
_conformance_latest: dict[str, str]  = {}  # graph_id    -> latest evidence_id
_hash_store:         dict[str, str]  = {}  # graph_id    -> doc_hash
_workflow_cache:     dict[str, list] = {}  # doc_hash    -> workflows (cross-session)

app = FastAPI(title="Metafore Discovery Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Parse uploaded documents and return an extracted knowledge graph."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    raw_contents: list[bytes] = []
    documents: list[tuple[str, str]] = []
    for f in files:
        content = await f.read()
        raw_contents.append(content)
        try:
            text = parse_document(f.filename or "document", content)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if not text.strip():
            raise HTTPException(status_code=422, detail=f"{f.filename} appears to be empty")
        documents.append((f.filename or "document", text))

    try:
        graph = extract_graphs(documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph extraction failed: {e}")

    if ENABLE_NEO4J:
        try:
            from neo4j_adapter import sync_graph
            neo4j_result = sync_graph(graph)
            graph["_neo4j"] = neo4j_result
        except Exception as e:
            graph["_neo4j_error"] = str(e)

    graph_id = str(uuid.uuid4())
    doc_hash = hashlib.sha256(b"".join(raw_contents)).hexdigest()
    _graph_store[graph_id] = graph
    _doc_store[graph_id]   = "\n\n".join(t for _, t in documents)[:15_000]
    _hash_store[graph_id]  = doc_hash
    graph["graph_id"] = graph_id

    return graph


class GraphPayload(BaseModel):
    nodes: list
    edges: list
    graph_id: str | None = None


class WorkflowRequest(BaseModel):
    graph_id: str


@app.post("/api/workflows/generate")
async def generate_workflows_endpoint(payload: WorkflowRequest):
    """Generate workflow suggestions — cached by document hash across sessions."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    # Same-session cache: graph_id already has workflows
    if payload.graph_id in _workflow_store:
        return {"workflows": _workflow_store[payload.graph_id]}

    # Cross-session cache: same document uploaded in a different session
    doc_hash = _hash_store.get(payload.graph_id)
    if doc_hash and doc_hash in _workflow_cache:
        workflows = _workflow_cache[doc_hash]
        _workflow_store[payload.graph_id] = workflows
        return {"workflows": workflows}

    doc_text = _doc_store.get(payload.graph_id, "")
    try:
        workflows = generate_workflows(graph, doc_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow generation failed: {e}")

    valid_ids = {n["id"] for n in graph.get("nodes", [])}
    for wf in workflows:
        wf["source_node_ids"] = [nid for nid in wf.get("source_node_ids", []) if nid in valid_ids]
        for step_list_key in ("as_is_steps", "to_be_steps"):
            for step in wf.get(step_list_key, []):
                for field in ("responsible_role", "system_used"):
                    ref = step.get(field, {})
                    if ref.get("node_id") and ref["node_id"] not in valid_ids:
                        ref["node_id"] = None
                        ref["node_label"] = None

    if doc_hash:
        _workflow_cache[doc_hash] = workflows
    _workflow_store[payload.graph_id] = workflows
    return {"workflows": workflows}


@app.get("/api/workflows/{graph_id}")
async def get_workflows(graph_id: str):
    """Return previously generated workflows for a graph."""
    if graph_id not in _workflow_store:
        raise HTTPException(status_code=404, detail="No workflows for this graph")
    return {"workflows": _workflow_store[graph_id]}


@app.post("/api/generate-object-model")
async def object_model_endpoint(payload: GraphPayload):
    """Generate Pydantic models and JSON Schema from an extracted knowledge graph."""
    if payload.graph_id and payload.graph_id in _object_model_store:
        return _object_model_store[payload.graph_id]
    try:
        result = generate_object_model(payload.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object model generation failed: {e}")
    if payload.graph_id:
        _object_model_store[payload.graph_id] = result
    return result


class NlqRequest(BaseModel):
    graph_id: str
    question: str


@app.post("/api/query/natural-language")
async def natural_language_query(payload: NlqRequest):
    """Answer a natural language question about an extracted knowledge graph."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(payload.question) > 500:
        raise HTTPException(status_code=400, detail="Question exceeds 500 characters")

    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    doc_text = _doc_store.get(payload.graph_id, "")

    try:
        result = query_graph(graph, payload.question, doc_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    valid_node_ids = {n["id"] for n in graph.get("nodes", [])}
    valid_edge_ids = {e["id"] for e in graph.get("edges", [])}
    result["relevant_node_ids"] = [nid for nid in result.get("relevant_node_ids", []) if nid in valid_node_ids]
    result["relevant_edge_ids"] = [eid for eid in result.get("relevant_edge_ids", []) if eid in valid_edge_ids]

    entry = {"question": payload.question, **result}
    if payload.graph_id not in _query_history:
        _query_history[payload.graph_id] = []
    _query_history[payload.graph_id].append(entry)

    return result


@app.get("/api/query/history/{graph_id}")
async def get_query_history(graph_id: str):
    """Return last 10 queries for a graph."""
    return {"history": _query_history.get(graph_id, [])[-10:]}


def _calculate_gap_analysis(graph: dict) -> dict:
    import datetime
    from collections import defaultdict

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = {n["id"] for n in nodes}

    adjacency: dict = defaultdict(list)
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        lbl = (e.get("label") or "").lower().replace(" ", "_").replace("-", "_")
        if src in node_ids:
            adjacency[src].append({"label": lbl, "dir": "out", "other": tgt})
        if tgt in node_ids:
            adjacency[tgt].append({"label": lbl, "dir": "in", "other": src})

    def edge_labels(nid: str) -> set:
        return {e["label"] for e in adjacency[nid]}

    process_nodes = [n for n in nodes if n.get("type") == "Process"]
    policy_nodes  = [n for n in nodes if n.get("type") == "Policy"]
    obj_nodes     = [n for n in nodes if n.get("type") == "Objective"]

    role_labels   = {"executed_by", "assigned_to", "performed_by"}
    system_labels = {"uses_system", "stores_in", "uses"}

    no_role       = [n for n in process_nodes if not (role_labels & edge_labels(n["id"]))]
    no_system     = [n for n in process_nodes if not (system_labels & edge_labels(n["id"]))]
    unlinked_pol  = [n for n in policy_nodes  if "governed_by" not in edge_labels(n["id"])]
    unmeasured    = [n for n in obj_nodes     if "achieves"    not in edge_labels(n["id"])]
    orphaned      = [n for n in nodes         if len(adjacency[n["id"]]) == 0]

    groups: dict = defaultdict(list)
    for n in nodes:
        groups[(n.get("label", "").lower().strip(), n.get("type", ""))].append(n)
    dup_nodes = [n for grp in groups.values() if len(grp) > 1 for n in grp]

    low_conf = [n for n in nodes if isinstance(n.get("confidence"), (int, float)) and n["confidence"] < 0.65]

    def make_check(check_id, severity, title, affected, recommendation):
        return {
            "check_id": check_id,
            "severity": severity,
            "title": title,
            "affected_node_ids":    [n["id"]            for n in affected],
            "affected_node_labels": [n.get("label", "") for n in affected],
            "count": len(affected),
            "recommendation": recommendation,
        }

    checks = [
        make_check("no_role", "critical",
                   "Processes with no assigned role", no_role,
                   "Assign a responsible Role to each process to establish ownership and accountability."),
        make_check("no_system", "warning",
                   "Processes with no system linked", no_system,
                   "Link each process to the system or tool used to execute it."),
        make_check("unlinked_policy", "critical",
                   "Policies not enforced by any process", unlinked_pol,
                   "Connect each policy to the processes it governs to ensure compliance coverage."),
        make_check("unmeasured_objective", "warning",
                   "Objectives with no contributing process", unmeasured,
                   "Link objectives to the processes that contribute to achieving them."),
        make_check("orphaned", "warning",
                   "Isolated nodes with no relationships", orphaned,
                   "Review these nodes — they may represent incomplete extraction or genuinely standalone concepts."),
        make_check("duplicates", "info",
                   "Possible duplicate nodes detected", dup_nodes,
                   "Review and merge duplicate nodes to avoid redundancy in the knowledge graph."),
        make_check("low_confidence", "info",
                   "Low confidence extractions", low_conf,
                   "Review these nodes — the extraction engine was uncertain. Verify against the source document."),
    ]

    score = 100
    deductions = {"critical": 20, "warning": 8, "info": 3}
    for c in checks:
        if c["count"] > 0:
            score -= deductions[c["severity"]]
    score = max(0, min(100, score))

    score_label = (
        "Excellent" if score >= 85 else
        "Good"      if score >= 70 else
        "Fair"      if score >= 50 else
        "Needs Work"
    )

    type_counts: dict = {}
    for n in nodes:
        t = n.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    total_degree = sum(len(adjacency[n["id"]]) for n in nodes)
    avg_conn = round(total_degree / len(nodes), 1) if nodes else 0.0

    return {
        "coverage_score":   score,
        "score_label":      score_label,
        "total_nodes":      len(nodes),
        "total_edges":      len(edges),
        "node_type_counts": type_counts,
        "avg_connections":  avg_conn,
        "checks":           checks,
        "calculated_at":    datetime.datetime.utcnow().isoformat() + "Z",
    }


class GapRequest(BaseModel):
    graph_id: str


class BlueprintRequest(BaseModel):
    graph_id: str
    gap_analysis_id: str


@app.post("/api/gap-analysis/calculate")
async def calculate_gap_analysis(payload: GapRequest):
    """Calculate gap analysis from graph structure — no Claude call."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    result = _calculate_gap_analysis(graph)
    result["graph_id"] = payload.graph_id
    _gap_store[payload.graph_id] = result
    return result


@app.post("/api/gap-analysis/blueprint")
async def generate_blueprint_endpoint(payload: BlueprintRequest):
    """Generate AI blueprint from gap analysis — one Claude call, cached."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    gap = _gap_store.get(payload.graph_id)
    if not gap:
        raise HTTPException(status_code=404, detail="Gap analysis not found — run calculate first")
    cached = _blueprint_store.get(payload.graph_id)
    if cached and not payload.gap_analysis_id.endswith(":regen"):
        return cached
    try:
        result = generate_blueprint(graph, gap)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blueprint generation failed: {e}")
    _blueprint_store[payload.graph_id] = result
    return result


def _calculate_pulse_items(graph: dict, gap: dict) -> list:
    CHECK_MAP = {
        "no_role":              ("critical", "NOW",       "Processes have no assigned owner — automation will fail without a responsible role."),
        "unlinked_policy":      ("critical", "NOW",       "Policies are not enforced by any process — compliance risk is unmitigated."),
        "no_system":            ("warning",  "THIS_WEEK", "Processes are not linked to a system — tooling gaps may block automation."),
        "unmeasured_objective": ("warning",  "THIS_WEEK", "Objectives have no contributing process — strategic goals cannot be tracked."),
        "orphaned":             ("warning",  "BACKLOG",   "Isolated nodes have no relationships — they may be incomplete or redundant."),
        "duplicates":           ("info",     "BACKLOG",   "Duplicate nodes detected — merge to keep the graph clean and unambiguous."),
        "low_confidence":       ("info",     "BACKLOG",   "Low-confidence extractions may be inaccurate — verify against the source."),
    }
    items = []
    for check in gap.get("checks", []):
        if check.get("count", 0) == 0:
            continue
        mapping = CHECK_MAP.get(check["check_id"])
        if not mapping:
            continue
        severity, category, description = mapping
        items.append({
            "id":                   f"pulse_{check['check_id']}",
            "check_id":             check["check_id"],
            "title":                check["title"],
            "description":          description,
            "severity":             severity,
            "category":             category,
            "affected_node_ids":    check["affected_node_ids"],
            "affected_node_labels": check["affected_node_labels"],
            "count":                check["count"],
            "recommendation":       check["recommendation"],
        })
    cat_order = {"NOW": 0, "THIS_WEEK": 1, "BACKLOG": 2}
    sev_order = {"critical": 0, "warning": 1, "info": 2}
    items.sort(key=lambda x: (cat_order.get(x["category"], 9), sev_order.get(x["severity"], 9)))
    return items


class PulseRequest(BaseModel):
    graph_id: str


@app.post("/api/pulse/calculate")
async def calculate_pulse(payload: PulseRequest):
    """Calculate rule-based pulse items from graph — no Claude call."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    gap = _gap_store.get(payload.graph_id)
    if not gap:
        gap = _calculate_gap_analysis(graph)
        gap["graph_id"] = payload.graph_id
        _gap_store[payload.graph_id] = gap
    items = _calculate_pulse_items(graph, gap)
    result = {"graph_id": payload.graph_id, "items": items, "total": len(items)}
    _pulse_store[payload.graph_id] = result
    return result


@app.post("/api/pulse/ai-recommendations")
async def pulse_ai_recommendations(payload: PulseRequest):
    """Generate AI strategic recommendations — one Claude call, cached."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    pulse = _pulse_store.get(payload.graph_id)
    if not pulse:
        raise HTTPException(status_code=404, detail="Run /api/pulse/calculate first")
    cached = _pulse_ai_store.get(payload.graph_id)
    if cached:
        return cached
    try:
        result = generate_pulse_ai(graph, pulse.get("items", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pulse AI failed: {e}")
    _pulse_ai_store[payload.graph_id] = result
    return result


@app.post("/conformance/upload")
async def conformance_upload(
    graph_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload an evidence document for conformance checking."""
    if not _graph_store.get(graph_id):
        raise HTTPException(status_code=404, detail="Graph not found")
    content = await file.read()
    try:
        text = parse_document(file.filename or "evidence", content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not text.strip():
        raise HTTPException(status_code=422, detail="Evidence document appears to be empty")
    word_count = len(text.split())
    evidence_id = str(uuid.uuid4())
    _evidence_store[evidence_id] = {
        "text":       text,
        "filename":   file.filename or "evidence",
        "word_count": word_count,
        "graph_id":   graph_id,
    }
    return {
        "evidence_id": evidence_id,
        "graph_id":    graph_id,
        "filename":    file.filename or "evidence",
        "word_count":  word_count,
        "status":      "ready",
    }


class ConformanceAnalyseRequest(BaseModel):
    graph_id:    str
    evidence_id: str


@app.post("/conformance/analyse")
async def conformance_analyse(payload: ConformanceAnalyseRequest):
    """Run Claude conformance analysis — one call, result cached against evidence_id."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    evidence = _evidence_store.get(payload.evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence document not found")

    try:
        raw = run_conformance_analysis(graph, evidence["text"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conformance analysis failed: {e}")

    # Validate node_ids
    valid_ids = {n["id"] for n in graph.get("nodes", [])}
    node_map  = {n["id"]: n for n in graph.get("nodes", [])}
    results   = [r for r in raw.get("conformance_results", []) if r["node_id"] in valid_ids]

    confirmed  = [r for r in results if r["status"] == "confirmed"]
    deviated   = [r for r in results if r["status"] == "deviated"]
    not_found  = [r for r in results if r["status"] == "not_found"]

    # Recalculate rate from validated results
    assessed = len(confirmed) + len(deviated)
    rate      = round(len(confirmed) / assessed * 100) if assessed else 0

    full_result = {
        "evidence_id":              payload.evidence_id,
        "graph_id":                 payload.graph_id,
        "filename":                 evidence["filename"],
        "conformance_results":      results,
        "overall_conformance_rate": rate,
        "summary":                  raw.get("summary", ""),
        "confirmed_count":          len(confirmed),
        "deviated_count":           len(deviated),
        "not_found_count":          len(not_found),
        "critical_deviations":      [r for r in deviated if r["node_type"] in ("Policy",)],
        "process_deviations":       [r for r in deviated if r["node_type"] in ("Process", "Role")],
    }
    _conformance_store[payload.evidence_id] = full_result
    _conformance_latest[payload.graph_id]   = payload.evidence_id
    return full_result


@app.get("/conformance/{graph_id}/latest")
async def conformance_latest(graph_id: str):
    """Return the most recent conformance result for a graph."""
    eid = _conformance_latest.get(graph_id)
    if not eid or eid not in _conformance_store:
        raise HTTPException(status_code=404, detail="No conformance result for this graph")
    return _conformance_store[eid]


@app.get("/api/health")
async def health():
    return {"status": "ok", "neo4j_enabled": ENABLE_NEO4J}


# Serve frontend static files (JS, CSS) — must come after API routes
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
