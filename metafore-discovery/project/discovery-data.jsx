/* Discovery Engine — demo data
   Banking loan origination domain (matches the BRD: ~25 nodes, conformance findings, etc.) */

const NODE_TYPES = {
  Process:    { fill: '#C7F0ED', ring: '#0D9488', ink: '#0d8a83', label: 'Process' },
  Role:       { fill: '#FED7AA', ring: '#EA580C', ink: '#c2410c', label: 'Role' },
  System:     { fill: '#BFDBFE', ring: '#3B82F6', ink: '#1d4ed8', label: 'System' },
  Policy:     { fill: '#FECACA', ring: '#EF4444', ink: '#dc2626', label: 'Policy' },
  DataEntity: { fill: '#DDD6FE', ring: '#7C4FE0', ink: '#6d28d9', label: 'Data Entity' },
  Event:      { fill: '#FEF08A', ring: '#CA8A04', ink: '#a16207', label: 'Event' },
};

// 24 nodes — banking loan origination
const DEMO_NODES = [
  // Processes (core flow, left-to-right)
  { id: 'p1', type: 'Process', label: 'Application Intake',         x: 120, y: 360, deg: 4 },
  { id: 'p2', type: 'Process', label: 'KYC Verification',           x: 290, y: 240, deg: 5 },
  { id: 'p3', type: 'Process', label: 'Credit Assessment',          x: 470, y: 360, deg: 6 },
  { id: 'p4', type: 'Process', label: 'Underwriting Review',        x: 660, y: 220, deg: 5 },
  { id: 'p5', type: 'Process', label: 'Sanction & Approval',        x: 820, y: 380, deg: 4 },
  { id: 'p6', type: 'Process', label: 'Disbursement',               x: 990, y: 280, deg: 3 },
  // Roles
  { id: 'r1', type: 'Role',    label: 'Relationship Manager',       x: 220, y: 510, deg: 3 },
  { id: 'r2', type: 'Role',    label: 'KYC Analyst',                x: 360, y: 110, deg: 2 },
  { id: 'r3', type: 'Role',    label: 'Credit Officer',             x: 540, y: 510, deg: 4 },
  { id: 'r4', type: 'Role',    label: 'Senior Underwriter',         x: 720, y: 100, deg: 3 },
  { id: 'r5', type: 'Role',    label: 'Branch Manager',             x: 900, y: 530, deg: 2 },
  // Systems
  { id: 's1', type: 'System',  label: 'LOS · Loan OS',              x: 380, y: 410, deg: 5 },
  { id: 's2', type: 'System',  label: 'Credit Bureau API',          x: 580, y: 240, deg: 3 },
  { id: 's3', type: 'System',  label: 'Core Banking',               x: 1050, y: 410, deg: 3 },
  // Policies
  { id: 'po1', type: 'Policy', label: 'AML Threshold ≥ ₹10L',       x: 260, y: 60,  deg: 2 },
  { id: 'po2', type: 'Policy', label: 'DTI ≤ 50%',                  x: 580, y: 80,  deg: 2 },
  { id: 'po3', type: 'Policy', label: 'TAT ≤ 7 working days',       x: 880, y: 60,  deg: 2 },
  // Data
  { id: 'd1', type: 'DataEntity', label: 'Customer File',           x: 100, y: 220, deg: 3 },
  { id: 'd2', type: 'DataEntity', label: 'Credit Bureau Report',    x: 460, y: 530, deg: 3 },
  { id: 'd3', type: 'DataEntity', label: 'Appraisal Report',        x: 660, y: 540, deg: 2 },
  { id: 'd4', type: 'DataEntity', label: 'Sanction Letter',         x: 870, y: 220, deg: 3 },
  // Events
  { id: 'e1', type: 'Event',   label: 'Application Submitted',      x: 60,  y: 420, deg: 1 },
  { id: 'e2', type: 'Event',   label: 'Loan Disbursed',             x: 1130, y: 200, deg: 1 },
];

const DEMO_EDGES = [
  { from: 'p1', to: 'p2', label: 'triggers' },
  { from: 'p2', to: 'p3', label: 'precedes' },
  { from: 'p3', to: 'p4', label: 'feeds' },
  { from: 'p4', to: 'p5', label: 'precedes' },
  { from: 'p5', to: 'p6', label: 'authorises' },
  { from: 'r1', to: 'p1', label: 'performs' },
  { from: 'r2', to: 'p2', label: 'performs' },
  { from: 'r3', to: 'p3', label: 'performs' },
  { from: 'r4', to: 'p4', label: 'performs' },
  { from: 'r5', to: 'p5', label: 'approves' },
  { from: 'p1', to: 's1', label: 'uses' },
  { from: 'p3', to: 's2', label: 'queries' },
  { from: 'p6', to: 's3', label: 'writes to' },
  { from: 'po1', to: 'p2', label: 'governs' },
  { from: 'po2', to: 'p3', label: 'governs' },
  { from: 'po3', to: 'p5', label: 'governs' },
  { from: 'd1', to: 'p1', label: 'input' },
  { from: 'p3', to: 'd2', label: 'produces' },
  { from: 'p4', to: 'd3', label: 'produces' },
  { from: 'p5', to: 'd4', label: 'produces' },
  { from: 'e1', to: 'p1', label: 'starts' },
  { from: 'p6', to: 'e2', label: 'emits' },
  { from: 'p3', to: 'p2', label: 'depends on' },
  { from: 's1', to: 'd1', label: 'stores' },
];

const DEMO_GRAPH = { nodes: DEMO_NODES, edges: DEMO_EDGES };

const PULSE_ITEMS = [
  { id:1, severity:'critical', title:'AML check sequenced after credit pull',  source:'Audit Report Q3', age:'2h ago', count:9 },
  { id:2, severity:'high',     title:'TAT breach: 12 cases > 7 days SLA',       source:'Live ops',         age:'15m ago', count:12 },
  { id:3, severity:'high',     title:'DTI computation by RM (should be CO)',    source:'Conformance',      age:'1d ago',  count:4 },
  { id:4, severity:'medium',   title:'Appraisal before completeness check',     source:'Audit Report Q3', age:'1d ago',  count:6 },
  { id:5, severity:'medium',   title:'Missing sanction letter template ref',    source:'Gap analysis',     age:'2d ago',  count:1 },
  { id:6, severity:'low',      title:'Customer file lacks PAN field linkage',   source:'Object model',     age:'3d ago',  count:1 },
];

const CONFORMANCE_FINDINGS = [
  { node:'AML Threshold ≥ ₹10L', type:'Policy', status:'deviated',  severity:'critical',
    quote:'In 9 of 23 sampled cases, AML screening was performed after credit bureau query, breaching policy sequencing.',
    expected:'AML screening MUST precede credit bureau query.', source:'§4.2 Q3 Audit Report' },
  { node:'KYC Verification', type:'Process', status:'confirmed', severity:null,
    quote:'KYC was performed in all 47 sampled applications using approved bureau (CKYC).',
    expected:'KYC verification before credit assessment.', source:'§3.1 Q3 Audit Report' },
  { node:'DTI ≤ 50%', type:'Policy', status:'deviated', severity:'high',
    quote:'4 cases (Apps #2204, #2231, #2255, #2289) approved with DTI between 51% and 58%.',
    expected:'No loan sanction if DTI exceeds 50% without committee override.', source:'§4.4 Q3 Audit Report' },
  { node:'Sanction & Approval', type:'Process', status:'deviated', severity:'high',
    quote:'Mean approval-to-disbursement TAT was 9.2 working days vs 7-day policy.',
    expected:'Approval and disbursement within 7 working days of sanction.', source:'§5.1 Q3 Audit Report' },
  { node:'Credit Officer', type:'Role', status:'deviated', severity:'medium',
    quote:'In 4 cases the DTI computation was prepared by Relationship Manager, not Credit Officer.',
    expected:'DTI worksheet prepared by Credit Officer.', source:'§3.4 Q3 Audit Report' },
  { node:'Disbursement', type:'Process', status:'confirmed', severity:null,
    quote:'Disbursement records reconcile with Core Banking ledger in all 47 cases.',
    expected:'Disbursement posted to Core Banking same business day.', source:'§5.3 Q3 Audit Report' },
  { node:'Branch Manager', type:'Role', status:'confirmed', severity:null,
    quote:'Sanction approvals carry Branch Manager signature in all reviewed files.',
    expected:'Branch Manager approves sanction.', source:'§4.7 Q3 Audit Report' },
  { node:'Appraisal Report', type:'DataEntity', status:'deviated', severity:'medium',
    quote:'In 6 cases appraisal was commissioned before document completeness was confirmed.',
    expected:'Appraisal triggered after Underwriting completeness sign-off.', source:'§4.5 Q3 Audit Report' },
  { node:'TAT ≤ 7 working days', type:'Policy', status:'deviated', severity:'high',
    quote:'12 of 47 sampled cases breached the 7-day TAT, mean delay 2.1 days.',
    expected:'End-to-end TAT must not exceed 7 working days.', source:'§5.2 Q3 Audit Report' },
  { node:'Customer File', type:'DataEntity', status:'not_found', severity:null,
    quote:'',
    expected:'Customer file fields documented end-to-end.', source:'—' },
];

const GAP_CHECKS = [
  { id:'orphan',    label:'Orphan nodes',                status:'pass', detail:'0 isolated nodes',                  weight:15 },
  { id:'process_role', label:'Every Process has a Role', status:'pass', detail:'6/6 processes covered',             weight:20 },
  { id:'policy_link',  label:'Every Policy links to Process', status:'warn', detail:'2 policies missing process link', weight:15 },
  { id:'data_flow',    label:'Data flow continuity',     status:'pass', detail:'4/4 data entities linked',           weight:15 },
  { id:'event_anchor', label:'Events anchor processes',  status:'pass', detail:'2/2 events anchored',                weight:10 },
  { id:'system_use',   label:'Systems used by Process',  status:'warn', detail:'1/3 systems with single connection', weight:10 },
  { id:'naming',       label:'Naming consistency',       status:'pass', detail:'No duplicate labels detected',       weight:10 },
  { id:'description',  label:'Descriptions present',     status:'fail', detail:'4 nodes missing description',        weight: 5 },
];

const WORKFLOWS = [
  { id:'w1', label:'Loan Origination — As-Is', stepCount:7, status:'baseline', tag:'AS-IS',
    steps:['Application Intake','KYC Verification','Credit Assessment','Underwriting Review','Sanction & Approval','Disbursement','Post-Disbursement Audit'] },
  { id:'w2', label:'Loan Origination — To-Be (parallel KYC)', stepCount:6, status:'optimised', tag:'TO-BE',
    steps:['Application Intake','KYC + Credit (parallel)','Underwriting Review','Sanction & Approval','Disbursement','Post-Disbursement Audit'] },
  { id:'w3', label:'Exception path — Override committee', stepCount:4, status:'edge-case', tag:'EXCEPTION',
    steps:['DTI Threshold Breach','Committee Convene','Risk Memo','Override Decision'] },
];

const OBJECT_MODEL_ENTITIES = [
  { name:'customer', fields:[
    {name:'id', type:'UUID', pk:true},
    {name:'created_at', type:'datetime'},
    {name:'pan', type:'varchar(10)'},
    {name:'kyc_status', type:'enum'},
    {name:'risk_segment', type:'varchar(32)'},
  ]},
  { name:'loan_application', fields:[
    {name:'id', type:'UUID', pk:true},
    {name:'created_at', type:'datetime'},
    {name:'customer_id', type:'UUID', fk:'customer.id'},
    {name:'amount', type:'numeric(14,2)'},
    {name:'purpose', type:'varchar(64)'},
    {name:'state', type:'enum'},
  ]},
  { name:'credit_assessment', fields:[
    {name:'id', type:'UUID', pk:true},
    {name:'loan_application_id', type:'UUID', fk:'loan_application.id'},
    {name:'bureau_score', type:'integer'},
    {name:'dti_ratio', type:'numeric(5,4)'},
    {name:'verdict', type:'enum'},
  ]},
  { name:'sanction', fields:[
    {name:'id', type:'UUID', pk:true},
    {name:'loan_application_id', type:'UUID', fk:'loan_application.id'},
    {name:'approved_amount', type:'numeric(14,2)'},
    {name:'approved_by', type:'UUID', fk:'role.id'},
    {name:'sanctioned_at', type:'datetime'},
  ]},
];

const DASH_KPIS = [
  { id:'graphs', label:'Graphs',         value:14, delta:'+2 this week', tone:'ok' },
  { id:'nodes',  label:'Avg nodes',      value:23, delta:'+1.4',          tone:'ok' },
  { id:'cov',    label:'Coverage',       value:'78%', delta:'+5%',        tone:'ok' },
  { id:'conf',   label:'Conformance',    value:'47%', delta:'-3%',        tone:'bad' },
  { id:'tat',    label:'P50 TAT (days)', value:6.4, delta:'+0.8',         tone:'warn' },
  { id:'pulse',  label:'Pulse open',     value:6,   delta:'2 critical',   tone:'bad' },
];

const RECENT_DOCS = [
  { id:1, name:'commercial_banking_loan_sop.docx', size:'48 KB', when:'2h ago', kind:'SOP', graphId:'g-2024-q3-loan' },
  { id:2, name:'loan_audit_report.docx',           size:'62 KB', when:'1h ago', kind:'Audit', graphId:'g-2024-q3-loan' },
  { id:3, name:'hr_onboarding_policy.txt',         size:'12 KB', when:'2d ago', kind:'Policy', graphId:'g-hr-onb' },
  { id:4, name:'supply_chain_sop.txt',             size:'19 KB', when:'5d ago', kind:'SOP', graphId:'g-sc-2024' },
];

/* ── Process mining (Celonis-style) data ────────────────────────────
   Activities laid out as a DAG. Edges carry case counts (frequency)
   and median duration. Variants list summarises the top execution paths. */
const PM_ACTIVITIES = [
  { id:'a1', label:'Application Intake',    cases:1247, x:120,  y:200, role:'RM' },
  { id:'a2', label:'KYC Verification',      cases:1247, x:340,  y:120, role:'KYC' },
  { id:'a3', label:'Credit Assessment',     cases:1232, x:340,  y:280, role:'Credit' },
  { id:'a4', label:'Document Completeness', cases:1198, x:560,  y:200, role:'Credit' },
  { id:'a5', label:'Underwriting Review',   cases:1158, x:780,  y:200, role:'Underwriter' },
  { id:'a6', label:'Risk Committee',        cases:142,  x:780,  y:340, role:'Committee' },
  { id:'a7', label:'Sanction & Approval',   cases:1102, x:1000, y:200, role:'Branch Mgr' },
  { id:'a8', label:'Rejected',              cases:145,  x:1000, y:340, role:'—' },
  { id:'a9', label:'Disbursement',          cases:1087, x:1220, y:200, role:'Ops' },
];
const PM_EDGES = [
  // from, to, cases, median (hours), label, isBottleneck
  { f:'a1', t:'a2', cases:1247, med:2.1 },
  { f:'a1', t:'a3', cases:1232, med:1.8 },
  { f:'a2', t:'a4', cases:1240, med:6.4 },
  { f:'a3', t:'a4', cases:1198, med:8.2 },
  { f:'a4', t:'a5', cases:1158, med:42.0, slow:true },     // bottleneck
  { f:'a4', t:'a3', cases:34,   med:18.0, rework:true },   // rework loop
  { f:'a5', t:'a6', cases:142,  med:96.0, slow:true },
  { f:'a5', t:'a7', cases:1016, med:14.2 },
  { f:'a6', t:'a7', cases:86,   med:120.0, slow:true },
  { f:'a6', t:'a8', cases:56,   med:72.0 },
  { f:'a7', t:'a9', cases:1087, med:24.0 },
  { f:'a7', t:'a8', cases:89,   med:8.0 },
];
const PM_VARIANTS = [
  { id:'v1', cases:842, freq:0.674, dur:'4.2d',  steps:['Intake','KYC','Credit','Completeness','Underwriting','Sanction','Disbursement'], conformant:true },
  { id:'v2', cases:174, freq:0.139, dur:'5.8d',  steps:['Intake','Credit','KYC','Completeness','Underwriting','Sanction','Disbursement'], conformant:false, note:'KYC after Credit' },
  { id:'v3', cases:142, freq:0.114, dur:'9.4d',  steps:['Intake','KYC','Credit','Completeness','Underwriting','Risk Committee','Sanction','Disbursement'], conformant:true, note:'Committee path' },
  { id:'v4', cases:56,  freq:0.045, dur:'7.1d',  steps:['Intake','KYC','Credit','Completeness','Underwriting','Risk Committee','Rejected'], conformant:true, note:'Rejected after committee' },
  { id:'v5', cases:34,  freq:0.027, dur:'11.2d', steps:['Intake','KYC','Credit','Completeness','Credit','Completeness','Underwriting','Sanction','Disbursement'], conformant:false, note:'Rework loop' },
];
const PM_KPIS = [
  { id:'cases',  label:'Cases',          value:'1,247',  delta:'+8.4%', tone:'ok' },
  { id:'tat',    label:'Median TAT',     value:'4.8 d',  delta:'+0.6d', tone:'warn' },
  { id:'auto',   label:'Auto-routed',    value:'67%',    delta:'+4%',   tone:'ok' },
  { id:'rework', label:'Rework rate',    value:'2.7%',   delta:'-0.4%', tone:'ok' },
  { id:'breach', label:'SLA breaches',   value:'12.1%',  delta:'+2.1%', tone:'bad' },
  { id:'cost',   label:'Cost per case',  value:'₹4,820', delta:'-3.1%', tone:'ok' },
];

Object.assign(window, {
  NODE_TYPES, DEMO_NODES, DEMO_EDGES, DEMO_GRAPH,
  PULSE_ITEMS, CONFORMANCE_FINDINGS, GAP_CHECKS, WORKFLOWS,
  OBJECT_MODEL_ENTITIES, DASH_KPIS, RECENT_DOCS,
  PM_ACTIVITIES, PM_EDGES, PM_VARIANTS, PM_KPIS,
});
