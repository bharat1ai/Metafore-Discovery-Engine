/* Discovery Engine — view modules (one screen per artboard) */

const { useState: uS } = React;

/* ── 1. KNOWLEDGE GRAPH view ─────────────────────────────── */
function KnowledgeGraphView({ nodeStyle = 'filled' }) {
  const [selected, setSelected] = uS(null);
  const sel = selected || DEMO_NODES[3]; // Underwriting Review default
  const incomingEdges = DEMO_EDGES.filter((e) => e.to === sel.id);
  const outgoingEdges = DEMO_EDGES.filter((e) => e.from === sel.id);
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar active="graph" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
          <Header />
          <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr 320px', flex: 1, minHeight: 0 }}>
            {/* left: upload + sources */}
            <div style={{ borderRight: `1px solid ${D.border}`, background: D.bg, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
              <SectionBar title="Documents" meta="2 SOURCES" />
              <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{
                  border: `1.5px dashed ${D.borderHi}`, borderRadius: 10,
                  padding: '18px 14px', textAlign: 'center', background: D.panelHi
                }}>
                  <div style={{ display: 'inline-flex', width: 38, height: 38, borderRadius: 10, background: D.brandLight, alignItems: 'center', justifyContent: 'center', marginBottom: 8, color: D.brand }}>
                    <Icon name="upload" size={18} />
                  </div>
                  <div style={{ fontSize: 12, color: D.textMid, marginBottom: 4 }}>Drop documents or <span style={{ color: D.brand, textDecoration: 'underline', cursor: 'pointer' }}>browse</span></div>
                  <div style={{ fontFamily: D.mono, fontSize: 10, color: D.textFaint, letterSpacing: '0.04em' }}>PDF · DOCX · TXT · max 20MB</div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {RECENT_DOCS.slice(0, 2).map((d) =>
                  <div key={d.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 11px', background: D.panel,
                    border: `1px solid ${D.border}`, borderRadius: 8
                  }}>
                      <div style={{ width: 28, height: 28, borderRadius: 6, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: D.brand, border: `1px solid ${D.border}` }}>
                        <Icon name="file" size={13} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontFamily: D.mono, fontSize: 11, color: D.text, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{d.name}</div>
                        <div style={{ fontSize: 10, color: D.textDim }}>{d.size} · {d.when}</div>
                      </div>
                      <Pill tone="brand">{d.kind}</Pill>
                    </div>
                  )}
                </div>

                <Btn kind="primary" icon="sparkles" style={{ width: '100%' }}>Extract Knowledge Graph</Btn>

                <div>
                  <Label style={{ marginBottom: 8 }}>Node Types</Label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                    {Object.entries(NODE_TYPES).map(([k, t]) =>
                    <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: D.textMid }}>
                        <span style={{ width: 11, height: 11, borderRadius: '50%', background: t.fill, border: `1.5px solid ${t.ring}` }} />
                        <span style={{ flex: 1 }}>{t.label}</span>
                        <span style={{ fontFamily: D.mono, fontSize: 10, color: D.textFaint }}>{DEMO_NODES.filter((n) => n.type === k).length}</span>
                      </div>
                    )}
                  </div>
                </div>

                <Card tight style={{ background: '#fff' }}>
                  <Label style={{ marginBottom: 6 }}>Cross-Document Insights</Label>
                  <div style={{ fontSize: 11, color: D.textMid, lineHeight: 1.5, marginBottom: 8 }}>
                    SOP and audit reference the <strong>same loan flow</strong> but disagree on AML sequencing.
                  </div>
                  <Btn kind="ghost" size="sm" icon="arrowRight">View 3 findings</Btn>
                </Card>
              </div>
            </div>

            {/* center: graph canvas */}
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
              <SectionBar title="Knowledge Graph"
              meta="EXTRACTED · 2 DOCS · 14:32"
              actions={
              <>
                    <Btn kind="ghost" size="sm" icon="filter">Filter</Btn>
                    <Btn kind="ghost" size="sm" icon="layers">Layout</Btn>
                  </>
              } />
              <div style={{ flex: 1, position: 'relative' }}>
                <GraphCanvas graph={DEMO_GRAPH} nodeStyle={nodeStyle}
                selectedId={sel.id} onNodeClick={setSelected}
                showMinimap />
              </div>
              {/* NLQ bar */}
              <div style={{
                padding: 14, borderTop: `1px solid ${D.border}`, background: D.bg,
                display: 'flex', flexDirection: 'column', gap: 8
              }}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Chip>Who approves sanctions?</Chip>
                  <Chip>Show all policies</Chip>
                  <Chip>What writes to Core Banking?</Chip>
                </div>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  background: D.bg, border: `1px solid ${D.borderHi}`,
                  borderRadius: 10, padding: '4px 4px 4px 14px',
                  boxShadow: D.shadowSm
                }}>
                  <Icon name="sparkles" size={14} color={D.brand} />
                  <input className="text-input" placeholder="Ask about your graph…"
                  style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', padding: '8px 0', fontSize: 13 }} />
                  <button style={{
                    width: 30, height: 30, borderRadius: 7, border: 'none', background: D.brand,
                    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
                  }}>
                    <Icon name="send" size={13} />
                  </button>
                </div>
              </div>
            </div>

            {/* right: inspector */}
            <NodeInspector node={sel} incoming={incomingEdges} outgoing={outgoingEdges} />
          </div>
        </div>
      </div>
    </Frame>);

}

function NodeInspector({ node, incoming = [], outgoing = [] }) {
  return (
    <div style={{ borderLeft: `1px solid ${D.border}`, background: D.bg, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      <div style={{ padding: '14px 16px', borderBottom: `1px solid ${D.border}`, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <TypeBadge type={node.type} />
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
          <button style={iconBtn()}><Icon name="eye" size={12} /></button>
          <button style={iconBtn()}><Icon name="close" size={12} /></button>
        </div>
      </div>
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: D.text, lineHeight: 1.3, marginBottom: 6 }}>{node.label}</div>
          <div style={{ fontSize: 12, color: D.textMid, lineHeight: 1.6 }}>
            Reviewed by Senior Underwriter against credit assessment, completeness checklist, and DTI threshold. Produces appraisal report and underwriting memo.
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1, padding: '8px 10px', background: D.panel, border: `1px solid ${D.border}`, borderRadius: 8 }}>
            <div style={{ fontFamily: D.mono, fontSize: 14, fontWeight: 700, color: D.text }}>{incoming.length}</div>
            <div style={{ fontSize: 10, color: D.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Incoming</div>
          </div>
          <div style={{ flex: 1, padding: '8px 10px', background: D.panel, border: `1px solid ${D.border}`, borderRadius: 8 }}>
            <div style={{ fontFamily: D.mono, fontSize: 14, fontWeight: 700, color: D.text }}>{outgoing.length}</div>
            <div style={{ fontSize: 10, color: D.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Outgoing</div>
          </div>
        </div>

        <div>
          <Label style={{ marginBottom: 6 }}>Connections</Label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {incoming.slice(0, 3).map((e, i) => {
              const f = DEMO_NODES.find((n) => n.id === e.from);
              return <div key={'i' + i} style={connRow()}>
                <Icon name="arrowRight" size={11} color={D.textDim} style={{ transform: 'rotate(180deg)' }} />
                <span style={{ flex: 1, fontSize: 11, color: D.text }}>{f?.label}</span>
                <span style={{ fontFamily: D.mono, fontSize: 9, color: D.textDim, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{e.label}</span>
              </div>;
            })}
            {outgoing.slice(0, 3).map((e, i) => {
              const t = DEMO_NODES.find((n) => n.id === e.to);
              return <div key={'o' + i} style={connRow()}>
                <Icon name="arrowRight" size={11} color={D.brand} />
                <span style={{ flex: 1, fontSize: 11, color: D.text }}>{t?.label}</span>
                <span style={{ fontFamily: D.mono, fontSize: 9, color: D.textDim, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{e.label}</span>
              </div>;
            })}
          </div>
        </div>

        <div>
          <Label style={{ marginBottom: 6 }}>Source</Label>
          <div style={{
            padding: '10px 12px', background: D.panel, borderLeft: `3px solid ${D.brand}`,
            borderRadius: '0 8px 8px 0', fontFamily: D.mono, fontSize: 11,
            color: D.textMid, lineHeight: 1.6, fontStyle: 'italic'
          }}>
            "Senior Underwriter conducts review of credit assessment, verifies completeness against checklist §3.2, and confirms DTI computation before sanctioning."
          </div>
          <div style={{ fontFamily: D.mono, fontSize: 10, color: D.textFaint, marginTop: 6, letterSpacing: '0.04em' }}>
            commercial_banking_loan_sop.docx · §3.4
          </div>
        </div>
      </div>
    </div>);

}
function iconBtn() {return {
    width: 26, height: 26, borderRadius: 6, border: `1px solid ${D.border}`,
    background: D.bg, color: D.textDim, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center'
  };}
function connRow() {return {
    display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px',
    background: D.bg, border: `1px solid ${D.border}`, borderRadius: 6
  };}

/* ── 2. WORKFLOWS view ─────────────────────────────────────── */
function WorkflowsView() {
  const [active, setActive] = uS('w1');
  const wf = WORKFLOWS.find((w) => w.id === active);
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar active="workflows" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
          <Header />
          <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', flex: 1, minHeight: 0 }}>
            <div style={{ borderRight: `1px solid ${D.border}`, background: D.bg, overflow: 'auto' }}>
              <SectionBar title="Workflows" meta={`${WORKFLOWS.length} GENERATED`} actions={<Btn kind="ghost" size="sm" icon="refresh">Regenerate</Btn>} />
              <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {WORKFLOWS.map((w) =>
                <button key={w.id} onClick={() => setActive(w.id)} style={{
                  textAlign: 'left', padding: 14, borderRadius: 10,
                  background: active === w.id ? D.brandLight : D.bg,
                  border: `1px solid ${active === w.id ? D.borderStrong : D.border}`,
                  cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 6
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Pill tone={w.tag === 'AS-IS' ? 'info' : w.tag === 'TO-BE' ? 'ok' : 'warn'}>{w.tag}</Pill>
                      <span style={{ marginLeft: 'auto', fontFamily: D.mono, fontSize: 10, color: D.textDim }}>{w.stepCount} steps</span>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: D.text, lineHeight: 1.35 }}>{w.label}</div>
                  </button>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, background: D.bgSolid }}>
              <SectionBar title={wf.label} meta={wf.tag} actions={<><Btn kind="ghost" size="sm" icon="download">Export</Btn><Btn kind="primary" size="sm" icon="play">Run scenario</Btn></>} />
              <div style={{ flex: 1, overflow: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 14 }}>
                {wf.steps.map((s, i) =>
                <div key={i} style={{ display: 'flex', alignItems: 'stretch', gap: 14 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
                      <div style={{
                      width: 40, height: 40, borderRadius: '50%',
                      background: '#fff', border: `2px solid ${D.brand}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: D.mono, fontWeight: 700, color: D.brand, fontSize: 13
                    }}>{String(i + 1).padStart(2, '0')}</div>
                      {i < wf.steps.length - 1 && <div style={{ width: 2, flex: 1, background: D.borderHi, marginTop: 4, marginBottom: -4 }} />}
                    </div>
                    <Card style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: D.text }}>{s}</span>
                        {wf.tag === 'TO-BE' && i === 1 && <Pill tone="ok">PARALLELISED</Pill>}
                        {wf.tag === 'AS-IS' && i === 4 && <Pill tone="warn">SLA 7d</Pill>}
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                        <Mini lbl="Owner" val="Credit Officer" />
                        <Mini lbl="System" val="LOS" />
                        <Mini lbl="P50 TAT" val={wf.tag === 'TO-BE' ? '1.4d' : '2.1d'} mono />
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Frame>);

}
function Mini({ lbl, val, mono }) {
  return <div>
    <div style={{ fontSize: 9, color: D.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 3 }}>{lbl}</div>
    <div style={{ fontFamily: mono ? D.mono : D.sans, fontSize: 12, fontWeight: 600, color: D.text }}>{val}</div>
  </div>;
}

/* ── 3. GAP ANALYSIS view ──────────────────────────────────── */
function GapAnalysisView() {
  const passed = GAP_CHECKS.filter((c) => c.status === 'pass').length;
  const score = Math.round(GAP_CHECKS.reduce((a, c) => a + (c.status === 'pass' ? c.weight : c.status === 'warn' ? c.weight * 0.5 : 0), 0));
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar active="gap" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
          <Header />
          <SectionBar title="Gap Analysis & Blueprint" meta={`LAST RUN · 14:32`} actions={<><Btn kind="ghost" size="sm" icon="refresh">Re-analyse</Btn><Btn kind="primary" size="sm" icon="sparkles">Generate Blueprint</Btn></>} />
          <div style={{ flex: 1, overflow: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16 }}>
              <Card>
                <Label>Coverage Score</Label>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 8 }}>
                  <div style={{ fontFamily: D.mono, fontSize: 48, fontWeight: 700, color: D.brand, letterSpacing: '-0.02em', lineHeight: 1 }}>{score}</div>
                  <div style={{ fontFamily: D.mono, fontSize: 18, color: D.textDim }}>/100</div>
                  <Pill tone="ok" style={{ marginLeft: 'auto' }}>HEALTHY</Pill>
                </div>
                <div style={{ marginTop: 14, height: 8, background: D.panel, borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ width: `${score}%`, height: '100%', background: `linear-gradient(90deg, ${D.brand}, ${D.tealBright})` }} />
                </div>
                <div style={{ marginTop: 14, display: 'flex', gap: 14, fontSize: 11 }}>
                  <span style={{ color: D.green, fontWeight: 600 }}>● {passed} pass</span>
                  <span style={{ color: '#b87f00', fontWeight: 600 }}>● {GAP_CHECKS.filter((c) => c.status === 'warn').length} warn</span>
                  <span style={{ color: '#c2421a', fontWeight: 600 }}>● {GAP_CHECKS.filter((c) => c.status === 'fail').length} fail</span>
                </div>
              </Card>
              <Card>
                <Label>Graph Statistics</Label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 10 }}>
                  {[
                  { l: 'Nodes', v: 24 }, { l: 'Edges', v: 24 }, { l: 'Density', v: '0.087' }, { l: 'Diameter', v: 6 },
                  { l: 'Roles', v: 5 }, { l: 'Systems', v: 3 }, { l: 'Policies', v: 3 }, { l: 'Orphans', v: 0 }].
                  map((s) =>
                  <div key={s.l}>
                      <div style={{ fontFamily: D.mono, fontSize: 18, fontWeight: 700, color: D.text, letterSpacing: '-0.02em' }}>{s.v}</div>
                      <div style={{ fontSize: 10, color: D.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginTop: 2 }}>{s.l}</div>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            <div>
              <Label style={{ marginBottom: 10 }}>Completeness Checks</Label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {GAP_CHECKS.map((c) =>
                <div key={c.id} style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '12px 14px', background: D.bg,
                  border: `1px solid ${D.border}`, borderRadius: 10
                }}>
                    <div style={{
                    width: 28, height: 28, borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: c.status === 'pass' ? 'rgba(0,200,150,0.12)' : c.status === 'warn' ? 'rgba(255,184,0,0.12)' : 'rgba(255,107,74,0.12)',
                    color: c.status === 'pass' ? '#00936b' : c.status === 'warn' ? '#b87f00' : '#c2421a'
                  }}>
                      <Icon name={c.status === 'pass' ? 'check' : 'alert'} size={13} strokeWidth={2.5} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: D.text }}>{c.label}</div>
                      <div style={{ fontSize: 11, color: D.textDim, marginTop: 2 }}>{c.detail}</div>
                    </div>
                    <Chip tone={c.status === 'pass' ? 'ok' : c.status === 'warn' ? 'warn' : 'bad'}>{c.status.toUpperCase()}</Chip>
                    <span style={{ fontFamily: D.mono, fontSize: 11, color: D.textDim, minWidth: 30, textAlign: 'right' }}>{c.weight}pts</span>
                  </div>
                )}
              </div>
            </div>

            <Card style={{ background: `linear-gradient(135deg, ${D.brandLight} 0%, ${D.bg} 60%)` }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: D.brand, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon name="sparkles" size={18} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: D.text, marginBottom: 4 }}>Blueprint Recommendation</div>
                  <div style={{ fontSize: 12, color: D.textMid, lineHeight: 1.6, marginBottom: 10 }}>
                    Two policy nodes (DTI ≤ 50%, AML Threshold) lack process linkage. Recommend connecting <strong>DTI ≤ 50%</strong> to <strong>Credit Assessment</strong> and adding a control point in <strong>Underwriting Review</strong>. Estimated coverage uplift: <span style={{ fontFamily: D.mono, fontWeight: 700, color: D.brand }}>+12pts</span>.
                  </div>
                  <Btn kind="primary" size="sm" icon="arrowRight">Apply 3 fixes to graph</Btn>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </Frame>);

}

/* ── 4. CONFORMANCE view ───────────────────────────────────── */
function ConformanceView() {
  const conf = CONFORMANCE_FINDINGS.filter((f) => f.status === 'confirmed').length;
  const dev = CONFORMANCE_FINDINGS.filter((f) => f.status === 'deviated').length;
  const nf = CONFORMANCE_FINDINGS.filter((f) => f.status === 'not_found').length;
  const total = conf + dev + nf;
  const rate = Math.round(100 * conf / total);
  const [tab, setTab] = uS('all');
  const filtered = tab === 'all' ? CONFORMANCE_FINDINGS : CONFORMANCE_FINDINGS.filter((f) => f.status === tab);
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar active="conf" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
          <Header stats={{ nodes: 24, edges: 24, conformance: rate }} />
          <SectionBar title="Conformance Checker" meta="EVIDENCE: loan_audit_report.docx · Q3 2024" actions={<><Btn kind="ghost" size="sm" icon="upload">New Evidence</Btn><Btn kind="primary" size="sm" icon="refresh">Re-run</Btn></>} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 420px', flex: 1, minHeight: 0 }}>
            <div style={{ overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* score row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 16, alignItems: 'stretch' }}>
                <Card style={{ minWidth: 240 }}>
                  <Label>Conformance Rate</Label>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8 }}>
                    <div style={{ fontFamily: D.mono, fontSize: 44, fontWeight: 700, color: rate >= 70 ? D.green : rate >= 50 ? '#b87f00' : '#c2421a', letterSpacing: '-0.02em', lineHeight: 1 }}>{rate}%</div>
                    <Pill tone={rate >= 70 ? 'ok' : rate >= 50 ? 'warn' : 'bad'}>{rate >= 70 ? 'PASS' : rate >= 50 ? 'PARTIAL' : 'BREACH'}</Pill>
                  </div>
                  <div style={{ fontSize: 11, color: D.textDim, marginTop: 8 }}>{conf} of {total} eligible nodes confirmed by evidence.</div>
                </Card>
                <Card>
                  <Label>Coverage Breakdown</Label>
                  <div style={{ height: 14, marginTop: 12, borderRadius: 999, overflow: 'hidden', display: 'flex', background: D.panel }}>
                    <div style={{ flex: conf, background: D.green }} />
                    <div style={{ flex: dev, background: D.red }} />
                    <div style={{ flex: nf, background: D.borderHi }} />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 14 }}>
                    <CovStat color={D.green} val={conf} lbl="Confirmed" />
                    <CovStat color={D.red} val={dev} lbl="Deviated" />
                    <CovStat color={D.borderHi} val={nf} lbl="No Evidence" />
                  </div>
                </Card>
              </div>

              {/* tabs */}
              <Tabs active={tab} onChange={setTab} items={[
              { id: 'all', label: 'All', count: total },
              { id: 'deviated', label: 'Deviations', count: dev },
              { id: 'confirmed', label: 'Confirmed', count: conf },
              { id: 'not_found', label: 'No Evidence', count: nf }]
              } style={{ padding: 0, borderBottom: 'none' }} />

              {/* findings */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {filtered.map((f, i) =>
                <Card key={i} style={{
                  borderLeft: `3px solid ${f.status === 'confirmed' ? D.green : f.status === 'deviated' ? D.red : D.borderHi}`,
                  background: D.bg
                }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 8 }}>
                      <TypeBadge type={f.type} />
                      <span style={{ fontSize: 13, fontWeight: 600, color: D.text }}>{f.node}</span>
                      <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                        {f.severity && <Pill tone={f.severity === 'critical' ? 'crit' : f.severity === 'high' ? 'bad' : 'warn'}>{f.severity}</Pill>}
                        <Pill tone={f.status === 'confirmed' ? 'ok' : f.status === 'deviated' ? 'bad' : 'info'}>{f.status.replace('_', ' ')}</Pill>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: D.textMid, lineHeight: 1.6, marginBottom: 8 }}>
                      <strong style={{ color: D.text }}>Expected · </strong>{f.expected}
                    </div>
                    {f.quote &&
                  <div style={{
                    padding: '8px 12px', background: D.panel,
                    borderLeft: `3px solid ${D.brand}`, borderRadius: '0 6px 6px 0',
                    fontFamily: D.mono, fontSize: 11, color: D.textMid, fontStyle: 'italic', lineHeight: 1.6
                  }}>"{f.quote}"</div>
                  }
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
                      <span style={{ fontFamily: D.mono, fontSize: 10, color: D.textFaint, letterSpacing: '0.04em' }}>{f.source}</span>
                      <Btn kind="ghost" size="sm" icon="graph" style={{ marginLeft: 'auto' }}>View in Graph</Btn>
                    </div>
                  </Card>
                )}
              </div>
            </div>

            {/* graph rail */}
            <div style={{ borderLeft: `1px solid ${D.border}`, background: D.bgSolid, display: 'flex', flexDirection: 'column' }}>
              <SectionBar title="Graph Overlay" meta="DEVIATIONS" />
              <div style={{ flex: 1, position: 'relative' }}>
                <GraphCanvas graph={DEMO_GRAPH}
                highlight={{ ids: ['p2', 'p3', 'p5', 'po1', 'po2', 'po3', 'd3', 'r3'], severity: 'critical' }}
                showLegend={false} />
              </div>
              <div style={{ padding: 12, borderTop: `1px solid ${D.border}`, display: 'flex', gap: 6 }}>
                <Btn kind="ghost" size="sm" style={{ flex: 1 }}>All</Btn>
                <Btn kind="primary" size="sm" style={{ flex: 1 }}>Deviated</Btn>
                <Btn kind="ghost" size="sm" style={{ flex: 1 }}>Confirmed</Btn>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Frame>);

}
function CovStat({ color, val, lbl }) {
  return <div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
      <span style={{ width: 9, height: 9, borderRadius: '50%', background: color }} />
      <span style={{ fontFamily: D.mono, fontSize: 18, fontWeight: 700, color: D.text }}>{val}</span>
    </div>
    <div style={{ fontSize: 10, color: D.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginTop: 2 }}>{lbl}</div>
  </div>;
}

/* ── 5. OBJECT MODEL view ──────────────────────────────────── */
function ObjectModelView() {
  const [tab, setTab] = uS('erd');
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar active="om" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
          <Header />
          <SectionBar title="Object Model" meta={`${OBJECT_MODEL_ENTITIES.length} ENTITIES · BRD §4`} actions={<><Btn kind="ghost" size="sm" icon="download">Pydantic</Btn><Btn kind="ghost" size="sm" icon="download">JSON Schema</Btn><Btn kind="primary" size="sm" icon="refresh">Regenerate</Btn></>} />
          <Tabs active={tab} onChange={setTab} items={[
          { id: 'erd', label: 'Entity Diagram' }, { id: 'pyd', label: 'Pydantic' }, { id: 'json', label: 'JSON Schema' }]
          } />
          <div style={{ flex: 1, overflow: 'auto', padding: 24, background: D.bgSolid }}>
            {tab === 'erd' &&
            <div style={{ position: 'relative', height: 560 }}>
                <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
                  {/* relationship lines */}
                  <line x1="280" y1="200" x2="380" y2="200" stroke={D.brand} strokeWidth="1.5" markerEnd="url(#erd-arr)" />
                  <line x1="660" y1="200" x2="760" y2="120" stroke={D.brand} strokeWidth="1.5" markerEnd="url(#erd-arr)" />
                  <line x1="660" y1="240" x2="760" y2="360" stroke={D.brand} strokeWidth="1.5" markerEnd="url(#erd-arr)" />
                  <defs>
                    <marker id="erd-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M0,0 L10,5 L0,10 z" fill={D.brand} />
                    </marker>
                  </defs>
                </svg>
                <Entity name="customer" x={20} y={120} fields={OBJECT_MODEL_ENTITIES[0].fields} />
                <Entity name="loan_application" x={380} y={100} fields={OBJECT_MODEL_ENTITIES[1].fields} />
                <Entity name="credit_assessment" x={760} y={20} fields={OBJECT_MODEL_ENTITIES[2].fields} />
                <Entity name="sanction" x={760} y={300} fields={OBJECT_MODEL_ENTITIES[3].fields} />
              </div>
            }
            {tab === 'pyd' &&
            <Card style={{ background: '#0f1415', color: '#e8f4f4', fontFamily: D.mono, fontSize: 12, lineHeight: 1.7, padding: 20 }}>
{`from pydantic import BaseModel, UUID4
from datetime import datetime
from enum import Enum
from decimal import Decimal

class KycStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"

class Customer(BaseModel):
    id: UUID4                                  # PK
    created_at: datetime
    pan: str                                   # varchar(10)
    kyc_status: KycStatus
    risk_segment: str

class LoanApplication(BaseModel):
    id: UUID4                                  # PK
    created_at: datetime
    customer_id: UUID4                         # FK → customer.id
    amount: Decimal
    purpose: str
    state: str                                 # OPEN | IN_PROGRESS | APPROVED | REJECTED`}
              </Card>
            }
            {tab === 'json' &&
            <Card style={{ background: '#0f1415', color: '#e8f4f4', fontFamily: D.mono, fontSize: 12, lineHeight: 1.7, padding: 20 }}>
{`{
  "entities": [
    {
      "name": "customer",
      "fields": [
        { "name": "id", "type": "UUID", "pk": true },
        { "name": "created_at", "type": "datetime", "not_null": true },
        { "name": "pan", "type": "varchar(10)" },
        { "name": "kyc_status", "type": "enum:[PENDING,VERIFIED,FAILED]" }
      ]
    }
  ],
  "relationships": [
    { "parent": "customer", "child": "loan_application",
      "via": "loan_application.customer_id = customer.id" }
  ]
}`}
              </Card>
            }
          </div>
        </div>
      </div>
    </Frame>);

}
function Entity({ name, x, y, fields }) {
  return (
    <div style={{
      position: 'absolute', left: x, top: y, width: 280,
      background: '#fff', border: `1px solid ${D.borderHi}`, borderRadius: 10,
      boxShadow: D.shadowMd, overflow: 'hidden'
    }}>
      <div style={{ padding: '9px 14px', background: D.brand, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
        <Icon name="box" size={13} color="#fff" />
        <span style={{ fontFamily: D.mono, fontSize: 12, fontWeight: 700, letterSpacing: '0.02em' }}>{name}</span>
      </div>
      <div>
        {fields.map((f, i) =>
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '7px 14px', borderTop: i === 0 ? 'none' : `1px solid ${D.border}`,
          fontFamily: D.mono, fontSize: 11
        }}>
            <span style={{
            width: 14, fontFamily: D.mono, fontSize: 9, fontWeight: 700,
            color: f.pk ? D.brand : f.fk ? D.violet : D.textFaint
          }}>{f.pk ? 'PK' : f.fk ? 'FK' : ''}</span>
            <span style={{ flex: 1, color: D.text, fontWeight: f.pk ? 700 : 500 }}>{f.name}</span>
            <span style={{ color: D.textDim }}>{f.type}</span>
          </div>
        )}
      </div>
    </div>);

}

/* ── 6. DASHBOARD view (invented overview) ─────────────────── */
function DashboardView() {
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar active="dash" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
          <Header graphName="Discovery Engine — Workspace Overview" />
          <SectionBar title="Workspace" meta="14 GRAPHS · 47 DOCS" actions={<><Btn kind="ghost" size="sm" icon="filter">All time</Btn><Btn kind="primary" size="sm" icon="plus">New Graph</Btn></>} />
          <div style={{ flex: 1, overflow: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 18 }}>
            {/* KPI strip */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
              {DASH_KPIS.map((k) =>
              <Card key={k.id} tight style={{ background: '#fff' }}>
                  <Label>{k.label}</Label>
                  <div style={{ fontFamily: D.mono, fontSize: 24, fontWeight: 700, color: D.text, letterSpacing: '-0.02em', marginTop: 6, lineHeight: 1 }}>{k.value}</div>
                  <div style={{ fontSize: 10, marginTop: 6, fontFamily: D.mono, color: k.tone === 'ok' ? '#00936b' : k.tone === 'warn' ? '#b87f00' : '#c2421a', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600 }}>
                    <Icon name={k.tone === 'bad' ? 'trendDown' : 'trend'} size={10} />
                    {k.delta}
                  </div>
                </Card>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 18 }}>
              {/* recent graphs */}
              <Card style={{ background: '#fff' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                  <Label>Recent Knowledge Graphs</Label>
                  <Btn kind="ghost" size="sm" icon="arrowRight" style={{ marginLeft: 'auto' }}>View all</Btn>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
                  {RECENT_DOCS.map((g) =>
                  <div key={g.id} style={{
                    display: 'flex', flexDirection: 'column', gap: 8,
                    padding: 14, background: D.panelHi,
                    border: `1px solid ${D.border}`, borderRadius: 10
                  }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Pill tone="brand">{g.kind}</Pill>
                        <span style={{ marginLeft: 'auto', fontFamily: D.mono, fontSize: 10, color: D.textFaint }}>{g.when}</span>
                      </div>
                      <div style={{ fontFamily: D.mono, fontSize: 12, color: D.text, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{g.name}</div>
                      <div style={{ height: 32, position: 'relative', background: D.panel, borderRadius: 6, overflow: 'hidden' }}>
                        {/* mini graph */}
                        <svg viewBox="0 0 100 32" style={{ width: '100%', height: '100%' }}>
                          {[0.6, 0.8, 0.4, 0.9, 0.7, 0.5].map((v, i) =>
                        <rect key={i} x={4 + i * 15} y={32 - v * 24} width={10} height={v * 24} fill={D.brand} opacity={0.3 + v * 0.5} />
                        )}
                        </svg>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: D.textDim }}>
                        <span style={{ fontFamily: D.mono }}>24 nodes</span>
                        <span style={{ fontFamily: D.mono }}>· 24 edges</span>
                        <Pill tone="ok" style={{ marginLeft: 'auto' }}>78%</Pill>
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              {/* activity */}
              <Card style={{ background: '#fff' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                  <Label>Activity</Label>
                  <span style={{ marginLeft: 'auto', fontFamily: D.mono, fontSize: 10, color: D.textFaint }}>LIVE</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[
                  { icon: 'check', tone: 'ok', t: 'Conformance check completed', s: 'loan_audit_report.docx · 47% rate', age: '2m' },
                  { icon: 'sparkles', tone: 'brand', t: 'AI Blueprint generated', s: 'Coverage uplift +12pts available', age: '14m' },
                  { icon: 'alert', tone: 'bad', t: 'Critical deviation flagged', s: 'AML sequencing in 9/23 cases', age: '1h' },
                  { icon: 'upload', tone: 'info', t: '2 documents uploaded', s: 'commercial_banking_loan_sop.docx', age: '2h' },
                  { icon: 'workflow', tone: 'ok', t: 'TO-BE workflow generated', s: 'Parallel KYC + Credit · saves 1.2d', age: '3h' }].
                  map((a, i) =>
                  <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                      <div style={{
                      width: 28, height: 28, borderRadius: 7, flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: a.tone === 'ok' ? 'rgba(0,200,150,0.12)' : a.tone === 'bad' ? 'rgba(255,107,74,0.12)' : a.tone === 'brand' ? D.brandLight : 'rgba(74,144,255,0.12)',
                      color: a.tone === 'ok' ? '#00936b' : a.tone === 'bad' ? '#c2421a' : a.tone === 'brand' ? D.brand : '#2563d4'
                    }}><Icon name={a.icon} size={13} /></div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: D.text, lineHeight: 1.4 }}>{a.t}</div>
                        <div style={{ fontSize: 11, color: D.textDim, lineHeight: 1.5, marginTop: 2 }}>{a.s}</div>
                      </div>
                      <span style={{ fontFamily: D.mono, fontSize: 10, color: D.textFaint, flexShrink: 0 }}>{a.age}</span>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              {/* node distribution */}
              <Card style={{ background: '#fff' }}>
                <Label style={{ marginBottom: 14 }}>Node Distribution · This Workspace</Label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {Object.entries(NODE_TYPES).map(([k, t]) => {
                    const count = DEMO_NODES.filter((n) => n.type === k).length;
                    const pct = count / DEMO_NODES.length * 100;
                    return (
                      <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 120 }}>
                          <span style={{ width: 10, height: 10, borderRadius: '50%', background: t.fill, border: `1.5px solid ${t.ring}` }} />
                          <span style={{ fontSize: 12, color: D.text, fontWeight: 500 }}>{t.label}</span>
                        </div>
                        <div style={{ flex: 1, height: 8, background: D.panel, borderRadius: 4, overflow: 'hidden' }}>
                          <div style={{ width: `${pct}%`, height: '100%', background: t.ring }} />
                        </div>
                        <span style={{ fontFamily: D.mono, fontSize: 12, fontWeight: 700, color: D.text, minWidth: 24, textAlign: 'right' }}>{count}</span>
                      </div>);

                  })}
                </div>
              </Card>

              {/* pulse summary */}
              <Card style={{ background: '#fff' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                  <Label>Pulse Recommendations</Label>
                  <Pill tone="bad" style={{ marginLeft: 'auto' }}>{PULSE_ITEMS.filter((p) => p.severity === 'critical').length} CRITICAL</Pill>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {PULSE_ITEMS.slice(0, 4).map((p) =>
                  <div key={p.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 11px', background: D.panelHi,
                    border: `1px solid ${D.border}`, borderRadius: 8,
                    borderLeft: `3px solid ${
                    p.severity === 'critical' ? D.red :
                    p.severity === 'high' ? '#f97316' :
                    p.severity === 'medium' ? D.amber : D.green}`
                  }}>
                      <Pill tone={p.severity === 'critical' ? 'crit' : p.severity === 'high' ? 'bad' : p.severity === 'medium' ? 'warn' : 'ok'}>{p.severity}</Pill>
                      <span style={{ flex: 1, fontSize: 12, color: D.text }}>{p.title}</span>
                      <span style={{ fontFamily: D.mono, fontSize: 10, color: D.textFaint, whiteSpace: 'nowrap' }}>{p.age}</span>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </Frame>);

}

/* ── 7. PULSE drawer (overlay sample) ─────────────────────── */
function PulseDrawerView() {
  return (
    <Frame>
      <div style={{ display: 'flex', flex: 1, minHeight: 0, position: 'relative' }}>
        <Sidebar active="graph" />
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, opacity: 0.6 }}>
          <Header />
          <div style={{ flex: 1, position: 'relative' }}>
            <GraphCanvas graph={DEMO_GRAPH} showLegend={false} />
          </div>
        </div>
        {/* drawer */}
        <div style={{
          position: 'absolute', top: 0, right: 0, bottom: 0, width: 420,
          background: D.bg, borderLeft: `1px solid ${D.border}`,
          boxShadow: '-12px 0 30px rgba(0,0,0,0.06)',
          display: 'flex', flexDirection: 'column',
          animation: 'mf-slide-in 0.25s ease'
        }}>
          <div style={{ padding: '14px 18px', borderBottom: `1px solid ${D.border}`, display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 30, height: 30, borderRadius: 8, background: D.brandLight,
              display: 'flex', alignItems: 'center', justifyContent: 'center', color: D.brand
            }}><Icon name="bell" size={14} /></div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: D.text }}>Pulse</div>
              <div style={{ fontSize: 10, color: D.textDim, fontFamily: D.mono, letterSpacing: '0.04em' }}>{PULSE_ITEMS.length} ACTIVE · 2 CRITICAL</div>
            </div>
            <button style={iconBtn()}><Icon name="close" size={12} /></button>
          </div>
          <div style={{ padding: 14, display: 'flex', gap: 6, overflowX: 'auto' }}>
            {['All', 'Critical', 'High', 'Medium', 'Low'].map((t, i) =>
            <button key={t} style={{
              padding: '5px 11px', fontFamily: D.sans, fontSize: 11, fontWeight: 600,
              background: i === 0 ? D.brand : D.panel, color: i === 0 ? '#fff' : D.textMid,
              border: `1px solid ${i === 0 ? D.brand : D.border}`, borderRadius: 999, cursor: 'pointer', whiteSpace: 'nowrap'
            }}>{t}</button>
            )}
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 14px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {PULSE_ITEMS.map((p) =>
            <Card key={p.id} style={{ background: D.bg, borderLeft: `3px solid ${
              p.severity === 'critical' ? D.red : p.severity === 'high' ? '#f97316' :
              p.severity === 'medium' ? D.amber : D.green}` }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
                  <Pill tone={p.severity === 'critical' ? 'crit' : p.severity === 'high' ? 'bad' : p.severity === 'medium' ? 'warn' : 'ok'}>{p.severity}</Pill>
                  <span style={{ marginLeft: 'auto', fontFamily: D.mono, fontSize: 10, color: D.textFaint }}>{p.age}</span>
                </div>
                <div style={{ fontSize: 13, fontWeight: 600, color: D.text, lineHeight: 1.4, marginBottom: 6 }}>{p.title}</div>
                <div style={{ fontSize: 11, color: D.textDim, marginBottom: 10 }}>Source: <span style={{ fontFamily: D.mono }}>{p.source}</span> · {p.count} affected</div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <Btn kind="primary" size="sm" icon="graph">View in Graph</Btn>
                  <Btn kind="ghost" size="sm">Dismiss</Btn>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </Frame>);

}

Object.assign(window, {
  KnowledgeGraphView, WorkflowsView, GapAnalysisView, ConformanceView, ObjectModelView, DashboardView, PulseDrawerView
});