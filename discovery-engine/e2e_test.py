import requests, json, time, sys

BASE = "http://localhost:8083"
SOP  = "sample_docs/commercial_banking_loan_sop.docx"
AUDIT= "sample_docs/loan_audit_report.docx"

def ok(label, val):
    mark = "PASS" if val else "FAIL"
    print(f"  [{mark}]  {label}")
    if not val:
        sys.exit(1)

print("\n-- 1. UPLOAD (graph extraction) --")
with open(SOP, "rb") as f:
    r = requests.post(f"{BASE}/api/upload",
        files=[("files", (SOP, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
        timeout=120)
assert r.status_code == 200, f"Upload failed: {r.text}"
g = r.json()
graph_id = g.get("graph_id")
nodes    = len(g.get("nodes", []))
edges    = len(g.get("edges", []))
ok(f"graph_id present: {graph_id[:8]}...", bool(graph_id))
ok(f"nodes: {nodes}", nodes >= 5)
ok(f"edges: {edges}", edges >= 5)

print("\n-- 2. GAP ANALYSIS --")
r = requests.post(f"{BASE}/api/gap-analysis/calculate", json={"graph_id": graph_id}, timeout=30)
assert r.status_code == 200, r.text
gap   = r.json()
score = gap.get("coverage_score", 0)
checks= len(gap.get("checks", []))
ok(f"score: {score}", score > 0)
ok(f"checks: {checks}", checks > 0)

print("\n-- 3. BLUEPRINT --")
gap_id = gap.get("gap_analysis_id", "test")
r = requests.post(f"{BASE}/api/gap-analysis/blueprint",
    json={"graph_id": graph_id, "gap_analysis_id": gap_id}, timeout=60)
assert r.status_code == 200, r.text
bp = r.json()
ok(f"summary present", bool(bp.get("summary")))
ok(f"next_steps: {len(bp.get('next_steps', []))}", len(bp.get("next_steps", [])) > 0)

print("\n-- 4. PULSE --")
r = requests.post(f"{BASE}/api/pulse/calculate", json={"graph_id": graph_id}, timeout=30)
assert r.status_code == 200, r.text
pulse = r.json()
items = pulse.get("items", [])
ok(f"pulse items: {len(items)}", len(items) > 0)

print("\n-- 5. NLQ --")
r = requests.post(f"{BASE}/api/query/natural-language",
    json={"graph_id": graph_id, "question": "Who is responsible for AML screening?"}, timeout=30)
assert r.status_code == 200, r.text
nlq = r.json()
ok(f"answer present", bool(nlq.get("answer")))

print("\n-- 6. WORKFLOW GENERATION --")
t0 = time.time()
r = requests.post(f"{BASE}/api/workflows/generate", json={"graph_id": graph_id}, timeout=180)
elapsed = round(time.time() - t0, 1)
assert r.status_code == 200, r.text
wf = r.json()
workflows = wf.get("workflows", [])
ok(f"workflows: {len(workflows)} in {elapsed}s", len(workflows) >= 3)
if workflows:
    w = workflows[0]
    ok(f"as_is_steps: {len(w.get('as_is_steps', []))}", len(w.get("as_is_steps", [])) > 0)
    ok(f"to_be_steps: {len(w.get('to_be_steps', []))}", len(w.get("to_be_steps", [])) > 0)

print("\n-- 7. WORKFLOW CACHE (GET) --")
r2 = requests.get(f"{BASE}/api/workflows/{graph_id}", timeout=10)
cached = r2.json().get("workflows", [])
ok(f"GET returns stored workflows: {len(cached)}", len(cached) >= 3)
elapsed2 = 0

print("\n-- 8. OBJECT MODEL --")
r = requests.post(f"{BASE}/api/generate-object-model",
    json={"nodes": g["nodes"], "edges": g["edges"], "graph_id": graph_id}, timeout=120)
assert r.status_code == 200, r.text
om = r.json()
ok(f"pydantic_code present", bool(om.get("pydantic_code")))
ok(f"json_schema present",   bool(om.get("json_schema")))
ok(f"summary present",       bool(om.get("summary")))

print("\n-- 9. CONFORMANCE --")
with open(AUDIT, "rb") as f:
    r = requests.post(f"{BASE}/conformance/upload",
        data={"graph_id": graph_id},
        files={"file": (AUDIT, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        timeout=30)
assert r.status_code == 200, r.text
evidence_id = r.json().get("evidence_id")
ok(f"evidence_id: {evidence_id[:8]}...", bool(evidence_id))

r = requests.post(f"{BASE}/conformance/analyse",
    json={"graph_id": graph_id, "evidence_id": evidence_id}, timeout=120)
assert r.status_code == 200, r.text
conf      = r.json()
rate      = conf.get("overall_conformance_rate", 0)
confirmed = conf.get("confirmed_count", 0)
deviated  = conf.get("deviated_count", 0)
not_found = conf.get("not_found_count", 0)
ok(f"conformance_rate: {rate}%", rate > 0)
ok(f"confirmed: {confirmed}", confirmed > 0)
ok(f"deviated:  {deviated}",  deviated > 0)

print("\n========== SUMMARY ==========")
print(f"  Nodes={nodes}  Edges={edges}")
print(f"  Gap score={score}  Checks={checks}")
print(f"  Workflows={len(workflows)}  Cache hit={elapsed2}s")
print(f"  Object model: ok")
print(f"  Conformance={rate}  confirmed={confirmed}  deviated={deviated}  not_found={not_found}")
print("  All tests passed.")
