# Metafore Works — Discovery Engine

This file is read by Claude at the start of every session under this folder.
It captures all design decisions, architecture patterns, and setup steps for the Discovery Engine.

---

## Project Structure

```
[this folder]/
  START.bat                  ← double-click to launch (Windows)
  STOP.bat                   ← double-click to stop
  START.command              ← double-click to launch (Mac)
  STOP.command               ← double-click to stop (Mac)
  HOW_TO_RUN.html            ← visual guide for non-technical users
  ONBOARDING.md              ← setup guide for new machines (Windows + Mac)
  BRD_Discovery_Engine.docx  ← Business Requirements Document (generated)
  generate_brd_docx.py       ← script that generates the BRD docx
  ROOT_CLAUDE_METAFOREWORKS.md ← copy of root CLAUDE.md for colleague onboarding
  CLAUDE.md                  ← this file
  .claude/launch.json        ← preview_start config for Claude Code (port 8083)
  discovery-engine/
    .env                     ← API key (never commit)
    .env.example
    README.md
    backend/
      main.py                ← FastAPI app, all endpoints, in-memory stores
      graph_extractor.py     ← all Claude calls, tool schemas, prompts
      document_parser.py     ← PDF/DOCX/TXT parsing
      neo4j_adapter.py       ← optional Neo4j sync (disabled by default)
      requirements.txt
    frontend/
      index.html             ← full SPA shell, all panel HTML
      styles.css             ← all styles including feature panels
      app.js                 ← all frontend logic
      vis-network.min.js     ← self-hosted (do NOT switch back to CDN)
      vis-network.min.css    ← self-hosted
      fonts/                 ← GT America, IBM Plex Mono, Inter
      metafore-logo.png
      metafore-logo-horizontal.png
    samples/
      supply_chain_sop.txt
      hr_onboarding_policy.txt
    sample_docs/
      commercial_banking_loan_sop.docx  ← banking demo: upload for extraction
      loan_audit_report.docx            ← banking demo: upload for conformance
```

---

## Standing Operating Principles

1. **Do everything autonomously.** Never ask the user to run commands, move files, or edit configs manually.
2. **Use relative paths only.** Never hardcode machine-specific paths. Always derive paths from `__file__` in Python or `%~dp0` in batch files.
3. **Server port is 8083.** Always kill the existing process before restarting. Find PID with `netstat -ano | findstr :8083`, kill with `taskkill /PID <pid> /F`.
4. **Claude extraction uses tool use** — not raw JSON prompting. This guarantees valid structured output. Never revert to text/JSON prompt approach.
5. **vis-network is self-hosted.** Edge browser Tracking Prevention blocks unpkg.com CDN. Never switch back to CDN links.
6. **After changing .env, the server must be fully restarted.** `--reload` watches Python files only — it does NOT pick up new API keys from `.env`.
7. **Start server with `--app-dir`** — uvicorn must be launched with `--app-dir discovery-engine/backend` so it finds `main.py` regardless of working directory. Also use `--reload-dir` scoped to the backend only.

---

## How to Start the App

### Windows (preferred)
Double-click `START.bat` — it handles Python check, package install, port cleanup, and browser open.

### Mac (preferred)
Double-click `START.command` — same behaviour as START.bat but for Mac.
First run only: if Mac blocks it, right-click → Open → Open.
One-time permission fix via Claude Code: `chmod +x START.command STOP.command`

### Manual (dev)
```bat
python -m uvicorn main:app --port 8083 ^
  --app-dir "discovery-engine\backend" ^
  --reload ^
  --reload-dir "discovery-engine\backend"
```
Then open http://localhost:8083

### Kill existing process first (if port busy)
```bat
netstat -ano | findstr :8083
taskkill /PID <pid> /F
```

---

## Environment Variables

Stored in `discovery-engine/.env` (never commit):

```env
ANTHROPIC_API_KEY=sk-ant-...    # Required — get from console.anthropic.com
ENABLE_NEO4J=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

`.env` is loaded in `backend/graph_extractor.py` via:
```python
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
```

---

## Features — Complete List

| # | Feature | Endpoint(s) | Claude call? | Cached? |
|---|---------|-------------|-------------|---------|
| 1 | Graph extraction | `POST /api/upload` | Yes — Sonnet | No cache — always runs fresh |
| 2 | Workflow generation | `POST /api/workflows/generate` `GET /api/workflows/{id}` | Yes — Sonnet | `_workflow_store` |
| 3 | Object model | `POST /api/generate-object-model` | Yes — Sonnet | `_object_model_store` by `graph_id` |
| 4 | Natural language query | `POST /api/query/natural-language` `GET /api/query/history/{id}` | Yes — Haiku | History only |
| 5 | Gap analysis | `POST /api/gap-analysis/calculate` | No — rule-based | `_gap_store` |
| 6 | Blueprint | `POST /api/gap-analysis/blueprint` | Yes — Haiku | `_blueprint_store` |
| 7 | Pulse recommendations | `POST /api/pulse/calculate` `POST /api/pulse/ai-recommendations` | Rule-based + Haiku | `_pulse_store`, `_pulse_ai_store` |
| 8 | Conformance checker | `POST /conformance/upload` `POST /conformance/analyse` `GET /conformance/{id}/latest` | Yes — Sonnet | `_conformance_store` |

---

## In-Memory Stores (main.py)

All keyed by `graph_id` (UUID) except evidence stores:

```python
_graph_store:        dict[str, dict]  # graph_id → graph (nodes/edges)
_doc_store:          dict[str, str]   # graph_id → combined doc text (≤15,000 chars)
_workflow_store:     dict[str, list]  # graph_id → workflows list
_object_model_store: dict[str, dict]  # graph_id → object model result
_query_history:      dict[str, list]  # graph_id → list of NLQ entries
_gap_store:          dict[str, dict]  # graph_id → gap analysis result
_blueprint_store:    dict[str, dict]  # graph_id → blueprint result
_pulse_store:        dict[str, dict]  # graph_id → pulse items
_pulse_ai_store:     dict[str, dict]  # graph_id → AI recommendations
_evidence_store:     dict[str, dict]  # evidence_id → {text, filename, word_count, graph_id}
_conformance_store:  dict[str, dict]  # evidence_id → full conformance result
_conformance_latest: dict[str, str]   # graph_id → latest evidence_id
```

All stores are in-memory only — reset when the server restarts. There is no extraction cache; every upload runs a fresh Claude call.

---

## Claude API Integration

### Model Routing — Token Cost Optimisation

| Call | Model | max_tokens | Why |
|------|-------|-----------|-----|
| Graph extraction | `claude-sonnet-4-6` | 8,096 | Needs highest accuracy — lower limit returns 0 edges |
| Workflow generation | `claude-sonnet-4-6` | 16,000 | Complex nested schema |
| Object model | `claude-sonnet-4-6` | 4,096 | Code generation quality |
| Conformance analysis | `claude-sonnet-4-6` | 6,000 | Precise evidence matching |
| NLQ | `claude-haiku-4-5-20251001` | 800 | Simple Q&A |
| Blueprint | `claude-haiku-4-5-20251001` | 800 | Short summary |
| Pulse AI | `claude-haiku-4-5-20251001` | 2,048 | Structured recs list |

Constants defined at top of `graph_extractor.py`:
```python
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"
```

### Input Truncation Limits

| Input | Limit | Location |
|-------|-------|----------|
| Extraction document text | 20,000 chars | `extract_graph_from_text()` |
| Stored doc text | 15,000 chars | `_doc_store` in `/api/upload` |
| Workflow doc section | 8,000 chars | `_build_workflow_prompt()` |
| NLQ doc section | 3,000 chars | `query_graph()` |
| Conformance evidence | 8,000 chars | `run_conformance_analysis()` |

### Core Call Pattern

All Claude calls go through `_call_tool()` with forced `tool_choice`:
```python
def _call_tool(system, prompt, tool, model=SONNET, max_tokens=8096) -> dict:
    response = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        tools=[tool], tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input
    raise RuntimeError("Claude did not return a tool_use block")
```

### Prompt Lean Rules

- NLQ and conformance node lines: `id | label | type` only — no descriptions
- Object model: compact `id | type | label` node list + edge list — no full JSON dump
- Blueprint/pulse: summary stats only — no full node list

---

## Graph Extraction

- **Target:** 15–20 nodes, 15–20 edges per document
- **Node types:** Process, Role, System, Policy, DataEntity, Event
- **Edge IDs** are remapped on merge: `n1, n2, …` / `e1, e2, …`
- **graph_id** is a UUID attached to the graph after extraction and stored in `_graph_store`

### Conformance — Eligible Node Types

`run_conformance_analysis()` filters to:
```python
ELIGIBLE_TYPES = {"Process", "Role", "Policy", "DataEntity"}
```
Event and Objective nodes are skipped (not assessable from evidence docs).

---

## Object Model — BRD Authoring Standard §4

The object model generator (`OBJECT_MODEL_SYSTEM` + `OBJECT_MODEL_PROMPT` in `graph_extractor.py`) enforces BRD Authoring Standard §4 rules:

| Rule | Detail |
|------|--------|
| snake_case field names | No spaces, no camelCase, under 63 chars |
| First field: `id: UUID` | Primary Key — non-negotiable on every entity |
| Always include `created_at: datetime` | Not Null — audit trail |
| Audit fields `created_by`, `last_changed_by` | Marked `AUDIT ONLY – no relationship` |
| FK naming: `<parent_table>_id: UUID` | e.g. `customer_id`, `account_id` |
| Enum values UPPERCASE | e.g. `OPEN`, `IN_PROGRESS`, `BLOCKED` |
| Relationships format | `entity_a (parent) → entity_b (child) via entity_b.fk_column = entity_a.id` |

The JSON schema output includes an `"entities"` array and a `"relationships"` array.  
The ERD renderer in `app.js` (`_renderErdEntities`) handles both the new BRD format and the legacy `$defs`/`definitions` format.

### Object Model Loading States (`_omSetState`)

```javascript
_omSetState('empty')    // no graph loaded yet
_omSetState('loading')  // API call in flight — shows spinner
_omSetState('ready')    // result received — shows tabs + content
```

---

## Graph Highlighting — Three Implementations

Three separate highlight systems exist in `app.js`. Do NOT consolidate without testing all features:

| Function | Used by | Notes |
|----------|---------|-------|
| `focusNode(nodeId)` | Node click in detail panel | Single node focus |
| `gapHighlightNodes(nodeIds, severity)` / `gapResetHighlight()` | Gap analysis "View in Graph" | Updates gap banner |
| `highlightNodes(nodeIds, severity)` / `resetGraphHighlight()` | Pulse, Conformance, NLQ reset | Shared new functions |

`nlqResetGraphHighlight()` delegates to `resetGraphHighlight()` — this fixed a bug where NLQ highlights were never fully cleared.

The `gapHighlightBanner` is reused by all features. `gapBannerSource` span shows dynamic source text (e.g. "Gap Analysis", pulse item title, conformance deviation label).

---

## Frontend Architecture

### Navigation — Sidebar (200px labeled)

Five nav items in a 200px labeled sidebar. Navigation is controlled by two functions:

```javascript
setNavActive(id)      // highlights the active nav item
switchView(view)      // shows/hides panels + sets split ratio
```

`switchView` handles: `'graph'`, `'workflows'`, `'gap'`, `'conformance'`, `'object-model'`

### Split Panel Ratios

The left panel (`#upload-panel`) width is set dynamically per view:

```javascript
const PANEL_RATIOS = { graph: 35, workflows: 60, gap: 50, conformance: 50, 'object-model': 55 };
```

The right `.graph-area` always takes the remaining width — it is **always visible** in all views.

### Panel Layout — All Inside `#upload-panel`

All left-side panels are view slots inside `#upload-panel` (flex column):

| Element | View key | Notes |
|---------|----------|-------|
| `#graph-panel-view` | `'graph'` | Upload form + node legend |
| `#workflows-panel-view` | `'workflows'` | Generate button + workflow cards |
| `#gap-panel` | `'gap'` | Gap analysis + blueprint |
| `#conformance-panel` | `'conformance'` | Evidence upload + results |
| `#object-model-panel` | `'object-model'` | BRD-compliant pydantic/JSON/ERD |

**Important:** `body-area` is never hidden. Gap and conformance are inside `upload-panel`, not siblings of `body-area`. The old `modalOverlay` for object model has been removed.

### CSS Fix — `display: flex` overrides `hidden` attribute

Any element with `display: flex` in CSS must have an explicit `[hidden] { display: none; }` rule, otherwise the HTML `hidden` attribute is ignored. This affects:
- `.gap-empty-state[hidden] { display: none; }`
- `.om-loading[hidden]`, `.om-empty-state[hidden]` etc.

### Key State Variables

```javascript
let currentGraph     = null;   // full graph object {nodes, edges, graph_id}
let currentGraphId   = null;   // UUID string
let network          = null;   // vis-network instance
let pulseData        = null;   // pulse items
let pulseAiData      = null;   // AI recommendations
let conformanceEvidenceId    = null;
let conformanceResult        = null;
let conformanceActiveOverlay = null;  // 'all' | 'confirmed' | 'deviated' | null
```

### Workflow Panel

Inside `#workflows-panel-view` in the left panel. Uses `highlightNode(nodeId)` / `unhighlightNode(nodeId)` for step hover interactions with vis-network.

### Pulse Drawer

Slide-in drawer from the right, triggered by bell button in sidebar bottom. Badge auto-populates after graph extraction via `fetchPulse()`. "View in Graph" closes drawer, switches to graph nav, calls `highlightNodes()`.

### Conformance Panel

Shown as the left panel at 50% width alongside the always-visible graph. Three overlay modes via `confApplyOverlay(mode)`:
- `'all'` — green confirmed + red deviated + faded not_found
- `'confirmed'` — green only
- `'deviated'` — red only
- `null` — reset via `resetGraphHighlight()`

---

## Brand Identity — Metafore Works Design System

### Header
- Left: "DISCOVERY ENGINE" only (no brand name — moved to sidebar)
- Sidebar top: logo + "Metafore Works" text

### Colours

| Token | Value | Usage |
|-------|-------|-------|
| `--brand` | `#036868` | Header background |
| `--brand-dark` | `#024F4F` | Hover states |
| `--brand-mid` | `#007F7F` | Sidebar background |
| `--brand-light` | `#E6F4F4` | Upload zone hover, tints |
| `--brand-border` | `#0a9090` | Accent borders |
| `--bg` | `#EEF6F6` | Page / graph canvas background |
| `--bg-card` | `#F7FAFA` | Upload panel, detail panel |
| `--bg-panel` | `#E6F4F4` | File items, source quote block |
| `--border` | `#C4E0E0` | Card borders, dividers |
| `--text` | `#0f2020` | Primary text |
| `--text-sec` | `#4a6868` | Secondary / body text |
| `--text-muted` | `#7a9a9a` | Labels, muted values |

### Typography

- **Primary:** GT America (self-hosted OTF)
- **Monospace:** IBM Plex Mono (self-hosted TTF) — edge labels, source quotes, data values
- **Fallback:** Inter → system sans-serif
- `@font-face` declarations are in the `<style>` block inside `index.html`

---

## Graph Visualisation — vis-network

### Golden Rule: ALL nodes are circles

Every node type uses `shape: 'dot'`. No boxes, stars, diamonds — uniform circles only.

### Node Type → Colour Mapping

| Type | Fill | Border | Font |
|------|------|--------|------|
| Process | `#C7F0ED` | `#0D9488` | `#0D9488` |
| Role | `#FED7AA` | `#EA580C` | `#C2410C` |
| System | `#BFDBFE` | `#3B82F6` | `#1D4ED8` |
| Policy | `#FECACA` | `#EF4444` | `#DC2626` |
| DataEntity | `#DDD6FE` | `#7C3AED` | `#6D28D9` |
| Event | `#FEF08A` | `#CA8A04` | `#92400E` |

### Node Sizing

```js
size = 28 + Math.round((degree[n.id] / maxDeg) * 18)  // range 28–46px
```

### Edge Styling

- Colour: `#B0CECE`, width 1px (2px selected)
- Labels: IBM Plex Mono 10px, `#7a9a9a`
- Arrow: `scaleFactor: 0.45`, type `arrow`, curve `curvedCW` roundness `0.1`

### Physics

```js
solver: 'forceAtlas2Based'
gravitationalConstant: -80, centralGravity: 0.005
springLength: 160, springConstant: 0.06, damping: 0.9, avoidOverlap: 0.8
stabilization.iterations: 250
```
Physics disabled after stabilisation. Graph fits to view with 700ms ease.

---

## Sample Documents — Banking Demo

| File | Purpose | Expected output |
|------|---------|-----------------|
| `sample_docs/commercial_banking_loan_sop.docx` | Upload for graph extraction | ~25 nodes: 8 processes, 6 roles, 4 systems, 3+ policies |
| `sample_docs/loan_audit_report.docx` | Upload for conformance checking | ~47% conformance rate: 9 confirmed, 10 deviated, 2 not_found |

The audit report is a Q3 2024 internal audit of the same loan origination process described in the SOP. Key deviations it surfaces: AML sequencing (critical), appraisal before completeness, sanctioning timeline breach, DTI by wrong role.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| AI | Anthropic Claude — Sonnet 4.6 + Haiku 4.5 via tool use |
| Backend | Python 3.11+ · FastAPI 0.115 · Uvicorn 0.32 |
| Document parsing | PyMuPDF (PDF) · python-docx (DOCX) · built-in (TXT) |
| Graph DB (optional) | Neo4j 5 — disabled by default |
| Frontend | Vanilla JS · vis-network 9.1.9 (self-hosted) |
| Fonts | GT America · IBM Plex Mono · Inter (all self-hosted) |

---

## Distribution — Zip Package

The app is distributed as `MetaforeWorks_DiscoveryEngine_v1.0.zip` (built on Windows Desktop).

### What is included
- All source files (frontend + backend)
- `discovery-engine/.env` with pre-configured API key
- `START.bat` + `STOP.bat` (Windows launchers)
- `START.command` + `STOP.command` (Mac launchers)
- `ONBOARDING.md` (setup guide for both platforms)
- `BRD_Discovery_Engine.docx`
- `ROOT_CLAUDE_METAFOREWORKS.md` (root CLAUDE.md copy for colleague's merge)
- Sample documents

### What is excluded
- `__pycache__/`, `*.pyc`, `.git`, `*.jsonl`

### To rebuild the zip (PowerShell)
```powershell
$src = "C:\Users\bhara\Desktop\MetaforeWorks\Metafore Discovery Engine"
$tmp = "C:\Users\bhara\AppData\Local\Temp\mw_de_export"
$out = "C:\Users\bhara\Desktop\MetaforeWorks_DiscoveryEngine_v1.0.zip"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
robocopy $src $tmp /E /XD "__pycache__" ".git" /XF "*.pyc" "*.jsonl" /NFL /NDL /NJH /NJS | Out-Null
if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path "$tmp\*" -DestinationPath $out -CompressionLevel Optimal
Remove-Item $tmp -Recurse -Force
```

### Mac setup note
`.command` files must be made executable after unzip:
```bash
chmod +x START.command STOP.command
```
Claude Code on the colleague's machine handles this during setup (see ONBOARDING.md).

---

## Lessons Learned

1. **Tool use is mandatory** — text/JSON prompting truncates at 8096 tokens for large documents.
2. **`load_dotenv` must use `Path(__file__).resolve()`** — CWD-relative paths break when uvicorn changes working directory internally.
3. **Port 8083** — 8001 and 8080 are prone to orphaned sockets on Windows. When `netstat` shows a PID as LISTENING but `taskkill` says "not found", the socket is leaked — use a different port.
4. **`ENABLE_NEO4J=false` by default** — if accidentally `true` without Neo4j running, the retry loop blocks HTTP responses for 30+ seconds.
5. **All circle shapes** — uniform `dot` shape only; mixed shapes look unprofessional.
6. **vis-network must be self-hosted** — Edge browser Tracking Prevention silently blocks CDN loads from unpkg.com. Download and serve locally.
7. **`--reload` does not reload `.env`** — changing the API key requires a full server restart (kill + relaunch). The reloader only watches `.py` files.
8. **Workflow generation needs max_tokens=16000** — the AS-IS/TO-BE schema with 3–5 workflows easily exceeds 8096 output tokens. Lower limit silently returns an empty workflows array.
9. **API credits on the right account** — always verify the key in `.env` matches the account where credits were purchased. Credits on a different account/workspace show the same "too low" error.
10. **Windows orphaned sockets** — `netstat -ano` may show PIDs as LISTENING even after the process is gone. `taskkill` returns "not found". Fix: use a different port.
11. **No extraction cache** — graph extraction always runs a fresh Claude call. The SHA-256 content hash cache was removed by design; each upload should produce its own independent result.
12. **`display: flex` overrides `hidden` attribute** — any element with CSS `display: flex` needs an explicit `[hidden] { display: none; }` rule or the HTML hidden attribute is ignored by the browser.
13. **`switchView` initialisation** — call `switchView('graph'); setNavActive('nav-graph')` once at script load, otherwise the default view starts hidden if any prior navigation state remains.
14. **`--app-dir` for uvicorn** — use `--app-dir path/to/backend` so `main.py` is found regardless of the working directory. Pair with `--reload-dir` scoped to the backend only to prevent watching the entire worktree.
15. **Mac `.command` files need `chmod +x`** — files extracted from a zip on Mac are not executable by default. Always include `chmod +x START.command STOP.command` in the Mac setup step. Without this, double-clicking does nothing.
16. **Server stops on computer restart** — the uvicorn process is not a system service. On both Windows and Mac, the server must be restarted after each reboot. START.bat / START.command handle this. Auto-start via LaunchAgent (Mac) or Startup folder (Windows) is optional.
17. **BRD is a generated docx** — `BRD_Discovery_Engine.docx` is generated by `generate_brd_docx.py` using python-docx. If BRD content needs updating, edit the script and re-run it, then rebuild the zip.
