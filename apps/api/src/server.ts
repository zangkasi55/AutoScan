/**
 * AutoScan / AVS API Gateway
 * - OIDC bearer authentication (Entra ID, Google, Okta — verified via JWKS)
 * - WebSocket /scans/:id/events for the live timeline
 * - REST endpoints per build-spec §10
 */
import Fastify from 'fastify';
import cors from '@fastify/cors';
import websocket from '@fastify/websocket';
import { jwtVerify, createRemoteJWKSet } from 'jose';
import pg from 'pg';
import { z } from 'zod';

const TENANT_ID = process.env.AZURE_TENANT_ID || '';
const ALLOWED_AUDIENCES = (process.env.OIDC_ALLOWED_AUDIENCES || '').split(',').filter(Boolean);
const PG_URL = process.env.EVIDENCE_DB_URL || 'postgres://avsadmin:avsadmin@localhost:5432/evidence?sslmode=disable';

const jwks = TENANT_ID
  ? createRemoteJWKSet(new URL(`https://login.microsoftonline.com/${TENANT_ID}/discovery/v2.0/keys`))
  : null;

const pool = new pg.Pool({ connectionString: PG_URL });

const app = Fastify({ logger: true });
await app.register(cors, { origin: true, credentials: true });
await app.register(websocket);

// ──────────── Auth hook ────────────
app.addHook('preHandler', async (req, reply) => {
  if (req.url.startsWith('/healthz') || req.url.startsWith('/readyz')) return;
  if (!jwks) { reply.code(500).send({ error: 'OIDC not configured (set AZURE_TENANT_ID)' }); return; }
  const auth = req.headers.authorization || '';
  if (!auth.startsWith('Bearer ')) { reply.code(401).send({ error: 'missing_bearer' }); return; }
  try {
    const { payload } = await jwtVerify(auth.slice(7), jwks, {
      audience: ALLOWED_AUDIENCES.length ? ALLOWED_AUDIENCES : undefined,
    });
    (req as any).user = payload;
  } catch (e: any) {
    reply.code(401).send({ error: 'invalid_token', detail: e.message });
  }
});

// ──────────── Health ────────────
app.get('/healthz', async () => ({ status: 'ok' }));
app.get('/readyz', async () => {
  const r = await pool.query('SELECT 1 AS ok');
  return { status: 'ok', db: r.rows[0].ok === 1 };
});

// ──────────── RoE / Scopes ────────────
app.post('/api/v1/scopes', async (req) => {
  const draft = z.object({
    tenantId: z.string(),
    scope: z.unknown(),
    exclusions: z.unknown(),
    testCategories: z.array(z.string()),
    timeWindow: z.unknown(),
  }).parse(req.body);
  const r = await pool.query(
    `INSERT INTO roe_documents (tenant_id, document_jws, document_hash, scope_json,
        test_categories, starts_at, ends_at, signed_by_oidc_sub, webauthn_cred_id, signed_at, status)
     VALUES ($1, '', $2, $3, $4, now(), now(), '', '', now(), 'draft') RETURNING roe_id`,
    [draft.tenantId, Buffer.alloc(0), JSON.stringify(draft.scope), draft.testCategories],
  );
  return { roe_id: r.rows[0].roe_id, status: 'draft' };
});

app.post('/api/v1/scopes/:id/sign', async (req: any) => {
  const { id } = req.params;
  const body = z.object({ jws: z.string() }).parse(req.body);
  // TODO: verify JWS + WebAuthn assertion (deferred to v0.2 per known-gaps.md G2/G7)
  await pool.query(
    `UPDATE roe_documents SET document_jws = $1, signed_at = now(), status = 'active' WHERE roe_id = $2`,
    [body.jws, id],
  );
  return { ok: true };
});

// ──────────── Scans ────────────
app.post('/api/v1/scans', async (req: any) => {
  const body = z.object({ tenantId: z.string(), roeId: z.string().uuid() }).parse(req.body);
  const created = await pool.query(
    `INSERT INTO scans (tenant_id, roe_id, status, created_by)
     VALUES ($1, $2, 'pending', $3) RETURNING scan_id`,
    [body.tenantId, body.roeId, (req as any).user.oid || (req as any).user.sub],
  );
  // TODO: enqueue plan request → orchestrator (Phase 2)
  return { scan_id: created.rows[0].scan_id, status: 'pending' };
});

app.get('/api/v1/scans/:id', async (req: any) => {
  const r = await pool.query('SELECT * FROM scans WHERE scan_id = $1', [req.params.id]);
  return r.rows[0] || null;
});

app.get('/api/v1/scans/:id/findings', async (req: any) => {
  const r = await pool.query(
    'SELECT * FROM findings WHERE scan_id = $1 ORDER BY headline_score DESC LIMIT 500',
    [req.params.id],
  );
  return r.rows;
});

// ──────────── Live timeline (WebSocket) ────────────
app.register(async (app) => {
  app.get('/api/v1/scans/:id/events', { websocket: true }, (conn, req: any) => {
    const scanId = req.params.id;
    let lastIdx = 0;
    const interval = setInterval(async () => {
      const r = await pool.query(
        `SELECT idx, actor, action, payload_blob, created_at FROM evidence
         WHERE scan_id = $1 AND idx > $2 ORDER BY idx LIMIT 50`,
        [scanId, lastIdx],
      );
      for (const row of r.rows) {
        lastIdx = row.idx;
        conn.socket.send(JSON.stringify(row));
      }
    }, 1000);
    conn.socket.on('close', () => clearInterval(interval));
  });
});

// ──────────── Evidence read (auto-logs to access_log) ────────────
app.get('/api/v1/evidence/:idx', async (req: any) => {
  const idx = parseInt(req.params.idx, 10);
  const user = (req as any).user;
  await pool.query(
    `INSERT INTO access_log (subject_oidc_sub, resource_kind, resource_id, client_ip, user_agent)
     VALUES ($1, 'evidence', $2, $3, $4)`,
    [user.oid || user.sub, String(idx), req.ip, req.headers['user-agent'] || ''],
  );
  const r = await pool.query('SELECT * FROM evidence WHERE idx = $1', [idx]);
  return r.rows[0] || null;
});

const port = Number(process.env.PORT || 8080);
await app.listen({ port, host: '0.0.0.0' });
console.log(`API listening on :${port}`);
