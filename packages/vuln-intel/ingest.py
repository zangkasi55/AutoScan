"""vuln-intel — Daily ingest job: NVD CVE feed, CISA KEV catalog, FIRST EPSS CSV.

Run as a Kubernetes CronJob (see infra/helm/autoscan/templates/vuln-intel-cron.yaml).
Stores normalized rows in Postgres tables vi_cve, vi_kev, vi_epss.
"""
from __future__ import annotations

import asyncio
import csv
import gzip
import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone

import asyncpg
import httpx

log = logging.getLogger("vuln-intel")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

DB_URL = os.environ["VULN_INTEL_DB_URL"]
NVD_API_KEY = os.environ.get("NVD_API_KEY", "")  # optional; raises rate limit


SCHEMA = """
CREATE TABLE IF NOT EXISTS vi_cve (
  cve_id TEXT PRIMARY KEY,
  description TEXT,
  cvss40_score NUMERIC(3,1),
  cvss40_vector TEXT,
  cvss31_score NUMERIC(3,1),
  cvss31_vector TEXT,
  references_json JSONB,
  published_at TIMESTAMPTZ,
  modified_at TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS vi_cve_modified_idx ON vi_cve(modified_at DESC);

CREATE TABLE IF NOT EXISTS vi_kev (
  cve_id TEXT PRIMARY KEY,
  vendor TEXT,
  product TEXT,
  short_description TEXT,
  required_action TEXT,
  date_added DATE,
  due_date DATE,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vi_epss (
  cve_id TEXT PRIMARY KEY,
  epss NUMERIC(7,6) NOT NULL,
  percentile NUMERIC(7,6) NOT NULL,
  scored_at DATE NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def init_schema(pool):
    async with pool.acquire() as c:
        await c.execute(SCHEMA)


async def ingest_kev(pool):
    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    log.info("KEV: fetching %s", url)
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.get(url)
        r.raise_for_status()
        d = r.json()
    rows = d.get("vulnerabilities", [])
    log.info("KEV: %d entries", len(rows))
    async with pool.acquire() as c:
        async with c.transaction():
            await c.execute("TRUNCATE vi_kev")
            for v in rows:
                await c.execute(
                    """INSERT INTO vi_kev(cve_id,vendor,product,short_description,
                       required_action,date_added,due_date) VALUES ($1,$2,$3,$4,$5,$6,$7)
                       ON CONFLICT (cve_id) DO UPDATE SET
                       short_description=EXCLUDED.short_description,
                       required_action=EXCLUDED.required_action,
                       due_date=EXCLUDED.due_date""",
                    v["cveID"], v.get("vendorProject"), v.get("product"),
                    v.get("shortDescription"), v.get("requiredAction"),
                    _date(v.get("dateAdded")), _date(v.get("dueDate")),
                )
    log.info("KEV: ingest done")


async def ingest_epss(pool):
    today = datetime.now(timezone.utc).date()
    url = f"https://epss.cyentia.com/epss_scores-{today.isoformat()}.csv.gz"
    log.info("EPSS: fetching %s", url)
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.get(url)
        if r.status_code == 404:
            # Yesterday's file — EPSS is sometimes a day late
            url = f"https://epss.cyentia.com/epss_scores-{(today - timedelta(days=1)).isoformat()}.csv.gz"
            r = await c.get(url)
        r.raise_for_status()
        body = gzip.decompress(r.content).decode("utf-8", "replace")
    reader = csv.DictReader(io.StringIO("\n".join(line for line in body.splitlines() if not line.startswith("#"))))
    rows = list(reader)
    log.info("EPSS: %d rows", len(rows))
    async with pool.acquire() as c:
        async with c.transaction():
            await c.execute("TRUNCATE vi_epss")
            await c.executemany(
                """INSERT INTO vi_epss(cve_id,epss,percentile,scored_at)
                   VALUES ($1,$2,$3,$4) ON CONFLICT (cve_id) DO UPDATE SET
                   epss=EXCLUDED.epss, percentile=EXCLUDED.percentile,
                   scored_at=EXCLUDED.scored_at""",
                [(r["cve"], float(r["epss"]), float(r["percentile"]), today)
                 for r in rows if r.get("cve")],
            )
    log.info("EPSS: ingest done")


async def ingest_nvd_recent(pool, hours: int = 24):
    """Pull recently-modified CVEs from NVD 2.0 API. Full backfill is a one-time job."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000")
    until = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    base = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    start = 0
    total_inserted = 0
    async with httpx.AsyncClient(timeout=120, headers=headers) as c:
        while True:
            r = await c.get(base, params={
                "lastModStartDate": since, "lastModEndDate": until,
                "startIndex": start, "resultsPerPage": 2000,
            })
            r.raise_for_status()
            d = r.json()
            items = d.get("vulnerabilities", [])
            if not items:
                break
            async with pool.acquire() as conn:
                async with conn.transaction():
                    for it in items:
                        cve = it["cve"]
                        cvss40 = _extract_cvss(cve, "cvssMetricV40")
                        cvss31 = _extract_cvss(cve, "cvssMetricV31")
                        await conn.execute(
                            """INSERT INTO vi_cve(cve_id,description,cvss40_score,cvss40_vector,
                               cvss31_score,cvss31_vector,references_json,published_at,modified_at)
                               VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9)
                               ON CONFLICT (cve_id) DO UPDATE SET
                               description=EXCLUDED.description,
                               cvss40_score=EXCLUDED.cvss40_score,
                               cvss40_vector=EXCLUDED.cvss40_vector,
                               cvss31_score=EXCLUDED.cvss31_score,
                               cvss31_vector=EXCLUDED.cvss31_vector,
                               references_json=EXCLUDED.references_json,
                               modified_at=EXCLUDED.modified_at""",
                            cve["id"],
                            _description(cve),
                            cvss40[0], cvss40[1], cvss31[0], cvss31[1],
                            json.dumps(cve.get("references", [])),
                            _ts(cve.get("published")),
                            _ts(cve.get("lastModified")),
                        )
            total_inserted += len(items)
            start += 2000
            total = d.get("totalResults", 0)
            log.info("NVD: %d / %d", start, total)
            if start >= total:
                break
            await asyncio.sleep(6 if not NVD_API_KEY else 0.6)  # NVD rate limits
    log.info("NVD: %d entries upserted", total_inserted)


def _extract_cvss(cve, key):
    metrics = cve.get("metrics", {}).get(key) or []
    if not metrics:
        return None, None
    m = metrics[0].get("cvssData", {})
    return m.get("baseScore"), m.get("vectorString")


def _description(cve):
    for d in cve.get("descriptions", []):
        if d.get("lang") == "en":
            return d.get("value")
    return None


def _ts(s):
    if not s:
        return None
    return datetime.fromisoformat(s.rstrip("Z")).replace(tzinfo=timezone.utc)


def _date(s):
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


async def main():
    pool = await asyncpg.create_pool(DB_URL)
    try:
        await init_schema(pool)
        await asyncio.gather(
            ingest_kev(pool),
            ingest_epss(pool),
            ingest_nvd_recent(pool, hours=24),
        )
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
