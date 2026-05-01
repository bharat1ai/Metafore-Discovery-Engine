# Metafore One — Universal Design Template

A drop-in style/structure reference distilled from all MetaforeOne apps (MWorks Airtel, AI SOC, Orange FR EGI, UAL EGI, Roaming CEM, TelcoAssure, RingCentral). Use this when starting a new vertical or aligning an existing one.

---

## 1. Brand Identity

| Token | Value | Use |
|---|---|---|
| `brand` | `#036868` | Header bar, primary buttons, primary text on light |
| `brandMid` | `#007F7F` | Sidebar (48px rail), secondary actions |
| `brandDark` | `#024F4F` | Hover/pressed primary |
| `brandLight` | `#E6F4F4` | Light teal fills, hover backgrounds |
| `tealAccent` | `#00989E` | Links, accents |
| `tealBright` | `#00C4CC` | Active glow, focus rings |
| `green` | `#00C896` | OK / healthy |
| `amber` | `#FFB800` | Warning |
| `red` | `#FF6B4A` | Critical / breach |
| `blue` | `#4A90FF` | Info / probe nodes |
| `violet` | `#7C4FE0` | Secondary categorical |

> **Never** use generic dark blue. Always teal palette. **One** is sentence case (never "ONE").

---

## 2. Typography

```js
display: "'GT America','Inter',-apple-system,sans-serif"
sans:    "'GT America','Inter',-apple-system,sans-serif"
mono:    "'IBM Plex Mono','SF Mono','Consolas',monospace"
```

- **Self-hosted** OTF/TTF in `public/fonts/`. **No Google Fonts.**
- All numbers, KPIs, IDs, chips → **mono** (IBM Plex Mono).
- All prose, headings, labels → **GT America** (fallback Inter).
- Available extras: Brut Grotesque (display variant).

### Type scale
| Role | Size | Weight | Tracking |
|---|---|---|---|
| Page title | 22–24px | 700 | normal |
| App-name "One" in header | 17px | 700 | normal |
| Product name in header | 13px | 300 | `0.12em` |
| Section heading | 15–16px | 600 | normal |
| Body | 13–14px | 400 | normal |
| Label / caption | 11–12px | 500 | `0.04em` uppercase optional |
| KPI big number | 28–36px | 700 mono | `-0.02em` |
| Chip / badge | 11px | 600 mono | `0.06em` upper |

---

## 3. Surfaces & Tokens (`src/theme/tokens.js`)

```js
// Glassmorphic white — copy verbatim
bg: "#FFFFFF", bgSolid: "#F8FAFA",
panel:    "rgba(0,107,111,0.06)",
panelHi:  "rgba(0,107,111,0.03)",
panelSolid:"rgba(0,107,111,0.09)",
border:   "rgba(0,107,111,0.12)",
borderHi: "rgba(0,107,111,0.20)",

text:"#1A1A1A", textMid:"#404040", textDim:"#666666", textFaint:"#999999",

shadowSm:"0 1px 2px 0 rgba(0,0,0,0.05)",
shadowMd:"0 4px 6px -1px rgba(0,0,0,0.08)",
shadowLg:"0 10px 15px -3px rgba(0,0,0,0.08)",
shadowTeal:"0 10px 30px rgba(0,107,111,0.12)",

r: { sm:4, md:8, lg:12, xl:16, xxl:24 },
glass: "backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);",
```

Card pattern: `background: D.panel; border: 1px solid D.border; border-radius: 12px; padding: 16px; backdrop-filter: blur(16px);`

---

## 4. Layout System

```
┌─────┬──────────────────────────────┬──────────────────┐
│ Sb  │  Header  (#036868, 56–64px)  │                  │
│ 48px├──────────────────────────────┤  Right Panel     │
│ #007├                              │  (collapsible)   │
│ F7F │  Main content (flex:1)       │  expanded 520px  │
│     │                              │  collapsed 48px  │
│     │                              │                  │
└─────┴──────────────────────────────┴──────────────────┘
```

- **Sidebar:** fixed 48px, `D.brandMid`, icon-only, white icons.
- **Header:** `D.brand`, logo + "One" + product name + stats chips on right.
- **Main:** `flex: 1`, hosts active view.
- **Right panel:** AiAssistant (flex:1, scrollable) above PulseEngine (380px, flexShrink:0).

### Header HTML pattern
```jsx
<img src="/metafore-logo-horizontal.png" style={{ height: 22, objectFit: 'contain' }} />
<span style={{ fontWeight: 700, fontSize: 17, color: '#fff' }}>One</span>
<span style={{ fontWeight: 300, fontSize: 13, color: 'rgba(255,255,255,0.7)', letterSpacing: '0.12em' }}>
  {' '}PRODUCTNAME
</span>
{/* right-aligned stats chips: "8 CLAs Active", HITL count, "AI L3" */}
```

### Logo assets (in `public/`)
- `metafore-logo.png` — 34×34 square mark (sidebar)
- `metafore-logo-horizontal.png` — wide white mark (header)

---

## 5. Spacing & Radius

| Token | px |
|---|---|
| Tight (chip padding y) | 4 |
| Compact (chip padding x, card inner gap) | 8 |
| Default (card padding) | 16 |
| Section gap | 24 |
| View gutter | 32 |
| Radius `sm` / `md` / `lg` / `xl` / `xxl` | 4 / 8 / 12 / 16 / 24 |

---

## 6. Components — canonical patterns

### Button
```jsx
// Primary
{ background: D.brand, color: '#fff', padding: '8px 14px', borderRadius: 8,
  fontWeight: 600, fontSize: 13, border: 0 }
// Secondary
{ background: D.brandMid, color: '#fff', ...same }
// Ghost
{ background: 'transparent', color: D.brand, border: `1px solid ${D.border}`, ...same }
```

### StatusBadge
Severity → color map: `critical`→red, `high`→amber, `medium`→amber-dim, `low`→green. Pulse via CSS `@keyframes` only.

### Chip (mono)
```jsx
{ fontFamily: D.mono, fontSize: 11, padding: '3px 8px',
  background: D.panel, border: `1px solid ${D.border}`,
  borderRadius: 6, letterSpacing: '0.04em' }
```

### Card / SectionCard
```jsx
{ background: D.panel, border: `1px solid ${D.border}`,
  borderRadius: 12, padding: 16, boxShadow: D.shadowSm,
  backdropFilter: 'blur(16px)' }
```

### Icon
`<Icon name="GitBranch" size={14} color={D.brand} />` — Lucide names as strings.

---

## 7. Animation rules (CRITICAL)

- **Never** `setInterval`/`useState` for pulse, blink, glow — causes tree re-renders.
- **Always** inject CSS `@keyframes` once at module level with a unique id (`mf-pulse-style`, `mf-glow-style`, etc.).
- Each view uses **uniquely-named** keyframes (`mf-soc-pulse`, `mf-rca-traverse`) — never share names across views.
- **Exception:** self-contained components (PulseEngine live feed, LiveEventFeed) may use `setInterval`.

```js
const id = 'mf-pulse-style';
if (!document.getElementById(id)) {
  const el = document.createElement('style'); el.id = id;
  el.textContent = '@keyframes mf-pulse {0%,100%{opacity:1}50%{opacity:.2}}';
  document.head.appendChild(el);
}
// usage
<span style={{ animation: 'mf-pulse 1.8s ease-in-out infinite' }} />
```

---

## 8. State / Stack rules

- React 18 + Vite 6 + **Zustand 5** + plain JS (no TS).
- **Per-field primitive selectors only** in Zustand 5:
  ```js
  const view = useAppStore(s => s.view);          // ✅
  const { view } = useAppStore(s => ({view:s.view})); // ❌ infinite loop
  ```
- All data in-memory in `src/data/` — no backend, no API.

---

## 9. Navigation contract

| Action | Method | Saves previousView | Back button |
|---|---|---|---|
| Sidebar icon | `setViewDirect(view)` | No | No |
| In-app link/button | `setView(view)` | Yes | Yes |
| Back | `goBack()` | clears | — |

Back button renders in App.jsx title row when `previousView !== null`. Only `Sidebar.jsx` calls `setViewDirect`.

---

## 10. Folder convention

```
src/
  assets/        SVG, logo fallbacks
  components/
    dashboard/   Main panels per view
    inspector/   Detail/drilldown views
    ui/          Sidebar, AiAssistant, Primitives, Icon
  data/          In-memory datasets
  stores/        Zustand
  theme/         tokens.js  ← copy from any existing app
public/
  fonts/         OTF/TTF (copy from MWorks_Airtel_Source)
  metafore-logo.png
  metafore-logo-horizontal.png
```

---

## 11. New-solution setup checklist

Run automatically (no user prompt):
1. Copy `public/fonts/` from `MWorks_Airtel_Source/public/fonts/`.
2. Copy `@font-face` block from `MWorks_Airtel_Source/index.html`.
3. Copy `src/theme/tokens.js` verbatim.
4. Copy logo PNGs into `public/`.
5. `npm install`.
6. Wire Sidebar (48px, `D.brandMid`) + Header (`D.brand`, logo + "One" + PRODUCT).
7. Right panel: AiAssistant + PulseEngine (380px).
8. Create `_BRD/` and `_Script/DEMO_SCRIPT.html` companions.

---

## 12. Companion documents (every solution)

```
[solution]/
  _BRD/[Name]_BRD.md
  _Script/DEMO_SCRIPT.html   ← standalone, brand colors, sticky tabs
```

BRD sections: Exec Summary · Business Context · Solution Scope · Functional Reqs · CLA Registry · Maturity Model · Data & Integration · ROI · Governance/HITL · Deployment · Out of Scope · Glossary.

Demo script sections per view: *What to show / What to say / Key proof points / Anticipated questions* + Timing guide + Q&A prep. Demo flow lives **outside** the app, never as in-app overlay.

---

## 13. Do-not list (lessons learned)

1. No object selectors in Zustand 5.
2. No `setInterval` in shared render trees (use CSS keyframes).
3. No stray `]` in data arrays — lint before commit.
4. No RCA finding text below SVG — push to right panel via store.
5. No 4-column rigid graph — 6-column organic with staggered `cy`.
6. No Google Fonts — self-host.
7. No shared keyframe names across views.
8. No "ONE" — always "One".
9. No dark blue primary — always teal.
10. No backend — all data in `src/data/`.
