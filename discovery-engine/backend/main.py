import hashlib
import os
import uuid
from pathlib import Path
from typing import List

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# find_dotenv() walks up from backend/ until it finds .env in discovery-engine/
_env_file = find_dotenv(usecwd=True) or str(Path(__file__).parent.parent / ".env")
load_dotenv(_env_file, override=True)

from document_parser import parse_document  # noqa: E402
from graph_extractor import extract_graphs, generate_object_model, generate_workflows, query_graph, generate_blueprint, generate_pulse_ai, run_conformance_analysis, generate_cross_doc_insights, generate_pm_optimise  # noqa: E402
import db  # noqa: E402
import seed_db  # noqa: E402
import demo_cache  # noqa: E402  # disk-persisted cache for repeat demos
import report as report_builder  # noqa: E402

# Auto-seed local SQLite demo DB on startup. Idempotent — no-op when already seeded.
try:
    seed_db.seed_if_needed()
except Exception as _seed_err:
    import sys
    print(f"[seed_db] WARNING: failed to seed demo DB: {_seed_err}", file=sys.stderr)

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
_doc_sources_store:  dict[str, list] = {}  # graph_id    -> [{filename, word_count}]
_cross_doc_store:    dict[str, dict] = {}  # graph_id    -> cross-doc insights result

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

    # Validate / fill the per-node `sources` field. Claude is instructed to set
    # it but we defensively cap to the actual filenames the user uploaded.
    valid_filenames = [name for name, _ in documents]
    valid_set = set(valid_filenames)
    for n in graph.get("nodes", []):
        srcs = n.get("sources") or []
        cleaned = [s for s in srcs if s in valid_set]
        if not cleaned:
            cleaned = valid_filenames[:1]   # fallback to first/only filename
        n["sources"] = cleaned

    graph_id = str(uuid.uuid4())
    doc_hash = hashlib.sha256(b"".join(raw_contents)).hexdigest()
    _graph_store[graph_id] = graph
    _doc_store[graph_id]   = "\n\n".join(t for _, t in documents)[:15_000]
    _hash_store[graph_id]  = doc_hash
    _doc_sources_store[graph_id] = [
        {"filename": name, "word_count": len(text.split())}
        for name, text in documents
    ]
    graph["graph_id"] = graph_id

    return graph


@app.get("/api/report/{graph_id}", response_class=HTMLResponse)
async def executive_report(graph_id: str) -> HTMLResponse:
    """Self-contained, print-styled HTML executive report for the graph.

    Pulls from existing in-memory stores and (when seeded) the SQLite demo DB
    — no new LLM calls. Open in a new tab; users save to PDF via browser print.
    Sections render conditionally based on what features have been run.
    """
    graph = _graph_store.get(graph_id)
    if not graph:
        html = report_builder._error_page(
            "Report unavailable",
            f"No graph for id {graph_id[:8]}…. Upload a document and try again.",
        )
        return HTMLResponse(content=html, status_code=404)

    gap        = _gap_store.get(graph_id)
    blueprint  = _blueprint_store.get(graph_id)
    sources    = _doc_sources_store.get(graph_id)
    cross_doc  = _cross_doc_store.get(graph_id)
    object_model = _object_model_store.get(graph_id)
    optimise   = _pm_optimise_store.get(graph_id)

    # Latest conformance result for this graph (if any)
    eid = _conformance_latest.get(graph_id)
    conformance = _conformance_store.get(eid) if eid else None

    # Process Mining data — pure SQL aggregation over the seeded SQLite DB.
    # Same call the /api/process-mining/{graph_id} endpoint uses.
    pm = None
    try:
        snapshot = _compute_process_mining()
        if not snapshot.get("unseeded") and not snapshot.get("error"):
            pm = snapshot
    except Exception:
        pm = None

    html = report_builder.render_report(
        graph_id,
        graph=graph,
        pm=pm,
        gap=gap,
        blueprint=blueprint,
        conformance=conformance,
        cross_doc=cross_doc,
        sources=sources,
        object_model=object_model,
        optimise=optimise,
    )
    return HTMLResponse(content=html)


@app.get("/api/graph/{graph_id}/sources")
async def graph_sources(graph_id: str):
    """List the documents that contributed to this graph."""
    sources = _doc_sources_store.get(graph_id)
    if sources is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    return {"graph_id": graph_id, "documents": sources}


@app.post("/api/graph/{graph_id}/cross-doc-insights")
async def cross_doc_insights_endpoint(graph_id: str):
    """One Haiku call that surfaces cross-document gaps / inconsistencies.
    Cached per graph_id (session) and by doc_hash (cross-session, on disk).
    400s when fewer than 2 source documents."""
    if graph_id in _cross_doc_store:
        return _cross_doc_store[graph_id]
    graph = _graph_store.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    sources = _doc_sources_store.get(graph_id, [])
    if len(sources) < 2:
        raise HTTPException(status_code=400, detail="Cross-document insights require 2+ source documents")

    doc_hash = _hash_store.get(graph_id)
    disk_cached = demo_cache.get(doc_hash, "cross_doc") if doc_hash else None
    if disk_cached is not None:
        _cross_doc_store[graph_id] = disk_cached
        return disk_cached

    try:
        result = generate_cross_doc_insights(graph, [s["filename"] for s in sources])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {e}")
    _cross_doc_store[graph_id] = result
    if doc_hash:
        demo_cache.put(doc_hash, "cross_doc", result)
    return result


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

    # Cross-session cache (in-memory + disk): same document uploaded again
    doc_hash = _hash_store.get(payload.graph_id)
    if doc_hash and doc_hash in _workflow_cache:
        workflows = _workflow_cache[doc_hash]
        _workflow_store[payload.graph_id] = workflows
        return {"workflows": workflows}
    cached = demo_cache.get(doc_hash, "workflows") if doc_hash else None
    if cached is not None and doc_hash:
        _workflow_cache[doc_hash] = cached
        _workflow_store[payload.graph_id] = cached
        return {"workflows": cached}

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
        # Validate variant.node_ids and enrich with live SQLite data.
        for v in (wf.get("variants") or []):
            v["node_ids"] = [nid for nid in (v.get("node_ids") or []) if nid in valid_ids]
        _enrich_variants_with_live_data(wf)

    if doc_hash:
        _workflow_cache[doc_hash] = workflows
        demo_cache.put(doc_hash, "workflows", workflows)
    _workflow_store[payload.graph_id] = workflows
    return {"workflows": workflows}


@app.get("/api/workflows/{graph_id}")
async def get_workflows(graph_id: str):
    """Return previously generated workflows for a graph."""
    if graph_id not in _workflow_store:
        raise HTTPException(status_code=404, detail="No workflows for this graph")
    return {"workflows": _workflow_store[graph_id]}


@app.post("/api/generate-object-model")
async def object_model_endpoint(payload: GraphPayload, force: bool = False):
    """Generate Pydantic models and JSON Schema from an extracted knowledge graph.
    Cached by graph_id (same session) and by doc_hash (cross-session, on disk).
    Pass ?force=true to bust both caches and re-run the Sonnet call."""
    if force and payload.graph_id:
        _object_model_store.pop(payload.graph_id, None)
        doc_hash = _hash_store.get(payload.graph_id)
        if doc_hash:
            demo_cache.invalidate(doc_hash, "object_model")

    if payload.graph_id and payload.graph_id in _object_model_store:
        return _object_model_store[payload.graph_id]

    doc_hash = _hash_store.get(payload.graph_id) if payload.graph_id else None
    cached = demo_cache.get(doc_hash, "object_model") if doc_hash else None
    if cached is not None:
        if payload.graph_id:
            _object_model_store[payload.graph_id] = cached
        return cached

    try:
        result = generate_object_model(payload.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object model generation failed: {e}")
    if payload.graph_id:
        _object_model_store[payload.graph_id] = result
    if doc_hash:
        demo_cache.put(doc_hash, "object_model", result)
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

    # Build a compact operational-data context from the local SQLite demo DB so
    # the NLQ can ground answers in actual breach rates / who-actually-did-what.
    try:
        live_data_text = _build_live_nlq_context()
    except Exception:
        live_data_text = ""

    try:
        result = query_graph(graph, payload.question, doc_text, live_data_text)
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
    """Generate AI blueprint from gap analysis — Claude call, cached by doc_hash."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    gap = _gap_store.get(payload.graph_id)
    if not gap:
        raise HTTPException(status_code=404, detail="Gap analysis not found — run calculate first")

    is_regen = payload.gap_analysis_id.endswith(":regen")

    # Same-session cache
    cached = _blueprint_store.get(payload.graph_id)
    if cached and not is_regen:
        return cached

    # Cross-session cache
    doc_hash = _hash_store.get(payload.graph_id)
    disk_cached = demo_cache.get(doc_hash, "blueprint") if doc_hash and not is_regen else None
    if disk_cached is not None:
        _blueprint_store[payload.graph_id] = disk_cached
        return disk_cached

    try:
        result = generate_blueprint(graph, gap)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blueprint generation failed: {e}")
    _blueprint_store[payload.graph_id] = result
    if doc_hash:
        demo_cache.put(doc_hash, "blueprint", result)
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
    """Generate AI strategic recommendations — Claude call, cached by doc_hash."""
    graph = _graph_store.get(payload.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    pulse = _pulse_store.get(payload.graph_id)
    if not pulse:
        raise HTTPException(status_code=404, detail="Run /api/pulse/calculate first")

    cached = _pulse_ai_store.get(payload.graph_id)
    if cached:
        return cached

    doc_hash = _hash_store.get(payload.graph_id)
    disk_cached = demo_cache.get(doc_hash, "pulse_ai") if doc_hash else None
    if disk_cached is not None:
        _pulse_ai_store[payload.graph_id] = disk_cached
        return disk_cached

    try:
        result = generate_pulse_ai(graph, pulse.get("items", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pulse AI failed: {e}")
    _pulse_ai_store[payload.graph_id] = result
    if doc_hash:
        demo_cache.put(doc_hash, "pulse_ai", result)
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
    return {
        "status":          "ok",
        "neo4j_enabled":   ENABLE_NEO4J,
        "demo_db_seeded":  db.has_table("process_steps") and db.row_count("process_steps") > 0,
        "demo_cache":      demo_cache.stats(),
    }


# ── SQLite-backed demo data endpoints ───────────────────────────────────────
# Read-only views over the banking demo data seeded via backend/seed_db.py.

def _parse_iso(ts):
    """Parse a SQLite ISO timestamp string to datetime; return None on failure.

    SQLite's `datetime('now', ...)` returns 'YYYY-MM-DD HH:MM:SS' (no T, no tz).
    `datetime.fromisoformat` handles this in Python 3.11+.
    """
    if not ts:
        return None
    from datetime import datetime
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _match_live_step_for_name(name: str) -> dict | None:
    """Find the live SQLite process_steps row whose step_name matches `name`.

    Match strategy: case-insensitive exact, then substring fallback. Returns the
    full step row plus computed live stats (breach_count, breach_rate_pct,
    role_mismatch_count, etc.) — same shape as /api/data/step/{step_name}.
    """
    if not name:
        return None
    if not (db.has_table("process_steps") and db.row_count("process_steps") > 0):
        return None
    try:
        cfg_rows = db.query("SELECT * FROM process_steps")
    except Exception:
        return None

    target = name.strip().lower()
    matched_cfg = None
    for r in cfg_rows:
        if (r.get("step_name") or "").strip().lower() == target:
            matched_cfg = r
            break
    if matched_cfg is None:
        for r in cfg_rows:
            sn = (r.get("step_name") or "").strip().lower()
            if sn and (sn in target or target in sn):
                matched_cfg = r
                break
    if matched_cfg is None:
        return None

    try:
        execs = db.query("SELECT * FROM step_executions WHERE step_name = ?", (matched_cfg["step_name"],))
    except Exception:
        execs = []

    breached = sum(1 for e in execs if e.get("status") == "breached")
    role_mismatch = sum(
        1 for e in execs
        if e.get("actual_role") and e.get("actual_role") != matched_cfg.get("expected_role")
    )
    total = len(execs)
    return {
        **matched_cfg,
        "execution_count":     total,
        "breach_count":        breached,
        "breach_rate_pct":     round(breached / total * 100, 1) if total else 0.0,
        "role_mismatch_count": role_mismatch,
    }


def _enrich_variants_with_live_data(workflow: dict) -> None:
    """Annotate each variant with data_source ('live' | 'estimated') and, when live,
    expose the actual breach rate from SQLite alongside Claude's frequency_pct.

    Does NOT mutate frequency_pct (would break sum-to-100). Frontend can show both
    figures so the customer sees Claude estimate vs operational reality.
    """
    for v in (workflow.get("variants") or []):
        div = (v.get("divergence_point") or "").strip()
        if not div:
            # Variant A baseline — no divergence step to look up.
            v["data_source"] = "estimated"
            continue
        live = _match_live_step_for_name(div)
        if live and live.get("execution_count"):
            v["data_source"] = "live"
            v["live_breach_rate_pct"] = live.get("breach_rate_pct")
            v["live_step_name"]       = live.get("step_name")
        else:
            v["data_source"] = "estimated"


def _build_live_nlq_context() -> str:
    """Return a compact text summary of the SQLite demo DB for NLQ grounding.

    Empty string when the demo DB is missing or empty — the NLQ then falls
    back to graph + document only. Capped at a few hundred tokens.
    """
    if not (db.has_table("process_steps") and db.row_count("process_steps") > 0):
        return ""
    try:
        apps  = db.query("SELECT status, loan_amount_usd FROM loan_applications")
        steps = db.query("""
            SELECT ps.step_name, ps.expected_role, ps.expected_system, ps.sla_hours,
                   COUNT(se.id) AS execs,
                   SUM(CASE WHEN se.status = 'breached' THEN 1 ELSE 0 END) AS breaches,
                   SUM(CASE WHEN se.actual_role IS NOT NULL AND se.actual_role <> ps.expected_role THEN 1 ELSE 0 END) AS role_mismatches
            FROM process_steps ps
            LEFT JOIN step_executions se ON se.step_name = ps.step_name
            GROUP BY ps.step_name
        """)
    except Exception:
        return ""

    if not apps:
        return ""

    status_counts: dict[str, int] = {}
    total_amount = 0.0
    for a in apps:
        status_counts[a.get("status", "?")] = status_counts.get(a.get("status", "?"), 0) + 1
        try:
            total_amount += float(a.get("loan_amount_usd") or 0)
        except (TypeError, ValueError):
            pass

    lines = [f"{len(apps)} loan applications. Status: " +
             ", ".join(f"{v} {k}" for k, v in status_counts.items()) +
             f". Total value: ${total_amount:,.0f}."]
    for s in steps:
        if not s.get("execs"):
            continue
        bits = [f"{s['execs']} runs"]
        if s.get("breaches"):
            bits.append(f"{s['breaches']} SLA breaches")
        if s.get("role_mismatches"):
            bits.append(f"{s['role_mismatches']} done by wrong role (SOP says {s['expected_role']})")
        lines.append(f"- {s['step_name']} (SLA {s['sla_hours']}h): " + ", ".join(bits) + ".")
    return "\n".join(lines)


# ── Process Mining (Celonis-style) ──────────────────────────────────────────
# Pure SQL aggregation over process_steps + loan_applications + step_executions.
# No Claude calls; recomputes on every fetch (data is small — 71 rows).

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# AI-recommendation copy keyed by step_name. v1: static lookup; future: Haiku.
_PM_AI_RECOS: dict[str, str] = {
    "Underwriting Review":
        "Auto-route applications under $100k to Junior Underwriter — projected −1.4d median TAT.",
    "KYC Verification":
        "Pre-fetch sanctions/PEP results during application submission to cut wait by ~30%.",
    "Credit Check":
        "Cache credit-bureau pulls for 24h to avoid redundant queries on repeat applicants.",
    "Approval Decision":
        "Enforce role-based routing — only Credit Officers can decision; eliminates wrong-role events.",
    "Disbursement":
        "Batch core-banking transfers hourly to reduce per-application processing overhead.",
    "Post-Disbursement Audit":
        "Move from sample-based to risk-based audit — focus on >$1M loans.",
    "Application Submission":
        "Pre-validate required fields client-side to reduce return-for-correction loops.",
}


def _compute_process_mining(filters: dict | None = None) -> dict:
    """Aggregate process_steps + loan_applications + step_executions into a
    Celonis-style process-mining dataset: KPIs, activities (nodes), edges,
    variants, and conformance.

    Optional filters narrow the set of loan_applications considered:
        loan_types: list[str]  — keep apps whose loan_type is in this list
        statuses:   list[str]  — keep apps whose status   is in this list

    Returns a dict ready for JSON serialization. Empty dict if DB unseeded.
    """
    import statistics

    filters = filters or {}
    loan_types_filter = set(filters.get("loan_types") or [])
    statuses_filter   = set(filters.get("statuses") or [])

    if not (db.has_table("process_steps") and db.row_count("process_steps") > 0):
        return {"unseeded": True}

    try:
        cfg_rows = db.query("SELECT * FROM process_steps ORDER BY rowid")
        apps     = db.query("SELECT * FROM loan_applications")
        execs    = db.query("SELECT * FROM step_executions")
    except Exception as e:
        return {"error": f"Demo DB query failed: {e}"}

    if not cfg_rows or not apps:
        return {"unseeded": True}

    # Capture full universe before filtering — used for the available-filters
    # surface in the response and for the "n of total" indicator.
    all_loan_types: list[str] = sorted({str(a["loan_type"]) for a in apps if a.get("loan_type")})
    all_statuses:   list[str] = sorted({str(a["status"])    for a in apps if a.get("status")})
    total_unfiltered = len(apps)

    # Apply filters.
    if loan_types_filter:
        apps = [a for a in apps if a.get("loan_type") in loan_types_filter]
    if statuses_filter:
        apps = [a for a in apps if a.get("status") in statuses_filter]

    # Restrict executions to filtered apps so all downstream aggregates are coherent.
    if loan_types_filter or statuses_filter:
        kept_ids = {a["id"] for a in apps}
        execs = [e for e in execs if e.get("application_id") in kept_ids]

    if not apps:
        return {
            "filtered":          True,
            "filters_applied":   {"loan_types": sorted(loan_types_filter), "statuses": sorted(statuses_filter)},
            "filter_options":    {"loan_types": all_loan_types, "statuses": all_statuses},
            "total_unfiltered":  total_unfiltered,
            "kpis":         {"total_cases": 0, "total_activities": 0, "total_step_executions": 0,
                              "completed_cases": 0, "in_progress_cases": 0, "declined_cases": 0,
                              "median_tat_days": None, "breach_rate_pct": 0.0,
                              "role_mismatch_rate_pct": 0.0, "role_mismatch_total": 0,
                              "conformant_cases": 0, "deviating_cases": 0,
                              "bottleneck_step": None, "total_disbursed_usd": 0.0,
                              "avg_loan_usd": 0.0, "fitness": 0.0},
            "activities":   [], "edges": [], "variants": [],
            "conformance":  {"fitness": 0.0, "conformant_cases": 0, "deviating_cases": 0,
                              "deviation_patterns": [], "deviating_cases_top": []},
            "ai_recommendations": _PM_AI_RECOS,
        }

    canonical_order = [r["step_name"] for r in cfg_rows]
    step_index      = {sn: i for i, sn in enumerate(canonical_order)}
    cfg_by_name     = {r["step_name"]: r for r in cfg_rows}

    # ── group executions by application, sorted by started_at ──
    by_app: dict[str, list] = {}
    for e in execs:
        by_app.setdefault(e.get("application_id"), []).append(e)
    for k in by_app:
        by_app[k].sort(key=lambda e: e.get("started_at") or "")

    # ── KPIs ────────────────────────────────────────────────────
    status_counts: dict[str, int] = {}
    for a in apps:
        status_counts[a.get("status", "?")] = status_counts.get(a.get("status", "?"), 0) + 1

    cycle_days = []
    for a in apps:
        if a.get("status") != "disbursed":
            continue
        app_execs = by_app.get(a["id"], [])
        if not app_execs:
            continue
        s_dt = _parse_iso(app_execs[0].get("started_at"))
        completed_ts = [_parse_iso(e.get("completed_at")) for e in app_execs if e.get("completed_at")]
        completed_ts = [t for t in completed_ts if t]
        if s_dt and completed_ts:
            cycle_days.append((max(completed_ts) - s_dt).total_seconds() / 86400)
    median_tat = round(statistics.median(cycle_days), 1) if cycle_days else None

    breached_n = sum(1 for e in execs if e.get("status") == "breached")
    finished_n = sum(1 for e in execs if e.get("status") in ("completed", "breached"))
    breach_rate_pct = round(breached_n / finished_n * 100, 1) if finished_n else 0.0

    # ── Activities ──────────────────────────────────────────────
    activities = []
    for i, cfg in enumerate(cfg_rows):
        sn = cfg["step_name"]
        step_execs = [e for e in execs if e.get("step_name") == sn]
        case_count = len({e.get("application_id") for e in step_execs})
        breach_count = sum(1 for e in step_execs if e.get("status") == "breached")
        role_mismatch = sum(
            1 for e in step_execs
            if e.get("actual_role") and e.get("actual_role") != cfg.get("expected_role")
        )

        dwell_hours = []
        for e in step_execs:
            s_dt = _parse_iso(e.get("started_at"))
            c_dt = _parse_iso(e.get("completed_at"))
            if s_dt and c_dt:
                dwell_hours.append((c_dt - s_dt).total_seconds() / 3600)
        median_dwell = round(statistics.median(dwell_hours), 1) if dwell_hours else None

        sla = cfg.get("sla_hours") or 0
        # Bottleneck flag deferred — set after we've seen all activities so we
        # can pick the single most problematic step rather than every step
        # whose dwell happens to exceed SLA.
        is_exception  = breach_count >= 2 or role_mismatch >= 1

        activities.append({
            "id":               sn,
            "label":            sn,
            "expected_role":    cfg.get("expected_role"),
            "expected_system":  cfg.get("expected_system"),
            "sla_hours":        sla,
            "case_count":       case_count,
            "exec_count":       len(step_execs),
            "breach_count":     breach_count,
            "role_mismatch_count": role_mismatch,
            "median_dwell_hours": median_dwell,
            "dwell_samples":    [round(d, 2) for d in dwell_hours],
            "is_bottleneck":    False,
            "is_exception":     is_exception,
            "x":                80 + i * 200,
            "y":                60,
            "width":            168,
            "height":           64,
        })

    # Pick the single most-problematic activity as the bottleneck:
    # priority = breach_count, role_mismatch_count, then dwell/SLA ratio.
    def _pm_problem_score(a: dict) -> tuple:
        ratio = ((a["median_dwell_hours"] or 0) / a["sla_hours"]) if a["sla_hours"] else 0
        return (a["breach_count"], a["role_mismatch_count"], ratio)
    if activities:
        worst = max(activities, key=_pm_problem_score)
        if _pm_problem_score(worst) > (0, 0, 0.95):
            worst["is_bottleneck"] = True

    # ── Edges (transitions) ─────────────────────────────────────
    edge_acc: dict[tuple, dict] = {}
    for app_id, app_execs in by_app.items():
        for a, b in zip(app_execs, app_execs[1:]):
            sa = a.get("step_name"); sb = b.get("step_name")
            if not sa or not sb:
                continue
            key = (sa, sb)
            entry = edge_acc.setdefault(key, {"cases": 0, "transitions": []})
            entry["cases"] += 1
            t1 = _parse_iso(a.get("completed_at")) or _parse_iso(a.get("started_at"))
            t2 = _parse_iso(b.get("started_at"))
            if t1 and t2:
                # Clamp to ≥0 — seed dates can overlap (parallel-running steps);
                # negative transition time is nonsensical to surface in UI.
                entry["transitions"].append(max(0.0, (t2 - t1).total_seconds() / 3600))

    edges = []
    for (sa, sb), entry in edge_acc.items():
        med = round(statistics.median(entry["transitions"]), 1) if entry["transitions"] else None
        ia = step_index.get(sa, -1)
        ib = step_index.get(sb, -1)
        is_rework = (sa == sb) or (ia >= 0 and ib >= 0 and ib < ia)
        is_slow   = bool(med and med > 24)
        edges.append({
            "from": sa, "to": sb,
            "cases": entry["cases"],
            "median_transition_hours": med,
            "is_slow":   is_slow,
            "is_rework": is_rework,
        })
    edges.sort(key=lambda e: -e["cases"])

    # ── Variants (unique step sequences per app) ────────────────
    seq_to_apps: dict[tuple, list] = {}
    for a in apps:
        app_execs = by_app.get(a["id"], [])
        seen = []
        seq = []
        for e in app_execs:
            sn = e.get("step_name")
            if sn and sn not in seen:
                seen.append(sn)
                seq.append(sn)
        seq_to_apps.setdefault(tuple(seq), []).append(a)

    total_apps = len(apps)
    variants = []
    for seq, app_list in seq_to_apps.items():
        # Sequence is conformant if it's a prefix of canonical order.
        is_canonical_prefix = list(seq) == canonical_order[:len(seq)]
        # Per-case conformance: all executions completed/in-progress, no role mismatch, no breach, no skip
        conformant_count = 0
        for a in app_list:
            ok = True
            for e in by_app.get(a["id"], []):
                if e.get("status") in ("breached", "skipped"):
                    ok = False; break
                cfg = cfg_by_name.get(e.get("step_name") or "")
                if cfg and e.get("actual_role") and e.get("actual_role") != cfg.get("expected_role"):
                    ok = False; break
            if ok and is_canonical_prefix:
                conformant_count += 1
        median_tat_v = None
        durs = []
        for a in app_list:
            ee = by_app.get(a["id"], [])
            if not ee: continue
            s_dt = _parse_iso(ee[0].get("started_at"))
            ct = [_parse_iso(e.get("completed_at")) for e in ee if e.get("completed_at")]
            ct = [t for t in ct if t]
            if s_dt and ct:
                durs.append((max(ct) - s_dt).total_seconds() / 86400)
        if durs:
            median_tat_v = round(statistics.median(durs), 1)

        variants.append({
            "steps":            list(seq),
            "case_count":       len(app_list),
            "frequency_pct":    round(len(app_list) / total_apps * 100, 1) if total_apps else 0.0,
            "median_tat_days":  median_tat_v,
            "is_conformant":    is_canonical_prefix and conformant_count == len(app_list),
            "conformant_count": conformant_count,
            "deviating_count":  len(app_list) - conformant_count,
            "deviation_note":   None if is_canonical_prefix else "Non-canonical sequence",
            "case_ids":         [a["id"] for a in app_list],
            "applicants":       [a.get("applicant_name") for a in app_list],
        })
    variants.sort(key=lambda v: -v["case_count"])
    for i, v in enumerate(variants):
        v["id"]   = f"v{i+1}"
        v["rank"] = i + 1

    # ── Conformance: deviation patterns + top deviating cases ───
    pattern_acc: dict[tuple, int] = {}  # (label, severity) -> count
    case_devs: dict[str, list] = {}     # app_id -> list of (severity, label)

    for e in execs:
        sn = e.get("step_name") or ""
        cfg = cfg_by_name.get(sn) or {}
        app_id = e.get("application_id") or ""
        if not app_id:
            continue
        # Wrong-role
        ar = e.get("actual_role")
        if ar and cfg.get("expected_role") and ar != cfg["expected_role"]:
            label = f"Wrong-role {sn}"
            pattern_acc[(label, "high")] = pattern_acc.get((label, "high"), 0) + 1
            case_devs.setdefault(app_id, []).append(("high", label))
        # Skipped
        if e.get("status") == "skipped":
            sev = "critical" if sn in ("Underwriting Review", "KYC Verification", "Credit Check") else "high"
            label = f"Skipped {sn}"
            pattern_acc[(label, sev)] = pattern_acc.get((label, sev), 0) + 1
            case_devs.setdefault(app_id, []).append((sev, label))
        # SLA breach
        if e.get("status") == "breached":
            label = f"SLA-breached {sn}"
            pattern_acc[(label, "medium")] = pattern_acc.get((label, "medium"), 0) + 1
            case_devs.setdefault(app_id, []).append(("medium", label))

    # Detect SOP-skipped activities (canonical step not executed at all
    # before the app's furthest-progressed step) and out-of-sequence steps
    # (executed in a different order than the SOP defines).
    for a in apps:
        app_id = a["id"]
        app_execs = by_app.get(app_id, [])
        if not app_execs:
            continue
        # Set of executed step names + ordered seq by started_at
        executed_set = set()
        ordered_seq = []
        for e in app_execs:
            sn = e.get("step_name")
            if sn and sn not in executed_set:
                executed_set.add(sn)
                ordered_seq.append(sn)
        # Furthest canonical index this app has reached
        canonical_indices = [step_index[sn] for sn in executed_set if sn in step_index]
        if not canonical_indices:
            continue
        max_idx = max(canonical_indices)
        # Skipped: any canonical step between 0..max_idx not in executed_set
        for i in range(max_idx):
            cname = canonical_order[i]
            if cname not in executed_set:
                sev = "critical" if cname in ("Underwriting Review", "KYC Verification", "Credit Check") else "high"
                label = f"Skipped {cname}"
                pattern_acc[(label, sev)] = pattern_acc.get((label, sev), 0) + 1
                case_devs.setdefault(app_id, []).append((sev, label))
        # Out-of-sequence: executed_seq differs from canonical-sorted-by-index
        executed_canonical_sorted = sorted(
            (sn for sn in ordered_seq if sn in step_index),
            key=lambda sn: step_index[sn],
        )
        executed_in_canonical_order = [sn for sn in ordered_seq if sn in step_index]
        if executed_in_canonical_order != executed_canonical_sorted:
            label = "Out-of-sequence steps"
            pattern_acc[(label, "high")] = pattern_acc.get((label, "high"), 0) + 1
            case_devs.setdefault(app_id, []).append(("high", label))

    deviation_patterns = sorted(
        [{"label": lbl, "severity": sev, "case_count": n}
         for (lbl, sev), n in pattern_acc.items()],
        key=lambda d: (_SEVERITY_ORDER.get(d["severity"], 9), -d["case_count"]),
    )

    # Top deviating cases — pick worst severity per case, sort by severity then start desc
    apps_by_id = {a["id"]: a for a in apps}
    deviating_cases_top = []
    for app_id, devs in case_devs.items():
        if not devs:
            continue
        devs.sort(key=lambda x: _SEVERITY_ORDER.get(x[0], 9))
        worst_sev, worst_label = devs[0]
        a = apps_by_id.get(app_id) or {}
        first_exec = (by_app.get(app_id) or [{}])[0]
        s_dt = _parse_iso(first_exec.get("started_at"))
        ct = [_parse_iso(e.get("completed_at")) for e in by_app.get(app_id, []) if e.get("completed_at")]
        ct = [t for t in ct if t]
        tat_days = round((max(ct) - s_dt).total_seconds() / 86400, 1) if (s_dt and ct) else None
        deviating_cases_top.append({
            "case_id":    app_id,
            "applicant":  a.get("applicant_name"),
            "loan_type":  a.get("loan_type"),
            "amount_usd": a.get("loan_amount_usd"),
            "deviation":  worst_label,
            "started_at": (first_exec.get("started_at") or "")[:10],
            "tat_days":   tat_days,
            "severity":   worst_sev,
            "all_deviations": [d[1] for d in devs],
        })
    deviating_cases_top.sort(
        key=lambda c: (_SEVERITY_ORDER.get(c["severity"], 9), -(c["tat_days"] or 0))
    )

    deviating_cases = len(case_devs)
    conformant_cases = total_apps - deviating_cases
    fitness = round(conformant_cases / total_apps, 2) if total_apps else 0.0

    # Loan-amount aggregates (from disbursed apps only — declined/in-progress
    # don't reflect actual portfolio value).
    disbursed_amounts = [
        float(a.get("loan_amount_usd") or 0)
        for a in apps if a.get("status") == "disbursed"
    ]
    total_disbursed_usd = round(sum(disbursed_amounts), 2)
    avg_loan_usd = round(sum(disbursed_amounts) / len(disbursed_amounts), 2) if disbursed_amounts else 0.0

    # Role-mismatch rate across all completed/breached executions.
    role_mismatch_total = sum(a["role_mismatch_count"] for a in activities)
    role_mismatch_rate_pct = (
        round(role_mismatch_total / finished_n * 100, 1) if finished_n else 0.0
    )

    return {
        "kpis": {
            "total_cases":           total_apps,
            "completed_cases":       status_counts.get("disbursed", 0),
            "in_progress_cases":     status_counts.get("pending", 0) + status_counts.get("underwriting", 0),
            "declined_cases":        status_counts.get("declined", 0),
            "median_tat_days":       median_tat,
            "breach_rate_pct":       breach_rate_pct,
            "role_mismatch_rate_pct": role_mismatch_rate_pct,
            "role_mismatch_total":   role_mismatch_total,
            "total_step_executions": len(execs),
            "total_activities":      len(activities),
            "conformant_cases":      conformant_cases,
            "deviating_cases":       deviating_cases,
            "bottleneck_step":       next((a["id"] for a in activities if a["is_bottleneck"]), None),
            "total_disbursed_usd":   total_disbursed_usd,
            "avg_loan_usd":          avg_loan_usd,
            "fitness":               fitness,
        },
        "activities": activities,
        "edges":      edges,
        "variants":   variants,
        "conformance": {
            "fitness":            fitness,
            "conformant_cases":   conformant_cases,
            "deviating_cases":    deviating_cases,
            "deviation_patterns": deviation_patterns,
            "deviating_cases_top": deviating_cases_top[:10],
        },
        "ai_recommendations": _PM_AI_RECOS,
        "filter_options":     {"loan_types": all_loan_types, "statuses": all_statuses},
        "filters_applied":    {"loan_types": sorted(loan_types_filter), "statuses": sorted(statuses_filter)},
        "total_unfiltered":   total_unfiltered,
        "filtered":           bool(loan_types_filter or statuses_filter),
    }


@app.get("/api/process-mining/{graph_id}")
async def process_mining_endpoint(
    graph_id: str,
    loan_types: str | None = None,
    statuses:   str | None = None,
):
    """Celonis-style process mining over the seeded SQLite operational data.

    Requires a graph_id to anchor the call (the demo data is global, but we
    gate on a graph existing so the customer has uploaded a doc first).

    Optional comma-separated filter params:
      ?loan_types=Commercial,Retail
      ?statuses=disbursed,underwriting
    """
    if graph_id not in _graph_store:
        raise HTTPException(status_code=404, detail="Graph not found")
    filters = {
        "loan_types": [s.strip() for s in (loan_types or "").split(",") if s.strip()],
        "statuses":   [s.strip() for s in (statuses   or "").split(",") if s.strip()],
    }
    try:
        return _compute_process_mining(filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process mining failed: {e}")


_pm_optimise_store: dict[str, dict] = {}  # graph_id -> Haiku optimise result


@app.post("/api/process-mining/{graph_id}/optimise")
async def process_mining_optimise(graph_id: str):
    """Haiku-powered optimisation suggestions over the current PM snapshot."""
    if graph_id not in _graph_store:
        raise HTTPException(status_code=404, detail="Graph not found")
    if graph_id in _pm_optimise_store:
        return _pm_optimise_store[graph_id]
    try:
        snapshot = _compute_process_mining()
        if snapshot.get("unseeded") or snapshot.get("error"):
            raise HTTPException(status_code=409, detail="Process-mining data unavailable")
        result = generate_pm_optimise(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimise generation failed: {e}")
    _pm_optimise_store[graph_id] = result
    return result


@app.post("/api/data/summary")
async def data_summary():
    """Aggregate banking-loan operations stats from the local SQLite demo DB.

    Returns totals, status breakdown, average end-to-end cycle time on
    disbursed loans, and the steps with the most SLA breaches.
    """
    try:
        apps  = db.query("SELECT * FROM loan_applications")
        execs = db.query("SELECT * FROM step_executions")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Demo DB query failed: {e}")

    total_apps    = len(apps)
    status_counts: dict[str, int] = {}
    total_amount  = 0.0
    for a in apps:
        s = a.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
        try:
            total_amount += float(a.get("loan_amount_usd") or 0)
        except (TypeError, ValueError):
            pass

    # End-to-end cycle time: first-step started_at → Disbursement completed_at, on disbursed apps.
    by_app: dict[str, list] = {}
    for e in execs:
        by_app.setdefault(e.get("application_id"), []).append(e)

    cycle_hours = []
    disbursed_ids = {a["id"] for a in apps if a.get("status") == "disbursed"}
    for app_id, app_execs in by_app.items():
        if app_id not in disbursed_ids:
            continue
        starts = [e for e in app_execs if e.get("step_name") == "Application Submission"]
        ends   = [e for e in app_execs if e.get("step_name") == "Disbursement" and e.get("completed_at")]
        if not starts or not ends:
            continue
        s_dt = _parse_iso(starts[0].get("started_at"))
        e_dt = _parse_iso(ends[0].get("completed_at"))
        if s_dt and e_dt:
            cycle_hours.append((e_dt - s_dt).total_seconds() / 3600)

    avg_cycle = round(sum(cycle_hours) / len(cycle_hours), 1) if cycle_hours else None

    # Top SLA breaches by step
    breach_counts: dict[str, int] = {}
    for e in execs:
        if e.get("status") == "breached":
            sn = e.get("step_name", "")
            breach_counts[sn] = breach_counts.get(sn, 0) + 1
    top_breaches = sorted(breach_counts.items(), key=lambda kv: -kv[1])[:5]

    return {
        "total_applications":    total_apps,
        "total_amount_usd":      round(total_amount, 2),
        "status_breakdown":      status_counts,
        "avg_cycle_time_hours":  avg_cycle,
        "step_executions_total": len(execs),
        "top_breached_steps":    [{"step_name": k, "breach_count": v} for k, v in top_breaches],
    }


@app.get("/api/data/step/{step_name}")
async def step_reality(step_name: str):
    """Compare the SOP-defined step (process_steps) to its actual execution log.

    Returns expected role/system/SLA, actual execution stats, role and system
    distributions, and an SLA-breach rate. Same response shape as before.
    """
    try:
        cfg_rows  = db.query("SELECT * FROM process_steps   WHERE step_name = ?", (step_name,))
        exec_rows = db.query("SELECT * FROM step_executions WHERE step_name = ?", (step_name,))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Demo DB query failed: {e}")

    if not cfg_rows:
        raise HTTPException(status_code=404, detail=f"No process_steps row for step_name='{step_name}'")
    expected = cfg_rows[0]

    durations = []
    breached = 0
    completed = 0
    skipped = 0
    in_progress = 0
    role_counts:   dict[str, int] = {}
    system_counts: dict[str, int] = {}
    role_mismatch_count = 0
    system_mismatch_count = 0

    for e in exec_rows:
        status = e.get("status")
        if status == "completed":   completed += 1
        if status == "breached":    breached += 1
        if status == "skipped":     skipped += 1
        if status == "in_progress": in_progress += 1

        s_dt = _parse_iso(e.get("started_at"))
        e_dt = _parse_iso(e.get("completed_at"))
        if s_dt and e_dt:
            durations.append((e_dt - s_dt).total_seconds() / 3600)

        actual_role = e.get("actual_role")
        if actual_role:
            role_counts[actual_role] = role_counts.get(actual_role, 0) + 1
            if actual_role != expected.get("expected_role"):
                role_mismatch_count += 1

        actual_system = e.get("actual_system")
        if actual_system:
            system_counts[actual_system] = system_counts.get(actual_system, 0) + 1
            if actual_system != expected.get("expected_system"):
                system_mismatch_count += 1

    total = len(exec_rows)
    avg_duration = round(sum(durations) / len(durations), 1) if durations else None
    breach_rate  = round(breached / total * 100, 1) if total else 0.0

    return {
        "step_name":           step_name,
        "expected_role":       expected.get("expected_role"),
        "expected_system":     expected.get("expected_system"),
        "sla_hours":           expected.get("sla_hours"),
        "execution_count":     total,
        "completed_count":     completed,
        "breach_count":        breached,
        "skipped_count":       skipped,
        "in_progress_count":   in_progress,
        "breach_rate_pct":     breach_rate,
        "avg_duration_hours":  avg_duration,
        "role_mismatch_count":   role_mismatch_count,
        "system_mismatch_count": system_mismatch_count,
        "actual_roles":   sorted([{"role": r, "count": c} for r, c in role_counts.items()],     key=lambda x: -x["count"]),
        "actual_systems": sorted([{"system": s, "count": c} for s, c in system_counts.items()], key=lambda x: -x["count"]),
    }


# Serve frontend static files (JS, CSS) — must come after API routes
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
