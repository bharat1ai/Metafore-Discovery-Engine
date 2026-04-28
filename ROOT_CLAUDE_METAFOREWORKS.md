# MetaforeOne — Engineering Handbook

This file is read by Claude at the start of every session under this folder.
It captures architecture decisions, patterns, and lessons learned across all MetaforeOne products.

---

## Standing Operating Principles — Read First

These rules govern how Claude behaves across every session under this folder.

1. **Do everything autonomously.** The user is not technical and should not be asked to run commands, move files, create folders, edit configs, or perform any manual step that Claude can do directly. If something needs doing, just do it.

2. **Never ask the user to do something Claude can do.** This includes: creating directories, running terminal commands, copying files, creating symlinks, editing config files, installing dependencies, or any filesystem operation.

3. **Check before assuming.** Before starting work on any solution folder, silently verify the environment is correct (fonts symlinked, dependencies installed, dev server registered). Fix anything missing without mentioning it unless something genuinely cannot proceed.

4. **Remember context across sessions via this file.** If a decision, pattern, or setup step was established in a previous session, it will be documented here. Claude reads this file first and acts accordingly — no re-explaining needed.

5. **New solution setup checklist** — run automatically when starting work in any new `15-xx` folder:
   - [ ] Check `public/fonts/` exists — if not, create the symlink to `_shared/fonts/`
   - [ ] Check `index.html` has `@font-face` declarations — if not, copy from `15-11 - MetaWorks-AN/index.html`
   - [ ] Check dev server is registered in `.claude/launch.json` — add if missing
   - [ ] Check `node_modules` exists — run `npm install` if not

6. **Proactively maintain this file.** After any significant decision, pattern discovery, or setup step, update `CLAUDE.md` so the next session inherits the knowledge automatically.

---

---

## Brand Identity

- **Primary brand color (header):** `#036868` (dark teal)
- **Secondary brand color (sidebar):** `#007F7F` (mid teal)
- **Light accent:** `#E6F4F4`
- **Brand text on dark:** `#FFFFFF`
- **Token file pattern:** `src/theme/tokens.js` exports a `D` object with all colors

### Logo assets
- **Icon logo** (square mark, white): `public/metafore-logo.png` — used in sidebar (34×34px)
- **Horizontal logo** (wide text mark, white): `public/metafore-logo-horizontal.png` — used in header bar
- **App name pattern in header:** `[horizontal logo img] + "One" (bold white) + " " + [ProductName] (lighter weight, spaced)`
- **ONE is always sentence case: "One"** — not "ONE"

### Typography
- **Primary font:** GT America Standard (OTF, self-hosted)
- **Monospace:** IBM Plex Mono (TTF, self-hosted) — used for all data, chips, numbers
- **Fallback:** Inter (TTF, self-hosted) → system sans-serif
- **Also available:** Brut Grotesque (OTF, self-hosted)
- **BRAND_FONT constant** defined at top of `App.jsx`
- **`D.mono`** in `tokens.js` → `'IBM Plex Mono','SF Mono','Consolas',monospace`
- **`D.sans` / `D.display`** in `tokens.js` → `'GT America','Inter',-apple-system,sans-serif`
- **No Google Fonts** — all fonts are self-hosted from `public/fonts/`

### Shared font library — AUTOMATIC SETUP REQUIRED
All font files live in one master location:
```
15 - MetaforeOne/_shared/fonts/
```
Each solution's `public/fonts/` is a **symlink** to this folder — NOT a copy.

**When starting work on any new solution under `15 - MetaforeOne/`:**
Claude must automatically check whether `public/fonts/` exists in that solution. If it does not, create the symlink immediately without being asked:
```bash
ln -s "/Users/deep_b/Desktop/Work/00 - CtrlAgent/Solutions/15 - MetaforeOne/_shared/fonts" \
  "<solution-path>/public/fonts"
```
Then add the `@font-face` declarations to that solution's `index.html` (copy the pattern from `15-11 - MetaWorks-AN/index.html`).

This ensures every solution automatically gets GT America, IBM Plex Mono, Inter, and Brut Grotesque without any manual steps.

---

## Application Architecture

### Stack
- **React 18** + **Vite 6** + **Zustand 5**
- No backend — all data is in-memory, defined in `src/data/`
- No database, no API calls (all simulated)
- TypeScript is NOT used — plain JavaScript throughout

### Zustand 5 — Critical Rule
Zustand 5 changed selector behaviour. **Always use per-field primitive selectors**, never object-returning selectors:

```js
// CORRECT
const view = useAppStore(s => s.view)
const activeNode = useAppStore(s => s.activeNode)

// WRONG — causes infinite re-renders in Zustand 5
const { view, activeNode } = useAppStore(s => ({ view: s.view, activeNode: s.activeNode }))
```

### Folder structure convention
```
src/
  assets/          SVG components, logo fallbacks
  components/
    dashboard/     Main content panels (Today's Focus, Pulse Engine, etc.)
    inspector/     Node detail views (ActiveNodeInspector, GraphView)
    ui/            Shared UI (Sidebar, AiAssistant, Primitives, Icon)
  data/            All in-memory data (knowledgeGraph, insightFrames, rootCauseChains)
  stores/          Zustand store(s)
  theme/           tokens.js
public/
  fonts/           Self-hosted OTF/TTF files
  *.png            Logo assets
```

---

## Layout System

### Top-level layout (App.jsx)
```
[Sidebar 48px fixed] | [Main column flex:1] | [Right panel variable width]
```
- **Sidebar:** fixed 48px wide, `background: D.brandMid`, icon-only nav
- **Header:** `background: D.brand`, height ~56–64px, contains logo + app name + stats chips
- **Main area:** `flex: 1`, hosts the active view (dashboard / graph / inspector)
- **Right panel:** collapsible, width controlled by `aiCollapsed` state. Expanded = 520px, collapsed = 48px

### Right panel structure (when expanded)
```
[AiAssistant — flex:1 scrollable]
[PulseEngine — fixed height 380px, flexShrink:0]
```

### Header app name pattern
```jsx
<img src="/metafore-logo-horizontal.png" style={{ height: 22, objectFit: 'contain' }} />
<span style={{ fontWeight: 700, fontSize: 17, color: '#fff' }}>One</span>
<span style={{ fontWeight: 300, fontSize: 13, color: 'rgba(255,255,255,0.7)', letterSpacing: '0.12em' }}>
  {' '}PRODUCTNAME
</span>
```

---

## Navigation — Back Button Pattern

The platform uses a two-path navigation model to support a contextual back button:

| Action | Store method | Saves previousView? | Back button appears? |
|--------|-------------|---------------------|----------------------|
| Sidebar icon click | `setViewDirect(view)` | No — clears to null | Never |
| In-app link / button | `setView(view)` | Yes — saves current view | Yes, until dismissed |

```js
// appStore.js — three actions
setView: (view) => { ... set({ view, previousView: currentView }) }   // in-app navigation
setViewDirect: (view) => { ... set({ view, previousView: null }) }    // sidebar only
goBack: () => { ... set({ view: previousView, previousView: null }) } // back button
```

**Rule:** Always use `setView` for programmatic navigation inside components (buttons, cards, chips).
Only `Sidebar.jsx` uses `setViewDirect`. The back button renders in `App.jsx` title row when `previousView !== null`.

**CLA chip navigation in BenchmarksView:** `CLA_VIEW_MAP` object maps CLA IDs to view keys:
```js
const CLA_VIEW_MAP = { 'CLA-OPS1': 'shield', 'CLA-COMM1': 'sword', 'CLA-MEM1': 'agents', ... }
```
Each chip is a `<button>` that calls `setView(CLA_VIEW_MAP[cla])` — triggers back button on arrival.

---

## Animation Rules — CRITICAL

**Never use `setInterval` or `useState`/`useEffect` for visual pulse/blink animations.**
This causes entire component trees to re-render on every tick, producing visible flickering.

**Always use CSS `@keyframes` instead:**

```js
// Inject once at module level (not inside a component)
const pulseStyle = document.getElementById('mf-pulse-style') || (() => {
  const el = document.createElement('style')
  el.id = 'mf-pulse-style'
  el.textContent = '@keyframes mf-pulse { 0%,100%{opacity:1} 50%{opacity:0.2} }'
  document.head.appendChild(el)
  return el
})()
```

```jsx
// Then in JSX — zero React re-renders
<span style={{ animation: 'mf-pulse 1.8s ease-in-out infinite' }} />
```

**Exception:** `setInterval` is acceptable in self-contained components that manage their own
isolated state and do NOT cause parent re-renders (e.g. PulseEngine live feed, which is
positioned outside the main content column).

---

## Graph Conventions (SVG Knowledge Graph)

### Layout approach
- **6-column organic layout** — not a rigid grid. Columns have cx ranges but nodes are
  staggered vertically to feel natural, not matrix-like
- Column zones (cx): ~60–90, ~190–225, ~320–360, ~450–490, ~580–620, ~710–750
- `svgW = 840`, `svgH = 1400` (tall enough to spread nodes without crowding)
- Nodes spread across full SVG height — avoid leaving large whitespace at bottom

### Node styling
- **Circle nodes**, radius `CIRCLE_R = 28`
- Node type drives colour (exception-event = red/amber, vplmn = teal, probe = blue, etc.)
- Active/selected node gets a glow filter via SVG `<filter>`
- Node labels sit below the circle, centred

### Edge rendering
- Edges connect circle *circumferences*, not centres — use `circleEdgePts()` helper
- Edges are directional (arrow markers)
- Edge labels sit at midpoint

### RCA traversal animation
- Uses SVG `<animateMotion>` + `<mpath>` following the edge path
- State: `rcaTraversal: { chainId, activeStep }` in Zustand store
- Finding text is pushed to right panel via `rcaFindingText` store field — NOT rendered below SVG

### RCA chain structure (rootCauseChains.js)
```js
{
  id: 'rca-xxx',
  title: 'Human readable title',
  steps: [
    { id: 'step-1', phase: 'reflex',     nodeId: 'node-id', finding: 'text...' },
    { id: 'step-2', phase: 'reflection', nodeId: 'node-id', finding: 'text...' },
    { id: 'step-3', phase: 'resolve',    nodeId: 'node-id', finding: 'text...' },
  ]
}
```
Phases: `reflex` (red) → `reflection` (amber) → `resolve` (green)

---

## Pulse Engine Pattern

A live-feed component that simulates real-time event ingestion:
- Self-contained — manages its own state with `useState` + `setInterval`
- Pre-seeded pool of events, new event prepended every 4s, max 40 events
- 1s tick for relative timestamp display
- Severity communicated via left-border colour: red / amber / teal
- Green pulsing "Live" dot via CSS keyframes
- Placed at bottom of right panel, `height: 380px`, `flexShrink: 0`

---

## Component Patterns

### StatusBadge
- Severity levels: `critical` / `high` / `medium` / `low`
- Pulse animation via CSS only — no JS

### Action buttons
- Primary action: `background: #036868`
- Secondary action: `background: #007F7F`
- Never dark blue — always brand teal palette

### Icon component
Uses Lucide icons by name string: `<Icon name="GitBranch" size={14} color="#fff" />`

---

## BRD & Demo Script Conventions

Every solution under MetaforeOne produces two companion documents alongside the app. Claude creates these proactively — do not wait to be asked.

### Folder structure
```
[solution-folder]/
  _BRD/
    [SolutionName]_BRD.docx      ← Business Requirements Document
  _Script/
    DEMO_SCRIPT.html             ← Standalone demo guide (opens in browser)
```

Reference example: `15-11 - MetaWorks-AN/_BRD/` and `15-11 - MetaWorks-AN/_Script/`

---

### BRD — `_BRD/[Name]_BRD.docx`

A Word document. Sections (adapt as needed per domain):

1. **Executive Summary** — problem statement, solution overview, value proposition
2. **Business Context** — industry, operator profile, current pain points
3. **Solution Scope** — what the platform does, what it does not do
4. **Functional Requirements** — per view/module, each with acceptance criteria
5. **Closed Loop / CLA Registry** — each autonomous loop: trigger, action, outcome, HITL gate
6. **AN Maturity Model** — current level, target level, journey roadmap
7. **Data & Integration** — data sources, feed types, simulated vs live
8. **ROI & Value Framework** — savings categories, pipeline, realised value
9. **Governance & HITL** — approval workflow, audit trail, escalation rules
10. **Deployment Profile** — currency, market, regulator, scale assumptions
11. **Out of Scope** — explicit exclusions to manage expectations
12. **Glossary** — domain terms defined

---

### Demo Script — `_Script/DEMO_SCRIPT.html`

A **standalone HTML file** — no server needed, opens directly in a browser. Styled with MetaforeOne brand colours (#036868 header, #024F4F navbar). Structure:

- **Cover** — solution name, tagline, version, date, "CONFIDENTIAL" badge
- **Sticky navbar** — one tab per demo section, smooth-scrolls
- **Sections** — each covering one narrative beat of the demo:
  - Opening / context setting
  - One section per major view (Dashboard, key CLAs, CFO, ROI, etc.)
  - Each section has: *What to show*, *What to say*, *Key proof points*, *Anticipated questions*
- **Timing guide** — suggested minutes per section for a 30/45/60 min slot
- **Q&A Prep** — objection handling, common questions with suggested answers

The script is the *presenter's guide*, not a user manual. Write it in the voice of someone coaching the presenter through the story — what to click, what to emphasise, what to watch out for.

The app itself should NOT contain demo flow UI or overlay panels — the script is the external guide. This was a lesson learned in `15-11`.

---

## Lessons Learned / What NOT to Do

1. **Don't use object selectors in Zustand 5** — causes infinite render loops
2. **Don't use `setInterval` in components that share a render tree** — causes flickering
3. **Don't close JS arrays prematurely** — a stray `]` in a data file closes the array silently,
   then subsequent entries cause `Unexpected token ':'` errors. Always lint data files.
4. **Don't put RCA finding text below the SVG** — it forces scrolling. Push it to the right panel via store.
5. **Don't hardcode node positions in a 4-column grid** — use the 6-column organic layout with
   staggered cy values for a more natural knowledge graph feel
6. **Don't use Google Fonts for custom brand fonts** — if the font isn't on Google Fonts,
   self-host the OTF/TTF in `public/fonts/` and declare with `@font-face` in `index.html`
7. **Don't reference another view's CSS keyframes** — e.g. `cmd-pulse` is injected by CommandView; if WorkforceView uses it and loads first, the animation silently fails. Each view injects its own `<style id="mf-xx-style">` tag with its own uniquely-named keyframes.
8. **FINANCIALS field naming** — always include both `fy24`/`fy25` historical fields AND a `target` alias when a view needs to compare against target. `revenuePerHead` needs `fy24`, `fy25`, `current`, and `target` all present to avoid undefined errors in ScorecardView.

---

## Local Domain Routing — Caddy Setup

All MetaforeOne solutions can be served via a **Caddy reverse proxy** running locally, replacing `localhost:PORT` with clean branded URLs like `united.mira.metafore.ai`. This makes demos look like live hosted products.

### Infrastructure
- **Caddy config:** `/Users/deep_b/Desktop/Work/00 - CtrlAgent/Solutions/15 - MetaforeOne/_caddy/Caddyfile`
- **Hosts file:** `/etc/hosts` — maps custom domains to `127.0.0.1`
- **Domain pattern:** `[client].[product].metafore.ai` → solution's localhost port

### Starting Caddy
Caddy must be running for the custom domains to work. Start it with:
```bash
caddy run --config "/Users/deep_b/Desktop/Work/00 - CtrlAgent/Solutions/15 - MetaforeOne/_caddy/Caddyfile" &
```

### Currently configured domains
| Domain | Port | Solution |
|--------|------|----------|
| `united.mira.metafore.ai` | 6081 | `15-14(b)_MIRA_UAL` |

### Adding a new solution
1. **Claude** adds a new block to the Caddyfile:
   ```
   [client].[product].metafore.ai:80 {
       reverse_proxy localhost:PORT
   }
   ```
2. **Claude** adds `allowedHosts: ['[client].[product].metafore.ai']` to that solution's `vite.config.js`
3. **User** runs one Terminal command (Claude will provide it):
   ```bash
   echo "127.0.0.1    [client].[product].metafore.ai" | sudo tee -a /etc/hosts
   ```
4. **Claude** restarts Caddy

### Important notes
- `/etc/hosts` requires `sudo` — the one step only the user can do
- Caddy runs in the background and survives dev server restarts
- Domains only work on this machine (local `/etc/hosts`) — not accessible by the audience on their own devices
- This is designed for screen-share / in-person demos where the audience watches your screen

---

## Solution Registry

| Folder | Product | Port | Domain | Status |
|--------|---------|------|--------|--------|
| `15-11 - MetaWorks-AN` | MetaWorks ONE — Autonomous Networks (Telco, Singapore) | 5184 | `telco-an-nsoc.metaworks.metafore.ai` | Complete |
| `15-12_United Airlines` | United EGI v1 — first iteration | 6060 | — | Complete |
| `15-12(a)_UAL` | United Airlines EGI Transformation Platform — v2 | 6065 | — | Complete |
| `15-17_MobileTelco/15-17-001_OrangeFR` | Orange France — Mobile Telco EGI Platform | 6070 | `orange.egi.metafore.ai` | Active |
| `15-14_MIRATravel (OS)/mira-travel` | MIRA Travel — United Airlines (original / reference copy) | 6080 | — | Complete |
| `15-14(b)_MIRA_UAL` | MIRA Travel — United Airlines (active working version) | 6081 | `united.mira.metafore.ai` | Active |
| `15-4 - Telco_1/TelcoAssure` | MetaforeOne Telco — Service Assurance Platform | 6010 | `mfw-proto.telco-assure.metafore.ai` | Active |
| `15-15_Mplus` | Mplus One — BPTO AI Transformation Platform | 6085 | — | Active |
| `15-19_MWorks_Airtel` | MetaWorks ONE — Airtel India Autonomous Networks | 6090 | `airtel.mworks.metafore.ai` | Active |

### `15-17-001_OrangeFR` — Orange EGI Platform

**Key facts:**
- Exec team: Christel Heydemann (Group CEO), Laurent Martinez (EVP Finance), Jérôme Hénique (CEO Orange France), Mari-Noëlle Jégo-Laveissière (Deputy CEO Europe), Marie Bauer (Chief Digital Officer), Guillaume Poupard (Chief Trust Officer)
- 10 views: Command Centre, Terraformation, Network Shield, Revenue Sword, Knowledge Fabric, Exec Scorecard, Network Intelligence, AI Agent Registry, Value Realisation, Settings
- 6 CLAs across 3 thrusts: Shield (CLA-NET1, CLA-NET2), Sword (CLA-CHR1, CLA-ARV1), Memory (CLA-REG1, CLA-MEM1)
- EGI ontology: 4 entity types — Network, Subscriber, Incident, Regulatory
- Key data: Revenue €40.4B FY25, EBITDAaL €12.5B (+3.8%), OCF €3.7B (+8.3%), AI Value €330M → €600M 2028 target
- Strategy: Trust the Future 2026–2030; OCF €5.2B by 2028
- Brand: #FF6600 primary, dark theme, GT America + IBM Plex Mono
- Documents: `OrangeFR_EGI_Transformation.docx`, `_BRD/OrangeFR_EGI_BRD.docx`
- ROI_CATEGORIES in financials.js: use `realised`, `target`, `clas` (array), `color`, `desc` fields (not `fy25`/`target28`/`cla`)

### `15-15_Mplus` — Mplus One BPTO AI Transformation Platform

**Key facts (aligned to Project Atlas Info Memo, March 2026):**
- Company: Mplus Group — BPTO (Business Process & Technology Outsourcing), part of BOSQAR INVEST Group
- Scale: 14,700+ people (11,500 agents + 3,200 support/mgmt/tech) · 68 sites · 57 countries · 300+ blue-chip clients · 25+ industries · 32+ languages
- HQ: Zagreb, Croatia. Founded 2007.
- Exec team: Tomislav Glavaš (Group CEO), Darko Horvat (President, Mgmt Board), Petra Vučinić (CFO), Ogan Atasagun (CCO), Banu Hızlı (CEO Türkiye & MENA), Igor Varivoda (CEO Germany & CEE), Marko Martinović (CEO Graia)
- AI brand: **Graia** — proprietary agentic AI platform (CCaaS, prebuilt agent library, RAG KB), Juniper Research Leading Challenger
- **16 views**: Command Centre (BOSQAR group level), **BOSQAR Group Structure** (`orgchart`), Knowledge Graph, **Workplace Group** (`workplace`), **Future Food** (`futurefood`), CX Intelligence, Workforce, HR & People, Talent Acquisition, Back Office, Client Portfolio, Geographic Expansion, Executive Scorecard, Value Realization, Change Management, AI Agent Registry
- **BOSQAR group expansion (April 2026):** Command Centre is now the BOSQAR group-level entry point showing 3 verticals. OrgChartView (`orgchart`) has SVG org tree (BOSQAR → BPTO/HR/Food → sub-entities), Board & Management tab (MANAGEMENT_BOARD + SUPERVISORY_BOARD), Ownership tab (donut chart + shareholder table). WorkplaceView (`workplace`) is the Manpower franchise HR vertical. FutureFoodView (`futurefood`) is the Panvita + Mlinar agri-food vertical. Data in `src/data/bosqar.js`, `src/data/workplace.js`, `src/data/futurefood.js`.
- **Sidebar divider** between BOSQAR group views (command, orgchart, graph, workplace, futurefood) and Mplus-specific views — use `{ divider: true }` entry in NAV_ITEMS array.
- **Header label** adapts per view: 'BOSQAR' for command/orgchart, 'WORKPLACE' for workplace, 'FUTURE FOOD' for futurefood, 'MPLUS' for all others.
- **VerticalCard routing** in CommandView: each card's "Open Dashboard →" button calls `setView(vertical.view)` from VERTICALS array in bosqar.js — saves previousView so back button appears.
- 6 CLAs: CLA-OPS1 (capacity rebalance), CLA-OPS2 (Graia copilot), CLA-CX1 (account health), CLA-HR1 (retention), CLA-AI1 (quality guard), CLA-MEM1 (M&A integration)
- EGI ontology: 5-column KG — Function → Role → Process → Agent → Signal
- **Financials (PDF-aligned):** FY24 €226M / FY25 €258M / FY26B €311M · EBITDA 35/39/45 · Revenue CAGR 2019–2025: 40%
- **Key ratios:** EBITDA margin 15.1% FY25 · Cost/interaction €1.62 → target €1.40 · Rev/head €13.7K → target €22.5K
- Africa M&A: 51% of PLP Group (ZA, NA, MU) — March 2026, ~950 agents, €13.5M revenue
- HR transformation: LSS Yellow Belt (11 CEE countries, PwC), Graia AI Cert, CX Excellence, German upskilling (Goethe Institut), Team Lead Dev — 3,360 enrolled across 5 programmes
- Product accent colour: `#E07B2A` (warm amber) in tokens.js
- **ROI (updated):** €18.4M invested → €32.7M realised annual → €66M target annual → €94.2M 3yr NPV → 5.1x multiple → 8mo payback
- **WORKFLOW_ROI:** 9 granular workflows in `financials.js` — each has volume, automationRate, timeSavedPerUnit, agentCostPerHr, annualTimeSaving, costAvoidance, qualityUplift, revenueProtection, totalAnnual, investmentAllocated, roiMultiple
- **Change Management view:** 5 transformation pillars (OBP, AI penetration, rev productivity, geo expansion, workforce Tx) · milestone timeline (34 milestones) · change risk register (6 risks with heat map) · regional adoption metrics · quarterly progress chart. Data in `src/data/changeManagement.js`
- **ROI view tabs:** Summary (waterfall + savings trajectory) · By Category · Workflow Drill-Down (sortable table + detail panel) · By AI Agent (grouped by layer) · Payback Timeline (24mo bar chart, breakeven marker)
- **CSS keyframe pattern per view:** each view injects its own `<style>` tag with unique keyframe names (e.g. `wf-pulse`, `tx-pulse`, `roi-in`, `cmd-pulse`) — never share keyframes across views

---

### `15-12(a)_UAL` — United Airlines EGI Platform

**Key facts:**
- Exec team: CEO Scott Kirby, CFO Michael Leskinen, COO Torbjorn Enqvist, CCO Andrew Nocella, CCX David Kinzelman (replaced Linda Jojo, retired Jan 2025)
- 11 views: Command, Terraformation, Operations (key: `shield`), Commercial (key: `sword`), Knowledge Fabric, Executive Scorecard, Industry Benchmarks, Fleet Intelligence, AI Agent Registry, Value Realization, Settings
- Note: "Shield" and "Sword" are retired from all UI/display text. Internal view keys remain `shield`/`sword` (routing only, never user-visible)
- 10 AI agents across 3 thrusts: Operations / Commercial / Corporate Memory
- 8 CLAs: CLA-OPS1-3, CLA-COMM1-2, CLA-MEM1-2, CLA-REG1
- EGI ontology: 4 entity types — Asset, Passenger, Disruption, Regulatory
- Key data: EPS $11-$13 FY26, FCF $2.7B, A321XLR Summer 2026 (first U.S.), Polaris Studio Apr 2026 (787-9), Starlink 1,241 flights live, 46 Atlantic destinations
- "Terraformation" = 4-phase AI maturity journey (Sensing → Reasoning → Acting → Terraforming)
- Industry Benchmarks view: `BenchmarksView.jsx` + `benchmarkData.js` — 5 indexes: Cirium OTP (84.2%), Skytrax (60/100), ACSI (72), DOT Complaint Rate (1.18), NPS (40); master-detail layout with sparklines, 6-quarter trend chart, gap-to-target bar, EGI causal linkage, CLA chips
- ROI: $640M investment → $1,516M annual benefit → $4.2B 3yr NPV → 6.6x multiple; `roiData.js` + `RoiView.jsx`
- EGI Assistant: AI_KB array with 17 keyword-matched entries in `App.jsx`; each response includes in-app navigation link
- Companion docs: `_BRD/UAL_EGI_BRD.docx` (12 sections), `_Script/DEMO_SCRIPT.html` (11 sections + EGI Assistant + Timing + Q&A)
