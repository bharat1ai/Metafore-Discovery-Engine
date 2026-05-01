"""Build a self-contained, print-styled HTML executive report from in-memory stores.

No new LLM calls. Pulls from the existing graph, workflow, gap, conformance,
cross-document-insights, and SQLite live-data state. The frontend opens
GET /api/report/{graph_id} in a new tab; the user uses the browser's
"Save as PDF" / Print to produce a PDF.

Sections render conditionally — features that haven't been run are skipped.
"""
from __future__ import annotations

from datetime import datetime
from html import escape as _e
from typing import Any


# ── CSS (embedded so the report is one self-contained HTML file) ────────────

REPORT_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  /* Metafore brand */
  --brand:       #036868;
  --brand-dark:  #024F4F;
  --brand-mid:   #007F7F;
  --brand-light: #E6F4F4;
  --teal-bright: #00C4CC;
  /* Surfaces */
  --bg:          #FFFFFF;
  --bg-soft:     #F7FAFA;
  --bg-card:     #F0FAFA;
  --border:      #C4E0E0;
  --border-light:#E0EFEF;
  /* Text */
  --text:        #0f2020;
  --text-sec:    #4a6868;
  --text-muted:  #7a9a9a;
  /* Status quintet — design system colours, retuned for print legibility */
  --ok:          #00936b;
  --warn:        #b87f00;
  --critical:    #c2421a;
  --info:        #2563eb;
  --violet:      #7C4FE0;
  /* Type scale */
  --sans:        'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  --mono:        'IBM Plex Mono', ui-monospace, 'SF Mono', Consolas, monospace;
}
* { box-sizing: border-box; }
html, body { background: var(--bg-soft); }
body {
  font-family: var(--sans);
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--text);
  margin: 0;
  padding: 32px 40px 64px;
  max-width: 960px;
  margin-left: auto; margin-right: auto;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Floating action bar (hidden when printing) */
.report-actions {
  position: fixed;
  top: 16px; right: 16px;
  z-index: 10;
}
.btn-print {
  background: var(--brand);
  color: #fff;
  border: none;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(3,104,104,0.22);
  letter-spacing: 0;
  font-family: var(--sans);
  transition: background 0.12s, box-shadow 0.15s;
}
.btn-print:hover {
  background: var(--brand-dark);
  box-shadow: 0 6px 16px rgba(3,104,104,0.30);
}

/* Hero — page-1 cover. Solid teal (print-safe), brand wordmark, subtle accent bar */
.report-hero {
  position: relative;
  overflow: hidden;
  background: var(--brand);
  color: #fff;
  padding: 36px 36px 30px;
  border-radius: 14px;
  margin-bottom: 22px;
  page-break-after: always;
}
.report-hero::after {
  content: '';
  position: absolute;
  left: 36px; right: 36px; bottom: 22px;
  height: 2px;
  background: var(--teal-bright);
  opacity: 0.7;
}
.report-brand {
  position: relative; z-index: 1;
  display: flex; align-items: baseline; gap: 10px;
  font-family: var(--sans);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -0.01em;
  margin-bottom: 22px;
  color: #fff;
}
.report-brand b { font-weight: 700; }
.report-brand i {
  font-style: normal;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 10.5px;
  opacity: 0.78;
  border-left: 1px solid rgba(255,255,255,0.32);
  padding-left: 10px;
  margin-left: 4px;
}
.report-eyebrow {
  position: relative; z-index: 1;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.78);
  margin-bottom: 8px;
}
.report-title {
  position: relative; z-index: 1;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
  line-height: 1.18;
}
.report-subtitle {
  position: relative; z-index: 1;
  font-size: 11px;
  color: rgba(255,255,255,0.82);
  font-family: var(--mono);
  letter-spacing: 0;
}

/* Section cards — solid (print-safe), brand-teal mono section labels */
.report-section {
  background: var(--bg);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 20px 22px 18px;
  margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(3,104,104,0.04);
}
.report-section h2 {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--brand);
  margin: 0 0 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 10px;
}
.report-section h2::before {
  content: '';
  display: inline-block;
  width: 3px; height: 14px;
  background: var(--brand);
  border-radius: 2px;
}
.report-section h3 {
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin: 16px 0 8px;
  letter-spacing: -0.01em;
}
.report-section p { margin: 4px 0; }
.report-section strong { font-weight: 600; color: var(--text); }

/* KPI strip — IBM Plex Mono numerics, tightly tracked */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.kpi-card {
  background: var(--bg);
  border: 1px solid var(--border-light);
  border-radius: 9px;
  padding: 13px 14px;
  position: relative;
  overflow: hidden;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--brand);
}
.kpi-val {
  font-family: var(--mono);
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
  line-height: 1.05;
}
.kpi-label {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.10em;
  margin-top: 6px;
}

/* Tables */
table.report-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  margin: 6px 0 10px;
}
table.report-tbl th, table.report-tbl td {
  text-align: left;
  padding: 9px 10px;
  border-bottom: 1px solid var(--border-light);
  vertical-align: top;
}
table.report-tbl th {
  background: var(--bg-card);
  color: var(--brand);
  font-family: var(--mono);
  font-size: 9.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  border-bottom: 1px solid var(--border);
}
table.report-tbl tr:last-child td { border-bottom: none; }
table.report-tbl tr:nth-child(even) td { background: rgba(230,244,244,0.30); }

/* Badges — status quintet */
.badge {
  display: inline-block;
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 11px;
  letter-spacing: 0.06em;
  border: 1px solid;
  white-space: nowrap;
  text-transform: uppercase;
}
.badge-ok       { background: rgba(0, 200, 150, 0.10); color: var(--ok);       border-color: rgba(0, 200, 150, 0.35); }
.badge-warn     { background: rgba(255, 184, 0, 0.12); color: var(--warn);     border-color: rgba(255, 184, 0, 0.36); }
.badge-critical { background: rgba(255, 107, 74, 0.12); color: var(--critical); border-color: rgba(255, 107, 74, 0.36); }
.badge-info     { background: var(--brand-light);      color: var(--brand);    border-color: var(--border); }

/* Insight list */
ul.insight-list { padding-left: 0; list-style: none; margin: 6px 0; }
ul.insight-list li {
  padding: 10px 13px;
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
  border-left: 3px solid var(--brand);
  border-radius: 7px;
  margin-bottom: 6px;
  font-size: 11px;
  line-height: 1.55;
}
ul.insight-list li.cat-gap          { border-left-color: var(--warn); }
ul.insight-list li.cat-contradiction{ border-left-color: var(--critical); }
ul.insight-list li.cat-inconsistency{ border-left-color: var(--violet); }
ul.insight-list li.cat-missing      { border-left-color: var(--brand); }

/* Footer */
.report-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text-muted);
  text-align: center;
  letter-spacing: 0.04em;
  line-height: 1.7;
}

/* Print rules — break before each major section so each starts on its own page */
@media print {
  @page { margin: 16mm 14mm; }
  html, body { background: #fff; }
  body { padding: 0; max-width: none; }
  .no-print, .report-actions { display: none !important; }
  .report-section {
    page-break-inside: avoid;
    page-break-before: always;
    box-shadow: none;
    border-color: var(--border);
  }
  /* The hero owns page 1; the first section starts page 2 (already covered by page-break-after on hero). */
  .report-section:first-of-type { page-break-before: avoid; }
  .report-hero {
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
    box-shadow: none;
    page-break-after: always;
    margin-bottom: 0;
  }
  .kpi-card, .badge, ul.insight-list li {
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  table.report-tbl { page-break-inside: auto; }
  table.report-tbl tr { page-break-inside: avoid; }
  table.report-tbl tr:nth-child(even) td { background: transparent; }
}

/* Empty fallback */
.report-empty {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}
"""


# ── Helpers ─────────────────────────────────────────────────────────────────

def _e_or_dash(v) -> str:
    if v is None or v == "":
        return "—"
    return _e(str(v))


def _fmt_usd(n) -> str:
    if n is None:
        return "—"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"${round(n / 1_000)}K"
    return f"${n:.0f}"


def _avg_sla_compliance(pm: dict | None):
    """SLA compliance % derived from Process Mining: 100 − breach_rate_pct."""
    if not pm:
        return None
    rate = (pm.get("kpis") or {}).get("breach_rate_pct")
    if rate is None:
        return None
    return max(0, round(100 - rate))


def _health_score(coverage, sla, conform):
    parts = [(coverage, 0.40), (sla, 0.35), (conform, 0.25)]
    parts = [(v, w) for v, w in parts if v is not None]
    if not parts:
        return None
    total_w = sum(w for _, w in parts)
    return round(sum(v * w / total_w for v, w in parts))


def _band(score):
    if score is None:
        return ("—", "info")
    if score >= 80: return ("Strong",     "ok")
    if score >= 60: return ("Healthy",    "ok")
    if score >= 40: return ("At risk",    "warn")
    return ("Needs work", "critical")


# ── Section builders ────────────────────────────────────────────────────────

def _hero(graph_id: str, sources: list[dict] | None) -> str:
    # Windows strftime doesn't support %-d, so strip the leading zero manually
    today = datetime.now().strftime("%d %B %Y").lstrip("0")
    src_count = len(sources or [])
    src_text = ("1 source document" if src_count == 1
                else f"{src_count} source documents" if src_count > 1
                else "no source documents")
    return f"""
<header class="report-hero">
  <div class="report-brand"><b>Metafore</b><i>Discovery</i></div>
  <div class="report-eyebrow">Executive Report</div>
  <div class="report-title">Process Discovery</div>
  <div class="report-subtitle">Generated {_e(today)} · {_e(src_text)} · graph {_e(graph_id[:8])}…</div>
</header>"""


def _cover_documents(sources: list[dict] | None) -> str:
    if not sources:
        return ""
    rows = "".join(
        f"<tr><td>{_e(d.get('filename',''))}</td><td>{d.get('word_count', 0):,} words</td></tr>"
        for d in sources
    )
    return f"""
<section class="report-section">
  <h2>Source Documents</h2>
  <table class="report-tbl">
    <thead><tr><th>Document</th><th>Size</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>"""


def _executive_summary(graph, pm, gap, conformance) -> str:
    nodes = (graph or {}).get("nodes", []) or []
    edges = (graph or {}).get("edges", []) or []
    coverage = (gap or {}).get("coverage_score") if gap else None
    sla = _avg_sla_compliance(pm)
    conform = (conformance or {}).get("overall_conformance_rate") if conformance else None
    health = _health_score(coverage, sla, conform)
    band_label, band_cls = _band(health)

    pm_kpis = (pm or {}).get("kpis") or {}
    pm_cases = pm_kpis.get("total_cases") or 0
    pm_fitness = (pm or {}).get("conformance", {}).get("fitness")
    pm_bottleneck = pm_kpis.get("bottleneck_step") or "—"

    coverage_t = f"{coverage}" if coverage is not None else "n/a"
    sla_t = f"{sla}%" if sla is not None else "n/a"
    conform_t = f"{conform}%" if conform is not None else "n/a"
    health_t = f"{health}/100" if health is not None else "n/a"

    pm_narrative = ""
    if pm_kpis:
        pm_narrative = (
            f" Process Mining surfaced <strong>{pm_cases}</strong> operational cases "
            f"with a fitness of <strong>{pm_fitness if pm_fitness is not None else '—'}</strong> "
            f"and identified <strong>{_e(pm_bottleneck)}</strong> as the principal bottleneck."
        )

    return f"""
<section class="report-section">
  <h2>Executive Summary</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{len(nodes)}</div><div class="kpi-label">Graph nodes</div></div>
    <div class="kpi-card"><div class="kpi-val">{len(edges)}</div><div class="kpi-label">Relationships</div></div>
    <div class="kpi-card"><div class="kpi-val">{pm_cases}</div><div class="kpi-label">Operational cases</div></div>
    <div class="kpi-card"><div class="kpi-val">{health_t}</div><div class="kpi-label">Health score</div></div>
  </div>
  <p>
    Overall health: <span class="badge badge-{band_cls}">{_e(band_label.upper())}</span>
    &nbsp;·&nbsp; Coverage <strong>{coverage_t}</strong>
    &nbsp;·&nbsp; SLA compliance <strong>{sla_t}</strong>
    &nbsp;·&nbsp; Audit conformance <strong>{conform_t}</strong>
  </p>
  <p>
    The Discovery Engine extracted <strong>{len(nodes)}</strong> entities and
    <strong>{len(edges)}</strong> relationships from the source material.{pm_narrative}
  </p>
</section>"""


def _top_issues(gap, pm) -> str:
    items = []
    SEV_BY_CHECK = {
        "no_role": "critical", "unlinked_policy": "critical",
        "no_system": "warn", "unmeasured_objective": "warn", "orphaned": "warn",
    }
    for c in (gap or {}).get("checks", []) if gap else []:
        sev = SEV_BY_CHECK.get(c.get("check_id"), "info")
        if sev in ("critical", "warn") and (c.get("count") or 0) > 0:
            labels = ", ".join((c.get("affected_node_labels") or [])[:3])
            items.append((sev, c.get("title") or "", f"{c.get('count')} affected — {labels}"))
    # Process Mining deviation patterns (replaces workflow SLA breaches).
    pm_patterns = ((pm or {}).get("conformance") or {}).get("deviation_patterns") or []
    PM_SEV_TO_REPORT = {"critical": "critical", "high": "critical", "medium": "warn", "low": "info"}
    for p in pm_patterns:
        sev = PM_SEV_TO_REPORT.get(p.get("severity"), "info")
        if sev in ("critical", "warn"):
            items.append((sev, p.get("label") or "",
                          f"{p.get('case_count', 0)} case(s) · severity {p.get('severity', '—')}"))
    if not items:
        return f"""
<section class="report-section">
  <h2>Top Issues</h2>
  <p class="report-empty">No critical issues detected.</p>
</section>"""
    sev_order = {"critical": 0, "warn": 1, "info": 2}
    items.sort(key=lambda i: sev_order.get(i[0], 9))
    rows = "".join(
        f'<tr><td><span class="badge badge-{sev}">{_e(sev.upper())}</span></td>'
        f"<td>{_e(title)}</td><td>{_e(detail)}</td></tr>"
        for sev, title, detail in items[:8]
    )
    return f"""
<section class="report-section">
  <h2>Top Issues</h2>
  <table class="report-tbl">
    <thead><tr><th style="width:80px">Severity</th><th>Issue</th><th>Detail</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>"""


def _cross_doc_section(cross_doc: dict) -> str:
    insights = (cross_doc or {}).get("insights") or []
    if not insights:
        return ""
    items = "".join(
        f'<li class="cat-{_e(i.get("category","gap"))}">{_e(i.get("text",""))}</li>'
        for i in insights[:5]
    )
    return f"""
<section class="report-section">
  <h2>Cross-Document Insights</h2>
  <p>The following gaps and inconsistencies were detected across the uploaded source documents.</p>
  <ul class="insight-list">{items}</ul>
</section>"""


def _process_mining_section(pm: dict | None) -> str:
    if not pm or not pm.get("kpis"):
        return ""
    k = pm.get("kpis") or {}
    conf = pm.get("conformance") or {}
    activities = pm.get("activities") or []

    fitness = conf.get("fitness")
    fitness_pct = round(fitness * 100) if fitness is not None else None
    fitness_cls = "ok" if (fitness or 0) >= 0.80 else "warn" if (fitness or 0) >= 0.60 else "critical"
    breach_pct = round(k.get("breach_rate_pct") or 0)
    breach_cls = "ok" if breach_pct < 5 else "warn" if breach_pct < 20 else "critical"

    bottleneck_name = k.get("bottleneck_step") or "—"
    bottleneck_act = next((a for a in activities if a.get("id") == bottleneck_name), None)
    bottleneck_detail = ""
    if bottleneck_act:
        parts = []
        if bottleneck_act.get("breach_count"):
            parts.append(f"{bottleneck_act['breach_count']} SLA breach(es)")
        if bottleneck_act.get("role_mismatch_count"):
            parts.append(f"{bottleneck_act['role_mismatch_count']} wrong-role event(s)")
        bottleneck_detail = " · ".join(parts) if parts else "no breaches recorded"

    # Top deviation patterns
    pattern_rows = "".join(
        f"<tr>"
        f'<td><span class="badge badge-{("critical" if p.get("severity") in ("critical","high") else "warn" if p.get("severity")=="medium" else "info")}">{_e((p.get("severity") or "").upper())}</span></td>'
        f"<td>{_e(p.get('label',''))}</td>"
        f"<td>{p.get('case_count', 0)}</td>"
        f"</tr>"
        for p in (conf.get("deviation_patterns") or [])[:6]
    ) or '<tr><td colspan="3" class="report-empty">No deviation patterns detected.</td></tr>'

    # Top deviating cases
    case_rows = "".join(
        f"<tr>"
        f"<td style='font-family:var(--mono); font-size:10.5px;'>{_e((c.get('case_id') or '')[:8])}</td>"
        f"<td>{_e(c.get('applicant') or '—')}</td>"
        f"<td>{_e(c.get('deviation') or '')}</td>"
        f"<td>{c.get('tat_days') if c.get('tat_days') is not None else '—'}d</td>"
        f'<td><span class="badge badge-{("critical" if c.get("severity") in ("critical","high") else "warn")}">{_e((c.get("severity") or "").upper())}</span></td>'
        f"</tr>"
        for c in (conf.get("deviating_cases_top") or [])[:6]
    ) or '<tr><td colspan="5" class="report-empty">No deviating cases recorded.</td></tr>'

    # Status breakdown
    completed = k.get("completed_cases", 0)
    in_progress = k.get("in_progress_cases", 0)
    declined = k.get("declined_cases", 0)
    breakdown = f"<strong>{completed}</strong> disbursed · <strong>{in_progress}</strong> in-progress · <strong>{declined}</strong> declined"

    return f"""
<section class="report-section">
  <h2>Process Mining</h2>
  <p style="color:var(--text-sec); font-size:11.5px; margin-bottom:14px;">
    Operational behaviour mined from <strong>{k.get('total_step_executions', 0)}</strong> step executions
    across <strong>{k.get('total_cases', 0)}</strong> cases ({breakdown}).
  </p>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{k.get('total_cases', 0)}</div><div class="kpi-label">Cases</div></div>
    <div class="kpi-card"><div class="kpi-val">{k.get('median_tat_days', '—')}d</div><div class="kpi-label">Median TAT</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:var(--{fitness_cls})">{fitness_pct if fitness_pct is not None else '—'}%</div><div class="kpi-label">Fitness</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:var(--{breach_cls})">{breach_pct}%</div><div class="kpi-label">SLA breaches</div></div>
  </div>
  <h3>Bottleneck</h3>
  <p>
    <strong>{_e(bottleneck_name)}</strong> &nbsp;·&nbsp; {_e(bottleneck_detail or '—')}
  </p>
  <h3>Top Deviation Patterns</h3>
  <table class="report-tbl">
    <thead><tr><th style="width:90px">Severity</th><th>Pattern</th><th style="width:90px">Cases</th></tr></thead>
    <tbody>{pattern_rows}</tbody>
  </table>
  <h3>Top Deviating Cases</h3>
  <table class="report-tbl">
    <thead><tr><th style="width:90px">Case</th><th>Applicant</th><th>Deviation</th><th style="width:60px">TAT</th><th style="width:90px">Severity</th></tr></thead>
    <tbody>{case_rows}</tbody>
  </table>
</section>"""


def _gap_section(gap, blueprint) -> str:
    if not gap:
        return ""
    score = gap.get("coverage_score")
    label = gap.get("score_label", "")
    checks = [c for c in (gap.get("checks") or []) if (c.get("count") or 0) > 0]
    rows = "".join(
        f"<tr><td>{_e(c.get('title',''))}</td>"
        f"<td>{c.get('count',0)}</td>"
        f"<td>{_e(', '.join((c.get('affected_node_labels') or [])[:5]))}</td></tr>"
        for c in checks[:8]
    ) or '<tr><td colspan="3" class="report-empty">No gap items recorded.</td></tr>'

    bp_html = ""
    if blueprint:
        summary = blueprint.get("summary", "")
        steps = blueprint.get("next_steps") or []
        steps_html = "".join(f"<li>{_e(s)}</li>" for s in steps)
        bp_html = f"""
  <h3>Blueprint Summary</h3>
  <p>{_e(summary)}</p>
  <h3>Recommended Next Steps</h3>
  <ol>{steps_html}</ol>"""

    return f"""
<section class="report-section">
  <h2>Gap Analysis</h2>
  <p>Coverage score: <strong>{_e_or_dash(score)} / 100</strong> &nbsp;·&nbsp; <span class="badge badge-info">{_e(label.upper())}</span></p>
  <table class="report-tbl">
    <thead><tr><th>Gap check</th><th style="width:80px">Count</th><th>Affected entities</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {bp_html}
</section>"""


def _conformance_section(conf: dict) -> str:
    if not conf:
        return ""
    rate = conf.get("overall_conformance_rate", 0)
    sev_cls = "ok" if rate >= 70 else "warn" if rate >= 50 else "critical"
    confirmed = conf.get("confirmed_count", 0)
    deviated = conf.get("deviated_count", 0)
    not_found = conf.get("not_found_count", 0)
    deviations = [r for r in (conf.get("conformance_results") or []) if r.get("status") == "deviated"]
    rows = "".join(
        f"<tr><td>{_e(r.get('node_label',''))}</td>"
        f"<td>{_e(r.get('node_type',''))}</td>"
        f"<td>{_e((r.get('deviation_detail') or '')[:140])}</td></tr>"
        for r in deviations[:6]
    ) or '<tr><td colspan="3" class="report-empty">No deviations recorded.</td></tr>'

    summary = conf.get("summary", "")
    return f"""
<section class="report-section">
  <h2>Audit Check</h2>
  <p style="color:var(--text-sec); font-size:11.5px; margin-bottom:14px;">
    Audit document compared against the SOP-extracted graph using Claude.
    For data-vs-SOP analysis, see the Process Mining section above.
  </p>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{rate}%</div><div class="kpi-label">Audit match rate</div></div>
    <div class="kpi-card"><div class="kpi-val">{confirmed}</div><div class="kpi-label">Confirmed</div></div>
    <div class="kpi-card"><div class="kpi-val">{deviated}</div><div class="kpi-label">Deviated</div></div>
    <div class="kpi-card"><div class="kpi-val">{not_found}</div><div class="kpi-label">No evidence</div></div>
  </div>
  <p>Overall status: <span class="badge badge-{sev_cls}">{_e(('CONFORMING' if rate >= 70 else 'PARTIAL' if rate >= 50 else 'NON-CONFORMING'))}</span></p>
  <p>{_e(summary)}</p>
  <h3>Top Deviations</h3>
  <table class="report-tbl">
    <thead><tr><th>Entity</th><th style="width:90px">Type</th><th>Deviation</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>"""


def _live_data_section(summary: dict, steps: list[dict] | None) -> str:
    if not summary:
        return ""
    sb = summary.get("status_breakdown") or {}
    breakdown_html = " · ".join(
        f"<strong>{v}</strong> {_e(k)}" for k, v in sb.items()
    ) or "—"
    breaches = summary.get("top_breached_steps") or []
    breach_rows = "".join(
        f"<tr><td>{_e(b.get('step_name',''))}</td><td>{b.get('breach_count',0)}</td></tr>"
        for b in breaches[:5]
    )
    breach_section = f"""
  <h3>Top SLA Breach Steps</h3>
  <table class="report-tbl"><thead><tr><th>Step</th><th style="width:90px">Breaches</th></tr></thead>
    <tbody>{breach_rows}</tbody></table>""" if breaches else ""

    role_lines = []
    for s in steps or []:
        if (s.get("role_mismatch_count") or 0) > 0:
            role_lines.append(
                f"<li>{_e(s.get('step_name',''))}: {s.get('role_mismatch_count')} executions performed by a role other than {_e(s.get('expected_role',''))}.</li>"
            )
    role_html = ""
    if role_lines:
        role_html = "<h3>Role Mismatches Detected</h3><ul>" + "".join(role_lines) + "</ul>"

    return f"""
<section class="report-section">
  <h2>Live Operational Data</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{summary.get('total_applications', 0)}</div><div class="kpi-label">Loan applications</div></div>
    <div class="kpi-card"><div class="kpi-val">{_fmt_usd(summary.get('total_amount_usd', 0))}</div><div class="kpi-label">Total value</div></div>
    <div class="kpi-card"><div class="kpi-val">{summary.get('avg_cycle_time_hours','—')}h</div><div class="kpi-label">Avg cycle</div></div>
    <div class="kpi-card"><div class="kpi-val">{summary.get('step_executions_total', 0)}</div><div class="kpi-label">Step executions</div></div>
  </div>
  <p>Status breakdown: {breakdown_html}.</p>
  {breach_section}
  {role_html}
</section>"""


def _object_model_section(om: dict | None) -> str:
    if not om:
        return ""
    schema = om.get("json_schema") or {}
    entities = schema.get("entities") if isinstance(schema, dict) else None
    if not entities:
        # Legacy $defs / definitions format — surface only the entity count.
        defs = (schema.get("$defs") or schema.get("definitions") or {}) if isinstance(schema, dict) else {}
        entity_count = len(defs)
        if entity_count == 0:
            return ""
        names = list(defs.keys())[:8]
        return f"""
<section class="report-section">
  <h2>Object Model</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{entity_count}</div><div class="kpi-label">Entities</div></div>
  </div>
  <p>Entities: {_e(', '.join(names))}.</p>
</section>"""

    # BRD-format rendering — list each entity with field counts and a sample.
    rels = schema.get("relationships") or []
    rows = []
    for ent in entities[:8]:
        fields = ent.get("fields") or []
        pk_count = sum(1 for f in fields if "primary key" in (f.get("constraints") or "").lower())
        fk_count = sum(1 for f in fields if "foreign key" in (f.get("constraints") or "").lower())
        # Show first 3 non-audit field names as a sample
        sample_names = [
            f.get("name", "")
            for f in fields
            if "audit only" not in (f.get("constraints") or "").lower()
        ][:3]
        sample = ", ".join(sample_names)
        rows.append(
            f"<tr>"
            f"<td style='font-family:var(--mono); font-size:11px;'>{_e(ent.get('name', ''))}</td>"
            f"<td>{len(fields)}</td>"
            f"<td>{pk_count}</td>"
            f"<td>{fk_count}</td>"
            f"<td style='font-family:var(--mono); font-size:10.5px; color:var(--text-sec);'>{_e(sample)}</td>"
            f"</tr>"
        )
    rel_count = len(rels)
    return f"""
<section class="report-section">
  <h2>Object Model</h2>
  <p style="color:var(--text-sec); font-size:11.5px; margin-bottom:14px;">
    BRD-compliant entity model generated from the knowledge graph
    (<strong>{len(entities)}</strong> entities · <strong>{rel_count}</strong> relationships).
  </p>
  <table class="report-tbl">
    <thead>
      <tr><th>Entity</th><th style="width:60px">Fields</th><th style="width:50px">PK</th><th style="width:50px">FK</th><th>Sample fields</th></tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>"""


def _optimise_section(opt: dict | None) -> str:
    if not opt:
        return ""
    summary = opt.get("summary") or ""
    recs = opt.get("recommendations") or []
    if not recs:
        return ""
    rows = []
    for i, r in enumerate(recs[:6]):
        effort = (r.get("effort") or "").lower()
        eff_cls = "ok" if effort == "low" else "warn" if effort == "medium" else "critical"
        rows.append(
            f"<tr>"
            f"<td style='width:30px; font-family:var(--mono); color:var(--brand);'>{i+1:02d}</td>"
            f"<td>"
            f"<div style='font-weight:600;'>{_e(r.get('title', ''))}</div>"
            f"<div style='color:var(--text-sec); font-size:10.5px; margin-top:3px;'>{_e(r.get('rationale', ''))}</div>"
            f"</td>"
            f'<td><span class="badge badge-{eff_cls}">{_e(effort.upper() or "—")}</span></td>'
            f"<td style='font-family:var(--mono); font-size:10.5px;'>{_e(r.get('expected_impact', ''))}</td>"
            f"<td style='font-family:var(--mono); font-size:10.5px; color:var(--text-sec);'>{_e(r.get('target_step', '') or '—')}</td>"
            f"</tr>"
        )
    return f"""
<section class="report-section">
  <h2>AI Optimisation Suggestions</h2>
  <p style="color:var(--text-sec); font-size:11.5px; margin-bottom:14px;">{_e(summary)}</p>
  <table class="report-tbl">
    <thead>
      <tr><th>#</th><th>Recommendation</th><th style="width:70px">Effort</th><th>Impact</th><th>Target step</th></tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p style="color:var(--text-muted); font-size:10px; margin-top:8px; font-style:italic;">
    Generated via Claude Haiku from the current Process Mining snapshot.
  </p>
</section>"""


def _footer() -> str:
    return f"""
<div class="report-footer">
  Generated by Metafore — Discovery · {_e(datetime.now().strftime('%Y-%m-%d %H:%M'))}
  <br>This report consolidates the extracted graph, process-mining, gap, audit, object-model, and AI-optimisation data already produced by the engine. The only optional LLM call composed into it is the AI Optimisation section, when run.
</div>"""


def _error_page(title: str, msg: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Report unavailable</title>
<style>{REPORT_CSS}</style></head>
<body>
  <header class="report-hero"><div class="report-title">{_e(title)}</div><div class="report-subtitle">{_e(msg)}</div></header>
</body></html>"""


# ── Public entry point ──────────────────────────────────────────────────────

def render_report(
    graph_id: str,
    *,
    graph: dict | None,
    pm: dict | None = None,
    gap: dict | None = None,
    blueprint: dict | None = None,
    conformance: dict | None = None,
    cross_doc: dict | None = None,
    sources: list[dict] | None = None,
    object_model: dict | None = None,
    optimise: dict | None = None,
) -> str:
    """Compose the full HTML report. All inputs except graph_id are optional —
    sections render conditionally based on what state has been populated."""
    if not graph:
        return _error_page("Report unavailable", "No graph for this id. Upload a document and try again.")

    parts: list[str] = [
        _hero(graph_id, sources),
        _cover_documents(sources),
        _executive_summary(graph, pm, gap, conformance),
        _top_issues(gap, pm),
    ]
    if cross_doc:
        parts.append(_cross_doc_section(cross_doc))
    if pm and pm.get("kpis"):
        parts.append(_process_mining_section(pm))
    if gap:
        parts.append(_gap_section(gap, blueprint))
    if conformance:
        parts.append(_conformance_section(conformance))
    if object_model:
        parts.append(_object_model_section(object_model))
    if optimise:
        parts.append(_optimise_section(optimise))
    parts.append(_footer())

    body = "\n".join(p for p in parts if p)
    short = _e(graph_id[:8])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Discovery Engine — Executive Report ({short})</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
  <div class="report-actions no-print">
    <button class="btn-print" onclick="window.print()">📄 Save as PDF / Print</button>
  </div>
  {body}
</body>
</html>"""
