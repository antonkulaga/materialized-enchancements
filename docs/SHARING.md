# Sharing, Metadata & Link Previews

How the app constructs URLs, renders link previews, publishes reports, and
distributes content through email, social, and ARTEX.

---

## Canonical URL Configuration

Two env vars control the public base URL. Only one is needed in practice.

| Variable | Purpose | When to set |
|---|---|---|
| `DEPLOY_URL` | Primary canonical base for everything: OG tags, share links, QR codes, PDF exports, emails, sitemap, robots.txt | Always in production |
| `PUBLIC_APP_URL` | Fallback when `DEPLOY_URL` is unset, or when permalinks must use a different hostname (e.g. CDN front) | Only if DEPLOY_URL is absent or a different permalink host is needed |

**Resolution order** (`env.py → public_app_url()`):

```
DEPLOY_URL  →  PUBLIC_APP_URL  →  http://localhost:3000
```

A variant `_explicit_deploy_url()` returns empty instead of localhost — used for
the hidden `<input id="report-canonical-base">` so client JS falls back to
`window.location.origin` in dev rather than baking `localhost:3000` into links.

### Client-side URL construction (me_report.js)

```
canonicalOrigin()  →  reads #report-canonical-base input
                      if empty → window.location.origin

absoluteShareUrl() →  canonicalOrigin() + sharePath()
reportTargetUrl()  →  published report URL (if exists) || absoluteShareUrl()
```

All social intents, QR codes, and copy-link actions use `reportTargetUrl()`.

---

## Open Graph & Twitter Card Meta Tags

### Site-level pages (/, /about)

Defined in `pages/index.py → _page_meta(route_path)`. Each page gets:

| Tag | Value |
|---|---|
| `og:type` | `website` |
| `og:site_name` | Materialized Enhancements |
| `og:title` | `{site_title} \| {page_title}` |
| `og:description` | Per-route description from `crawler_assets.PUBLIC_ROUTES` |
| `og:url` | `{DEPLOY_URL}/{route}` |
| `og:image` | `{DEPLOY_URL}/images/icons/share.jpg` (1090×849) |
| `og:image:width` / `height` | 1090 / 849 |
| `twitter:card` | `summary_large_image` |
| `twitter:title` / `description` / `image` | Mirrors OG values |

The `/materialization` route uses `noindex, nofollow` — it's gated behind gene
selection and has no meaningful default content for crawlers.

### Generated report landing pages

Each published report gets its own `index.html` with per-report OG tags built by
`state.py → _build_report_landing_html()`:

| Tag | Value |
|---|---|
| `og:title` | `Materialized Enhancements — {personal_tag}` |
| `og:description` | Summary with downloadable STL + report |
| `og:url` | Absolute URL to `index.html` |
| `og:image` | Absolute URL to `report.webp` |
| `og:image:type` | `image/webp` |
| `twitter:card` | `summary_large_image` |

The landing page auto-redirects to the interactive app via
`/materialization?shared_report={slug}` and has fallback buttons for manual
navigation.

### Verification after deploy

1. Confirm the OG image returns 200: `curl -I https://enhancement.bio/images/icons/share.jpg`
2. Force re-scrape at [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) — Slack/Discord/iMessage cache previews for days.
3. LinkedIn: [Post Inspector](https://www.linkedin.com/post-inspector/)
4. Generic: [opengraph.xyz](https://opengraph.xyz) or `curl -A "Twitterbot" https://enhancement.bio/ | grep -i "og:"`

### OG image requirements

Current: `assets/images/icons/share.jpg` (1090×849 JPEG, 124 KB).
Ideal: 1200×630 PNG under 5 MB — the Facebook/LinkedIn/Slack sweet spot. To
upgrade, replace the file; no code change needed (`_OG_IMAGE_PATH` in
`pages/index.py` points to `/images/icons/share.jpg`).

---

## Share URL Format

The recreate URL preserves enough state to rebuild a visitor's exact selection:

```
/materialization?report=1&name={name_b64}&cats={bitmask}&genes={genes_b64}
```

| Param | Encoding | Purpose |
|---|---|---|
| `report` | `1` | Flags this as a recreation link |
| `name` | Base64URL (no padding) of UTF-8 personal tag | Visitor name |
| `cats` | Integer bitmask (bit N = category N from `UNIQUE_CATEGORIES`, 1-indexed) | Selected categories |
| `genes` | Base64URL of JSON array of gene names (optional) | Exact gene checklist; without it, all genes in selected categories are included |

Built by `ComposeState.share_url` (state.py). Returns empty string if no tag or
categories are selected.

---

## Published Report Pipeline

### Trigger

Visitor clicks **Create public link** → calls
`ComposeState.on_click_publish_report_public()`.

### Browser-side (me_report.js)

`__meBuildReportBundleBase64(timeout, publicPath, slug)`:

1. Renders PNG card via `htmlToImage` → WebP at 92% quality
2. Builds multi-page PDF via `jspdf` (cover, model views, gene library, share footer)
3. If `slug` is provided, uploads PNG + PDF via `POST /_api/upload-report-assets`
4. Returns `{status: "uploaded", slug, share_url}` or base64 bundle

### Server-side (state.py)

`receive_report_bundle_and_publish()`:

1. Validates payload and STL existence
2. Creates report folder under `data/output/public/reports/{slug}/`
3. Writes artifacts:

```
reports/{slug}/
├── index.html      ← Landing page with OG tags + auto-redirect
├── report.webp     ← PNG card preview
├── report.pdf      ← A4 multi-page PDF
├── model.stl       ← 3D printable sculpture
├── params.json     ← Full artifact metadata (sculpture params, gene list, etc.)
└── portrait.webp   ← Optional user portrait
```

4. In dev mode, mirrors into `.web/public/generated/reports/{slug}/`
5. Sets `ComposeState.report_public_url` to absolute URL of `index.html`

### Slug format

`_safe_report_slug(name, seed)` → `{sanitized_name}-s{seed}`

- Name: lowercased, non-alnum → dash, max 36 chars, default "anonymous"
- Validation: `[a-zA-Z0-9_-]{1,96}`

### Serving

`app.py` mounts `StaticFiles(directory=GENERATED_PUBLIC_DIR)` at
`GENERATED_URL_PREFIX` (default `/generated`). Reports are accessible at
`/generated/reports/{slug}/index.html`.

---

## Social Sharing (me_report.js)

### Copy link

```js
window.__meCopyShareLink()
// → navigator.clipboard.writeText(reportTargetUrl() || absoluteShareUrl())
```

### Social intents

```js
window.__meShareIntent(network)
// network: 'twitter' | 'facebook' | 'linkedin' | 'whatsapp' | 'telegram'
```

Each opens a new window with the platform's share URL, encoding
`reportTargetUrl()` and a default share text.

### QR code

- On-page: `renderQrInto(el)` using `qrcode-generator` library → PNG `<img>`
- For PDF: `qrDataUrlForShare()` → canvas → PNG data URL
- Painted by `__mePaintReport()` mutation observer into `#report-qr`

---

## PDF & PNG Export

### PNG (WebP)

`__meDownloadPng()`:
- Snapshots `#me-report-png-card` or `#me-report-png-card-character`
- Uses `htmlToImage` with `skipFonts: true` (prevents Fomantic twemoji exhaustion)
- Output: WebP at 92% quality
- Filename: `materialized_{name}_s{seed}.webp`

### PDF

`__meDownloadPdf()` / `__meRenderPdfInPage()`:
- Uses `jspdf` library, A4 portrait
- 4-page structure:
  1. **Cover**: character name, categories, body-map pins, stat boxes
  2. **Model views**: front/side/back sculpture renders from `capture.html`
  3. **Gene library**: full narrative per gene with species silhouettes
  4. **Share footer**: QR code + recreation URL
- Reads metadata from hidden `<input>` / `<textarea>` elements
- Filename: `materialized_{name}_s{seed}.pdf`

---

## Email (Resend)

### Configuration

| Env var | Purpose |
|---|---|
| `RESEND_API_KEY` | API key (starts with `re_`) |
| `RESEND_FROM_EMAIL` | Verified sender address |
| `RESEND_REPLY_TO` | Optional reply-to (human inbox) |

### Flow

1. Visitor enters email → clicks **Send to email**
2. `ComposeState.start_email_send()` triggers browser PDF generation
3. `receive_pdf_and_send()` → `send_sculpture_email()`
4. Sends HTML email with PDF + STL attachments via Resend API
5. Attachments auto-zipped if total > 1.5 MB (hard cap 30 MB)

### Email body

Built by `_build_sculpture_email_html()` — mirrors the on-page report card:
name, categories, traits, genes, organisms, sculpture params, and a share-back
link to recreate the selection.

---

## ARTEX Publish

Pushes the sculpture to a venue display for physical exhibition.

### Configuration

| Env var | Purpose |
|---|---|
| `ARTEX_API_URL` | Platform API base (no trailing slash) |
| `ARTEX_API_TOKEN` | Admin token exchanged for session token |
| `ARTEX_DISPLAY_ID` | Target display ID (overridden by `?display_id=` query param) |

### Pipeline (`artex.py → publish_and_push_sync()`)

1. `build_artex_package_zip()` — in-memory zip with artwork config + STL + optional preview
2. `_upload_package()` — PUT zip to `/api/packages/:id`
3. `_get_session_token()` — POST to `/admin/dev-session` for Bearer token
4. `_publish_artwork()` — POST to `/publish/apply` → returns slug
5. `_push_to_display()` — POST to `/api/venue/displays/:displayId/load-slug`

Returns `(slug, delivery)` where delivery is `sse` (instant) or `queued`.

See [docs/ARTEX_INTEGRATION.md](ARTEX_INTEGRATION.md) for full protocol details.

---

## Crawler Assets

Generated by `crawler_assets.py → generate_crawler_assets()` into `assets/`.

| File | Content |
|---|---|
| `robots.txt` | Allow all except `/_event/` and `/ping`; links to sitemap and llms.txt |
| `sitemap.xml` | `<loc>` entries for `/`, `/materialization`, `/about` with canonical URLs |
| `llms.txt` | Human-readable project overview for LLM crawlers: gene counts, categories, routes, architecture |

All canonical URLs are derived from `public_app_url()`.

---

## Key Files

| File | Role |
|---|---|
| `src/materialized_enhancements/env.py` | URL resolution, env var loading |
| `src/materialized_enhancements/pages/index.py` | Page-level OG meta, hidden inputs for JS |
| `src/materialized_enhancements/state.py` | Report publishing, landing HTML, share URL, email |
| `assets/vendor/me_report.js` | Client-side PNG/PDF/QR/social/copy-link |
| `src/materialized_enhancements/email_send.py` | Resend API wrapper |
| `src/materialized_enhancements/artex.py` | ARTEX venue publish |
| `src/materialized_enhancements/crawler_assets.py` | robots.txt, sitemap, llms.txt |
| `src/materialized_enhancements/app.py` | Static file serving, head components |
