/* Discovery Engine — graph viz (SVG node-link, refined)
   Custom SVG renderer (no vis-network dep) — gives us full control over typography & spacing. */

const { useState: useStateG, useRef: useRefG, useMemo: useMemoG } = React;

function GraphCanvas({
  graph = DEMO_GRAPH,
  highlight = null,         // { ids:[], severity:'critical'|'high'|... }
  nodeStyle = 'filled',     // 'filled' | 'outlined' | 'icon'
  onNodeClick = ()=>{},
  selectedId = null,
  width = '100%',
  height = '100%',
  showLegend = true,
  showMinimap = false,
}) {
  const view = useMemoG(()=>{
    const xs = graph.nodes.map(n=>n.x), ys = graph.nodes.map(n=>n.y);
    return {
      minX: Math.min(...xs)-80, maxX: Math.max(...xs)+80,
      minY: Math.min(...ys)-80, maxY: Math.max(...ys)+80,
    };
  }, [graph]);
  const vbW = view.maxX - view.minX, vbH = view.maxY - view.minY;

  const byId = useMemoG(()=>Object.fromEntries(graph.nodes.map(n=>[n.id,n])), [graph]);
  const highlightSet = useMemoG(()=> new Set(highlight?.ids || []), [highlight]);
  const hasHighlight = highlightSet.size > 0;
  const severityColors = {
    critical: D.red, high: '#f97316', medium: D.amber, low: D.green, info: D.blue,
  };
  const ringColor = highlight?.severity ? severityColors[highlight.severity] || D.brand : D.brand;

  const nodeR = (n) => 18 + Math.min(12, (n.deg||1) * 1.6);

  return (
    <div style={{position:'relative', width, height, background: D.bgSolid, overflow:'hidden'}}>
      {/* subtle dot grid */}
      <div style={{
        position:'absolute', inset:0, opacity:0.5,
        backgroundImage:`radial-gradient(${D.border} 1px, transparent 1px)`,
        backgroundSize:'24px 24px',
        pointerEvents:'none',
      }}/>
      <svg viewBox={`${view.minX} ${view.minY} ${vbW} ${vbH}`}
           preserveAspectRatio="xMidYMid meet"
           style={{position:'absolute', inset:0, width:'100%', height:'100%'}}>
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={D.borderStrong}/>
          </marker>
          <marker id="arr-h" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill={ringColor}/>
          </marker>
        </defs>

        {/* edges */}
        {graph.edges.map((e, i) => {
          const a = byId[e.from], b = byId[e.to];
          if (!a || !b) return null;
          const isH = hasHighlight && (highlightSet.has(a.id) && highlightSet.has(b.id));
          const dim = hasHighlight && !isH;
          // curved path
          const dx = b.x - a.x, dy = b.y - a.y;
          const mx = (a.x+b.x)/2 + dy*0.06, my = (a.y+b.y)/2 - dx*0.06;
          const path = `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
          return (
            <g key={i} opacity={dim ? 0.18 : 1}>
              <path d={path} fill="none"
                stroke={isH ? ringColor : D.borderStrong}
                strokeWidth={isH ? 2 : 1.1}
                markerEnd={isH ? 'url(#arr-h)' : 'url(#arr)'} />
              {e.label && (
                <text x={mx} y={my-4}
                  fontFamily="'IBM Plex Mono','SF Mono',monospace" fontSize="8.5"
                  fill={isH ? ringColor : D.textFaint}
                  textAnchor="middle"
                  style={{letterSpacing:'0.04em'}}>
                  {e.label}
                </text>
              )}
            </g>
          );
        })}

        {/* nodes */}
        {graph.nodes.map(n => {
          const t = NODE_TYPES[n.type] || NODE_TYPES.Process;
          const r = nodeR(n);
          const isH = hasHighlight && highlightSet.has(n.id);
          const dim = hasHighlight && !isH;
          const isSel = n.id === selectedId;
          const fill = nodeStyle==='filled' ? t.fill : (nodeStyle==='outlined' ? '#fff' : t.fill);
          const stroke = isH ? ringColor : t.ring;
          const strokeW = nodeStyle==='outlined' ? 2 : (isH || isSel ? 2.5 : 1.5);

          return (
            <g key={n.id} opacity={dim ? 0.25 : 1}
               style={{cursor:'pointer'}}
               onClick={()=>onNodeClick(n)}>
              {(isH || isSel) && (
                <circle cx={n.x} cy={n.y} r={r+6} fill="none"
                  stroke={ringColor} strokeWidth={1.5} opacity={0.35}/>
              )}
              <circle cx={n.x} cy={n.y} r={r} fill={fill} stroke={stroke} strokeWidth={strokeW}/>
              {nodeStyle==='icon' && (
                <text x={n.x} y={n.y+4} textAnchor="middle"
                  fontFamily={D.sans} fontSize="13" fontWeight="700" fill={t.ink}>
                  {n.type[0]}
                </text>
              )}
              <text x={n.x} y={n.y + r + 14} textAnchor="middle"
                fontFamily={D.sans} fontSize="10.5" fontWeight="600" fill={D.text}
                style={{letterSpacing:'-0.005em'}}>
                {n.label.length > 22 ? n.label.slice(0,21)+'…' : n.label}
              </text>
              <text x={n.x} y={n.y + r + 25} textAnchor="middle"
                fontFamily={D.mono} fontSize="8" fill={t.ink}
                style={{letterSpacing:'0.06em', textTransform:'uppercase'}}>
                {n.type}
              </text>
            </g>
          );
        })}
      </svg>

      {/* legend */}
      {showLegend && (
        <div style={{
          position:'absolute', bottom:16, left:16,
          background:'rgba(255,255,255,0.94)', border:`1px solid ${D.border}`,
          borderRadius:10, padding:'10px 12px',
          backdropFilter:'blur(12px)', boxShadow:D.shadowSm,
          display:'flex', flexDirection:'column', gap:6,
          minWidth:140,
        }}>
          <div style={{fontSize:10, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:2}}>Node Types</div>
          {Object.entries(NODE_TYPES).map(([key, t]) => (
            <div key={key} style={{display:'flex', alignItems:'center', gap:7, fontSize:11, color:D.textMid}}>
              <span style={{width:10, height:10, borderRadius:'50%', background:t.fill, border:`1.5px solid ${t.ring}`}}/>
              <span>{t.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* viz controls (top-right) */}
      <div style={{
        position:'absolute', top:12, right:12,
        display:'flex', gap:4,
        background:'rgba(255,255,255,0.94)', border:`1px solid ${D.border}`,
        borderRadius:8, padding:3, boxShadow:D.shadowSm,
      }}>
        {['+','−','⤢'].map((s,i)=>(
          <button key={i} style={{
            width:26, height:26, border:'none', background:'transparent',
            cursor:'pointer', color:D.textMid, fontFamily:D.mono, fontSize:13, borderRadius:5,
          }}>{s}</button>
        ))}
      </div>

      {/* minimap */}
      {showMinimap && (
        <div style={{
          position:'absolute', bottom:16, right:16,
          width:160, height:100,
          background:'rgba(255,255,255,0.94)',
          border:`1px solid ${D.border}`, borderRadius:8,
          boxShadow:D.shadowSm, overflow:'hidden',
        }}>
          <svg viewBox={`${view.minX} ${view.minY} ${vbW} ${vbH}`}
               preserveAspectRatio="xMidYMid meet" style={{width:'100%', height:'100%'}}>
            {graph.edges.map((e,i)=>{
              const a=byId[e.from], b=byId[e.to];
              if(!a||!b) return null;
              return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={D.border} strokeWidth={1}/>;
            })}
            {graph.nodes.map(n=>{
              const t = NODE_TYPES[n.type] || NODE_TYPES.Process;
              return <circle key={n.id} cx={n.x} cy={n.y} r={6} fill={t.fill} stroke={t.ring} strokeWidth={1}/>;
            })}
          </svg>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { GraphCanvas });
