/* Process Mining (Celonis-style) view — adds to Workflows artboard family */

const { useState: uSp, useMemo: uMp } = React;

function ProcessMiningView() {
  const [view, setView] = uSp('map'); // map | variants | conformance
  const [selectedVariant, setSelectedVariant] = uSp('v1');

  return (
    <Frame>
      <div style={{display:'flex', flex:1, minHeight:0}}>
        <Sidebar active="workflows"/>
        <div style={{display:'flex', flexDirection:'column', flex:1, minWidth:0}}>
          <Header graphName="Commercial Banking · Loan Origination · Process Mining"
                  stats={{nodes:9, edges:12, coverage:78, conformance:81}}/>
          <SectionBar title="Process Explorer" meta="1,247 CASES · 12 ACTIVITIES · LAST 90 DAYS"
            actions={<>
              <Btn kind="ghost" size="sm" icon="filter">Filter cases</Btn>
              <Btn kind="ghost" size="sm" icon="refresh">Refresh</Btn>
              <Btn kind="primary" size="sm" icon="sparkles">Optimise</Btn>
            </>}/>

          {/* KPI strip */}
          <div style={{
            display:'grid', gridTemplateColumns:'repeat(6, 1fr)', gap:12,
            padding:'14px 20px', borderBottom:`1px solid ${D.border}`, background:D.bg,
          }}>
            {PM_KPIS.map(k=>(
              <div key={k.id} style={{padding:'10px 12px', background:D.panelHi, border:`1px solid ${D.border}`, borderRadius:10}}>
                <div style={{fontSize:10, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em'}}>{k.label}</div>
                <div style={{fontFamily:D.mono, fontSize:22, fontWeight:700, color:D.text, letterSpacing:'-0.02em', marginTop:4, lineHeight:1}}>{k.value}</div>
                <div style={{fontSize:10, marginTop:5, fontFamily:D.mono, color: k.tone==='ok'?'#00936b':k.tone==='warn'?'#b87f00':'#c2421a', display:'flex', alignItems:'center', gap:4, fontWeight:600}}>
                  <Icon name={k.tone==='bad'?'trendDown':'trend'} size={10}/>
                  {k.delta}
                </div>
              </div>
            ))}
          </div>

          {/* tabs */}
          <Tabs active={view} onChange={setView} items={[
            {id:'map', label:'Process Map'},
            {id:'variants', label:'Variants', count:PM_VARIANTS.length},
            {id:'conformance', label:'Conformance'},
          ]}/>

          {view==='map' && <ProcessMap/>}
          {view==='variants' && <VariantsView selected={selectedVariant} setSelected={setSelectedVariant}/>}
          {view==='conformance' && <ProcessConformance/>}
        </div>
      </div>
    </Frame>
  );
}

/* ── Process Map (animated edges + thickness encodes case count) ── */
function ProcessMap() {
  const byId = uMp(()=>Object.fromEntries(PM_ACTIVITIES.map(a=>[a.id,a])), []);
  const maxCases = Math.max(...PM_EDGES.map(e=>e.cases));
  const nodeW = 168, nodeH = 64;
  return (
    <div style={{flex:1, display:'grid', gridTemplateColumns:'1fr 320px', minHeight:0}}>
      <div style={{position:'relative', background:D.bgSolid, overflow:'hidden'}}>
        {/* dot grid */}
        <div style={{position:'absolute', inset:0, opacity:0.5,
          backgroundImage:`radial-gradient(${D.border} 1px, transparent 1px)`, backgroundSize:'24px 24px'}}/>
        <svg viewBox="0 0 1380 480" preserveAspectRatio="xMidYMid meet"
             style={{position:'absolute', inset:0, width:'100%', height:'100%'}}>
          <defs>
            <marker id="pm-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={D.brandMid}/>
            </marker>
            <marker id="pm-arr-slow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={D.red}/>
            </marker>
            <marker id="pm-arr-rew" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L10,5 L0,10 z" fill={D.amber}/>
            </marker>
          </defs>
          {/* edges */}
          {PM_EDGES.map((e,i)=>{
            const a=byId[e.f], b=byId[e.t];
            const w = 1 + (e.cases/maxCases)*7;
            const color = e.slow ? D.red : e.rework ? D.amber : D.brandMid;
            const marker = e.slow ? 'url(#pm-arr-slow)' : e.rework ? 'url(#pm-arr-rew)' : 'url(#pm-arr)';
            // straight or curved edges
            const isRework = e.rework;
            // approach node edges with a small offset
            const ax = a.x + nodeW/2, ay = a.y + nodeH;
            const bx = b.x + nodeW/2, by = b.y;
            const path = isRework
              ? `M ${a.x} ${a.y+nodeH/2} C ${a.x-80} ${a.y+nodeH/2}, ${a.x-80} ${b.y+nodeH+40}, ${bx} ${b.y+nodeH}`
              : `M ${ax} ${ay} C ${ax} ${ay+30}, ${bx} ${by-30}, ${bx} ${by}`;
            const midX = (ax+bx)/2, midY = (ay+by)/2;
            return (
              <g key={i}>
                <path d={path} stroke={color} strokeWidth={w} fill="none"
                  opacity={0.32 + 0.5*(e.cases/maxCases)}
                  markerEnd={marker}
                  strokeDasharray={isRework ? '6 4' : 'none'}/>
                {/* edge label */}
                <g transform={`translate(${isRework?a.x-100:midX}, ${isRework?b.y+nodeH+18:midY})`}>
                  <rect x="-32" y="-10" width="64" height="22" rx="4"
                    fill="#fff" stroke={color} strokeWidth="1" opacity="0.95"/>
                  <text x="0" y="-1" textAnchor="middle"
                    fontFamily={D.mono} fontSize="10" fontWeight="700" fill={color}>
                    {e.cases.toLocaleString()}
                  </text>
                  <text x="0" y="9" textAnchor="middle"
                    fontFamily={D.mono} fontSize="8" fill={D.textDim}>
                    {e.med < 24 ? `${e.med.toFixed(1)}h` : `${(e.med/24).toFixed(1)}d`}
                  </text>
                </g>
              </g>
            );
          })}
          {/* nodes */}
          {PM_ACTIVITIES.map(a=>{
            const isStart = a.id==='a1', isEnd = a.id==='a9' || a.id==='a8';
            const isException = a.id==='a8' || a.id==='a6';
            const fill = isException ? '#FFF1ED' : '#fff';
            const stroke = isException ? D.red : D.brand;
            return (
              <g key={a.id} transform={`translate(${a.x},${a.y})`} style={{cursor:'pointer'}}>
                {/* shadow */}
                <rect x="0" y="0" width={nodeW} height={nodeH} rx="10"
                  fill="rgba(0,0,0,0.04)" transform="translate(0,2)"/>
                <rect x="0" y="0" width={nodeW} height={nodeH} rx="10"
                  fill={fill} stroke={stroke} strokeWidth={isStart||isEnd?2:1.4}/>
                {/* color bar */}
                <rect x="0" y="0" width="4" height={nodeH} rx="2"
                  fill={isException?D.red:D.brand}/>
                <text x="14" y="22" fontFamily={D.sans} fontSize="12" fontWeight="600" fill={D.text}>
                  {a.label}
                </text>
                <text x="14" y="38" fontFamily={D.mono} fontSize="9.5" fill={D.textDim} style={{letterSpacing:'0.04em'}}>
                  {a.role}
                </text>
                {/* case count bar */}
                <rect x="14" y={nodeH-14} width={nodeW-28} height="3" rx="1.5" fill={D.panel}/>
                <rect x="14" y={nodeH-14}
                  width={(nodeW-28) * (a.cases/PM_ACTIVITIES[0].cases)} height="3" rx="1.5"
                  fill={isException?D.red:D.brand}/>
                <text x={nodeW-14} y={nodeH-18} textAnchor="end"
                  fontFamily={D.mono} fontSize="10" fontWeight="700" fill={D.text}>
                  {a.cases.toLocaleString()}
                </text>
              </g>
            );
          })}
          {/* badges */}
          {PM_ACTIVITIES.filter(a=>a.id==='a5').map(a=>(
            <g key="bot" transform={`translate(${a.x+nodeW-22}, ${a.y-8})`}>
              <rect x="-26" y="0" width="52" height="18" rx="9" fill={D.red}/>
              <text x="0" y="12" textAnchor="middle" fontFamily={D.mono}
                fontSize="9" fontWeight="700" fill="#fff" style={{letterSpacing:'0.06em'}}>BOTTLENECK</text>
            </g>
          ))}
        </svg>

        {/* legend */}
        <div style={{
          position:'absolute', bottom:14, left:14,
          background:'rgba(255,255,255,0.94)', border:`1px solid ${D.border}`,
          borderRadius:10, padding:'10px 12px',
          backdropFilter:'blur(12px)', boxShadow:D.shadowSm,
          display:'flex', flexDirection:'column', gap:6,
        }}>
          <div style={{fontSize:10, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em'}}>Edges</div>
          <LegendRow color={D.brandMid} label="Normal flow · thickness = cases"/>
          <LegendRow color={D.red} label="SLA breach / slow"/>
          <LegendRow color={D.amber} label="Rework loop" dashed/>
        </div>

        {/* slider */}
        <div style={{
          position:'absolute', top:14, left:14, right:14,
          display:'flex', alignItems:'center', gap:14, flexWrap:'wrap',
        }}>
          <div style={{
            display:'flex', alignItems:'center', gap:10,
            background:'rgba(255,255,255,0.94)', border:`1px solid ${D.border}`,
            borderRadius:10, padding:'8px 12px',
            backdropFilter:'blur(12px)', boxShadow:D.shadowSm, flex:'0 1 360px',
          }}>
            <span style={{fontSize:10, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em'}}>Activities</span>
            <div style={{flex:1, height:4, background:D.panel, borderRadius:2, position:'relative'}}>
              <div style={{position:'absolute', left:0, top:0, bottom:0, width:'82%', background:D.brand, borderRadius:2}}/>
              <div style={{position:'absolute', left:'82%', top:-4, width:12, height:12, borderRadius:'50%', background:'#fff', border:`2px solid ${D.brand}`, transform:'translateX(-50%)'}}/>
            </div>
            <span style={{fontFamily:D.mono, fontSize:11, color:D.text, fontWeight:600, minWidth:32, textAlign:'right'}}>9/12</span>
          </div>
          <div style={{
            display:'flex', alignItems:'center', gap:10,
            background:'rgba(255,255,255,0.94)', border:`1px solid ${D.border}`,
            borderRadius:10, padding:'8px 12px',
            backdropFilter:'blur(12px)', boxShadow:D.shadowSm, flex:'0 1 360px',
          }}>
            <span style={{fontSize:10, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em'}}>Connections</span>
            <div style={{flex:1, height:4, background:D.panel, borderRadius:2, position:'relative'}}>
              <div style={{position:'absolute', left:0, top:0, bottom:0, width:'68%', background:D.brand, borderRadius:2}}/>
              <div style={{position:'absolute', left:'68%', top:-4, width:12, height:12, borderRadius:'50%', background:'#fff', border:`2px solid ${D.brand}`, transform:'translateX(-50%)'}}/>
            </div>
            <span style={{fontFamily:D.mono, fontSize:11, color:D.text, fontWeight:600, minWidth:32, textAlign:'right'}}>12/18</span>
          </div>
        </div>
      </div>

      {/* right panel — selected activity insights */}
      <div style={{borderLeft:`1px solid ${D.border}`, background:D.bg, overflow:'auto'}}>
        <div style={{padding:'14px 16px', borderBottom:`1px solid ${D.border}`}}>
          <Pill tone="bad">BOTTLENECK</Pill>
          <div style={{fontSize:16, fontWeight:600, color:D.text, marginTop:8, lineHeight:1.3}}>Underwriting Review</div>
          <div style={{fontFamily:D.mono, fontSize:11, color:D.textDim, marginTop:4, letterSpacing:'0.04em'}}>1,158 cases · Senior Underwriter</div>
        </div>
        <div style={{padding:14, display:'flex', flexDirection:'column', gap:14}}>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:8}}>
            <div style={{padding:'10px 12px', background:D.panel, border:`1px solid ${D.border}`, borderRadius:8}}>
              <div style={{fontFamily:D.mono, fontSize:18, fontWeight:700, color:D.red}}>42h</div>
              <div style={{fontSize:10, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600, marginTop:2}}>Median wait</div>
            </div>
            <div style={{padding:'10px 12px', background:D.panel, border:`1px solid ${D.border}`, borderRadius:8}}>
              <div style={{fontFamily:D.mono, fontSize:18, fontWeight:700, color:D.text}}>2.1d</div>
              <div style={{fontSize:10, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600, marginTop:2}}>P50 dwell</div>
            </div>
          </div>

          <div>
            <Label style={{marginBottom:8}}>Wait time · last 30 days</Label>
            <svg viewBox="0 0 280 80" style={{width:'100%', height:80}}>
              {[28,32,40,36,44,52,48,42,46,54,42,38,44,48,52,42,38,36,40,42,46,52,48,44,42,46,42,40,38,42].map((v,i)=>(
                <rect key={i} x={4+i*9} y={80-v} width={6} height={v} rx={1.5}
                  fill={v>48?D.red:v>40?D.amber:D.brandMid} opacity={0.85}/>
              ))}
              <line x1="0" x2="280" y1="32" y2="32" stroke={D.brand} strokeWidth="1" strokeDasharray="3 3" opacity="0.5"/>
              <text x="278" y="29" textAnchor="end" fontFamily={D.mono} fontSize="8" fill={D.brand}>SLA 32h</text>
            </svg>
          </div>

          <div>
            <Label style={{marginBottom:8}}>Top causes</Label>
            <div style={{display:'flex', flexDirection:'column', gap:6}}>
              {[
                {l:'Awaiting credit memo',  pct:42},
                {l:'Senior availability',    pct:28},
                {l:'Document re-request',    pct:18},
                {l:'System: LOS lag',        pct:12},
              ].map(c=>(
                <div key={c.l} style={{display:'flex', alignItems:'center', gap:10}}>
                  <span style={{flex:1, fontSize:11, color:D.textMid}}>{c.l}</span>
                  <div style={{width:80, height:5, background:D.panel, borderRadius:3}}>
                    <div style={{width:`${c.pct}%`, height:'100%', background:D.red, borderRadius:3, opacity:0.7+c.pct/200}}/>
                  </div>
                  <span style={{fontFamily:D.mono, fontSize:11, fontWeight:700, color:D.text, minWidth:28, textAlign:'right'}}>{c.pct}%</span>
                </div>
              ))}
            </div>
          </div>

          <Card tight style={{background:`linear-gradient(135deg, ${D.brandLight} 0%, ${D.bg} 100%)`, borderLeft:`3px solid ${D.brand}`}}>
            <div style={{display:'flex', alignItems:'center', gap:6, marginBottom:6}}>
              <Icon name="sparkles" size={12} color={D.brand}/>
              <span style={{fontSize:11, fontWeight:700, color:D.brand, textTransform:'uppercase', letterSpacing:'0.06em'}}>AI Recommendation</span>
            </div>
            <div style={{fontSize:11, color:D.textMid, lineHeight:1.6, marginBottom:8}}>
              Auto-route memos under <span style={{fontFamily:D.mono, fontWeight:700, color:D.text}}>₹50L</span> to Junior Underwriter — projected <span style={{fontFamily:D.mono, fontWeight:700, color:D.brand}}>−1.4d</span> median TAT.
            </div>
            <Btn kind="primary" size="sm" icon="arrowRight">Simulate impact</Btn>
          </Card>
        </div>
      </div>
    </div>
  );
}
function LegendRow({ color, label, dashed }) {
  return <div style={{display:'flex', alignItems:'center', gap:8, fontSize:11, color:D.textMid}}>
    <svg width="22" height="6">
      <line x1="0" y1="3" x2="22" y2="3" stroke={color} strokeWidth="2.5"
        strokeDasharray={dashed?'4 3':'none'}/>
    </svg>
    {label}
  </div>;
}

/* ── Variants list ──────────────────────────────────────── */
function VariantsView({ selected, setSelected }) {
  const v = PM_VARIANTS.find(x=>x.id===selected) || PM_VARIANTS[0];
  return (
    <div style={{flex:1, display:'grid', gridTemplateColumns:'440px 1fr', minHeight:0}}>
      <div style={{borderRight:`1px solid ${D.border}`, background:D.bg, overflow:'auto'}}>
        <div style={{padding:'12px 16px', borderBottom:`1px solid ${D.border}`, display:'flex', alignItems:'center', gap:10}}>
          <span style={{fontSize:11, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em'}}>Variants · sorted by frequency</span>
          <Btn kind="ghost" size="sm" style={{marginLeft:'auto'}}>5 of 23</Btn>
        </div>
        <div style={{padding:10, display:'flex', flexDirection:'column', gap:8}}>
          {PM_VARIANTS.map((vr, i)=>{
            const isSel = vr.id===selected;
            return (
              <button key={vr.id} onClick={()=>setSelected(vr.id)} style={{
                textAlign:'left', cursor:'pointer',
                background: isSel ? D.brandLight : D.bg,
                border: `1px solid ${isSel?D.borderStrong:D.border}`, borderRadius:10, padding:12,
                display:'flex', flexDirection:'column', gap:8,
              }}>
                <div style={{display:'flex', alignItems:'center', gap:8}}>
                  <span style={{fontFamily:D.mono, fontSize:11, fontWeight:700, color:D.brand}}>#{i+1}</span>
                  <span style={{fontFamily:D.mono, fontSize:14, fontWeight:700, color:D.text}}>{vr.cases.toLocaleString()}</span>
                  <span style={{fontFamily:D.mono, fontSize:10, color:D.textDim}}>cases · {(vr.freq*100).toFixed(1)}%</span>
                  <span style={{marginLeft:'auto', display:'flex', gap:4}}>
                    {vr.conformant ? <Pill tone="ok">conform</Pill> : <Pill tone="bad">deviation</Pill>}
                  </span>
                </div>
                {/* freq bar */}
                <div style={{height:4, background:D.panel, borderRadius:2}}>
                  <div style={{width:`${vr.freq*100}%`, height:'100%', background:vr.conformant?D.brand:D.red, borderRadius:2}}/>
                </div>
                {/* mini path */}
                <div style={{display:'flex', alignItems:'center', gap:3, flexWrap:'wrap'}}>
                  {vr.steps.map((s,j)=>(
                    <React.Fragment key={j}>
                      <span style={{
                        fontSize:9.5, fontFamily:D.mono, padding:'2px 6px', borderRadius:4,
                        background:'#fff', border:`1px solid ${D.border}`, color:D.textMid,
                        whiteSpace:'nowrap',
                      }}>{s}</span>
                      {j<vr.steps.length-1 && <span style={{color:D.textFaint, fontSize:10}}>›</span>}
                    </React.Fragment>
                  ))}
                </div>
                <div style={{display:'flex', alignItems:'center', gap:10, fontSize:10, color:D.textDim}}>
                  <span><span style={{fontFamily:D.mono, fontWeight:700, color:D.text}}>{vr.dur}</span> median</span>
                  {vr.note && <><span>·</span><span>{vr.note}</span></>}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* selected variant detail */}
      <div style={{background:D.bgSolid, overflow:'auto', padding:24, display:'flex', flexDirection:'column', gap:16}}>
        <div style={{display:'flex', alignItems:'center', gap:10}}>
          <span style={{fontSize:14, fontWeight:600, color:D.text}}>Variant detail</span>
          {v.conformant ? <Pill tone="ok">Conformant</Pill> : <Pill tone="bad">Deviation: {v.note}</Pill>}
          <Btn kind="ghost" size="sm" icon="play" style={{marginLeft:'auto'}}>Replay cases</Btn>
        </div>
        {/* swimlane */}
        <Card style={{background:'#fff', padding:20}}>
          <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:16}}>
            <div>
              <div style={{fontSize:11, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em'}}>Execution path</div>
              <div style={{fontFamily:D.mono, fontSize:11, color:D.textDim, marginTop:2}}>{v.cases.toLocaleString()} cases · median {v.dur}</div>
            </div>
            <div style={{display:'flex', gap:14, alignItems:'center'}}>
              <div><span style={{fontFamily:D.mono, fontSize:18, fontWeight:700, color:D.text}}>{v.steps.length}</span><span style={{fontFamily:D.mono, fontSize:11, color:D.textDim, marginLeft:4}}>steps</span></div>
              <div><span style={{fontFamily:D.mono, fontSize:18, fontWeight:700, color:D.text}}>{v.dur}</span><span style={{fontFamily:D.mono, fontSize:11, color:D.textDim, marginLeft:4}}>p50</span></div>
            </div>
          </div>
          <div style={{display:'flex', alignItems:'center', gap:0, overflowX:'auto', paddingBottom:8}}>
            {v.steps.map((s,i)=>(
              <React.Fragment key={i}>
                <div style={{
                  flexShrink:0, padding:'10px 14px',
                  background:D.brandLight, border:`1.5px solid ${D.borderHi}`,
                  borderRadius:8, minWidth:120, textAlign:'center',
                }}>
                  <div style={{fontFamily:D.mono, fontSize:9, color:D.brandDark, fontWeight:700, letterSpacing:'0.06em'}}>STEP {String(i+1).padStart(2,'0')}</div>
                  <div style={{fontSize:11, fontWeight:600, color:D.text, marginTop:3, lineHeight:1.3}}>{s}</div>
                </div>
                {i<v.steps.length-1 && (
                  <div style={{flexShrink:0, padding:'0 8px', display:'flex', flexDirection:'column', alignItems:'center', gap:2}}>
                    <Icon name="arrowRight" size={14} color={D.borderStrong}/>
                    <span style={{fontFamily:D.mono, fontSize:9, color:D.textFaint}}>{[2.1,8.2,6.4,42.0,14.2,24.0,18.0,12.0][i] || 4}h</span>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </Card>

        {/* compare to happy path */}
        <Card style={{background:'#fff'}}>
          <Label style={{marginBottom:10}}>Comparison vs happy path (Variant #1)</Label>
          <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:14}}>
            {[
              {l:'Cases',     a:v.cases.toLocaleString(), d:v.id==='v1'?'baseline':`-${(842-v.cases).toLocaleString()}`},
              {l:'Median TAT',a:v.dur, d:v.id==='v1'?'baseline':`+${(parseFloat(v.dur)-4.2).toFixed(1)}d`,                  tone:v.id==='v1'?'ok':'warn'},
              {l:'Steps',    a:v.steps.length, d:v.id==='v1'?'baseline':`${v.steps.length-7>0?'+':''}${v.steps.length-7}`},
              {l:'Conformance', a:v.conformant?'100%':'0%', d:v.conformant?'pass':'breach', tone:v.conformant?'ok':'bad'},
            ].map(s=>(
              <div key={s.l}>
                <div style={{fontSize:10, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600}}>{s.l}</div>
                <div style={{fontFamily:D.mono, fontSize:22, fontWeight:700, color:D.text, letterSpacing:'-0.02em', marginTop:4}}>{s.a}</div>
                <div style={{fontFamily:D.mono, fontSize:10, marginTop:4, color: s.tone==='bad'?'#c2421a':s.tone==='warn'?'#b87f00':D.textDim}}>{s.d}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ── Process Conformance overview ──────────────────────────── */
function ProcessConformance() {
  return (
    <div style={{flex:1, overflow:'auto', padding:24, display:'flex', flexDirection:'column', gap:18, background:D.bgSolid}}>
      <div style={{display:'grid', gridTemplateColumns:'auto 1fr', gap:16}}>
        <Card style={{minWidth:280, background:'#fff'}}>
          <Label>Fitness</Label>
          <div style={{display:'flex', alignItems:'baseline', gap:10, marginTop:8}}>
            <div style={{fontFamily:D.mono, fontSize:48, fontWeight:700, color:D.green, letterSpacing:'-0.02em', lineHeight:1}}>0.81</div>
            <Pill tone="ok">HEALTHY</Pill>
          </div>
          <div style={{fontSize:11, color:D.textDim, marginTop:8}}>1,016 of 1,247 cases conform to the SOP-defined process. 231 deviations across 4 patterns.</div>
        </Card>
        <Card style={{background:'#fff'}}>
          <Label>Deviation Patterns</Label>
          <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:10, marginTop:12}}>
            {[
              {l:'KYC after Credit', n:174, sev:'medium'},
              {l:'Rework loops',     n:34,  sev:'high'},
              {l:'Skipped Underwriting', n:14, sev:'critical'},
              {l:'Out-of-hours sanction', n:9, sev:'high'},
            ].map(d=>(
              <div key={d.l} style={{padding:'10px 12px', background:D.panelHi, border:`1px solid ${D.border}`, borderRadius:8, borderLeft:`3px solid ${d.sev==='critical'?D.red:d.sev==='high'?'#f97316':D.amber}`}}>
                <div style={{fontFamily:D.mono, fontSize:18, fontWeight:700, color:D.text, letterSpacing:'-0.02em'}}>{d.n}</div>
                <div style={{fontSize:11, color:D.textMid, marginTop:2}}>{d.l}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      <Card style={{background:'#fff'}}>
        <Label style={{marginBottom:12}}>Top deviating cases</Label>
        <div style={{display:'flex', flexDirection:'column'}}>
          <div style={{display:'grid', gridTemplateColumns:'120px 1fr 100px 90px 80px', gap:14, padding:'8px 12px', borderBottom:`1px solid ${D.border}`, fontFamily:D.mono, fontSize:10, fontWeight:700, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.06em'}}>
            <span>Case ID</span><span>Deviation</span><span>Started</span><span>TAT</span><span>Severity</span>
          </div>
          {[
            {id:'LN-2024-08-3142', dev:'Underwriting skipped — direct sanction', s:'2024-08-14', t:'2.1d', sev:'critical'},
            {id:'LN-2024-08-2987', dev:'Rework: Credit re-run after Completeness', s:'2024-08-14', t:'11.4d', sev:'high'},
            {id:'LN-2024-08-2941', dev:'KYC initiated after Credit Assessment', s:'2024-08-13', t:'5.8d', sev:'medium'},
            {id:'LN-2024-08-2876', dev:'Sanction outside business hours', s:'2024-08-12', t:'3.2d', sev:'high'},
            {id:'LN-2024-08-2802', dev:'Rework: Completeness redone twice', s:'2024-08-11', t:'9.6d', sev:'high'},
          ].map((c,i)=>(
            <div key={i} style={{display:'grid', gridTemplateColumns:'120px 1fr 100px 90px 80px', gap:14, padding:'10px 12px', borderBottom:`1px solid ${D.border}`, alignItems:'center'}}>
              <span style={{fontFamily:D.mono, fontSize:11, color:D.brand, fontWeight:600}}>{c.id}</span>
              <span style={{fontSize:12, color:D.text}}>{c.dev}</span>
              <span style={{fontFamily:D.mono, fontSize:11, color:D.textDim}}>{c.s}</span>
              <span style={{fontFamily:D.mono, fontSize:12, color:D.text, fontWeight:600}}>{c.t}</span>
              <Pill tone={c.sev==='critical'?'crit':c.sev==='high'?'bad':'warn'}>{c.sev}</Pill>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

Object.assign(window, { ProcessMiningView });
