#!/usr/bin/env node
// i18n-lint: enforce EN/TH key parity.
// Build-spec §3.8 / ADR-8: missing key in either language fails the build.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const en = JSON.parse(fs.readFileSync(path.join(here, 'en.json'), 'utf8'));
const th = JSON.parse(fs.readFileSync(path.join(here, 'th.json'), 'utf8'));

function flatten(obj, prefix = '') {
  const keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const fk = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) keys.push(...flatten(v, fk));
    else keys.push(fk);
  }
  return keys;
}

const ek = new Set(flatten(en));
const tk = new Set(flatten(th));
const missingInTh = [...ek].filter(k => !tk.has(k)).sort();
const missingInEn = [...tk].filter(k => !ek.has(k)).sort();

if (missingInTh.length === 0 && missingInEn.length === 0) {
  console.log(`✓ i18n-lint: ${ek.size} keys parity-clean (EN ↔ TH).`);
  process.exit(0);
}
if (missingInTh.length) {
  console.error('✗ Missing in TH:', missingInTh);
}
if (missingInEn.length) {
  console.error('✗ Missing in EN:', missingInEn);
}
process.exit(1);
