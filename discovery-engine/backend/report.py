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
:root {
  --brand:       #036868;
  --brand-dark:  #024F4F;
  --brand-mid:   #007F7F;
  --brand-light: #E6F4F4;
  --bg:          #FFFFFF;
  --bg-soft:     #F7FAFA;
  --bg-card:     #F0FAFA;
  --border:      #C4E0E0;
  --border-light:#E0EFEF;
  --text:        #0f2020;
  --text-sec:    #4a6868;
  --text-muted:  #7a9a9a;
  --critical:    #b91c1c;
  --warn:        #b45309;
  --ok:          #15803d;
}
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 11.5px;
  line-height: 1.55;
  color: var(--text);
  background: var(--bg);
  margin: 0;
  padding: 28px 36px 60px;
  max-width: 920px;
  margin-left: auto; margin-right: auto;
}

/* Floating action bar (hidden when printing) */
.report-actions {
  position: fixed;
  top: 14px; right: 14px;
  z-index: 10;
}
.btn-print {
  background: var(--brand);
  color: #fff;
  border: none;
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(3,104,104,0.25);
}
.btn-print:hover { background: var(--brand-dark); }

/* Hero header */
.report-hero {
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-mid) 100%);
  color: #fff;
  padding: 26px 30px 22px;
  border-radius: 10px;
  margin-bottom: 18px;
}
.report-eyebrow {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.78);
  margin-bottom: 4px;
}
.report-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-bottom: 6px;
}
.report-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.84);
}

/* Section cards */
.report-section {
  background: var(--bg);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 14px;
}
.report-section h2 {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--brand);
  margin: 0 0 12px;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--brand-light);
}
.report-section h3 {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  margin: 14px 0 6px;
}
.report-section p { margin: 4px 0; }

/* KPI strip */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 10px 12px;
  text-align: center;
}
.kpi-val {
  font-size: 22px;
  font-weight: 800;
  color: var(--brand);
  font-family: 'SF Mono', Consolas, monospace;
  letter-spacing: -0.02em;
  line-height: 1.05;
}
.kpi-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: 4px;
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
  padding: 6px 8px;
  border-bottom: 1px solid var(--border-light);
  vertical-align: top;
}
table.report-tbl th {
  background: var(--bg-card);
  color: var(--text-sec);
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1.5px solid var(--border);
}
table.report-tbl tr:last-child td { border-bottom: none; }

/* Badges */
.badge {
  display: inline-block;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  letter-spacing: 0.04em;
  border: 1px solid;
  white-space: nowrap;
}
.badge-ok       { background: #dcfce7; color: var(--ok);       border-color: #86efac; }
.badge-warn     { background: #fef3c7; color: var(--warn);     border-color: #fcd34d; }
.badge-critical { background: #fee2e2; color: var(--critical); border-color: #fca5a5; }
.badge-info     { background: var(--brand-light); color: var(--brand); border-color: var(--border); }

/* Workflow card */
.wf-summary-card {
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
  border-left: 4px solid var(--brand);
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.wf-summary-card h3 { margin-top: 0; }
.wf-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 6px;
}
.wf-summary-stat-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.wf-summary-stat-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  font-family: 'SF Mono', Consolas, monospace;
}

/* Insight list */
ul.insight-list { padding-left: 0; list-style: none; margin: 6px 0; }
ul.insight-list li {
  padding: 7px 10px;
  background: var(--bg-soft);
  border: 1px solid var(--border-light);
  border-left: 3px solid var(--brand);
  border-radius: 5px;
  margin-bottom: 5px;
  font-size: 11px;
}
ul.insight-list li.cat-gap          { border-left-color: var(--warn); }
ul.insight-list li.cat-contradiction{ border-left-color: var(--critical); }
ul.insight-list li.cat-inconsistency{ border-left-color: #7C3AED; }
ul.insight-list li.cat-missing      { border-left-color: var(--brand); }

/* Footer */
.report-footer {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--border-light);
  font-size: 10px;
  color: var(--text-muted);
  text-align: center;
}

/* Print rules */
@media print {
  body { padding: 14px 18px 18px; max-width: none; }
  .no-print, .report-actions { display: none !important; }
  .report-section { page-break-inside: avoid; box-shadow: none; }
  .report-section + .report-section { page-break-before: auto; }
  .report-hero { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .kpi-card, .badge, .wf-summary-card, ul.insight-list li { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
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


def _avg_sla_compliance(workflows: list[dict] | None):
    if not workflows:
        return None
    vals = []
    for w in workflows:
        try:
            v = float(w.get("sla_compliance_rate", "").rstrip("%"))
            vals.append(v)
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    return round(sum(vals) / len(vals))


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
    today = datetime.now().strftime("%-d %B %Y") if hasattr(datetime, "strftime") else str(datetime.now().date())
    # Windows strftime doesn't support %-d; fall back manually:
    today = datetime.now().strftime("%d %B %Y").lstrip("0")
    src_count = len(sources or [])
    src_text = ("1 source document" if src_count == 1
                else f"{src_count} source documents" if src_count > 1
                else "no source documents")
    return f"""
<header class="report-hero">
  <div class="report-eyebrow">METAFORE WORKS · DISCOVERY ENGINE</div>
  <div class="report-title">Process Discovery Executive Report</div>
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


def _executive_summary(graph, workflows, gap, conformance, live_summary) -> str:
    nodes = (graph or {}).get("nodes", []) or []
    edges = (graph or {}).get("edges", []) or []
    coverage = (gap or {}).get("coverage_score") if gap else None
    sla = _avg_sla_compliance(workflows)
    conform = (conformance or {}).get("overall_conformance_rate") if conformance else None
    health = _health_score(coverage, sla, conform)
    band_label, band_cls = _band(health)

    coverage_t = f"{coverage}" if coverage is not None else "n/a"
    sla_t = f"{sla}%" if sla is not None else "n/a"
    conform_t = f"{conform}%" if conform is not None else "n/a"
    health_t = f"{health}/100" if health is not None else "n/a"

    return f"""
<section class="report-section">
  <h2>Executive Summary</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{len(nodes)}</div><div class="kpi-label">Graph nodes</div></div>
    <div class="kpi-card"><div class="kpi-val">{len(edges)}</div><div class="kpi-label">Relationships</div></div>
    <div class="kpi-card"><div class="kpi-val">{len(workflows or [])}</div><div class="kpi-label">Workflows</div></div>
    <div class="kpi-card"><div class="kpi-val">{health_t}</div><div class="kpi-label">Health score</div></div>
  </div>
  <p>
    Overall health: <span class="badge badge-{band_cls}">{_e(band_label.upper())}</span>
    &nbsp;·&nbsp; Coverage <strong>{coverage_t}</strong>
    &nbsp;·&nbsp; SLA compliance <strong>{sla_t}</strong>
    &nbsp;·&nbsp; Conformance <strong>{conform_t}</strong>
  </p>
  <p>
    The Discovery Engine extracted <strong>{len(nodes)}</strong> entities and
    <strong>{len(edges)}</strong> relationships from the source material and
    produced <strong>{len(workflows or [])}</strong> automation workflows with
    embedded ROI, automation scoring, and process variants.
    {('Live operational data from <strong>' + str(live_summary.get('total_applications', 0)) + '</strong> loan applications has been overlaid where step names match.') if live_summary else ''}
  </p>
</section>"""


def _top_issues(gap, workflows) -> str:
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
    for w in workflows or []:
        for s in w.get("as_is_steps") or []:
            if s.get("sla_status") == "breach":
                items.append(("critical", f"SLA breach: {s.get('name','')}",
                              f"{w.get('title','')} — current {s.get('current_avg','?')} vs target {s.get('sla_target','?')}"))
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


def _workflows_section(workflows: list[dict]) -> str:
    if not workflows:
        return ""
    cards = []
    total_value = 0
    for w in workflows:
        title = w.get("title", "")
        desc = w.get("description", "")
        complexity = w.get("complexity", "")
        sla = w.get("sla_target", "")
        current = w.get("current_avg", "")
        compliance = w.get("sla_compliance_rate", "")
        roi = w.get("roi") or {}
        roi_val = roi.get("headline_value_display") or "—"
        roi_basis = roi.get("headline_basis") or ""
        try:
            total_value += int(roi.get("headline_value_usd") or 0)
        except (TypeError, ValueError):
            pass
        auto = w.get("automation") or {}
        avg_auto = auto.get("average_score")
        pct_auto = auto.get("automatable_percentage")
        variants = w.get("variants") or []
        variant_a = next((v for v in variants if (v.get("divergence_point") is None)), None)
        variant_a_freq = variant_a.get("frequency_pct") if variant_a else None
        n_variants = len(variants)

        cards.append(f"""
<div class="wf-summary-card">
  <h3>{_e(title)} <span class="badge badge-info">{_e(complexity or '—').upper()}</span></h3>
  <p style="color:var(--text-sec); font-size:11px;">{_e(desc)}</p>
  <div class="wf-summary-grid">
    <div>
      <div class="wf-summary-stat-label">SLA target / current</div>
      <div class="wf-summary-stat-val">{_e_or_dash(sla)} / {_e_or_dash(current)}</div>
    </div>
    <div>
      <div class="wf-summary-stat-label">Compliance</div>
      <div class="wf-summary-stat-val">{_e_or_dash(compliance)}</div>
    </div>
    <div>
      <div class="wf-summary-stat-label">Estimated ROI</div>
      <div class="wf-summary-stat-val" style="color:var(--brand);">{_e(roi_val)}</div>
    </div>
  </div>
  <p style="font-size:10.5px; color:var(--text-sec); margin-top:8px;">
    <strong>ROI basis:</strong> {_e(roi_basis)}<br>
    <strong>Automation:</strong> avg {_e_or_dash(avg_auto)}/10 — {_e_or_dash(pct_auto)}% steps automatable
    {f' &nbsp;·&nbsp; <strong>Variants:</strong> {n_variants} — Variant A coverage {variant_a_freq}%' if n_variants else ''}
  </p>
</div>""")

    summary_total = _fmt_usd(total_value) if total_value > 0 else "—"
    return f"""
<section class="report-section">
  <h2>Workflow Automation Opportunities</h2>
  <p><strong>Total estimated annual value (sum of all workflows): {summary_total}</strong></p>
  {''.join(cards)}
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
  <h2>Conformance Results</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{rate}%</div><div class="kpi-label">Conformance</div></div>
    <div class="kpi-card"><div class="kpi-val">{confirmed}</div><div class="kpi-label">Confirmed</div></div>
    <div class="kpi-card"><div class="kpi-val">{deviated}</div><div class="kpi-label">Deviated</div></div>
    <div class="kpi-card"><div class="kpi-val">{not_found}</div><div class="kpi-label">Not found</div></div>
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


def _footer() -> str:
    return f"""
<div class="report-footer">
  Generated by Metafore Works · Discovery Engine — {_e(datetime.now().strftime('%Y-%m-%d %H:%M'))}
  <br>This report consolidates extracted graph, workflow, gap, conformance, cross-document and operational data already produced by the engine. No additional LLM calls were made to compose it.
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
    workflows: list[dict] | None,
    gap: dict | None,
    blueprint: dict | None,
    conformance: dict | None,
    cross_doc: dict | None,
    sources: list[dict] | None,
    live_summary: dict | None,
    live_steps: list[dict] | None,
) -> str:
    """Compose the full HTML report. All inputs except graph_id are optional —
    sections render conditionally based on what state has been populated."""
    if not graph:
        return _error_page("Report unavailable", "No graph for this id. Upload a document and try again.")

    parts: list[str] = [
        _hero(graph_id, sources),
        _cover_documents(sources),
        _executive_summary(graph, workflows, gap, conformance, live_summary),
        _top_issues(gap, workflows),
    ]
    if cross_doc:
        parts.append(_cross_doc_section(cross_doc))
    if workflows:
        parts.append(_workflows_section(workflows))
    if gap:
        parts.append(_gap_section(gap, blueprint))
    if conformance:
        parts.append(_conformance_section(conformance))
    if live_summary:
        parts.append(_live_data_section(live_summary, live_steps))
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
