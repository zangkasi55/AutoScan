# Corporate Identity — AVS (Agentic Vulnerability Scanner)

**Codename:** Sentry-AI
**Product short name:** AVS
**Tagline (EN):** *Autonomous defenders. Verifiable proof.*
**Tagline (TH):** *เอเจนต์ไซเบอร์อัตโนมัติ. หลักฐานพิสูจน์ได้.*

---

## 1. Brand Personality

- **Calm authority** — like a senior incident commander. Never alarmist.
- **Evidence-first** — every claim is backed; the brand does not bluff.
- **Bilingual by design** — Thai and English share equal weight in all surfaces.
- **Defender, not predator** — we hunt for the customer's own weaknesses; we do not glamorize attack capability.

## 2. Color Palette

### Primary

| Token | Hex | Usage |
|---|---|---|
| `--avs-ink` | `#0B1220` | Background of dark surfaces; default heading color on light surfaces |
| `--avs-paper` | `#F7F9FC` | Background of light surfaces |
| `--avs-shield` | `#1F6FEB` | Primary brand blue — buttons, links, brand mark |
| `--avs-pulse` | `#22D3EE` | Accent cyan — agent activity, real-time signals |

### Severity (use ONLY for finding severity)

| Token | Hex | Severity |
|---|---|---|
| `--sev-critical` | `#DC2626` | Critical |
| `--sev-high` | `#EA580C` | High |
| `--sev-medium` | `#D97706` | Medium |
| `--sev-low` | `#65A30D` | Low |
| `--sev-info` | `#0EA5E9` | Informational |

### Neutrals

| Token | Hex |
|---|---|
| `--gray-50` | `#F8FAFC` |
| `--gray-100` | `#F1F5F9` |
| `--gray-200` | `#E2E8F0` |
| `--gray-300` | `#CBD5E1` |
| `--gray-500` | `#64748B` |
| `--gray-700` | `#334155` |
| `--gray-900` | `#0F172A` |

### Status

| Token | Hex | Use |
|---|---|---|
| `--ok-500` | `#10B981` | Verified / passed / safe |
| `--warn-500` | `#F59E0B` | Pending / awaiting review |
| `--danger-500` | `#EF4444` | Blocked / failed / scope violation |

## 3. Typography

- **Headings:** *Inter* (English), *Sarabun* (Thai). Weights 600–800.
- **Body:** *Inter* (English), *Sarabun* (Thai). Weights 400–500.
- **Mono:** *JetBrains Mono*, *Cascadia Mono* fallback. For commands, code, hashes, IPs.

Type scale (rem): 0.75 / 0.875 / 1.0 / 1.125 / 1.25 / 1.5 / 1.875 / 2.25 / 3.0.

## 4. Logo

Two variants ship in `brand/`:

- `logo.svg` — full lockup: shield mark + "AVS" wordmark + Thai/EN tagline.
- `logo-mark.svg` — icon-only, square, for favicons and avatars.

The mark is a stylized **shield** containing a **node-graph** motif (three interconnected nodes), suggesting both protection and the multi-agent orchestration. Stroke-only on the mark; never fill the inner graph.

**Clear space:** minimum padding equal to the height of the "A" glyph on every side.
**Minimum size:** 24 px tall for the mark; 80 px wide for the lockup.

**Don'ts:**
- Don't recolor the mark in severity colors.
- Don't add drop-shadows or 3D bevels.
- Don't stretch non-uniformly.
- Don't place on busy photographic backgrounds without a solid container.

## 5. Iconography

- **Style:** Lucide-style 1.5px stroke icons, rounded line caps.
- **Sizes:** 16 / 20 / 24 / 32 px.
- **Severity icons:** filled circles in the severity colors; never use emoji for severity.

## 6. Visual Motifs

- **Node graph** — recurring motif suggesting multi-agent orchestration. Use sparingly; never over decorative dashboards.
- **Hashed evidence chip** — a monospace short-hash component (e.g., `evd-c8f3…2a4b`) used to denote any auditable artifact.
- **Bilingual stack** — when a heading appears in both Thai and English, English on top, Thai immediately below at 0.875× size with `--gray-500`. This is a brand commitment, not decoration.

## 7. Voice and Copy

**Do:**
- Lead with the verified fact, then the recommendation.
- Quantify (count, severity, EPSS, KEV-listed yes/no).
- Use plain Thai (ภาษาไทยทั่วไป), no foreign slang.

**Don't:**
- Do NOT use words like "hacker," "elite," "ninja," "0-day haxxor."
- Do NOT use gun, skull, hoodie imagery.
- Do NOT promise things the agent cannot prove.

## 8. Component Tokens (CSS variable contract)

```css
:root {
  --avs-ink: #0B1220;
  --avs-paper: #F7F9FC;
  --avs-shield: #1F6FEB;
  --avs-pulse: #22D3EE;
  --sev-critical: #DC2626;
  --sev-high: #EA580C;
  --sev-medium: #D97706;
  --sev-low: #65A30D;
  --sev-info: #0EA5E9;
  --ok-500: #10B981;
  --warn-500: #F59E0B;
  --danger-500: #EF4444;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, .06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, .08);
  --shadow-lg: 0 10px 28px rgba(15, 23, 42, .12);
  --font-sans: 'Inter', 'Sarabun', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Cascadia Mono', ui-monospace, monospace;
}
```

All HTML mockups MUST consume these tokens — they are the contract between the design system and the developer / GitHub Copilot phase.
