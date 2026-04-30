/**
 * Shared schemas — Rules of Engagement, Finding, Chain, Evidence.
 * Single source of truth; consumed by API, web, orchestrator (via codegen).
 */
import { z } from 'zod';

const CIDR = /^(?:\d{1,3}\.){3}\d{1,3}\/\d{1,2}$|^[\dA-Fa-f:]+\/\d{1,3}$/;

export const RoESchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string(),
  scope: z.object({
    cidrs: z.array(z.string().regex(CIDR)),
    hosts: z.array(z.string()),
    cloudAccounts: z.array(
      z.object({
        provider: z.enum(['aws', 'azure', 'gcp']),
        id: z.string(),
        tagFilter: z.string().optional(),
      })
    ),
  }),
  exclusions: z.object({
    cidrs: z.array(z.string().regex(CIDR)),
    hosts: z.array(z.string()),
    tags: z.array(z.string()),
  }),
  testCategories: z.array(z.enum(['recon', 'cve', 'webapp', 'ad', 'chain', 'dos'])),
  destructiveOptIns: z.array(
    z.object({
      asset: z.string(),
      allow: z.boolean(),
      justification: z.string().min(10),
    })
  ),
  timeWindow: z.object({
    startsAt: z.string().datetime(),
    endsAt: z.string().datetime(),
    noGoWindows: z.array(
      z.object({ start: z.string(), end: z.string(), reason: z.string() })
    ),
  }),
  contacts: z.array(
    z.object({ role: z.string(), name: z.string(), channel: z.string() })
  ),
  authorizingParty: z.object({
    oidcSub: z.string(),
    webAuthnCredId: z.string(),
  }),
  signature: z.object({
    alg: z.literal('ES256'),
    jws: z.string(),
    signedAt: z.string().datetime(),
  }),
  ledgerAnchor: z
    .object({ merkleRoot: z.string(), tsaToken: z.string(), idx: z.number() })
    .optional(),
});
export type RoE = z.infer<typeof RoESchema>;

export const Severity = z.enum(['critical', 'high', 'medium', 'low', 'info']);

export const FindingSchema = z.object({
  id: z.string().uuid(),
  scanId: z.string().uuid(),
  assetRef: z.string(),
  titleEn: z.string(),
  titleTh: z.string(),
  summaryEn: z.string().optional(),
  summaryTh: z.string().optional(),
  severity: Severity,
  cvss40: z.number().min(0).max(10).optional(),
  epss: z.number().min(0).max(1).optional(),
  inKEV: z.boolean(),
  ssvc: z.enum(['act', 'attend', 'track', 'track_star']).optional(),
  reachability: z.number().min(0).max(1).optional(),
  headlineScore: z.number().min(0).max(100),
  cveIds: z.array(z.string()),
  producedBy: z.object({
    agent: z.string(),
    model: z.string(),
    provider: z.string(),
  }),
  evidenceIdxs: z.array(z.number()),
  criticVerdict: z
    .object({
      confirmed: z.boolean(),
      model: z.string(),
      reasons: z.array(z.string()),
    })
    .optional(),
  status: z.enum([
    'new', 'triaged', 'false_positive', 'accepted_risk', 'remediated', 'snoozed',
  ]),
});
export type Finding = z.infer<typeof FindingSchema>;

export const ChainSchema = z.object({
  id: z.string().uuid(),
  scanId: z.string().uuid(),
  ordinal: z.number().int().nonnegative(),
  headlineScore: z.number().min(0).max(100),
  reachability: z.number().min(0).max(1),
  narrativeEn: z.string(),
  narrativeTh: z.string(),
  graph: z.object({
    nodes: z.array(z.object({ id: z.string(), kind: z.string(), label: z.string() })),
    edges: z.array(z.object({ from: z.string(), to: z.string(), label: z.string() })),
  }),
  findingIds: z.array(z.string().uuid()),
});
export type Chain = z.infer<typeof ChainSchema>;

export const EvidenceSchema = z.object({
  idx: z.number().int().positive(),
  scanId: z.string().uuid(),
  actor: z.string(),
  action: z.string(),
  payloadHash: z.string(),
  payloadBlob: z.unknown().optional(),
  blobUri: z.string().optional(),
  parentHash: z.string(),
  leafHash: z.string(),
  policyDecision: z.unknown().optional(),
  createdAt: z.string().datetime(),
});
export type Evidence = z.infer<typeof EvidenceSchema>;
