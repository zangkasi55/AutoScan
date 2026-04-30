-- AutoScan / AVS — Evidence Ledger schema (PostgreSQL 16)
-- Implements ADR-4: append-only, hash-chained, RFC 3161 anchored.
-- Reference: final/github-copilot-build-spec.md §5.1

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ───────────────────────── Tenants ─────────────────────────
CREATE TABLE IF NOT EXISTS tenants (
  tenant_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  display_name    TEXT NOT NULL,
  language_pref   TEXT NOT NULL DEFAULT 'th'  CHECK (language_pref IN ('th','en')),
  data_residency  TEXT NOT NULL DEFAULT 'th-central-1',
  kms_key_uri     TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Rules of Engagement (signed) ─────────────────────────
CREATE TABLE IF NOT EXISTS roe_documents (
  roe_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id       UUID NOT NULL REFERENCES tenants(tenant_id),
  document_jws    TEXT NOT NULL,
  document_hash   BYTEA NOT NULL,
  scope_json      JSONB NOT NULL,
  destructive_optins JSONB NOT NULL DEFAULT '[]'::jsonb,
  test_categories TEXT[] NOT NULL,
  starts_at       TIMESTAMPTZ NOT NULL,
  ends_at         TIMESTAMPTZ NOT NULL,
  signed_by_oidc_sub TEXT NOT NULL,
  webauthn_cred_id TEXT NOT NULL,
  signed_at       TIMESTAMPTZ NOT NULL,
  ledger_anchor_idx BIGINT,
  status          TEXT NOT NULL DEFAULT 'active'
                  CHECK (status IN ('draft','active','expired','revoked'))
);
CREATE INDEX IF NOT EXISTS roe_tenant_idx ON roe_documents(tenant_id, status);

-- ───────────────────────── Scans ─────────────────────────
CREATE TABLE IF NOT EXISTS scans (
  scan_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id       UUID NOT NULL REFERENCES tenants(tenant_id),
  roe_id          UUID NOT NULL REFERENCES roe_documents(roe_id),
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','planning','running','paused','completed','aborted','failed')),
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  plan_json       JSONB,
  notes           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS scans_tenant_idx ON scans(tenant_id, status, created_at DESC);

-- ───────────────────────── Evidence Ledger (append-only, Merkle-chained) ─────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
  idx           BIGSERIAL PRIMARY KEY,
  scan_id       UUID NOT NULL REFERENCES scans(scan_id),
  actor         TEXT NOT NULL,
  action        TEXT NOT NULL,
  payload_hash  BYTEA NOT NULL,
  payload_blob  JSONB,
  blob_uri      TEXT,
  parent_hash   BYTEA NOT NULL,
  leaf_hash     BYTEA NOT NULL,
  policy_decision JSONB,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (scan_id, idx)
);
CREATE INDEX IF NOT EXISTS evidence_scan_idx ON evidence(scan_id, idx);
CREATE INDEX IF NOT EXISTS evidence_actor_idx ON evidence(actor, created_at DESC);

CREATE OR REPLACE FUNCTION evidence_immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'evidence ledger is append-only';
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS evidence_no_update ON evidence;
CREATE TRIGGER evidence_no_update BEFORE UPDATE OR DELETE ON evidence
  FOR EACH ROW EXECUTE FUNCTION evidence_immutable();

CREATE TABLE IF NOT EXISTS ledger_anchors (
  anchor_id     BIGSERIAL PRIMARY KEY,
  scan_id       UUID NOT NULL REFERENCES scans(scan_id),
  from_idx      BIGINT NOT NULL,
  to_idx        BIGINT NOT NULL,
  merkle_root   BYTEA NOT NULL,
  tsa_token     BYTEA,
  tsa_authority TEXT,
  anchored_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (to_idx >= from_idx)
);
CREATE INDEX IF NOT EXISTS ledger_anchors_scan_idx ON ledger_anchors(scan_id, anchored_at DESC);

-- ───────────────────────── Findings & Chains ─────────────────────────
CREATE TABLE IF NOT EXISTS findings (
  finding_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scan_id         UUID NOT NULL REFERENCES scans(scan_id),
  asset_ref       TEXT NOT NULL,
  title_en        TEXT NOT NULL,
  title_th        TEXT NOT NULL,
  summary_en      TEXT,
  summary_th      TEXT,
  severity        TEXT NOT NULL CHECK (severity IN ('critical','high','medium','low','info')),
  cvss40_score    NUMERIC(3,1),
  epss_score      NUMERIC(5,4),
  in_kev          BOOLEAN NOT NULL DEFAULT false,
  ssvc_decision   TEXT CHECK (ssvc_decision IN ('act','attend','track','track_star')),
  reachability    NUMERIC(4,3),
  headline_score  NUMERIC(5,2) NOT NULL,
  cve_ids         TEXT[] NOT NULL DEFAULT '{}',
  produced_by     JSONB NOT NULL,
  evidence_idxs   BIGINT[] NOT NULL DEFAULT '{}',
  critic_verdict  JSONB,
  status          TEXT NOT NULL DEFAULT 'new'
                  CHECK (status IN ('new','triaged','false_positive','accepted_risk','remediated','snoozed')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS findings_scan_idx ON findings(scan_id, severity, headline_score DESC);

CREATE TABLE IF NOT EXISTS chains (
  chain_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scan_id         UUID NOT NULL REFERENCES scans(scan_id),
  ordinal         INT NOT NULL,
  headline_score  NUMERIC(5,2) NOT NULL,
  reachability    NUMERIC(4,3) NOT NULL,
  narrative_en    TEXT NOT NULL,
  narrative_th    TEXT NOT NULL,
  graph_json      JSONB NOT NULL,
  finding_ids     UUID[] NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS chains_scan_idx ON chains(scan_id, headline_score DESC);

-- ───────────────────────── Audit log (every read of evidence) ─────────────────────────
CREATE TABLE IF NOT EXISTS access_log (
  log_id          BIGSERIAL PRIMARY KEY,
  subject_oidc_sub TEXT NOT NULL,
  resource_kind   TEXT NOT NULL,
  resource_id     TEXT NOT NULL,
  purpose         TEXT,
  client_ip       INET,
  user_agent      TEXT,
  accessed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS access_log_subject_idx ON access_log(subject_oidc_sub, accessed_at DESC);
CREATE INDEX IF NOT EXISTS access_log_resource_idx ON access_log(resource_kind, resource_id, accessed_at DESC);

-- ───────────────────────── evidence_append() helper ─────────────────────────
CREATE OR REPLACE FUNCTION evidence_append(
  p_scan_id UUID, p_actor TEXT, p_action TEXT,
  p_payload_blob JSONB, p_blob_uri TEXT, p_policy JSONB
) RETURNS BIGINT AS $$
DECLARE
  v_payload_hash BYTEA;
  v_parent_hash  BYTEA;
  v_leaf_hash    BYTEA;
  v_idx          BIGINT;
BEGIN
  v_payload_hash := digest(coalesce(p_payload_blob::text,''), 'sha256');
  SELECT leaf_hash INTO v_parent_hash FROM evidence
    WHERE scan_id = p_scan_id ORDER BY idx DESC LIMIT 1;
  IF v_parent_hash IS NULL THEN
    v_parent_hash := decode(repeat('00',32),'hex');
  END IF;
  v_leaf_hash := digest(v_parent_hash || v_payload_hash, 'sha256');
  INSERT INTO evidence(scan_id, actor, action, payload_hash, payload_blob,
                       blob_uri, parent_hash, leaf_hash, policy_decision)
  VALUES (p_scan_id, p_actor, p_action, v_payload_hash, p_payload_blob,
          p_blob_uri, v_parent_hash, v_leaf_hash, p_policy)
  RETURNING idx INTO v_idx;
  RETURN v_idx;
END $$ LANGUAGE plpgsql;
