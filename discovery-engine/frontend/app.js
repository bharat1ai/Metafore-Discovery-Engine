/* ── Metafore One — Discovery Engine ── */

const API_BASE = '';

/* ── Design tokens (mirrors tokens.js) ── */
const D = {
  brand:    '#036868',
  brandDark:'#024F4F',
  brandMid: '#007F7F',
  bg:       '#EEF6F6',
  bgCard:   '#F7FAFA',
  bgPanel:  '#E6F4F4',
  border:   '#C4E0E0',
  text:     '#0f2020',
  textSec:  '#4a6868',
  textMuted:'#7a9a9a',
};

/* ── Node type definitions — all circles, pastel fills ── */
// bg = fill, border = ring, font = label colour
const NODE_TYPES = {
  Process:    { bg: '#C7F0ED', border: '#0D9488', font: '#0D9488' }, // teal   — like CLA nodes
  Role:       { bg: '#FED7AA', border: '#EA580C', font: '#C2410C' }, // orange — actors / teams
  System:     { bg: '#BFDBFE', border: '#3B82F6', font: '#1D4ED8' }, // blue   — platforms / tools
  Policy:     { bg: '#FECACA', border: '#EF4444', font: '#DC2626' }, // red    — rules / compliance
  DataEntity: { bg: '#DDD6FE', border: '#7C3AED', font: '#6D28D9' }, // purple — records / docs
  Event:      { bg: '#FEF08A', border: '#CA8A04', font: '#92400E' }, // amber  — triggers / milestones
};

/* ── State ── */
let selectedFiles       = [];
let currentGraph        = null;
let currentGraphId      = null;
let network             = null;
const _originalNodeColors = {};

/* ── Pulse state ── */
let pulseData   = null;
let pulseAiData = null;

/* ── NLQ state ── */
let nlqHistory          = [];
let nlqAbortController  = null;
const NLQ_SAMPLES = [
  'What are the main processes?',
  'Who approves decisions?',
  'What systems are used?',
];

/* ── DOM refs ── */
const uploadZone      = document.getElementById('upload-zone');
const fileInput       = document.getElementById('file-input');
const fileList        = document.getElementById('file-list');
const btnExtract      = document.getElementById('btn-extract');
const btnObjectModel  = document.getElementById('nav-object-model');
const btnReset        = document.getElementById('btn-reset');
const placeholder     = document.getElementById('placeholder');
const spinner         = document.getElementById('spinner');
const netContainer    = document.getElementById('network-container');
const chipNodes       = document.getElementById('chip-nodes');
const chipEdges       = document.getElementById('chip-edges');
const statNodes       = document.getElementById('stat-nodes');
const statEdges       = document.getElementById('stat-edges');
const chipNodeEl      = document.getElementById('chip-nodes');
const chipEdgeEl      = document.getElementById('chip-edges');
const legendSection   = document.getElementById('legend-section');
const legendList      = document.getElementById('legend-list');
const detailPanel     = document.getElementById('detail-panel');
const detailBadge     = document.getElementById('detail-badge');
const detailTitle     = document.getElementById('detail-title');
const detailDesc      = document.getElementById('detail-desc');
const detailSource    = document.getElementById('detail-source');
const closeDetail     = document.getElementById('close-detail');
const btnWorkflows    = document.getElementById('btn-generate-workflows');
const workflowSpinner = document.getElementById('workflow-spinner');
const workflowThinMsg = document.getElementById('workflow-thin-graph-msg');
const workflowList    = document.getElementById('workflow-list');
const modelSummary    = document.getElementById('model-summary');
const pydanticCode    = document.getElementById('pydantic-code');
const schemaCode      = document.getElementById('schema-code');
const copyPydantic    = document.getElementById('copy-pydantic');
const copySchema      = document.getElementById('copy-schema');
const erdContainer    = document.getElementById('erd-container');
const erdEntities     = document.getElementById('erd-entities');
const erdSvg          = document.getElementById('erd-svg');

/* ── Pulse DOM refs ── */
const btnPulse         = document.getElementById('btn-pulse');
const pulseBadge       = document.getElementById('pulse-badge');
const pulseDrawer      = document.getElementById('pulse-drawer');
const pulseOverlay     = document.getElementById('pulse-overlay');
const pulseDrawerClose = document.getElementById('pulse-drawer-close');
const pulseDrawerBody  = document.getElementById('pulse-drawer-body');
const gapBannerSource  = document.getElementById('gap-banner-source');

/* ── NLQ DOM refs ── */
const nlqContainer     = document.getElementById('nlq-container');
const nlqAnswerCard    = document.getElementById('nlq-answer-card');
const nlqShimmer       = document.getElementById('nlq-shimmer');
const nlqAnswerContent = document.getElementById('nlq-answer-content');
const nlqQuestionEcho  = document.getElementById('nlq-question-echo');
const nlqAnswerText    = document.getElementById('nlq-answer-text');
const nlqNodeChips     = document.getElementById('nlq-node-chips');
const nlqFollowupChips = document.getElementById('nlq-followup-chips');
const nlqContextChips  = document.getElementById('nlq-context-chips');
const nlqInput         = document.getElementById('nlq-input');
const nlqCharCount     = document.getElementById('nlq-char-count');
const nlqSubmit        = document.getElementById('nlq-submit');
const nlqCloseBtn      = document.getElementById('nlq-close-btn');

/* ── Panel view switcher ── */
const PANEL_RATIOS = { graph: 35, workflows: 60, gap: 50, conformance: 50, 'object-model': 55 };

function switchView(view) {
  document.getElementById('gap-panel').hidden             = (view !== 'gap');
  document.getElementById('conformance-panel').hidden     = (view !== 'conformance');
  document.getElementById('graph-panel-view').hidden      = (view !== 'graph');
  document.getElementById('workflows-panel-view').hidden  = (view !== 'workflows');
  document.getElementById('object-model-panel').hidden    = (view !== 'object-model');

  const pct = PANEL_RATIOS[view] ?? 35;
  const panel = document.querySelector('.upload-panel');
  panel.style.flex = `0 0 ${pct}%`;
  panel.style.width = `${pct}%`;
}

function setNavActive(id) {
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id)?.classList.add('active');
}

switchView('graph');
setNavActive('nav-graph');

/* ── Base nav handlers ── */
document.getElementById('nav-graph').addEventListener('click', () => {
  setNavActive('nav-graph');
  switchView('graph');
});

document.getElementById('nav-workflows').addEventListener('click', () => {
  setNavActive('nav-workflows');
  switchView('workflows');
  if (currentGraphId && !workflowList.innerHTML.trim() && workflowSpinner.classList.contains('hidden')) {
    generateWorkflows();
  }
});

/* ── File handling ── */
uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  addFiles([...e.dataTransfer.files]);
});
fileInput.addEventListener('change', () => {
  addFiles([...fileInput.files]);
  fileInput.value = '';
});

function addFiles(files) {
  files.forEach(f => {
    if (!selectedFiles.find(x => x.name === f.name && x.size === f.size))
      selectedFiles.push(f);
  });
  renderFileList();
}

function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  return { pdf: '📄', docx: '📝', doc: '📝', txt: '📃' }[ext] || '📎';
}

function renderFileList() {
  fileList.innerHTML = '';
  selectedFiles.forEach((f, i) => {
    const li = document.createElement('li');
    li.className = 'file-item';
    li.innerHTML = `
      <span class="file-name" title="${f.name}">${fileIcon(f.name)} ${f.name}</span>
      <button class="file-remove" data-i="${i}" title="Remove">✕</button>
    `;
    fileList.appendChild(li);
  });
  fileList.querySelectorAll('.file-remove').forEach(btn =>
    btn.addEventListener('click', () => { selectedFiles.splice(+btn.dataset.i, 1); renderFileList(); })
  );
  btnExtract.disabled = selectedFiles.length === 0;
}

/* ── Extraction ── */
btnExtract.addEventListener('click', extractGraph);

async function extractGraph() {
  if (!selectedFiles.length) return;

  const fd = new FormData();
  selectedFiles.forEach(f => fd.append('files', f));

  placeholder.style.display = 'none';
  spinner.classList.remove('hidden');
  btnExtract.disabled = true;
  btnObjectModel.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    currentGraph   = await res.json();
    currentGraphId = currentGraph.graph_id || null;
    renderGraph(currentGraph);

    btnObjectModel.disabled      = false;
    btnWorkflows.disabled        = false;
    btnGapAnalyse.disabled       = false;
    btnGapAnalyseEmpty.disabled  = false;
    document.getElementById('btn-pulse').disabled = false;
    fetchPulse();
    nlqInit();
  } catch (e) {
    alert(`Extraction failed:\n${e.message}`);
    placeholder.style.display = '';
  } finally {
    spinner.classList.add('hidden');
    btnExtract.disabled = selectedFiles.length === 0;
  }
}

/* ── Graph rendering ── */
function buildLegend(types) {
  legendList.innerHTML = '';
  types.forEach(type => {
    const t = NODE_TYPES[type] || { border: D.textMuted };
    const li = document.createElement('li');
    li.className = 'legend-item';
    li.innerHTML = `<span class="legend-dot" style="background:${t.bg};border:2px solid ${t.border}"></span>${type}`;
    legendList.appendChild(li);
  });
  legendSection.hidden = false;
}

function renderGraph(graph) {
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];

  /* Stats */
  statNodes.textContent = nodes.length;
  statEdges.textContent = edges.length;
  chipNodeEl.hidden = false;
  chipEdgeEl.hidden = false;

  /* Legend */
  buildLegend([...new Set(nodes.map(n => n.type))].sort());

  /* Degree map — more connections = slightly larger circle */
  const degree = {};
  nodes.forEach(n => { degree[n.id] = 0; });
  edges.forEach(e => {
    degree[e.source] = (degree[e.source] || 0) + 1;
    degree[e.target] = (degree[e.target] || 0) + 1;
  });
  const maxDeg = Math.max(...Object.values(degree), 1);

  /* vis node dataset — ALL circles via shape:'dot' */
  const visNodes = nodes.map(n => {
    const t = NODE_TYPES[n.type] || { bg: '#E2E8F0', border: '#94A3B8', font: '#475569' };
    // Scale radius 28–46px based on relative degree
    const size = 28 + Math.round(((degree[n.id] || 0) / maxDeg) * 18);
    return {
      id:    n.id,
      label: n.label,
      shape: 'dot',          // ← uniform circle for every node type
      size,
      color: {
        background: t.bg,
        border:     t.border,
        highlight:  { background: t.bg, border: '#0f2020' },
        hover:      { background: t.bg, border: D.brand   },
      },
      font: {
        color: t.font,
        size:  12,
        face:  "'GT America','Inter',sans-serif",
        vadjust: 0,
      },
      borderWidth:         2,
      borderWidthSelected: 3,
      shadow: { enabled: true, color: 'rgba(0,0,0,0.07)', size: 8, x: 0, y: 2 },
      _data: n,
    };
  });

  /* vis edge dataset — thin grey lines with small mono labels */
  const visEdges = edges.map(e => ({
    id:     e.id,
    from:   e.source,
    to:     e.target,
    label:  e.label,
    arrows: { to: { enabled: true, scaleFactor: 0.45, type: 'arrow' } },
    color:  { color: '#B0CECE', highlight: D.brand, hover: D.brandMid },
    font:   {
      color:       D.textMuted,
      size:        10,
      face:        "'IBM Plex Mono','Consolas',monospace",
      align:       'middle',
      strokeWidth: 2,
      strokeColor: '#EEF6F6',
    },
    smooth: { type: 'curvedCW', roundness: 0.1 },
    width:  1,
    selectionWidth: 2,
    _data:  e,
  }));

  const data = {
    nodes: new vis.DataSet(visNodes),
    edges: new vis.DataSet(visEdges),
  };

  const options = {
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -80,
        centralGravity:        0.005,
        springLength:          160,
        springConstant:        0.06,
        damping:               0.9,
        avoidOverlap:          0.8,
      },
      stabilization: { iterations: 250, updateInterval: 25 },
    },
    interaction: {
      hover:             true,
      tooltipDelay:      200,
      navigationButtons: false,
      zoomView:          true,
      multiselect:       false,
    },
    layout: { improvedLayout: true },
    nodes: {
      labelHighlightBold: false,
    },
  };

  if (network) network.destroy();
  network = new vis.Network(netContainer, data, options);

  network.on('click', params => {
    if (params.nodes.length > 0) {
      const node = visNodes.find(n => n.id === params.nodes[0]);
      if (node) showDetail(node._data, 'node');
    } else if (params.edges.length > 0) {
      const edge = visEdges.find(e => e.id === params.edges[0]);
      if (edge) showDetail(edge._data, 'edge');
    } else {
      closeDetailPanel();
    }
  });

  network.once('stabilizationIterationsDone', () => {
    network.setOptions({ physics: { enabled: false } });
    network.fit({ animation: { duration: 700, easingFunction: 'easeInOutQuad' } });
  });
}

/* ── Detail panel ── */
function showDetail(data, kind) {
  if (kind === 'node') {
    detailBadge.textContent = data.type;
    detailBadge.className   = `detail-type-badge badge-${data.type}`;
  } else {
    detailBadge.textContent = data.label;
    detailBadge.className   = 'detail-type-badge badge-Edge';
  }
  detailTitle.textContent  = data.label;
  detailDesc.textContent   = data.description || '—';
  detailSource.textContent = data.source_text  || '—';
  detailPanel.classList.add('open');
}

function closeDetailPanel() { detailPanel.classList.remove('open'); }
closeDetail.addEventListener('click', closeDetailPanel);

/* ── Object model ── */
const omLoading = document.getElementById('om-loading');
const omEmpty   = document.getElementById('om-empty');
const omTabs    = document.getElementById('om-tabs');
const omBody    = document.getElementById('om-body');

function _omSetState(state) {
  omLoading.hidden = state !== 'loading';
  omEmpty.hidden   = state !== 'empty';
  omTabs.hidden    = state !== 'ready';
  omBody.hidden    = state !== 'ready';
}

async function generateObjectModel() {
  if (!currentGraph) return;
  btnObjectModel.disabled = true;
  _omSetState('loading');
  try {
    const res = await fetch(`${API_BASE}/api/generate-object-model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nodes: currentGraph.nodes, edges: currentGraph.edges, graph_id: currentGraphId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    showObjectModel(await res.json());
  } catch (e) {
    _omSetState('empty');
    alert(`Object model generation failed:\n${e.message}`);
  } finally {
    btnObjectModel.disabled = false;
  }
}

document.getElementById('nav-object-model').addEventListener('click', () => {
  setNavActive('nav-object-model');
  switchView('object-model');
  if (!currentGraph) { _omSetState('empty'); return; }
  if (!pydanticCode.textContent || !schemaCode.textContent) generateObjectModel();
  else _omSetState('ready');
});

function showObjectModel(result) {
  modelSummary.textContent = result.summary || '';
  pydanticCode.textContent = result.pydantic_code || '';
  schemaCode.textContent   = JSON.stringify(result.json_schema, null, 2);
  _renderErdEntities(result.json_schema);
  activateTab('pydantic');
  _omSetState('ready');
}

/* ── Modal tabs ── */
document.querySelectorAll('.tab').forEach(tab =>
  tab.addEventListener('click', () => activateTab(tab.dataset.tab))
);
function activateTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.getElementById('tab-pydantic').classList.toggle('hidden', name !== 'pydantic');
  document.getElementById('tab-schema').classList.toggle('hidden', name !== 'schema');
  document.getElementById('tab-diagram').classList.toggle('hidden', name !== 'diagram');
  if (name === 'diagram') {
    requestAnimationFrame(() => requestAnimationFrame(_drawErdArrows));
  }
}

/* ── ERD Diagram ── */
let _erdRelationships = [];

function _renderErdEntities(jsonSchema) {
  erdEntities.innerHTML = '';
  erdSvg.innerHTML = '';
  _erdRelationships = [];

  // BRD format: { entities: [{name, fields:[{name,type,constraints}]}], relationships: [...] }
  // Legacy format: { $defs / definitions: { EntityName: { properties: {...} } } }
  const isBrd = Array.isArray(jsonSchema?.entities) && jsonSchema.entities.length > 0;

  if (isBrd) {
    const entities = jsonSchema.entities;
    const nameSet  = new Set(entities.map(e => e.name));

    // Parse relationships: "entity_a (parent) → entity_b (child) via entity_b.fk_col = entity_a.id"
    (jsonSchema.relationships || []).forEach(rel => {
      const m = rel.match(/^(\w+)\s*\(parent\)\s*→\s*(\w+)\s*\(child\)/i);
      if (m && nameSet.has(m[1]) && nameSet.has(m[2])) {
        _erdRelationships.push({ from: m[1], to: m[2], label: '', many: true });
      }
    });

    entities.forEach(entity => {
      const BOTTOM_FIELDS = new Set(['created_at', 'created_by', 'last_changed_by']);
      const raw    = entity.fields || [];
      const fields = [
        ...raw.filter(f => !BOTTOM_FIELDS.has(f.name)),
        ...raw.filter(f =>  BOTTOM_FIELDS.has(f.name)),
      ];
      const isPk   = f => /primary key/i.test(f.constraints || '');
      const isFk   = f => /foreign key/i.test(f.constraints || '');
      const isAudit= f => /audit only/i.test(f.constraints || '');

      const fieldsHtml = fields.map(f => {
        const badge = isPk(f) ? ' <span class="erd-pk-badge">PK</span>'
                   : isFk(f) ? ' <span class="erd-fk-badge">FK</span>'
                   : isAudit(f) ? ' <span class="erd-audit-badge">AUDIT</span>'
                   : '';
        return `<div class="erd-field">
          <span class="erd-field-name">${f.name}${badge}</span>
          <span class="erd-field-type">${f.type || 'any'}</span>
        </div>`;
      }).join('');

      const el = document.createElement('div');
      el.className = 'erd-entity';
      el.id = `erd-${entity.name}`;
      el.innerHTML = `
        <div class="erd-entity-header">${entity.name}</div>
        <div class="erd-fields">${fieldsHtml || '<div class="erd-field erd-empty-field">no fields</div>'}</div>`;
      erdEntities.appendChild(el);
    });
    return;
  }

  // Legacy $defs / definitions format
  const defs  = jsonSchema?.$defs || jsonSchema?.definitions || {};
  const names = Object.keys(defs);
  if (!names.length) {
    erdEntities.innerHTML = '<p class="erd-empty-msg">No entity definitions found in schema.</p>';
    return;
  }

  const nameSet = new Set(names);
  const seen    = new Set();

  names.forEach(name => {
    const props = defs[name]?.properties || {};
    Object.entries(props).forEach(([propName, propDef]) => {
      const ref = propDef.$ref || propDef.items?.$ref;
      if (!ref) return;
      const target = ref.split('/').pop();
      if (!nameSet.has(target)) return;
      const key = `${name}→${target}`;
      if (seen.has(key)) return;
      seen.add(key);
      _erdRelationships.push({ from: name, to: target, label: propName, many: !!propDef.items });
    });

    const fieldsHtml = Object.entries(props).map(([pName, pDef]) => {
      let typeStr, isRef = false;
      if (pDef.$ref) {
        typeStr = pDef.$ref.split('/').pop(); isRef = true;
      } else if (pDef.type === 'array' && pDef.items?.$ref) {
        typeStr = `[${pDef.items.$ref.split('/').pop()}]`; isRef = true;
      } else if (pDef.type === 'array' && pDef.items?.type) {
        typeStr = `[${pDef.items.type}]`;
      } else {
        typeStr = pDef.type || 'any';
      }
      return `<div class="erd-field">
        <span class="erd-field-name">${pName}</span>
        <span class="erd-field-type${isRef ? ' erd-ref-type' : ''}">${typeStr}</span>
      </div>`;
    }).join('');

    const el = document.createElement('div');
    el.className = 'erd-entity';
    el.id = `erd-${name}`;
    el.innerHTML = `
      <div class="erd-entity-header">${name}</div>
      <div class="erd-fields">${fieldsHtml || '<div class="erd-field erd-empty-field">no fields</div>'}</div>`;
    erdEntities.appendChild(el);
  });
}

function _drawErdArrows() {
  erdSvg.innerHTML = `<defs>
    <marker id="erd-ah" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
      <polygon points="0 0, 7 2.5, 0 5" fill="#0891b2" opacity="0.65"/>
    </marker>
  </defs>`;

  const cr = erdContainer.getBoundingClientRect();
  erdSvg.style.width  = erdContainer.scrollWidth  + 'px';
  erdSvg.style.height = erdContainer.scrollHeight + 'px';

  _erdRelationships.forEach(({ from, to, label, many }) => {
    const fromEl = document.getElementById(`erd-${from}`);
    const toEl   = document.getElementById(`erd-${to}`);
    if (!fromEl || !toEl || from === to) return;

    const fr  = fromEl.getBoundingClientRect();
    const tr  = toEl.getBoundingClientRect();
    const fcx = fr.left + fr.width  / 2 - cr.left;
    const fcy = fr.top  + fr.height / 2 - cr.top;
    const tcx = tr.left + tr.width  / 2 - cr.left;
    const tcy = tr.top  + tr.height / 2 - cr.top;

    let x1, y1, x2, y2;
    if (Math.abs(fcx - tcx) >= Math.abs(fcy - tcy)) {
      if (fcx < tcx) { x1 = fr.right - cr.left; y1 = fcy; x2 = tr.left  - cr.left; y2 = tcy; }
      else           { x1 = fr.left  - cr.left; y1 = fcy; x2 = tr.right - cr.left; y2 = tcy; }
    } else {
      if (fcy < tcy) { x1 = fcx; y1 = fr.bottom - cr.top; x2 = tcx; y2 = tr.top    - cr.top; }
      else           { x1 = fcx; y1 = fr.top    - cr.top; x2 = tcx; y2 = tr.bottom - cr.top; }
    }

    const dx   = Math.abs(x2 - x1) * 0.45;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${x1},${y1} C${x1+(x2>x1?dx:-dx)},${y1} ${x2+(x2>x1?-dx:dx)},${y2} ${x2},${y2}`);
    path.setAttribute('class', 'erd-arrow-path');
    path.setAttribute('marker-end', 'url(#erd-ah)');
    erdSvg.appendChild(path);

    const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txt.setAttribute('x', (x1 + x2) / 2);
    txt.setAttribute('y', (y1 + y2) / 2 - 5);
    txt.setAttribute('class', 'erd-arrow-label');
    txt.setAttribute('text-anchor', 'middle');
    txt.textContent = many ? `${label}[ ]` : label;
    erdSvg.appendChild(txt);
  });
}


copyPydantic.addEventListener('click', () => copyText(pydanticCode.textContent, copyPydantic));
copySchema.addEventListener('click',   () => copyText(schemaCode.textContent,  copySchema));

function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = orig, 1600);
  });
}

/* ── Graph focus helpers (workflow chip hover) ── */
function focusNode(nodeId) {
  if (!network || !nodeId || !currentGraph) return;
  const updates = currentGraph.nodes.map(n => ({ id: n.id, opacity: n.id === nodeId ? 1 : 0.15 }));
  network.body.data.nodes.update(updates);
}

function resetNodeFocus() {
  if (!network || !currentGraph) return;
  network.body.data.nodes.update(currentGraph.nodes.map(n => ({ id: n.id, opacity: 1 })));
}

/* ── Workflow suggestions ── */
const COMPLEXITY_CLASS = { low: 'badge-complexity-low', medium: 'badge-complexity-medium', high: 'badge-complexity-high' };
const EFFORT_CLASS     = { low: 'badge-complexity-low', medium: 'badge-complexity-medium', high: 'badge-complexity-high' };

btnWorkflows.addEventListener('click', generateWorkflows);

async function generateWorkflows() {
  if (!currentGraphId) return;
  workflowSpinner.classList.remove('hidden');
  workflowList.innerHTML = '';
  workflowThinMsg.hidden = true;
  btnWorkflows.disabled  = true;
  const origText = btnWorkflows.textContent;
  btnWorkflows.textContent = 'Generating…';

  try {
    const res = await fetch(`${API_BASE}/api/workflows/generate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ graph_id: currentGraphId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const { workflows } = await res.json();
    renderWorkflows(workflows);
  } catch (e) {
    alert(`Workflow generation failed:\n${e.message}`);
  } finally {
    workflowSpinner.classList.add('hidden');
    btnWorkflows.disabled  = false;
    btnWorkflows.textContent = origText;
  }
}

/* ── Helpers ── */
function _nodeChip(label, nodeId, extraClass) {
  if (!label) return '';
  return `<span class="node-chip ${extraClass}" data-node="${nodeId || ''}">${label}</span>`;
}

const _WF_CONNECTOR = '<div class="wf-flow-connector"><div class="wf-connector-line"></div><div class="wf-connector-arrow"></div></div>';

function _buildAsIsSteps(steps) {
  if (!steps || !steps.length) return '';
  return steps.map(step => {
    const roleChip   = _nodeChip(step.responsible_role?.node_label, step.responsible_role?.node_id, 'chip-role');
    const systemChip = _nodeChip(step.system_used?.node_label,      step.system_used?.node_id,      'chip-system');
    const dotClass   = { ok: 'sla-ok', warn: 'sla-warn', breach: 'sla-breach' }[step.sla_status] || 'sla-ok';
    const timeStr    = step.current_avg || step.sla_target || '';
    return `
      <div class="wf-flow-step">
        <div class="wf-flow-step-header">
          <span class="wf-step-badge">${step.step_number}</span>
          <span class="wf-step-name">${step.name}</span>
          <span class="sla-dot ${dotClass}" title="${step.sla_status || ''}"></span>
        </div>
        <div class="wf-step-meta">
          ${roleChip}${systemChip}
          ${timeStr ? `<span class="step-time">${timeStr}</span>` : ''}
        </div>
      </div>`;
  }).join(_WF_CONNECTOR);
}

function _buildToBeSteps(steps) {
  if (!steps || !steps.length) return '';
  return steps.map(step => {
    const roleChip   = _nodeChip(step.responsible_role?.node_label, step.responsible_role?.node_id, 'chip-role');
    const systemChip = _nodeChip(step.system_used?.node_label,      step.system_used?.node_id,      'chip-system');
    const stepClass  = step.changed ? 'step-changed' : 'step-unchanged';
    const autoTag    = step.changed ? '<span class="wf-step-auto-tag">⚡ automated</span>' : '';
    const note       = step.changed && step.improvement_note
      ? `<div class="step-improvement">${step.improvement_note}</div>` : '';
    const timeStr    = step.estimated_time || '';
    return `
      <div class="wf-flow-step ${stepClass}">
        <div class="wf-flow-step-header">
          <span class="wf-step-badge">${step.step_number}</span>
          <span class="wf-step-name">${step.name}</span>
          ${autoTag}
        </div>
        ${note}
        <div class="wf-step-meta">
          ${roleChip}${systemChip}
          ${timeStr ? `<span class="step-time">${timeStr}</span>` : ''}
        </div>
      </div>`;
  }).join(_WF_CONNECTOR);
}

function _calcTotal(steps, field) {
  let hrs = 0, hasData = false;
  (steps || []).forEach(s => {
    const m = (s[field] || '').match(/(\d+\.?\d*)\s*(hr|hour|day|min)/i);
    if (!m) return;
    hasData = true;
    const v = parseFloat(m[1]);
    const u = m[2].toLowerCase();
    hrs += u.startsWith('min') ? v / 60 : u.startsWith('day') ? v * 8 : v;
  });
  if (!hasData) return null;
  return hrs >= 8 ? `${(hrs / 8).toFixed(1)} days` : `${hrs.toFixed(1)} hrs`;
}

function _benefitsStrip(b) {
  const ef = b?.implementation_effort || '';
  const efClass = EFFORT_CLASS[ef] || 'badge-complexity-low';
  return `
    <div class="wf-benefits-strip">
      <div class="wf-benefit-box"><div class="wf-benefit-val">${b?.time_saved_per_transaction || '—'}</div><div class="wf-benefit-label">Time Saved</div></div>
      <div class="wf-benefit-box"><div class="wf-benefit-val">${b?.extra_capacity || '—'}</div><div class="wf-benefit-label">Extra Capacity</div></div>
      <div class="wf-benefit-box"><div class="wf-benefit-val">${b?.revenue_or_cost_impact || '—'}</div><div class="wf-benefit-label">Revenue Impact</div></div>
      <div class="wf-benefit-box"><div class="wf-benefit-val"><span class="complexity-badge ${efClass}">${ef || '—'}</span></div><div class="wf-benefit-label">Impl. Effort</div></div>
    </div>`;
}

function renderWorkflows(workflows) {
  workflowList.innerHTML = '';
  workflowThinMsg.hidden = true;

  if (!currentGraph || currentGraph.nodes.length < 5) {
    workflowThinMsg.hidden = false;
    return;
  }

  const collapseAfterFirst = workflows.length >= 3;

  workflows.forEach((wf, idx) => {
    const card = document.createElement('div');
    card.className = 'workflow-card';
    if (!collapseAfterFirst || idx === 0) card.classList.add('open');

    const complexityClass = COMPLEXITY_CLASS[wf.complexity] || 'badge-complexity-low';
    const compliance      = parseFloat(wf.sla_compliance_rate) || 0;
    const barColor        = compliance < 70 ? '#ef4444' : compliance < 85 ? '#f97316' : '#22c55e';
    const barFill         = Math.min(compliance, 100);

    const asIsHtml  = _buildAsIsSteps(wf.as_is_steps);
    const toBeHtml  = _buildToBeSteps(wf.to_be_steps);
    const asIsTotal = _calcTotal(wf.as_is_steps, 'current_avg');
    const toBeTotal = _calcTotal(wf.to_be_steps, 'estimated_time');
    const saving    = wf.benefits?.time_saved_per_transaction || '';

    const summaryRow = (asIsTotal || toBeTotal) ? `
      <div class="wf-summary-row">
        <span class="wf-sum-time">${asIsTotal || '?'}</span>
        <span class="wf-sum-arrow">→</span>
        <span class="wf-sum-time">${toBeTotal || '?'}</span>
        ${saving ? `<span class="wf-sum-saving">▼ ${saving}</span>` : ''}
      </div>` : '';

    card.innerHTML = `
      <div class="workflow-card-header">
        <div class="workflow-header-main">
          <span class="workflow-title">${wf.title}</span>
          <span class="complexity-badge ${complexityClass}">${wf.complexity}</span>
        </div>
        <div class="wf-perf-bar-wrap">
          <div class="wf-perf-bar-track"><div class="wf-perf-bar-fill" style="width:${barFill}%;background:${barColor}"></div></div>
          <span class="wf-perf-label" style="color:${barColor}">${wf.sla_compliance_rate || '—'}</span>
        </div>
        <div class="wf-stats-row">
          <div class="wf-stat"><span class="wf-stat-val">${wf.current_avg || '—'}</span><span class="wf-stat-label">Current avg</span></div>
          <div class="wf-stat"><span class="wf-stat-val">${wf.sla_target || '—'}</span><span class="wf-stat-label">SLA target</span></div>
          <div class="wf-stat"><span class="wf-stat-val" style="color:${barColor}">${wf.sla_compliance_rate || '—'}</span><span class="wf-stat-label">Compliance</span></div>
        </div>
        <div class="wf-benefit-preview">
          <span class="wf-bp-item">⏱ ${wf.benefits?.time_saved_per_transaction || '—'} saved</span>
          <span class="wf-bp-item">💰 ${wf.benefits?.revenue_or_cost_impact || '—'}</span>
        </div>
        <svg class="chevron-toggle" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <div class="workflow-body">
        <p class="workflow-desc">${wf.description}</p>
        <div class="wf-columns">
          <div class="wf-col">
            <div class="wf-col-header wf-col-asis">AS-IS — Today</div>
            <div class="wf-flow-steps wf-flow-asis">${asIsHtml}</div>
          </div>
          <div class="wf-col">
            <div class="wf-col-header wf-col-tobe">TO-BE — Improved</div>
            <div class="wf-flow-steps wf-flow-tobe">${toBeHtml}</div>
          </div>
        </div>
        ${summaryRow}
        ${_benefitsStrip(wf.benefits)}
      </div>`;

    card.querySelector('.workflow-card-header').addEventListener('click', () => {
      card.classList.toggle('open');
    });

    card.querySelectorAll('[data-node]').forEach(chip => {
      const nodeId = chip.dataset.node;
      if (!nodeId) return;
      chip.addEventListener('mouseenter', () => focusNode(nodeId));
      chip.addEventListener('mouseleave', resetNodeFocus);
    });

    workflowList.appendChild(card);
  });
}

/* ── Gap Analysis ── */
const gapPanel          = document.getElementById('gap-panel');
const gapEmptyState     = document.getElementById('gap-empty-state');
const gapLoading        = document.getElementById('gap-loading');
const gapResults        = document.getElementById('gap-results');
const gapLastAnalysed   = document.getElementById('gap-last-analysed');
const gapScoreNumber    = document.getElementById('gap-score-number');
const gapScoreBarFill   = document.getElementById('gap-score-bar-fill');
const gapScoreBadge     = document.getElementById('gap-score-badge');
const gapStatsGrid      = document.getElementById('gap-stats-grid');
const gapChecksSection  = document.getElementById('gap-checks-section');
const btnGapAnalyse     = document.getElementById('btn-gap-analyse');
const btnGapAnalyseEmpty= document.getElementById('btn-gap-analyse-empty');
const btnGenerateBP     = document.getElementById('btn-generate-blueprint');
const gapBlueprintPre   = document.getElementById('gap-blueprint-pre');
const gapBlueprintResult= document.getElementById('gap-blueprint-result');
const gapHighlightBanner= document.getElementById('gap-highlight-banner');
const gapBannerCount    = document.getElementById('gap-banner-count');
const gapBannerClear    = document.getElementById('gap-banner-clear');
const bodyArea          = document.querySelector('.body-area');

let gapAnalysisResult  = null;
let gapBlueprintData   = null;
let gapHighlightActive = false;

/* ── Gap nav switching ── */
document.getElementById('nav-gap').addEventListener('click', () => {
  setNavActive('nav-gap');
  switchView('gap');
  if (currentGraphId && !gapAnalysisResult) runGapAnalysis();
  btnGapAnalyse.disabled      = !currentGraphId;
  btnGapAnalyseEmpty.disabled = !currentGraphId;
});

btnGapAnalyse.addEventListener('click', runGapAnalysis);
btnGapAnalyseEmpty.addEventListener('click', runGapAnalysis);
gapBannerClear.addEventListener('click', () => {
  gapResetHighlight();
});

async function runGapAnalysis() {
  if (!currentGraphId) return;

  gapEmptyState.hidden  = true;
  gapResults.hidden     = true;
  gapLoading.hidden     = false;
  btnGapAnalyse.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/gap-analysis/calculate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ graph_id: currentGraphId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    gapAnalysisResult = await res.json();
    gapBlueprintData  = null;
    gapBlueprintPre.hidden    = false;
    gapBlueprintResult.hidden = true;
    renderGapResults(gapAnalysisResult);
  } catch (e) {
    alert(`Gap analysis failed:\n${e.message}`);
    gapEmptyState.hidden = false;
  } finally {
    gapLoading.hidden      = true;
    btnGapAnalyse.disabled = false;
  }
}

function renderGapResults(result) {
  const ts = result.calculated_at
    ? new Date(result.calculated_at).toLocaleString()
    : '';
  gapLastAnalysed.textContent = ts ? `Last analysed: ${ts}` : 'Just now';

  /* Score */
  const score = result.coverage_score ?? 0;
  const label = result.score_label   ?? '—';
  gapScoreNumber.textContent = score;
  gapScoreBarFill.style.width = `${score}%`;
  const barColor = score >= 85 ? '#22c55e' : score >= 70 ? '#036868' : score >= 50 ? '#f97316' : '#ef4444';
  gapScoreBarFill.style.background = barColor;
  gapScoreBadge.textContent = label;
  const badgeClass = label === 'Excellent' ? 'gap-badge-excellent'
                   : label === 'Good'      ? 'gap-badge-good'
                   : label === 'Fair'      ? 'gap-badge-fair'
                   :                         'gap-badge-needs';
  gapScoreBadge.className = `gap-score-badge ${badgeClass}`;

  /* Stats */
  const typeCounts = result.node_type_counts ?? {};
  const typeCount  = Object.keys(typeCounts).length;
  gapStatsGrid.innerHTML = `
    <div class="gap-stat-item"><span class="gap-stat-val">${result.total_nodes ?? 0}</span><span class="gap-stat-label">Total Nodes</span></div>
    <div class="gap-stat-item"><span class="gap-stat-val">${result.total_edges ?? 0}</span><span class="gap-stat-label">Total Edges</span></div>
    <div class="gap-stat-item"><span class="gap-stat-val">${typeCount}</span><span class="gap-stat-label">Node Types</span></div>
    <div class="gap-stat-item"><span class="gap-stat-val">${result.avg_connections ?? 0}</span><span class="gap-stat-label">Avg Connections</span></div>
  `;

  /* Checks */
  renderGapChecks(result.checks ?? []);

  gapLoading.hidden  = true;
  gapResults.hidden  = false;
}

const SEV_ORDER  = ['critical', 'warning', 'info'];
const SEV_ICON   = { critical: '🔴', warning: '🟡', info: '🔵' };
const SEV_LABEL  = { critical: 'CRITICAL', warning: 'WARNINGS', info: 'INFO' };

function renderGapChecks(checks) {
  gapChecksSection.innerHTML = '';
  const byGroup = { critical: [], warning: [], info: [] };
  checks.forEach(c => { if (byGroup[c.severity]) byGroup[c.severity].push(c); });

  SEV_ORDER.forEach(sev => {
    const group = byGroup[sev];
    if (!group.length) return;

    const failCount = group.filter(c => c.count > 0).length;
    const header = document.createElement('div');
    header.className = 'gap-group-header';
    header.innerHTML = `${SEV_ICON[sev]} ${SEV_LABEL[sev]} <span class="gap-group-count">${failCount} issue${failCount !== 1 ? 's' : ''}</span>`;
    gapChecksSection.appendChild(header);

    group.forEach(check => gapChecksSection.appendChild(buildCheckCard(check)));
  });
}

function buildCheckCard(check) {
  const passed = check.count === 0;
  const card   = document.createElement('div');
  card.className = `gap-check-card${passed ? ' gap-passed' : ''}`;

  const countClass = passed ? 'gap-count-passed'
    : check.severity === 'critical' ? 'gap-count-critical'
    : check.severity === 'warning'  ? 'gap-count-warning'
    :                                  'gap-count-info';

  const icon  = passed ? '✅' : SEV_ICON[check.severity];
  const label = passed ? 'All clear'
    : `${check.count} node${check.count !== 1 ? 's' : ''}`;

  card.innerHTML = `
    <div class="gap-card-header">
      <span class="gap-card-icon">${icon}</span>
      <span class="gap-card-title">${passed ? 'All ' + check.title.replace(/with.*/i, '').trim().toLowerCase() + ' — passed' : check.title}</span>
      <span class="gap-card-count ${countClass}">${label}</span>
    </div>
  `;

  if (!passed) {
    const body = document.createElement('div');
    body.className = 'gap-card-body';
    const affectedText = check.affected_node_labels.slice(0, 8).join(', ')
      + (check.affected_node_labels.length > 8 ? ` +${check.affected_node_labels.length - 8} more` : '');
    body.innerHTML = `
      <div class="gap-affected-labels">${affectedText}</div>
      <div class="gap-recommendation">${check.recommendation}</div>
      <button class="gap-view-btn" data-ids='${JSON.stringify(check.affected_node_ids)}' data-sev="${check.severity}" data-count="${check.count}" data-title="${check.title}">
        View in Graph →
      </button>
    `;
    body.querySelector('.gap-view-btn').addEventListener('click', e => {
      const btn   = e.currentTarget;
      const ids   = JSON.parse(btn.dataset.ids);
      const sev   = btn.dataset.sev;
      const count = parseInt(btn.dataset.count);
      viewInGraph(ids, sev, count);
    });
    card.appendChild(body);
  }
  return card;
}

function viewInGraph(nodeIds, severity, count, sourceLabel) {
  setNavActive('nav-graph');
  switchView('graph');

  requestAnimationFrame(() => {
    gapHighlightNodes(nodeIds, severity);
    gapBannerCount.textContent  = count;
    gapBannerSource.textContent = sourceLabel || 'Gap Analysis';
    gapHighlightBanner.hidden   = false;
    gapHighlightActive = true;

    /* pan to first node */
    if (nodeIds.length > 0 && network) {
      network.focus(nodeIds[0], {
        scale: 1.2,
        animation: { duration: 600, easingFunction: 'easeInOutQuad' },
      });
    }
  });
}

function gapHighlightNodes(nodeIds, severity) {
  if (!network || !currentGraph) return;
  const nodeSet = new Set(nodeIds);
  const borderColor = severity === 'critical' ? '#ef4444'
                    : severity === 'warning'  ? '#f97316'
                    :                           '#3b82f6';

  network.body.data.nodes.update(
    currentGraph.nodes.map(n => {
      const t = NODE_TYPES[n.type] || { bg: '#E2E8F0', border: '#94A3B8' };
      if (nodeSet.has(n.id)) {
        return {
          id: n.id, opacity: 1, borderWidth: 3,
          color: {
            background: t.bg, border: borderColor,
            highlight: { background: t.bg, border: borderColor },
            hover:      { background: t.bg, border: borderColor },
          },
        };
      }
      return { id: n.id, opacity: 0.2 };
    })
  );
}

function gapResetHighlight() {
  if (!network || !currentGraph) return;
  gapHighlightActive = false;
  gapHighlightBanner.hidden = true;
  network.body.data.nodes.update(
    currentGraph.nodes.map(n => {
      const t = NODE_TYPES[n.type] || { bg: '#E2E8F0', border: '#94A3B8' };
      return {
        id: n.id, opacity: 1, borderWidth: 2,
        color: {
          background: t.bg, border: t.border,
          highlight: { background: t.bg, border: '#0f2020' },
          hover:      { background: t.bg, border: D.brand },
        },
      };
    })
  );
  network.body.data.edges.update(
    currentGraph.edges.map(e => ({
      id: e.id,
      color: { color: '#B0CECE', highlight: D.brand, hover: D.brandMid },
    }))
  );
}

/* ── Shared highlight primitives ── */
function highlightNodes(nodeIds, severity) {
  if (!network || !currentGraph) return;
  const nodeSet     = new Set(nodeIds);
  const borderColor = severity === 'critical' ? '#ef4444'
                    : severity === 'warning'  ? '#f97316'
                    :                           '#3b82f6';
  network.body.data.nodes.update(
    currentGraph.nodes.map(n => {
      const t = NODE_TYPES[n.type] || { bg: '#E2E8F0', border: '#94A3B8' };
      if (nodeSet.has(n.id)) {
        return {
          id: n.id, opacity: 1, borderWidth: 3,
          color: {
            background: t.bg, border: borderColor,
            highlight: { background: t.bg, border: borderColor },
            hover:      { background: t.bg, border: borderColor },
          },
        };
      }
      return { id: n.id, opacity: 0.2 };
    })
  );
}

function resetGraphHighlight() {
  if (!network || !currentGraph) return;
  network.body.data.nodes.update(
    currentGraph.nodes.map(n => {
      const t = NODE_TYPES[n.type] || { bg: '#E2E8F0', border: '#94A3B8' };
      return {
        id: n.id, opacity: 1, borderWidth: 2,
        color: {
          background: t.bg, border: t.border,
          highlight: { background: t.bg, border: '#0f2020' },
          hover:      { background: t.bg, border: D.brand },
        },
      };
    })
  );
  network.body.data.edges.update(
    currentGraph.edges.map(e => ({
      id: e.id,
      color: { color: '#B0CECE', highlight: D.brand, hover: D.brandMid },
    }))
  );
}

/* Blueprint */
btnGenerateBP.addEventListener('click', () => generateBlueprint(false));

async function generateBlueprint(regen) {
  if (!currentGraphId || !gapAnalysisResult) return;

  const orig = btnGenerateBP.innerHTML;
  btnGenerateBP.disabled = true;
  btnGenerateBP.textContent = 'Generating…';

  try {
    const gapId = regen ? currentGraphId + ':regen' : currentGraphId;
    const res = await fetch(`${API_BASE}/api/gap-analysis/blueprint`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ graph_id: currentGraphId, gap_analysis_id: gapId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    gapBlueprintData = await res.json();
    renderBlueprint(gapBlueprintData);
  } catch (e) {
    alert(`Blueprint generation failed:\n${e.message}`);
  } finally {
    btnGenerateBP.disabled  = false;
    btnGenerateBP.innerHTML = orig;
  }
}

function renderBlueprint(bp) {
  gapBlueprintPre.hidden    = true;
  gapBlueprintResult.hidden = false;

  const nextStepsHtml = (bp.next_steps || []).map((s, i) => `
    <div class="gap-next-step">
      <span class="gap-step-num">${i + 1}</span>
      <span>${s}</span>
    </div>`).join('');

  const docChipsHtml = (bp.documents_to_upload || []).map(d =>
    `<button class="gap-doc-chip" data-doc="${d.replace(/"/g, '&quot;')}">${d}</button>`
  ).join('');

  gapBlueprintResult.innerHTML = `
    <div class="section-label">Blueprint Summary</div>
    <p class="gap-bp-summary">${bp.summary || ''}</p>
    <div>
      <div class="gap-bp-section-label">Recommended Next Steps</div>
      <div class="gap-next-steps">${nextStepsHtml}</div>
    </div>
    <div>
      <div class="gap-bp-section-label">Documents to Upload Next</div>
      <div class="gap-doc-chips">${docChipsHtml}</div>
    </div>
    <div class="gap-bp-actions">
      <button class="gap-bp-action-btn" id="gap-bp-regen">Regenerate</button>
      <button class="gap-bp-action-btn primary" id="gap-bp-export">Export</button>
    </div>
  `;

  gapBlueprintResult.querySelectorAll('.gap-doc-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      setNavActive('nav-graph');
      switchView('graph');
      document.getElementById('upload-panel').scrollTop = 0;
    });
  });
  gapBlueprintResult.querySelector('#gap-bp-regen').addEventListener('click', () => generateBlueprint(true));
  gapBlueprintResult.querySelector('#gap-bp-export').addEventListener('click', exportGapAnalysis);
}

function exportGapAnalysis() {
  if (!gapAnalysisResult) return;
  const lines = [
    'GAP ANALYSIS REPORT',
    'Generated by Metafore Discovery Engine',
    `Date: ${new Date().toLocaleString()}`,
    '',
    `Coverage Score: ${gapAnalysisResult.coverage_score} — ${gapAnalysisResult.score_label}`,
    `Total Nodes: ${gapAnalysisResult.total_nodes}   Total Edges: ${gapAnalysisResult.total_edges}`,
    '',
    '─── GAPS ───',
  ];
  (gapAnalysisResult.checks || []).forEach(c => {
    const status = c.count === 0 ? '✓ PASSED' : `✗ ${c.count} affected`;
    lines.push(`[${c.severity.toUpperCase()}] ${c.title} — ${status}`);
    if (c.count > 0) {
      lines.push(`  Nodes: ${c.affected_node_labels.join(', ')}`);
      lines.push(`  → ${c.recommendation}`);
    }
    lines.push('');
  });
  if (gapBlueprintData) {
    lines.push('─── BLUEPRINT ───', '', gapBlueprintData.summary || '', '');
    lines.push('Next Steps:');
    (gapBlueprintData.next_steps || []).forEach((s, i) => lines.push(`  ${i + 1}. ${s}`));
    lines.push('');
    lines.push('Documents to Upload:');
    (gapBlueprintData.documents_to_upload || []).forEach(d => lines.push(`  • ${d}`));
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'gap-analysis.txt'; a.click();
  URL.revokeObjectURL(url);
}

/* ── Conformance Checker ── */
const conformancePanel    = document.getElementById('conformance-panel');
const confGraphInfo       = document.getElementById('conf-graph-info');
const confMainDocRow      = document.getElementById('conf-main-doc-row');
const confDropZone        = document.getElementById('conf-drop-zone');
const confFileInput       = document.getElementById('conf-file-input');
const confFileSelected    = document.getElementById('conf-file-selected');
const btnRunConformance   = document.getElementById('btn-run-conformance');
const confLoading         = document.getElementById('conf-loading');
const confLoadingLabel    = document.getElementById('conf-loading-label');
const confResults         = document.getElementById('conf-results');
const confScoreCard       = document.getElementById('conf-score-card');
const confOverlayControls = document.getElementById('conf-overlay-controls');
const confReport          = document.getElementById('conf-report');
const btnConfResetUpload  = document.getElementById('btn-conf-reset-upload');
const btnConfRerun        = document.getElementById('btn-conf-rerun');

let conformanceEvidenceId    = null;
let conformanceResult        = null;
let conformanceActiveOverlay = null; // 'all' | 'confirmed' | 'deviated' | null

/* Nav */
document.getElementById('nav-conformance').addEventListener('click', () => {
  setNavActive('nav-conformance');
  switchView('conformance');
  confUpdateGraphLabel();
  if (conformanceResult) {
    confResults.hidden = false;
    confRenderOverlayControls();
  }
});

function confUpdateGraphLabel() {
  if (!currentGraph) {
    confGraphInfo.textContent = 'No graph loaded';
    confMainDocRow.hidden = true;
    return;
  }
  confGraphInfo.textContent = `${currentGraph.nodes.length} nodes · ${currentGraph.edges.length} edges`;
  const docName = selectedFiles[0]?.name || 'uploaded document';
  confMainDocRow.hidden = false;
  confMainDocRow.innerHTML =
    `<span class="conf-main-doc-label">Analysing against:</span>` +
    `<span class="conf-main-doc-name">${docName}</span>` +
    `<span class="conf-main-doc-check">✓</span>`;
}

/* Drop zone */
confDropZone.addEventListener('click', () => confFileInput.click());
confDropZone.addEventListener('dragover', e => { e.preventDefault(); confDropZone.classList.add('drag-over'); });
confDropZone.addEventListener('dragleave', () => confDropZone.classList.remove('drag-over'));
confDropZone.addEventListener('drop', e => {
  e.preventDefault();
  confDropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) confHandleFile(f);
});
confFileInput.addEventListener('change', () => {
  if (confFileInput.files[0]) confHandleFile(confFileInput.files[0]);
  confFileInput.value = '';
});

function confHandleFile(file) {
  if (!currentGraphId) {
    alert('Please extract a graph before uploading evidence.');
    return;
  }
  confUploadEvidence(file);
}

async function confUploadEvidence(file) {
  confDropZone.classList.add('uploading');
  btnRunConformance.disabled = true;
  btnRunConformance.textContent = 'Uploading…';

  const fd = new FormData();
  fd.append('graph_id', currentGraphId);
  fd.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/conformance/upload`, { method: 'POST', body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    conformanceEvidenceId = data.evidence_id;

    confFileSelected.hidden = false;
    confFileSelected.innerHTML =
      `<span class="conf-sel-name">${data.filename}</span>` +
      `<span class="conf-sel-words">${data.word_count.toLocaleString()} words</span>`;

    btnRunConformance.disabled = false;
    btnRunConformance.textContent = 'Run Conformance Check →';
  } catch (e) {
    alert(`Evidence upload failed: ${e.message}`);
    btnRunConformance.textContent = 'Run Conformance Check →';
  } finally {
    confDropZone.classList.remove('uploading');
  }
}

btnRunConformance.addEventListener('click', confRunAnalysis);

async function confRunAnalysis() {
  if (!currentGraphId || !conformanceEvidenceId) return;

  const eligible = (currentGraph?.nodes || []).filter(n =>
    ['Process', 'Role', 'Policy', 'DataEntity'].includes(n.type)
  );
  confLoadingLabel.textContent =
    `Comparing evidence against ${eligible.length} graph nodes…`;

  confResults.hidden  = true;
  confLoading.hidden  = false;
  btnRunConformance.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/conformance/analyse`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ graph_id: currentGraphId, evidence_id: conformanceEvidenceId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    conformanceResult = await res.json();
    confRenderResults(conformanceResult);
  } catch (e) {
    alert(`Conformance analysis failed:\n${e.message}`);
  } finally {
    confLoading.hidden = true;
    btnRunConformance.disabled = false;
  }
}

function confRenderResults(result) {
  confRenderScoreCard(result);
  confRenderOverlayControls();
  confRenderReport(result);
  confResults.hidden = false;
}

function confRenderScoreCard(result) {
  const rate  = result.overall_conformance_rate ?? 0;
  const color = rate >= 80 ? '#1D9E75' : rate >= 50 ? '#f97316' : '#ef4444';
  confScoreCard.innerHTML = `
    <div class="conf-score-header">CONFORMANCE SCORE</div>
    <div class="conf-score-bar-wrap">
      <div class="conf-score-bar-track">
        <div class="conf-score-bar-fill" style="width:${rate}%;background:${color}"></div>
      </div>
      <span class="conf-score-pct" style="color:${color}">${rate}%</span>
    </div>
    <div class="conf-score-counts">
      <span class="conf-count-confirmed">✓ ${result.confirmed_count ?? 0} confirmed</span>
      <span class="conf-count-deviated">✗ ${result.deviated_count ?? 0} deviated</span>
      <span class="conf-count-notfound">○ ${result.not_found_count ?? 0} not assessed</span>
    </div>
    <p class="conf-summary">${result.summary || ''}</p>
  `;
}

function confRenderOverlayControls() {
  confOverlayControls.innerHTML = '';
  const modes = [
    { key: 'all',       label: 'Show All' },
    { key: 'deviated',  label: 'Deviations only', prominent: true },
    { key: 'confirmed', label: 'Confirmed only' },
    { key: null,        label: 'Clear' },
  ];
  modes.forEach(({ key, label, prominent }) => {
    const btn = document.createElement('button');
    btn.className = 'conf-overlay-btn' + (prominent ? ' conf-overlay-btn-prominent' : '');
    if (conformanceActiveOverlay === key && key !== null) btn.classList.add('active');
    btn.textContent = label;
    btn.addEventListener('click', () => confApplyOverlay(key));
    confOverlayControls.appendChild(btn);
  });
}

function confApplyOverlay(mode) {
  if (!network || !currentGraph || !conformanceResult) return;
  conformanceActiveOverlay = mode;
  confRenderOverlayControls();

  const results      = conformanceResult.conformance_results || [];
  const confirmedSet = new Set(results.filter(r => r.status === 'confirmed').map(r => r.node_id));
  const deviatedSet  = new Set(results.filter(r => r.status === 'deviated').map(r => r.node_id));

  if (mode === null) {
    resetGraphHighlight();
    gapHighlightBanner.hidden = true;
    gapHighlightActive = false;
    return;
  }

  network.body.data.nodes.update(
    currentGraph.nodes.map(n => {
      const t = NODE_TYPES[n.type] || { bg: '#E2E8F0', border: '#94A3B8' };

      if (mode === 'all') {
        if (confirmedSet.has(n.id)) return {
          id: n.id, opacity: 1, borderWidth: 3,
          color: { background: t.bg, border: '#1D9E75',
                   highlight: { background: t.bg, border: '#1D9E75' },
                   hover:      { background: t.bg, border: '#1D9E75' } },
        };
        if (deviatedSet.has(n.id)) return {
          id: n.id, opacity: 1, borderWidth: 3,
          color: { background: '#FEF2F2', border: '#ef4444',
                   highlight: { background: '#FEF2F2', border: '#ef4444' },
                   hover:      { background: '#FEF2F2', border: '#ef4444' } },
        };
        return { id: n.id, opacity: 0.35, borderWidth: 2,
                 color: { background: t.bg, border: t.border,
                          highlight: { background: t.bg, border: '#0f2020' },
                          hover:      { background: t.bg, border: D.brand } } };
      }

      if (mode === 'confirmed') {
        if (confirmedSet.has(n.id)) return {
          id: n.id, opacity: 1, borderWidth: 3,
          color: { background: t.bg, border: '#1D9E75',
                   highlight: { background: t.bg, border: '#1D9E75' },
                   hover:      { background: t.bg, border: '#1D9E75' } },
        };
        return { id: n.id, opacity: 0.15 };
      }

      if (mode === 'deviated') {
        if (deviatedSet.has(n.id)) return {
          id: n.id, opacity: 1, borderWidth: 3,
          color: { background: '#FEF2F2', border: '#ef4444',
                   highlight: { background: '#FEF2F2', border: '#ef4444' },
                   hover:      { background: '#FEF2F2', border: '#ef4444' } },
        };
        return { id: n.id, opacity: 0.15 };
      }

      return { id: n.id, opacity: 1 };
    })
  );

  const count = mode === 'all'       ? confirmedSet.size + deviatedSet.size
              : mode === 'confirmed' ? confirmedSet.size
              :                        deviatedSet.size;
  const label = mode === 'all'       ? 'Conformance — All'
              : mode === 'confirmed' ? 'Conformance — Confirmed'
              :                        'Conformance — Deviations';
  gapBannerCount.textContent  = count;
  gapBannerSource.textContent = label;
  gapHighlightBanner.hidden   = false;
  gapHighlightActive = true;

  /* switch to graph view so the overlay is visible */
  if (conformancePanel && !conformancePanel.hidden) {
    setNavActive('nav-graph');
    switchView('graph');
  }
}

function confRenderReport(result) {
  confReport.innerHTML = '';

  /* 1 — Critical deviations (Policy) */
  const critical = result.critical_deviations || [];
  confReport.appendChild(confBuildDeviationSection(
    `🔴 Critical — Policy Violations (${critical.length})`,
    critical,
    'critical',
    'conf-section-critical'
  ));

  /* 2 — Process & Role deviations */
  const other = result.process_deviations || [];
  confReport.appendChild(confBuildDeviationSection(
    `🟡 Deviations — Process &amp; Role (${other.length})`,
    other,
    'warning',
    'conf-section-warning'
  ));

  /* 3 — Confirmed (collapsed) */
  const confirmed = (result.conformance_results || []).filter(r => r.status === 'confirmed');
  const confSection = document.createElement('div');
  confSection.className = 'conf-report-section conf-section-confirmed';
  const confToggle = document.createElement('button');
  confToggle.className = 'conf-section-toggle';
  confToggle.innerHTML =
    `<span>✓ Confirmed (${confirmed.length})</span>` +
    `<svg class="conf-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;
  const confList = document.createElement('ul');
  confList.className = 'conf-confirmed-list hidden';
  confirmed.forEach(r => {
    const li = document.createElement('li');
    li.className = 'conf-confirmed-item';
    const excerpt = r.evidence_excerpt
      ? `<span class="conf-confirmed-excerpt">"${r.evidence_excerpt.slice(0, 80)}${r.evidence_excerpt.length > 80 ? '…' : ''}"</span>`
      : '';
    li.innerHTML = `<span class="conf-confirmed-check">✓</span><span class="conf-confirmed-label">${r.node_label}</span>${excerpt}`;
    confList.appendChild(li);
  });
  confToggle.addEventListener('click', () => {
    confList.classList.toggle('hidden');
    confToggle.querySelector('.conf-chevron').classList.toggle('flipped');
  });
  confSection.appendChild(confToggle);
  confSection.appendChild(confList);
  confReport.appendChild(confSection);

  /* 4 — Not assessed */
  const notFound = (result.conformance_results || []).filter(r => r.status === 'not_found');
  if (notFound.length) {
    const nfSection = document.createElement('div');
    nfSection.className = 'conf-not-found-row';
    const nfToggle = document.createElement('button');
    nfToggle.className = 'conf-nf-toggle';
    nfToggle.innerHTML =
      `<span>○ ${notFound.length} node${notFound.length !== 1 ? 's' : ''} not mentioned in the evidence document</span>` +
      `<svg class="conf-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;
    const nfList = document.createElement('p');
    nfList.className = 'conf-nf-list hidden';
    nfList.textContent = notFound.map(r => r.node_label).join(' · ');
    nfToggle.addEventListener('click', () => {
      nfList.classList.toggle('hidden');
      nfToggle.querySelector('.conf-chevron').classList.toggle('flipped');
    });
    nfSection.appendChild(nfToggle);
    nfSection.appendChild(nfList);
    confReport.appendChild(nfSection);
  }
}

function confBuildDeviationSection(headerHtml, items, severity, sectionClass) {
  const section = document.createElement('div');
  section.className = `conf-report-section ${sectionClass}`;
  const header = document.createElement('div');
  header.className = 'conf-section-header';
  header.innerHTML = headerHtml;
  section.appendChild(header);
  if (!items.length) {
    const none = document.createElement('p');
    none.className = 'conf-none-msg';
    none.textContent = 'None found.';
    section.appendChild(none);
    return section;
  }
  items.forEach(r => {
    const card = document.createElement('div');
    card.className = `conf-dev-card conf-dev-${severity}`;
    const nodeData = currentGraph?.nodes.find(n => n.id === r.node_id);
    card.innerHTML = `
      <div class="conf-dev-card-header">
        <span class="conf-dev-dot"></span>
        <span class="conf-dev-title">${r.node_label}</span>
      </div>
      ${nodeData?.description ? `<div class="conf-dev-row"><span class="conf-dev-field">What SOP requires:</span><span class="conf-dev-value">${nodeData.description}</span></div>` : ''}
      ${r.evidence_excerpt   ? `<div class="conf-dev-row"><span class="conf-dev-field">What evidence shows:</span><span class="conf-dev-value conf-dev-quote">"${r.evidence_excerpt}"</span></div>` : ''}
      ${r.deviation_detail   ? `<div class="conf-dev-row"><span class="conf-dev-field">Deviation:</span><span class="conf-dev-value">${r.deviation_detail}</span></div>` : ''}
      <div class="conf-dev-footer">
        <button class="conf-view-btn" data-id="${r.node_id}" data-sev="${severity}" data-label="${r.node_label.replace(/"/g, '&quot;')}">View in Graph →</button>
      </div>
    `;
    card.querySelector('.conf-view-btn').addEventListener('click', e => {
      const btn   = e.currentTarget;
      const nid   = btn.dataset.id;
      const sev   = btn.dataset.sev;
      const lbl   = btn.dataset.label;
      highlightNodes([nid], sev);
      gapBannerCount.textContent  = 1;
      gapBannerSource.textContent = lbl;
      gapHighlightBanner.hidden   = false;
      gapHighlightActive = true;
      setNavActive('nav-graph');
      switchView('graph');
      if (network) network.focus(nid, { scale: 1.4, animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
    });
    section.appendChild(card);
  });
  return section;
}

/* Actions */
btnConfResetUpload.addEventListener('click', () => {
  conformanceEvidenceId = null;
  confFileSelected.hidden = true;
  confFileSelected.innerHTML = '';
  confResults.hidden = true;
  conformanceResult = null;
  conformanceActiveOverlay = null;
  btnRunConformance.disabled = true;
  btnRunConformance.textContent = 'Run Conformance Check →';
  resetGraphHighlight();
  gapHighlightBanner.hidden = true;
  gapHighlightActive = false;
});

btnConfRerun.addEventListener('click', () => {
  if (currentGraphId && conformanceEvidenceId) confRunAnalysis();
});

/* ── Pulse Recommendations ── */
btnPulse.addEventListener('click', openPulseDrawer);
pulseDrawerClose.addEventListener('click', closePulseDrawer);
pulseOverlay.addEventListener('click', closePulseDrawer);

function openPulseDrawer() {
  pulseDrawer.classList.add('open');
  pulseOverlay.hidden = false;
  if (pulseData) renderPulseItems(pulseData.items || []);
}

function closePulseDrawer() {
  pulseDrawer.classList.remove('open');
  pulseOverlay.hidden = true;
}

async function fetchPulse() {
  if (!currentGraphId) return;
  try {
    const res = await fetch(`${API_BASE}/api/pulse/calculate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ graph_id: currentGraphId }),
    });
    if (!res.ok) return;
    pulseData = await res.json();
    updatePulseBadge(pulseData.items || []);
  } catch (_) {}
}

function updatePulseBadge(items) {
  const urgentCount = items.filter(i => i.severity === 'critical' || i.severity === 'warning').length;
  const critCount   = items.filter(i => i.severity === 'critical').length;
  btnPulse.disabled  = false;
  pulseBadge.hidden  = urgentCount === 0;
  if (urgentCount > 0) {
    pulseBadge.textContent = urgentCount > 9 ? '9+' : String(urgentCount);
    pulseBadge.className   = 'pulse-badge' + (critCount > 0 ? '' : ' badge-warning');
  }
}

function renderPulseItems(items) {
  pulseDrawerBody.innerHTML = '';

  if (!items.length) {
    pulseDrawerBody.innerHTML = '<div class="pulse-empty-state">No issues detected — your graph looks healthy.</div>';
    return;
  }

  const ORDER     = ['NOW', 'THIS_WEEK', 'BACKLOG'];
  const CAT_LABEL = { NOW: '🔴 Now', THIS_WEEK: '🟡 This Week', BACKLOG: '🔵 Backlog' };

  ORDER.forEach(cat => {
    const group = items.filter(i => i.category === cat);
    if (!group.length) return;
    const header = document.createElement('div');
    header.className   = 'pulse-category-header';
    header.textContent = CAT_LABEL[cat];
    pulseDrawerBody.appendChild(header);
    group.forEach(item => pulseDrawerBody.appendChild(buildPulseCard(item)));
  });

  /* AI Insights section */
  const aiSection = document.createElement('div');
  aiSection.className = 'pulse-ai-section';
  aiSection.id        = 'pulse-ai-section';
  aiSection.innerHTML = `
    <div class="pulse-ai-header">
      <span class="pulse-ai-title">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        AI Strategic Insights
      </span>
      <button class="pulse-ai-btn" id="pulse-ai-btn">Generate →</button>
    </div>
    <div id="pulse-ai-content"></div>
  `;
  pulseDrawerBody.appendChild(aiSection);

  document.getElementById('pulse-ai-btn').addEventListener('click', fetchPulseAi);
  if (pulseAiData) renderPulseAi(pulseAiData);

  const disclaimer = document.createElement('p');
  disclaimer.className   = 'pulse-disclaimer';
  disclaimer.textContent = 'Auto-updated when a new graph is extracted';
  pulseDrawerBody.appendChild(disclaimer);
}

function buildPulseCard(item) {
  const card = document.createElement('div');
  card.className = `pulse-item-card sev-${item.severity}`;

  const hasNodes  = item.affected_node_ids && item.affected_node_ids.length > 0;
  const countText = hasNodes
    ? `${item.affected_node_ids.length} node${item.affected_node_ids.length !== 1 ? 's' : ''}`
    : '';
  const viewBtnHtml = hasNodes ? `<button class="pulse-view-btn">View in Graph →</button>` : '';

  card.innerHTML = `
    <div class="pulse-item-header">
      <span class="pulse-sev-dot sev-${item.severity}"></span>
      <span class="pulse-item-title">${item.title}</span>
    </div>
    <div class="pulse-item-desc">${item.description}</div>
    <div class="pulse-item-footer">
      <span class="pulse-affected-count">${countText}</span>
      ${viewBtnHtml}
    </div>
  `;

  if (hasNodes) {
    card.querySelector('.pulse-view-btn').addEventListener('click', () => {
      closePulseDrawer();
      setNavActive('nav-graph');
      switchView('graph');
      requestAnimationFrame(() => {
        highlightNodes(item.affected_node_ids, item.severity);
        gapBannerCount.textContent  = item.affected_node_ids.length;
        gapBannerSource.textContent = item.title;
        gapHighlightBanner.hidden   = false;
        gapHighlightActive = true;
        if (item.affected_node_ids.length > 0 && network) {
          network.focus(item.affected_node_ids[0], {
            scale: 1.2,
            animation: { duration: 600, easingFunction: 'easeInOutQuad' },
          });
        }
      });
    });
  }
  return card;
}

async function fetchPulseAi() {
  if (!currentGraphId || !pulseData) return;
  const btn     = document.getElementById('pulse-ai-btn');
  const content = document.getElementById('pulse-ai-content');
  if (!btn || !content) return;

  btn.disabled    = true;
  btn.textContent = 'Generating…';
  content.innerHTML = '<div class="pulse-empty-state">Analysing graph…</div>';

  try {
    const res = await fetch(`${API_BASE}/api/pulse/ai-recommendations`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ graph_id: currentGraphId }),
    });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    pulseAiData = await res.json();
    renderPulseAi(pulseAiData);
  } catch (e) {
    content.innerHTML = `<div class="pulse-empty-state">AI insights failed: ${e.message}</div>`;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Regenerate'; }
  }
}

function renderPulseAi(data) {
  const content = document.getElementById('pulse-ai-content');
  if (!content) return;
  const recs = data.recommendations || [];
  if (!recs.length) {
    content.innerHTML = '<div class="pulse-empty-state">No AI insights available.</div>';
    return;
  }
  content.innerHTML = recs.map(r => `
    <div class="pulse-ai-card">
      <div class="pulse-ai-rec-title">${r.title}</div>
      <div class="pulse-ai-rec-detail">${r.detail}</div>
      <div class="pulse-ai-rec-impact">💡 ${r.business_impact}</div>
    </div>
  `).join('');
}

/* ── Natural Language Query ── */

function nlqInit() {
  nlqContainer.hidden = false;
  nlqHistory = [];
  nlqAnswerCard.hidden = true;
  nlqAnswerCard.classList.remove('visible');
  nlqInput.value = '';
  nlqCharCount.className = 'nlq-char-count';
  nlqRenderContextChips();
}

function nlqRenderContextChips() {
  nlqContextChips.innerHTML = '';
  if (nlqHistory.length === 0) {
    NLQ_SAMPLES.forEach(q => {
      const btn = document.createElement('button');
      btn.className = 'nlq-sample-chip';
      btn.textContent = q;
      btn.addEventListener('click', () => nlqRunQuery(q));
      nlqContextChips.appendChild(btn);
    });
  } else {
    nlqHistory.slice(-3).forEach(entry => {
      const btn = document.createElement('button');
      btn.className = 'nlq-history-chip';
      btn.textContent = entry.question.length > 28 ? entry.question.slice(0, 26) + '…' : entry.question;
      btn.title = entry.question;
      btn.addEventListener('click', () => nlqRunQuery(entry.question));
      nlqContextChips.appendChild(btn);
    });
  }
}

nlqInput.addEventListener('input', () => {
  const len = nlqInput.value.length;
  if (len > 480) {
    nlqCharCount.textContent = `${len}/500`;
    nlqCharCount.className = 'nlq-char-count critical';
  } else if (len > 400) {
    nlqCharCount.textContent = `${len}/500`;
    nlqCharCount.className = 'nlq-char-count warn';
  } else {
    nlqCharCount.className = 'nlq-char-count';
  }
});

nlqInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const q = nlqInput.value.trim();
    if (q) nlqRunQuery(q);
  }
});

nlqSubmit.addEventListener('click', () => {
  const q = nlqInput.value.trim();
  if (q) nlqRunQuery(q);
});

nlqCloseBtn.addEventListener('click', () => {
  nlqAnswerCard.classList.remove('visible');
  setTimeout(() => { nlqAnswerCard.hidden = true; }, 230);
  nlqResetGraphHighlight();
});

async function nlqRunQuery(question) {
  if (!currentGraphId) return;

  if (currentGraph && currentGraph.nodes.length < 5) {
    nlqAnswerCard.hidden = false;
    requestAnimationFrame(() => nlqAnswerCard.classList.add('visible'));
    nlqShimmer.hidden = true;
    nlqAnswerContent.hidden = false;
    nlqQuestionEcho.textContent = question;
    nlqAnswerText.textContent = 'Upload a richer document to use natural language queries.';
    nlqNodeChips.innerHTML = '';
    nlqFollowupChips.innerHTML = '';
    return;
  }

  if (nlqAbortController) nlqAbortController.abort();
  nlqAbortController = new AbortController();
  const signal = nlqAbortController.signal;

  nlqAnswerCard.hidden = false;
  nlqAnswerCard.classList.remove('visible');
  requestAnimationFrame(() => nlqAnswerCard.classList.add('visible'));
  nlqShimmer.hidden = false;
  nlqAnswerContent.hidden = true;
  nlqInput.value = '';
  nlqCharCount.className = 'nlq-char-count';
  nlqSubmit.disabled = true;

  const timeout = setTimeout(() => nlqAbortController.abort(), 30000);

  try {
    const res = await fetch(`${API_BASE}/api/query/natural-language`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph_id: currentGraphId, question }),
      signal,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const result = await res.json();
    nlqHistory.push({ question, ...result });
    nlqShowAnswer(result, question);
    nlqHighlightGraph(result.relevant_node_ids || [], result.relevant_edge_ids || []);
    nlqRenderContextChips();
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') {
      nlqAnswerCard.classList.remove('visible');
      setTimeout(() => { nlqAnswerCard.hidden = true; }, 230);
    } else {
      nlqShimmer.hidden = true;
      nlqAnswerContent.hidden = false;
      nlqQuestionEcho.textContent = question;
      nlqAnswerText.textContent = `Error: ${e.message}`;
      nlqNodeChips.innerHTML = '';
      nlqFollowupChips.innerHTML = '';
    }
  } finally {
    nlqSubmit.disabled = false;
  }
}

function nlqShowAnswer(result, question) {
  nlqShimmer.hidden = true;
  nlqAnswerContent.hidden = false;
  nlqQuestionEcho.textContent = question;
  nlqAnswerText.textContent = result.answer || '';

  nlqNodeChips.innerHTML = '';
  (result.relevant_node_ids || []).forEach(nodeId => {
    const node = currentGraph?.nodes.find(n => n.id === nodeId);
    if (!node) return;
    const t = NODE_TYPES[node.type] || { bg: '#E2E8F0', border: '#94A3B8' };
    const chip = document.createElement('button');
    chip.className = 'nlq-node-chip';
    chip.style.background = t.bg;
    chip.style.color = t.border;
    chip.style.borderColor = t.border + '80';
    chip.innerHTML = `<span class="nlq-node-chip-dot" style="background:${t.border}"></span>${node.label}`;
    chip.title = `Pan to ${node.label}`;
    chip.addEventListener('click', () => panToNode(nodeId));
    nlqNodeChips.appendChild(chip);
  });

  nlqFollowupChips.innerHTML = '';
  (result.follow_up_questions || []).slice(0, 3).forEach(q => {
    const chip = document.createElement('button');
    chip.className = 'nlq-followup-chip';
    chip.textContent = q;
    chip.addEventListener('click', () => nlqRunQuery(q));
    nlqFollowupChips.appendChild(chip);
  });
}

function nlqHighlightGraph(nodeIds, edgeIds) {
  if (!network || !currentGraph) return;
  const nodeSet = new Set(nodeIds);
  const edgeSet = new Set(edgeIds);

  network.body.data.nodes.update(
    currentGraph.nodes.map(n => ({ id: n.id, opacity: nodeSet.has(n.id) ? 1 : 0.15 }))
  );
  network.body.data.edges.update(
    currentGraph.edges.map(e => ({
      id: e.id,
      color: edgeSet.has(e.id)
        ? { color: D.brand, highlight: D.brand, hover: D.brand }
        : { color: 'rgba(176,206,206,0.12)', highlight: 'rgba(176,206,206,0.12)', hover: 'rgba(176,206,206,0.12)' },
    }))
  );
}

function nlqResetGraphHighlight() {
  resetGraphHighlight();
}

function panToNode(nodeId) {
  if (!network) return;
  network.focus(nodeId, {
    scale: 1.5,
    animation: { duration: 600, easingFunction: 'easeInOutQuad' },
  });
}

/* ── Reset ── */
btnReset.addEventListener('click', () => {
  selectedFiles   = [];
  currentGraph    = null;
  currentGraphId  = null;
  renderFileList();
  if (network) { network.destroy(); network = null; }
  closeDetailPanel();
  chipNodeEl.hidden = true;
  chipEdgeEl.hidden = true;
  document.querySelectorAll('.cache-chip').forEach(el => el.remove());
  legendSection.hidden = true;
  legendList.innerHTML = '';
  placeholder.style.display = '';
  btnObjectModel.disabled  = true;
  btnWorkflows.disabled    = true;
  btnExtract.disabled      = true;
  workflowList.innerHTML   = '';
  workflowThinMsg.hidden   = true;
  workflowSpinner.classList.add('hidden');
  pydanticCode.textContent = '';
  schemaCode.textContent   = '';
  modelSummary.textContent = '';
  _omSetState('empty');
  if (nlqAbortController) { nlqAbortController.abort(); nlqAbortController = null; }
  nlqContainer.hidden          = true;
  gapAnalysisResult            = null;
  gapBlueprintData             = null;
  gapHighlightActive           = false;
  switchView('graph');
  gapEmptyState.hidden         = false;
  gapResults.hidden            = true;
  gapLoading.hidden            = true;
  gapHighlightBanner.hidden    = true;
  gapLastAnalysed.textContent  = 'Not yet analysed';
  btnGapAnalyse.disabled       = true;
  btnGapAnalyseEmpty.disabled  = true;
  gapBlueprintPre.hidden       = false;
  gapBlueprintResult.hidden    = true;
  nlqAnswerCard.hidden     = true;
  nlqAnswerCard.classList.remove('visible');
  nlqHistory               = [];
  nlqContextChips.innerHTML = '';
  nlqInput.value           = '';
  pulseData              = null;
  pulseAiData            = null;
  btnPulse.disabled      = true;
  pulseBadge.hidden      = true;
  closePulseDrawer();
  pulseDrawerBody.innerHTML = '<div class="pulse-empty-state">Extract a graph to see recommendations.</div>';
  conformanceEvidenceId    = null;
  conformanceResult        = null;
  conformanceActiveOverlay = null;
  confResults.hidden       = true;
  confFileSelected.hidden  = true;
  confFileSelected.innerHTML = '';
  btnRunConformance.disabled = true;
  btnRunConformance.textContent = 'Run Conformance Check →';
  confGraphInfo.textContent = 'No graph loaded';
  confMainDocRow.hidden = true;
  setNavActive('nav-graph');
});

/* ── Keyboard ── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (pulseDrawer.classList.contains('open')) { closePulseDrawer(); return; }
    closeDetailPanel();
  }
});
