"""Seed the local SQLite demo DB with banking-loan operations data.

Idempotent — running this when the tables are already populated is a no-op.
Auto-invoked from main.py at module load (i.e. server startup).

Mirrors the previous Supabase seed: 7 process_steps, 13 loan_applications,
~60 step_executions covering happy paths, SLA breaches, role mismatches,
in-progress and skipped steps. Date math uses SQLite's
`datetime('now', '-N days', '+H hours')` modifiers (equivalent to Postgres
`NOW() - INTERVAL 'N days' + INTERVAL 'H hours'`).
"""
from __future__ import annotations

import db


CREATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS process_steps (
  step_name        TEXT PRIMARY KEY,
  expected_role    TEXT NOT NULL,
  expected_system  TEXT NOT NULL,
  sla_hours        INTEGER NOT NULL,
  description      TEXT
);

CREATE TABLE IF NOT EXISTS loan_applications (
  id               TEXT PRIMARY KEY,
  applicant_name   TEXT NOT NULL,
  loan_type        TEXT NOT NULL,
  loan_amount_usd  REAL NOT NULL,
  status           TEXT NOT NULL,
  submitted_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS step_executions (
  id               TEXT PRIMARY KEY,
  application_id   TEXT NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
  step_name        TEXT NOT NULL REFERENCES process_steps(step_name),
  started_at       TEXT NOT NULL,
  completed_at     TEXT,
  actual_role      TEXT,
  actual_system    TEXT,
  status           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_step_executions_step_name   ON step_executions(step_name);
CREATE INDEX IF NOT EXISTS idx_step_executions_application ON step_executions(application_id);
"""


SEED_PROCESS_STEPS = """
INSERT INTO process_steps (step_name, expected_role, expected_system, sla_hours, description) VALUES
  ('Application Submission',  'Loan Officer',       'Loan Origination System',   4, 'Customer submits loan application via online portal or branch.'),
  ('KYC Verification',        'Compliance Analyst', 'KYC Platform',             24, 'Identity, sanctions, and PEP checks against regulatory databases.'),
  ('Credit Check',            'Credit Analyst',     'Credit Bureau Gateway',     8, 'Pull credit report and assign internal risk grade.'),
  ('Underwriting Review',     'Credit Officer',     'Underwriting Workbench',   48, 'Income verification, DSCR / DTI calculation, collateral validation.'),
  ('Approval Decision',       'Credit Officer',     'Underwriting Workbench',   24, 'Credit committee or auto-approval based on policy thresholds.'),
  ('Disbursement',            'Operations Officer', 'Core Banking',             24, 'Funds released to borrower account.'),
  ('Post-Disbursement Audit', 'Internal Audit',     'Audit Trail',             168, 'Sample-based review of recently disbursed loans.');
"""


SEED_LOAN_APPLICATIONS = """
INSERT INTO loan_applications (id, applicant_name, loan_type, loan_amount_usd, status, submitted_at) VALUES
  ('a0000001-0000-4000-8000-000000000001', 'Acme Manufacturing Corp',     'Commercial', 1500000.00, 'disbursed',    datetime('now', '-60 days')),
  ('a0000002-0000-4000-8000-000000000002', 'BlueRiver Logistics LLC',     'Commercial',  750000.00, 'disbursed',    datetime('now', '-52 days')),
  ('a0000003-0000-4000-8000-000000000003', 'Maria Chen',                  'Retail',       45000.00, 'disbursed',    datetime('now', '-40 days')),
  ('a0000004-0000-4000-8000-000000000004', 'Northwind Trading Co',        'SME',         220000.00, 'disbursed',    datetime('now', '-35 days')),
  ('a0000005-0000-4000-8000-000000000005', 'James Patel',                 'Retail',       62000.00, 'disbursed',    datetime('now', '-28 days')),
  ('a0000006-0000-4000-8000-000000000006', 'Stellar Tech Holdings',       'Commercial', 2200000.00, 'disbursed',    datetime('now', '-21 days')),
  ('a0000007-0000-4000-8000-000000000007', 'Greenfield Agro Pvt Ltd',     'SME',         180000.00, 'disbursed',    datetime('now', '-15 days')),
  ('a0000008-0000-4000-8000-000000000008', 'Aisha Rahman',                'Retail',       38000.00, 'disbursed',    datetime('now', '-10 days')),
  ('a0000009-0000-4000-8000-000000000009', 'Pacific Coast Construction',  'Commercial', 3100000.00, 'underwriting', datetime('now', '-6 days')),
  ('a0000010-0000-4000-8000-000000000010', 'Linton Family Bakery',        'SME',          85000.00, 'underwriting', datetime('now', '-4 days')),
  ('a0000011-0000-4000-8000-000000000011', 'David Okafor',                'Retail',       52000.00, 'pending',      datetime('now', '-2 days')),
  ('a0000012-0000-4000-8000-000000000012', 'Vertex Energy Partners',      'Commercial', 1800000.00, 'declined',     datetime('now', '-32 days')),
  ('a0000013-0000-4000-8000-000000000013', 'Sunita Iyer',                 'Retail',       28000.00, 'declined',     datetime('now', '-18 days'));
"""


# Each row uses lower(hex(randomblob(16))) for a unique id.
# Date arithmetic mirrors the original Postgres seed exactly.
SEED_STEP_EXECUTIONS = """
INSERT INTO step_executions (id, application_id, step_name, started_at, completed_at, actual_role, actual_system, status) VALUES
  -- Acme Manufacturing Corp — happy path, fully on-time
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'Application Submission',  datetime('now', '-60 days'),                       datetime('now', '-60 days', '+2 hours'),  'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'KYC Verification',        datetime('now', '-60 days', '+3 hours'),           datetime('now', '-59 days'),              'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'Credit Check',            datetime('now', '-59 days'),                       datetime('now', '-59 days', '+5 hours'),  'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'Underwriting Review',     datetime('now', '-59 days', '+6 hours'),           datetime('now', '-57 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'Approval Decision',       datetime('now', '-57 days'),                       datetime('now', '-56 days', '+12 hours'), 'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'Disbursement',            datetime('now', '-56 days', '+13 hours'),          datetime('now', '-55 days', '+8 hours'),  'Operations Officer', 'Core Banking',            'completed'),
  (lower(hex(randomblob(16))), 'a0000001-0000-4000-8000-000000000001', 'Post-Disbursement Audit', datetime('now', '-50 days'),                       datetime('now', '-46 days'),              'Internal Audit',     'Audit Trail',             'completed'),

  -- BlueRiver Logistics — KYC breached (>24h) and Credit Check done by wrong role (Loan Officer instead of Credit Analyst)
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'Application Submission',  datetime('now', '-52 days'),                       datetime('now', '-52 days', '+1 hour'),   'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'KYC Verification',        datetime('now', '-52 days', '+2 hours'),           datetime('now', '-49 days'),              'Compliance Analyst', 'KYC Platform',            'breached'),
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'Credit Check',            datetime('now', '-49 days'),                       datetime('now', '-48 days', '+20 hours'), 'Loan Officer',       'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'Underwriting Review',     datetime('now', '-48 days'),                       datetime('now', '-46 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'Approval Decision',       datetime('now', '-46 days'),                       datetime('now', '-45 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'Disbursement',            datetime('now', '-45 days'),                       datetime('now', '-44 days'),              'Operations Officer', 'Core Banking',            'completed'),
  (lower(hex(randomblob(16))), 'a0000002-0000-4000-8000-000000000002', 'Post-Disbursement Audit', datetime('now', '-40 days'),                       NULL,                                     NULL,                 NULL,                      'skipped'),

  -- Maria Chen — fast retail happy path
  (lower(hex(randomblob(16))), 'a0000003-0000-4000-8000-000000000003', 'Application Submission',  datetime('now', '-40 days'),                       datetime('now', '-40 days', '+1 hour'),   'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000003-0000-4000-8000-000000000003', 'KYC Verification',        datetime('now', '-40 days', '+2 hours'),           datetime('now', '-39 days', '+20 hours'), 'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000003-0000-4000-8000-000000000003', 'Credit Check',            datetime('now', '-39 days', '+20 hours'),          datetime('now', '-39 days', '+23 hours'), 'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000003-0000-4000-8000-000000000003', 'Underwriting Review',     datetime('now', '-39 days'),                       datetime('now', '-38 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000003-0000-4000-8000-000000000003', 'Approval Decision',       datetime('now', '-38 days'),                       datetime('now', '-37 days', '+12 hours'), 'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000003-0000-4000-8000-000000000003', 'Disbursement',            datetime('now', '-37 days', '+13 hours'),          datetime('now', '-36 days'),              'Operations Officer', 'Core Banking',            'completed'),

  -- Northwind Trading — Underwriting breached SLA
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'Application Submission',  datetime('now', '-35 days'),                       datetime('now', '-35 days', '+3 hours'),  'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'KYC Verification',        datetime('now', '-35 days'),                       datetime('now', '-34 days'),              'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'Credit Check',            datetime('now', '-34 days'),                       datetime('now', '-34 days', '+7 hours'),  'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'Underwriting Review',     datetime('now', '-34 days', '+8 hours'),           datetime('now', '-30 days'),              'Credit Officer',     'Underwriting Workbench',  'breached'),
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'Approval Decision',       datetime('now', '-30 days'),                       datetime('now', '-29 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'Disbursement',            datetime('now', '-29 days'),                       datetime('now', '-28 days'),              'Operations Officer', 'Core Banking',            'completed'),
  (lower(hex(randomblob(16))), 'a0000004-0000-4000-8000-000000000004', 'Post-Disbursement Audit', datetime('now', '-20 days'),                       datetime('now', '-14 days'),              'Internal Audit',     'Audit Trail',             'completed'),

  -- James Patel — Approval Decision breached, performed by Loan Officer (wrong role)
  (lower(hex(randomblob(16))), 'a0000005-0000-4000-8000-000000000005', 'Application Submission',  datetime('now', '-28 days'),                       datetime('now', '-28 days', '+2 hours'),  'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000005-0000-4000-8000-000000000005', 'KYC Verification',        datetime('now', '-28 days'),                       datetime('now', '-27 days'),              'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000005-0000-4000-8000-000000000005', 'Credit Check',            datetime('now', '-27 days'),                       datetime('now', '-27 days', '+6 hours'),  'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000005-0000-4000-8000-000000000005', 'Underwriting Review',     datetime('now', '-27 days'),                       datetime('now', '-25 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000005-0000-4000-8000-000000000005', 'Approval Decision',       datetime('now', '-25 days'),                       datetime('now', '-23 days'),              'Loan Officer',       'Underwriting Workbench',  'breached'),
  (lower(hex(randomblob(16))), 'a0000005-0000-4000-8000-000000000005', 'Disbursement',            datetime('now', '-23 days'),                       datetime('now', '-22 days'),              'Operations Officer', 'Core Banking',            'completed'),

  -- Stellar Tech Holdings — large commercial, fully on-time
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'Application Submission',  datetime('now', '-21 days'),                       datetime('now', '-21 days', '+3 hours'),  'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'KYC Verification',        datetime('now', '-21 days'),                       datetime('now', '-20 days'),              'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'Credit Check',            datetime('now', '-20 days'),                       datetime('now', '-20 days', '+6 hours'),  'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'Underwriting Review',     datetime('now', '-20 days'),                       datetime('now', '-18 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'Approval Decision',       datetime('now', '-18 days'),                       datetime('now', '-17 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'Disbursement',            datetime('now', '-17 days'),                       datetime('now', '-16 days'),              'Operations Officer', 'Core Banking',            'completed'),
  (lower(hex(randomblob(16))), 'a0000006-0000-4000-8000-000000000006', 'Post-Disbursement Audit', datetime('now', '-12 days'),                       datetime('now', '-6 days'),               'Internal Audit',     'Audit Trail',             'completed'),

  -- Greenfield Agro — KYC breached, Credit Check breached
  (lower(hex(randomblob(16))), 'a0000007-0000-4000-8000-000000000007', 'Application Submission',  datetime('now', '-15 days'),                       datetime('now', '-15 days', '+3 hours'),  'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000007-0000-4000-8000-000000000007', 'KYC Verification',        datetime('now', '-15 days'),                       datetime('now', '-12 days'),              'Compliance Analyst', 'KYC Platform',            'breached'),
  (lower(hex(randomblob(16))), 'a0000007-0000-4000-8000-000000000007', 'Credit Check',            datetime('now', '-12 days'),                       datetime('now', '-11 days'),              'Credit Analyst',     'Credit Bureau Gateway',   'breached'),
  (lower(hex(randomblob(16))), 'a0000007-0000-4000-8000-000000000007', 'Underwriting Review',     datetime('now', '-11 days'),                       datetime('now', '-9 days'),               'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000007-0000-4000-8000-000000000007', 'Approval Decision',       datetime('now', '-9 days'),                        datetime('now', '-8 days'),               'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000007-0000-4000-8000-000000000007', 'Disbursement',            datetime('now', '-8 days'),                        datetime('now', '-7 days'),               'Operations Officer', 'Core Banking',            'completed'),

  -- Aisha Rahman — fast retail
  (lower(hex(randomblob(16))), 'a0000008-0000-4000-8000-000000000008', 'Application Submission',  datetime('now', '-10 days'),                       datetime('now', '-10 days', '+1 hour'),   'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000008-0000-4000-8000-000000000008', 'KYC Verification',        datetime('now', '-10 days'),                       datetime('now', '-9 days', '+20 hours'),  'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000008-0000-4000-8000-000000000008', 'Credit Check',            datetime('now', '-9 days'),                        datetime('now', '-9 days', '+4 hours'),   'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000008-0000-4000-8000-000000000008', 'Underwriting Review',     datetime('now', '-9 days'),                        datetime('now', '-7 days'),               'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000008-0000-4000-8000-000000000008', 'Approval Decision',       datetime('now', '-7 days'),                        datetime('now', '-6 days'),               'Credit Officer',     'Underwriting Workbench',  'completed'),
  (lower(hex(randomblob(16))), 'a0000008-0000-4000-8000-000000000008', 'Disbursement',            datetime('now', '-6 days'),                        datetime('now', '-5 days'),               'Operations Officer', 'Core Banking',            'completed'),

  -- Pacific Coast Construction — currently in underwriting
  (lower(hex(randomblob(16))), 'a0000009-0000-4000-8000-000000000009', 'Application Submission',  datetime('now', '-6 days'),                        datetime('now', '-6 days', '+2 hours'),   'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000009-0000-4000-8000-000000000009', 'KYC Verification',        datetime('now', '-6 days'),                        datetime('now', '-5 days'),               'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000009-0000-4000-8000-000000000009', 'Credit Check',            datetime('now', '-5 days'),                        datetime('now', '-5 days', '+7 hours'),   'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000009-0000-4000-8000-000000000009', 'Underwriting Review',     datetime('now', '-4 days'),                        NULL,                                     'Credit Officer',     'Underwriting Workbench',  'in_progress'),

  -- Linton Family Bakery — currently in underwriting (SME)
  (lower(hex(randomblob(16))), 'a0000010-0000-4000-8000-000000000010', 'Application Submission',  datetime('now', '-4 days'),                        datetime('now', '-4 days', '+2 hours'),   'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000010-0000-4000-8000-000000000010', 'KYC Verification',        datetime('now', '-4 days'),                        datetime('now', '-3 days'),               'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000010-0000-4000-8000-000000000010', 'Credit Check',            datetime('now', '-3 days'),                        datetime('now', '-3 days', '+5 hours'),   'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000010-0000-4000-8000-000000000010', 'Underwriting Review',     datetime('now', '-2 days'),                        NULL,                                     'Credit Officer',     'Underwriting Workbench',  'in_progress'),

  -- David Okafor — pending KYC
  (lower(hex(randomblob(16))), 'a0000011-0000-4000-8000-000000000011', 'Application Submission',  datetime('now', '-2 days'),                        datetime('now', '-2 days', '+1 hour'),    'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000011-0000-4000-8000-000000000011', 'KYC Verification',        datetime('now', '-1 day'),                         NULL,                                     'Compliance Analyst', 'KYC Platform',            'in_progress'),

  -- Vertex Energy Partners — declined after Underwriting breach
  (lower(hex(randomblob(16))), 'a0000012-0000-4000-8000-000000000012', 'Application Submission',  datetime('now', '-32 days'),                       datetime('now', '-32 days', '+2 hours'),  'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000012-0000-4000-8000-000000000012', 'KYC Verification',        datetime('now', '-32 days'),                       datetime('now', '-31 days'),              'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000012-0000-4000-8000-000000000012', 'Credit Check',            datetime('now', '-31 days'),                       datetime('now', '-31 days', '+7 hours'),  'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000012-0000-4000-8000-000000000012', 'Underwriting Review',     datetime('now', '-31 days'),                       datetime('now', '-28 days'),              'Credit Officer',     'Underwriting Workbench',  'breached'),
  (lower(hex(randomblob(16))), 'a0000012-0000-4000-8000-000000000012', 'Approval Decision',       datetime('now', '-28 days'),                       datetime('now', '-27 days'),              'Credit Officer',     'Underwriting Workbench',  'completed'),

  -- Sunita Iyer — declined fast (low credit grade)
  (lower(hex(randomblob(16))), 'a0000013-0000-4000-8000-000000000013', 'Application Submission',  datetime('now', '-18 days'),                       datetime('now', '-18 days', '+1 hour'),   'Loan Officer',       'Loan Origination System', 'completed'),
  (lower(hex(randomblob(16))), 'a0000013-0000-4000-8000-000000000013', 'KYC Verification',        datetime('now', '-18 days'),                       datetime('now', '-17 days'),              'Compliance Analyst', 'KYC Platform',            'completed'),
  (lower(hex(randomblob(16))), 'a0000013-0000-4000-8000-000000000013', 'Credit Check',            datetime('now', '-17 days'),                       datetime('now', '-17 days', '+4 hours'),  'Credit Analyst',     'Credit Bureau Gateway',   'completed'),
  (lower(hex(randomblob(16))), 'a0000013-0000-4000-8000-000000000013', 'Approval Decision',       datetime('now', '-17 days'),                       datetime('now', '-16 days'),              'Credit Officer',     'Underwriting Workbench',  'completed');
"""


def is_seeded() -> bool:
    return db.has_table("process_steps") and db.row_count("process_steps") > 0


def seed_if_needed() -> bool:
    """Create schema (if missing) and insert demo rows (if empty).

    Returns True if data was inserted, False if already seeded.
    """
    db.executescript(CREATE_SCHEMA)
    if is_seeded():
        return False
    db.executescript(SEED_PROCESS_STEPS)
    db.executescript(SEED_LOAN_APPLICATIONS)
    db.executescript(SEED_STEP_EXECUTIONS)
    return True
