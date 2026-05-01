/* Discovery Engine — primitives: shell, sidebar, header, cards
   Every component embeds the design system locally so each artboard renders independently. */

const { useState, useEffect, useRef, useMemo } = React;

const D = {
  brand:'#036868', brandMid:'#007F7F', brandDark:'#024F4F',
  brandLight:'#E6F4F4', tealAccent:'#00989E', tealBright:'#00C4CC',
  green:'#00C896', amber:'#FFB800', red:'#FF6B4A', blue:'#4A90FF', violet:'#7C4FE0',
  bg:'#FFFFFF', bgSolid:'#F8FAFA',
  panel:'rgba(0,107,111,0.06)', panelHi:'rgba(0,107,111,0.03)', panelSolid:'rgba(0,107,111,0.09)',
  border:'rgba(0,107,111,0.12)', borderHi:'rgba(0,107,111,0.20)', borderStrong:'rgba(0,107,111,0.32)',
  text:'#1A1A1A', textMid:'#404040', textDim:'#666666', textFaint:'#999999',
  shadowSm:'0 1px 2px 0 rgba(0,0,0,0.05)',
  shadowMd:'0 4px 6px -1px rgba(0,0,0,0.08)',
  shadowLg:'0 10px 15px -3px rgba(0,0,0,0.08)',
  shadowTeal:'0 10px 30px rgba(0,107,111,0.12)',
  sans:"'GT America','Inter',-apple-system,sans-serif",
  mono:"'IBM Plex Mono','SF Mono','Consolas',monospace",
};

/* ── Lucide-style icons (inline SVG paths) ───────────────────── */
function Icon({ name, size=14, color='currentColor', strokeWidth=1.8, style }) {
  const paths = {
    graph:    <><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></>,
    workflow: <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>,
    gap:      <><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></>,
    shield:   <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>,
    dash:     <><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></>,
    db:       <><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></>,
    bell:     <><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    upload:   <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>,
    search:   <><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>,
    send:     <><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></>,
    close:    <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
    check:    <polyline points="20 6 9 17 4 12"/>,
    alert:    <><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></>,
    arrowRight:<><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>,
    file:     <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></>,
    trend:    <><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></>,
    trendDown:<><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></>,
    plus:     <><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></>,
    play:     <polygon points="5 3 19 12 5 21 5 3"/>,
    layers:   <><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></>,
    sparkles: <><path d="M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/></>,
    chev:     <polyline points="9 6 15 12 9 18"/>,
    chevDown: <polyline points="6 9 12 15 18 9"/>,
    eye:      <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>,
    grid:     <><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></>,
    list:     <><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></>,
    box:      <><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    refresh:  <><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></>,
    activity: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>,
    user:     <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    clock:    <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
    target:   <><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></>,
    filter:   <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>,
    drag:     <><circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/></>,
    code:     <><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" style={style}>
      {paths[name] || null}
    </svg>
  );
}

/* ── Frame: ties together a screen-sized artboard for the canvas ── */
function Frame({ width=1440, height=900, children, ...rest }) {
  return (
    <div style={{
      width, height, background: D.bgSolid, color: D.text,
      fontFamily: D.sans, fontSize: 13,
      display:'flex', flexDirection:'column', overflow:'hidden',
      position:'relative',
    }} {...rest}>
      {children}
    </div>
  );
}

/* ── Sidebar (48px rail per template) ────────────────────────── */
function Sidebar({ active='graph', onChange = ()=>{}, pulseDot=true }) {
  const items = [
    { id:'graph',     icon:'graph',    label:'Knowledge Graph' },
    { id:'workflows', icon:'workflow', label:'Workflows' },
    { id:'gap',       icon:'gap',      label:'Gap Analysis' },
    { id:'conf',      icon:'shield',   label:'Conformance' },
    { id:'om',        icon:'box',      label:'Object Model' },
    { id:'dash',      icon:'dash',     label:'Dashboard' },
  ];
  return (
    <aside style={{
      width:48, background:D.brandMid, display:'flex', flexDirection:'column',
      alignItems:'center', borderRight:'1px solid rgba(0,0,0,0.10)',
      flexShrink:0,
    }}>
      <div style={{
        height:56, width:'100%', background:D.brandDark,
        display:'flex', alignItems:'center', justifyContent:'center',
        borderBottom:'1px solid rgba(255,255,255,0.06)',
      }}>
        <img src="assets/metafore-logo.png" alt="" style={{width:26,height:26,opacity:0.95}}/>
      </div>
      <nav style={{display:'flex', flexDirection:'column', gap:2, padding:'10px 0', flex:1, width:'100%', alignItems:'center'}}>
        {items.map(it => (
          <button key={it.id} onClick={()=>onChange(it.id)} title={it.label}
            style={{
              width:36, height:36, borderRadius:8, border:'none', cursor:'pointer',
              display:'flex', alignItems:'center', justifyContent:'center',
              background: active===it.id ? 'rgba(255,255,255,0.18)' : 'transparent',
              color: active===it.id ? '#fff' : 'rgba(255,255,255,0.78)',
              position:'relative',
            }}>
            <Icon name={it.icon} size={16} />
            {active===it.id && (
              <span style={{position:'absolute', left:-6, top:8, bottom:8, width:2, background:D.tealBright, borderRadius:2}} />
            )}
          </button>
        ))}
      </nav>
      <div style={{display:'flex', flexDirection:'column', gap:4, padding:'10px 0', borderTop:'1px solid rgba(255,255,255,0.08)', width:'100%', alignItems:'center'}}>
        <button title="Pulse" style={{
          width:36, height:36, borderRadius:8, border:'none', cursor:'pointer',
          display:'flex', alignItems:'center', justifyContent:'center',
          background:'transparent', color:'rgba(255,255,255,0.78)', position:'relative',
        }}>
          <Icon name="bell" size={16}/>
          {pulseDot && <span style={{position:'absolute', top:6, right:6, width:7, height:7, borderRadius:'50%', background:D.red, boxShadow:`0 0 0 2px ${D.brandMid}`}}/>}
        </button>
        <button title="Settings" style={{
          width:36, height:36, borderRadius:8, border:'none', cursor:'pointer',
          display:'flex', alignItems:'center', justifyContent:'center',
          background:'transparent', color:'rgba(255,255,255,0.78)',
        }}>
          <Icon name="settings" size={16}/>
        </button>
      </div>
    </aside>
  );
}

/* ── Header (brand teal, "One" + product) ────────────────────── */
function Header({ graphName='\n', stats={nodes:24, edges:24, coverage:78, conformance:47}, action }) {
  return (
    <header style={{
      height:56, background:D.brand, display:'flex', alignItems:'center',
      padding:'0 18px', gap:14, flexShrink:0,
      boxShadow:'0 1px 0 rgba(0,0,0,0.08)',
    }}>
      <div style={{display:'flex', alignItems:'center', gap:10, color:'#fff'}}>
        <img src="assets/metafore-logo-horizontal.png" alt="" style={{height:22}}/>
        <span style={{fontWeight:700, fontSize:17, color:'#fff'}}>One</span>
        <span style={{fontWeight:300, fontSize:13, color:'rgba(255,255,255,0.72)', letterSpacing:'0.12em', textTransform:'uppercase'}}>Discovery</span>
      </div>
      <div style={{width:1, height:22, background:'rgba(255,255,255,0.18)'}}/>
      <div style={{display:'flex', alignItems:'center', gap:10, flex:1, minWidth:0}}>
        {graphName && (
          <span style={{
            fontSize:13, fontWeight:500, color:'rgba(255,255,255,0.94)',
            whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis',
          }}>{graphName}</span>
        )}
      </div>
      <div style={{display:'flex', alignItems:'center', gap:8}}>
        {stats?.nodes != null && <StatChip val={stats.nodes} lbl="Nodes"/>}
        {stats?.edges != null && <StatChip val={stats.edges} lbl="Edges"/>}
        {stats?.coverage != null && <StatChip val={`${stats.coverage}%`} lbl="Coverage" tone={stats.coverage>=70?'ok':stats.coverage>=50?'warn':'bad'}/>}
        {stats?.conformance != null && <StatChip val={`${stats.conformance}%`} lbl="Conform." tone={stats.conformance>=80?'ok':stats.conformance>=60?'warn':'bad'}/>}
      </div>
      <div style={{display:'flex', alignItems:'center', gap:8, flexShrink:0}}>
        <button style={btnHeader()}>
          <Icon name="download" size={13}/> Export
        </button>
        {action || (
          <button style={btnHeader('primary')}>
            <Icon name="sparkles" size={13}/> Generate Report
          </button>
        )}
      </div>
    </header>
  );
}

function btnHeader(variant) {
  if (variant==='primary') return {
    display:'inline-flex', alignItems:'center', gap:7,
    background:D.tealBright, color:D.brandDark, border:'1px solid transparent',
    borderRadius:7, fontFamily:D.sans, fontSize:12, fontWeight:600,
    padding:'6px 12px', cursor:'pointer',
  };
  return {
    display:'inline-flex', alignItems:'center', gap:7,
    background:'rgba(255,255,255,0.12)', color:'#fff',
    border:'1px solid rgba(255,255,255,0.18)', borderRadius:7,
    fontFamily:D.sans, fontSize:12, fontWeight:600,
    padding:'6px 12px', cursor:'pointer',
  };
}

function StatChip({ val, lbl, tone }) {
  const tones = {
    ok:   { bg:'rgba(0,200,150,0.18)',  bd:'rgba(0,200,150,0.30)' },
    warn: { bg:'rgba(255,184,0,0.18)',  bd:'rgba(255,184,0,0.30)' },
    bad:  { bg:'rgba(255,107,74,0.18)', bd:'rgba(255,107,74,0.30)' },
  };
  const t = tones[tone] || { bg:'rgba(0,0,0,0.20)', bd:'rgba(255,255,255,0.10)' };
  return (
    <div style={{
      display:'inline-flex', alignItems:'center', gap:6,
      background:t.bg, border:`1px solid ${t.bd}`, borderRadius:6, padding:'4px 9px',
      backdropFilter:'blur(4px)',
    }}>
      <span style={{fontFamily:D.mono, fontWeight:700, fontSize:12, color:'#fff', letterSpacing:'-0.02em'}}>{val}</span>
      <span style={{fontSize:10, color:'rgba(255,255,255,0.72)', textTransform:'uppercase', letterSpacing:'0.08em', fontWeight:600}}>{lbl}</span>
    </div>
  );
}

/* ── Section bar (under header, above content) ───────────────── */
function SectionBar({ title, meta, actions }) {
  return (
    <div style={{
      height:44, display:'flex', alignItems:'center',
      padding:'0 20px', gap:14, borderBottom:`1px solid ${D.border}`,
      background:D.bg, flexShrink:0,
    }}>
      <span style={{fontSize:14, fontWeight:600, color:D.text, letterSpacing:'-0.005em'}}>{title}</span>
      {meta && <span style={{fontFamily:D.mono, fontSize:11, color:D.textDim, letterSpacing:'0.04em'}}>{meta}</span>}
      <div style={{marginLeft:'auto', display:'flex', gap:8}}>{actions}</div>
    </div>
  );
}

/* ── Card / SectionCard ─────────────────────────────────────── */
function Card({ children, style, tight, ...rest }) {
  return (
    <div style={{
      background:D.panel, border:`1px solid ${D.border}`,
      borderRadius: tight?8:12, padding: tight?12:16,
      boxShadow:D.shadowSm, backdropFilter:'blur(16px)', WebkitBackdropFilter:'blur(16px)',
      ...style,
    }} {...rest}>
      {children}
    </div>
  );
}

function Label({ children, style }) {
  return <div style={{fontSize:10, fontWeight:600, color:D.textDim, textTransform:'uppercase', letterSpacing:'0.08em', ...style}}>{children}</div>;
}

function Chip({ children, strong, tone='neutral', style }) {
  const tones = {
    neutral:{ bg:D.panel, bd:D.border, fg:D.textMid },
    brand:{ bg:D.brandLight, bd:D.borderHi, fg:D.brandDark },
    ok:{ bg:'rgba(0,200,150,0.10)', bd:'rgba(0,200,150,0.25)', fg:'#00936b' },
    warn:{ bg:'rgba(255,184,0,0.10)', bd:'rgba(255,184,0,0.30)', fg:'#b87f00' },
    bad:{ bg:'rgba(255,107,74,0.10)', bd:'rgba(255,107,74,0.28)', fg:'#c2421a' },
    info:{ bg:'rgba(74,144,255,0.10)', bd:'rgba(74,144,255,0.25)', fg:'#2563d4' },
  };
  const t = strong ? { bg:D.brand, bd:D.brand, fg:'#fff' } : tones[tone];
  return <span style={{
    display:'inline-flex', alignItems:'center', gap:6,
    fontFamily:D.mono, fontSize:11, fontWeight:500,
    padding:'3px 8px', background:t.bg, border:`1px solid ${t.bd}`,
    borderRadius:6, letterSpacing:'0.04em', color:t.fg, ...style,
  }}>{children}</span>;
}

function Pill({ tone='ok', children, style }) {
  const tones = {
    ok:   { bg:'rgba(0,200,150,0.12)',  fg:'#00936b', bd:'rgba(0,200,150,0.28)' },
    warn: { bg:'rgba(255,184,0,0.12)',  fg:'#b87f00', bd:'rgba(255,184,0,0.28)' },
    bad:  { bg:'rgba(255,107,74,0.12)', fg:'#c2421a', bd:'rgba(255,107,74,0.28)' },
    info: { bg:'rgba(74,144,255,0.12)', fg:'#2563d4', bd:'rgba(74,144,255,0.28)' },
    brand:{ bg:D.brandLight, fg:D.brandDark, bd:D.borderHi },
    crit: { bg:'#FF6B4A', fg:'#fff', bd:'#FF6B4A' },
  };
  const t = tones[tone];
  return <span style={{
    display:'inline-flex', alignItems:'center', gap:5,
    fontSize:10, fontWeight:700, padding:'3px 8px',
    borderRadius:999, textTransform:'uppercase', letterSpacing:'0.08em',
    fontFamily:D.mono, background:t.bg, color:t.fg, border:`1px solid ${t.bd}`,
    ...style,
  }}>{children}</span>;
}

function TypeBadge({ type, style }) {
  const t = NODE_TYPES[type] || NODE_TYPES.Process;
  return <span style={{
    display:'inline-flex', alignItems:'center', gap:5,
    fontFamily:D.mono, fontSize:10, fontWeight:600,
    padding:'2px 7px', borderRadius:4, textTransform:'uppercase', letterSpacing:'0.06em',
    background: t.fill+'33', color: t.ink, border:`1px solid ${t.ring}55`,
    ...style,
  }}>
    <span style={{width:6, height:6, borderRadius:'50%', background:t.ring}}/>
    {t.label}
  </span>;
}

function Btn({ kind='primary', size='md', icon, children, style, ...rest }) {
  const base = {
    display:'inline-flex', alignItems:'center', justifyContent:'center', gap:6,
    fontFamily:D.sans, fontSize: size==='sm'?11:12, fontWeight:600,
    padding: size==='sm'?'5px 9px':'7px 12px',
    borderRadius:8, border:'1px solid transparent', cursor:'pointer',
    letterSpacing:'0.005em',
  };
  const variants = {
    primary:   { background:D.brand, color:'#fff' },
    secondary: { background:D.brandMid, color:'#fff' },
    ghost:     { background:'transparent', color:D.brand, borderColor:D.borderHi },
    danger:    { background:'#FF6B4A', color:'#fff' },
  };
  return <button style={{...base, ...variants[kind], ...style}} {...rest}>
    {icon && <Icon name={icon} size={size==='sm'?11:13}/>}
    {children}
  </button>;
}

function Tabs({ items, active, onChange = ()=>{}, style }) {
  return (
    <div style={{
      display:'flex', borderBottom:`1px solid ${D.border}`,
      padding:'0 20px', background:D.bg, ...style,
    }}>
      {items.map(it => (
        <button key={it.id} onClick={()=>onChange(it.id)} style={{
          position:'relative', padding:'10px 14px', background:'none', border:'none',
          borderBottom:'2px solid transparent', borderBottomColor: active===it.id?D.brand:'transparent',
          color: active===it.id?D.brand:D.textDim,
          fontFamily:D.sans, fontSize:12, fontWeight:600, cursor:'pointer',
          marginBottom:-1, display:'flex', alignItems:'center', gap:6,
        }}>
          {it.label}
          {it.count != null && (
            <span style={{
              fontFamily:D.mono, fontSize:10, fontWeight:700,
              padding:'1px 6px',
              background: active===it.id ? D.brand : D.panel,
              color: active===it.id ? '#fff' : D.textDim,
              borderRadius:999,
            }}>{it.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}

Object.assign(window, {
  D, Icon, Frame, Sidebar, Header, SectionBar, Card, Label, Chip, Pill, TypeBadge, Btn, Tabs, btnHeader, StatChip,
});
