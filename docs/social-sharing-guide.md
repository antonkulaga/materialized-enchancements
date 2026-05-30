# Social Sharing for Modern Dynamic Web Apps — A Practical Guide

A distilled, reusable guideline for making **dynamic / SPA / WebSocket-first web
apps** (Reflex, Next.js client-rendered, Vue, htmx-over-WS, etc.) produce correct
link previews on Twitter/X, Facebook, LinkedIn, Telegram, WhatsApp, Slack,
Discord, and iMessage.

This document is the *generalised* companion to the project-specific
[`SHARING.md`](SHARING.md). It explains the **why**, the **patterns**, and the
**pitfalls** we learned in practice on this Reflex app, with copy-pasteable
examples. If you only need the wiring for *this* repo, read `SHARING.md`. If you
are building sharing into another dynamic app, read this.

> TL;DR of everything below:
> 1. **Crawlers do not run your JavaScript and never open your WebSocket.** They
>    read the raw HTML the server returns and stop.
> 2. Put the preview metadata (`og:*`, `twitter:*`) **in that raw HTML**, with
>    **absolute** URLs.
> 3. For per-item shares (one preview per user/report/product), generate a tiny
>    **static landing `index.html`** per item whose only jobs are: carry the
>    meta tags, show the image, and **redirect humans** into the live app.
> 4. The OG `og:image` must be an **absolute URL to a real raster image** that
>    returns `200` with a correct `Content-Type` — not an SVG, not behind auth,
>    not generated on first request.
> 5. After deploy, **force a re-scrape** in each network's debugger. Previews are
>    cached for days; you will not see your fix until you bust the cache.

---

## 1. Why dynamic apps break link previews by default

A normal SPA / Reflex / WebSocket app serves an almost-empty HTML shell:

```html
<!doctype html>
<html><head><title>My App</title></head>
<body><div id="app"></div><script src="/bundle.js"></script></body>
</html>
```

The real content arrives only **after**:
- the JS bundle downloads and executes, and
- (for Reflex) a **WebSocket** connects to the backend and hydrates state.

A social crawler — `Twitterbot`, `facebookexternalhit`, `TelegramBot`,
`LinkedInBot`, `Slackbot`, `Discordbot`, WhatsApp's fetcher — does **none** of
that. It issues one HTTP `GET`, parses the bytes it gets back, looks for
`<meta property="og:...">` and `<meta name="twitter:...">` in the `<head>`, and
leaves. No JS. No WebSocket. No `on_load`. No client routing.

So three things must be true **in the first server response**:

1. The `<head>` already contains the OG/Twitter tags.
2. Their URLs are **absolute** (`https://host/...`), never relative or
   `localhost`.
3. The `og:image` URL resolves to a real image file on a plain `GET`.

Everything in this guide is a consequence of those three facts.

### Reflex-specific note: prerendering ≠ data loading

Reflex can prerender each registered route to static HTML (`REFLEX_SSR=true` →
`prerender: true`). **But it prerenders using the *default values* of your state
vars** — `on_load` handlers require the WebSocket and do **not** run at
prerender time.

> **Rule:** any content (including meta tags) that must be indexable has to come
> from a *default value* or be injected at page-definition time, **never** from
> an `on_load` handler.

In this app, page-level meta is attached statically at `rx.page(...)` definition
time (see `pages/index.py`), so it is present in the prerendered HTML.

---

## 2. The two sharing scenarios (and the two solutions)

Almost every app has exactly two sharing needs. They have different solutions.

| Scenario | Example | Solution |
|---|---|---|
| **A. Static site pages** — fixed routes, one preview each | `/`, `/about`, pricing | Attach OG/Twitter meta to each route at build time. One shared OG image. |
| **B. Per-item dynamic shares** — a unique preview per generated thing | a user's generated report, a product, a profile | Generate a **static landing `index.html` per item** with item-specific meta + a generated image, and **redirect humans** into the live app. |

Scenario A is solved in §3. Scenario B is solved in §4 (the landing-page +
redirect pattern) — this is the part most teams get wrong.

---

## 3. Scenario A — static page previews (the meta-tag baseline)

Attach the meta tags to every public route. Here is the project's helper
(`pages/index.py → _page_meta`), which is a clean, copyable template:

```python
OG_PREVIEW_SIZE = (1200, 630)          # the universal safe size (see §5)

def _page_image_url() -> str:
    # ABSOLUTE url + cache-buster version query so networks re-fetch on change
    return f"{public_app_url()}{OG_PREVIEW_URL_PATH}?v=2"

def _page_meta(route_path: str) -> list[dict[str, str]]:
    base  = public_app_url()                      # absolute canonical origin
    route = _ROUTE_METADATA[route_path]
    title = f"{_SITE_TITLE} | {route.title}"
    image = _page_image_url()
    url   = f"{base}/" if route_path == "/" else f"{base}{route_path}"
    return [
        {"name": "robots", "content": "index, follow"},
        # --- Open Graph (Facebook, LinkedIn, Telegram, Slack, Discord, iMessage) ---
        {"property": "og:type",          "content": "website"},
        {"property": "og:site_name",     "content": _SITE_TITLE},
        {"property": "og:title",         "content": title},
        {"property": "og:description",   "content": route.description},
        {"property": "og:url",           "content": url},
        {"property": "og:image",         "content": image},
        {"property": "og:image:type",    "content": "image/png"},
        {"property": "og:image:width",   "content": str(OG_PREVIEW_SIZE[0])},
        {"property": "og:image:height",  "content": str(OG_PREVIEW_SIZE[1])},
        {"property": "og:image:alt",     "content": "…social preview card."},
        # --- Twitter / X ---
        {"name": "twitter:card",         "content": "summary_large_image"},
        {"name": "twitter:title",        "content": title},
        {"name": "twitter:description",  "content": route.description},
        {"name": "twitter:image",        "content": image},
        {"name": "twitter:image:alt",    "content": "…social preview card."},
    ]
```

Then register it on each page (Reflex):

```python
rx.page(route="/", on_load=..., meta=_page_meta("/"), image=_page_image_url())
```

### The minimum viable tag set

If you remember nothing else, ship these eight:

```html
<meta property="og:title"       content="…">
<meta property="og:description" content="…">
<meta property="og:image"       content="https://host/og.png">   <!-- ABSOLUTE -->
<meta property="og:url"         content="https://host/page">     <!-- ABSOLUTE, canonical -->
<meta property="og:type"        content="website">
<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="…">
<meta name="twitter:image"       content="https://host/og.png">  <!-- ABSOLUTE -->
```

### `noindex` for gated routes

Routes with no meaningful default content for a crawler (gated, requires
selection, personalised) should be `noindex, nofollow` so empty shells don't
get indexed. In this app `/materialization` is gated and uses:

```python
{"name": "robots", "content": "noindex, nofollow"}
```

It still carries OG tags so that *direct* shares of it look fine, but it won't
pollute search results with an empty page.

---

## 4. Scenario B — per-item previews: the static-landing-+-redirect pattern

This is the crux. You have N generated artifacts (reports, profiles, products),
each needs its **own** title/description/image in the preview, and clicking the
link should drop the human into the **live, interactive** app.

You cannot do this with the live SPA route alone, because the crawler will only
ever see the shell. The proven solution:

> **For each shared item, write a tiny static `index.html`** that:
> 1. carries that item's OG/Twitter meta (with an item-specific generated image),
> 2. shows a minimal human-readable fallback (image + buttons), and
> 3. **redirects real browsers** into the live app via `<meta http-equiv="refresh">`.

The crawler reads the meta and stops (it ignores the redirect). The human's
browser honours the redirect and lands in the app. Both are happy.

### Why a redirect, not just a link

Crawlers parse meta and ignore `<meta http-equiv="refresh">`. Humans' browsers
follow it instantly. So the *same file* serves a rich preview to bots and a
seamless hop-into-the-app for people. This is why the landing page is a
"midround" — it exists only to be scraped and bounced through.

### The landing template (from `state.py → _build_report_landing_html`)

```python
return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1440">
  <!-- version stamp lets you detect & regenerate stale landing pages later -->
  <meta name="{REPORT_LANDING_HTML_VERSION_META_NAME}" content="{REPORT_LANDING_HTML_VERSION}">
  <!-- redirect humans into the live app; crawlers ignore this -->
  <meta http-equiv="refresh" content="0;url={escaped_recreate_url}">
  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}">
  <meta property="og:type"        content="website">
  <meta property="og:title"       content="{escaped_title}">
  <meta property="og:description" content="{escaped_description}">
  <meta property="og:url"         content="{escaped_page_url}">   <!-- THIS landing page -->
  <meta property="og:image"       content="{escaped_image_url}">  <!-- per-item image -->
  <meta property="og:image:type"  content="image/webp">
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="{escaped_title}">
  <meta name="twitter:description" content="{escaped_description}">
  <meta name="twitter:image"       content="{escaped_image_url}">
</head>
<body>
  <main>
    <h1>{escaped_title}</h1>
    <p>{escaped_description}</p>
    <p><img src="{escaped_image_url}" alt="{escaped_title} preview"></p>
    <div class="links">
      <a class="primary" href="{escaped_recreate_url}">Open this character</a>
      <a href="{escaped_make_own_url}">Make your own</a>
      <a href="{escaped_stl_url}">Download model</a>
    </div>
  </main>
</body>
</html>"""
```

Key decisions baked into that template, each learned the hard way:

- **`og:url` points at the landing page itself**, not the live app route. If you
  point `og:url` at the SPA route, a re-scrape of the *shared* link may follow
  it, hit the empty shell, and overwrite your good preview with nothing.
- **All URLs are absolute** (`generated_public_absolute_url(...)`), built from
  the canonical origin (§6) — never relative, never `localhost` in production.
- **HTML-escape every interpolated value.** Names/descriptions are user input;
  unescaped `"` or `<` breaks the `<head>` and silently kills the preview.
- **Version stamp** (`materialized-report-html-version`): lets a background job
  detect landing pages written by an older template and rewrite them
  (`regenerate_stale_report_landing_pages()`), so a meta-tag fix propagates to
  already-published links.
- **Human fallback body**: image + buttons, in case the redirect is blocked
  (some in-app browsers, reader modes) or the human is a crawler-curious dev.

### Directory layout per published item

```
data/output/public/reports/{slug}/
├── index.html      ← landing page (meta tags + redirect + fallback)
├── report.webp     ← the generated preview image referenced by og:image
├── report.pdf      ← downloadable artifact
├── model.stl       ← downloadable artifact
└── params.json     ← machine-readable reproduction data
```

`{slug}` is sanitised and validated (`[a-zA-Z0-9_-]{1,96}`) — **never** put raw
user input in a filesystem path or URL.

> **Preserve every user-authored field across *all* artifacts and across
> regeneration.** Free-text the visitor enters (here a "Character note") must
> appear consistently in the on-page card, the PNG, the PDF, **`params.json`**,
> *and* the regenerated share/landing links. `params.json` is the durable record
> the boot migrator (§10.1) rebuilds the landing page from — so any field that
> isn't captured in it is silently dropped on the next template upgrade. When you
> add a shareable field, add it to the sidecar JSON first.

### 4.1 Arriving from a shared link — the two return paths

A landing page (§4) exists to bounce a human into the live app. But *which* live
URL it bounces to, and how the app rehydrates from it, is a design decision with
real consequences. This app has **two** distinct return paths that behave very
differently. Both are registered on the materialization page's `on_load`
(`pages/index.py:9345`), tried in order
`apply_artex_params → apply_saved_report → apply_shared_report`.

| | **Recreate path** | **Saved-artifact path** |
|---|---|---|
| URL | `/materialization?report=1&name=<b64>&cats=<bitmask>&genes=<b64>` | `/materialization?shared_report=<slug>` |
| Handler (on_load) | `apply_shared_report` (`state.py:2303-2367`) | `apply_saved_report` (`state.py:2231-2302`) |
| Source of truth | the **URL itself** (encoded selection) | the published **`params.json` + `model.stl`** on disk |
| What it does | **re-runs the sculpture pipeline** (`yield ComposeState.materialize`) | **loads the exact saved bytes** (no recompute) |
| `is_shared_visit` | set `True` (`state.py:2314`) | not set |
| `shared_report_slug` | not set | set (`state.py:2237`) → drives the banner |
| "Shared with you" banner | **no** | yes (`_shared_report_banner`, `pages/index.py:4341`) |
| Auto-render PDF in page | **skipped** (`pages/index.py:8960`) | n/a — artifact already published |
| Restores character note / portrait | **no** (not encoded in the URL) | yes (from `params.json` / `portrait.webp`) |

**Key differences vs a normal front-door visit** (`/` with no params):

- A front-door visit opens an **empty builder**; a shared visit
  **pre-populates** the selection — and on the recreate path immediately
  **materializes** — so the visitor lands on a *finished* character, not a blank
  slate.
- The shared visitor is viewing **someone else's** creation, so the UI suppresses
  the "this is yours" affordances: on `is_shared_visit` it **skips auto-building
  the PDF** (`pages/index.py:8960` — they didn't make it) and swaps the edit CTA
  for a **"Create your own / Create new character"** CTA (`pages/index.py:4237`).
- `redirect_legacy_tab` (`state.py:872-887`) deliberately **preserves**
  `report`/`name`/`cats`/`genes`/`shared_report` when bouncing legacy `?tab=`
  URLs, so links minted before the multi-route migration still resolve.

> **Idempotency guard:** `apply_shared_report` no-ops if a model is already
> generated or generating (`state.py:2315`). This matters because Reflex re-fires
> `on_load` on client-side `replaceState`; without the guard, every history tweak
> would re-trigger the expensive regeneration.

#### Design decision: a thin static shell + deterministic on-the-fly regeneration

The published landing page's `<meta http-equiv="refresh">` (and its "Open this
character" button) redirect to **`recreate_url = self.share_url`** — the
`?report=1&…` URL (`state.py:1720, 1760`; `_build_report_landing_html_from_artifact`
sets `recreate_url = artifact["share_url"]`, `state.py:567`). So every shared link
takes the **recreate path**, which **deterministically regenerates** the sculpture
from the encoded seed (name + category bitmask) rather than serving a stored copy.
**This is intentional**, and it is the project's settled consensus — worth stating
explicitly, because statically storing and versioning per-item artifacts looks
tempting but doesn't pay off.

**Why regenerate instead of serving stored bytes:**

- **No invalidation / versioning / storage / serving overhead.** A stored artifact
  must be versioned (does it still match the current generator?), invalidated when
  the algorithm changes, stored, and served — for *every* shared item. A
  deterministic generator has none of that: **the seed *is* the artifact.**
- **Always up-to-date.** Regeneration reflects the *current* gene data and
  `sculpture.py`, so improvements propagate to every previously-shared link for
  free. A frozen blob would pin each link to its publish-time output.
- **One fewer surface to maintain.** Serving a rich artifact page *well* means
  re-solving responsive desktop/mobile rendering for a second page. A thin
  meta+redirect shell sidesteps that entirely.
- **Deterministic ⇒ reproducible.** Same seed + same code ⇒ same model, so the
  regenerated result matches what was previewed while the generator is unchanged;
  when the generator improves, the newer output is the *desired* one, not drift to
  fix.

> **The consensus, as a rule:** a per-item static page should hold only **(1) meta
> tags, (2) a template version stamp (§10.1), and (3) a redirect** into artifacts
> that are **generated and served on the fly**. Do **not** statically store
> regenerable artifacts — the per-sculpture **static STL sharing that used to
> exist is deprecated** for exactly these reasons. The *one* artifact that must
> persist is the **OG image** (`report.webp`): crawlers can't trigger generation,
> so the preview raster has to sit at a stable URL (§5). Everything a *human* pulls
> — STL, PDF, the interactive model — regenerates on demand.

**What this means for the `?shared_report=` path.** A second handler,
`apply_saved_report` (`state.py:2231-2302`), loads the *exact stored bytes* and
shows a "shared with you" banner (`has_loaded_shared_report`, `state.py:1542`) —
but **no code emits a `?shared_report=<slug>` URL** (verified by repo-wide grep),
so it is reachable only by hand. Given the consensus above it is **deprecated, not
a missing feature**: a candidate for *removal* (along with the banner and the
stored `model.stl`), not for wiring up. Keep it only if you ever need byte-exact
fidelity to a *specific historical* render — which this project explicitly does
not want.

> **Minor cleanup:** `apply_shared_report` still has `print("[DEBUG] …")`
> statements (`state.py:2310-2316`) left from development — demote to
> `logger.debug` in a template.

---

## 5. Image constraints — sizes, formats, and byte limits

This is where "it works on Twitter but not Telegram" bugs come from. The networks
disagree, so target the **intersection** that satisfies all of them.

### The one safe answer

> **1200×630 px, PNG or JPEG, well under 5 MB, served over HTTPS with a correct
> `Content-Type`, at an absolute URL.** Use `twitter:card = summary_large_image`.

1200×630 is the 1.91:1 "large image" card. It renders correctly everywhere and
is what `OG_PREVIEW_SIZE = (1200, 630)` encodes in this repo.

### Per-network reality

| Network | Reads | Preferred image | Hard limits / gotchas |
|---|---|---|---|
| Facebook | OG | 1200×630 (1.91:1) | < 8 MB; **min 200×200** or it's dropped; caches hard — use the debugger to re-scrape |
| LinkedIn | OG | 1200×627 | **caches by URL essentially forever** — change the URL (`?v=2`) to refresh; needs `og:image` absolute |
| Twitter/X | `twitter:*`, falls back to OG | 1200×630 | < 5 MB; **PNG/JPEG/WebP/GIF only**; `summary_large_image` for the big card |
| Telegram | OG | 1200×630 | follows `og:image`; **WebP works**; aggressive cache — see §7 to bust |
| WhatsApp | OG | smaller is better | fetches synchronously on send; **slow/large images = no preview**; keep image small & fast |
| Slack | OG + oEmbed | 1200×630 | caches ~days; unfurls server-side |
| Discord | OG | 1200×630 | `Discordbot` UA; WebP & PNG fine; caches per-URL |
| iMessage | OG (Apple LinkPresentation) | 1200×630 | caches very aggressively per device; often needs a brand-new URL to refresh |

### Format pitfalls (important)

- **Never use SVG for `og:image`.** Most crawlers won't rasterize it; the preview
  silently fails. Always serve a raster (PNG/JPEG/WebP).
- **WebP is accepted by Telegram, Discord, Twitter, Facebook** and is what this
  app generates for per-report images (`report.webp`). But for the **site-wide**
  OG image prefer **PNG/JPEG** — it's the lowest common denominator (WhatsApp /
  some link-preview libraries are flakier with WebP). This repo uses
  `images/og-preview.png` (1200×630 PNG) site-wide and per-report WebP for the
  dynamic cards.
- **Set `og:image:type`** to match the actual bytes (`image/png` vs
  `image/webp`). A mismatch makes some scrapers skip the image.
- **Declare `og:image:width`/`height`.** Some networks lay out a placeholder
  before fetching; without dimensions you get layout fl/cropping surprises.
- The image must return **`200` with the right `Content-Type` on a cold,
  unauthenticated `GET`.** If it's generated on first request, behind auth, or
  returns `302`, the preview fails.

---

## 6. Canonical URL configuration (dev vs prod, the `localhost` trap)

Every absolute URL above is only correct if you resolve the canonical origin
correctly. The single most common production bug is **`og:url` /`og:image`
containing `http://localhost:3000`** because the code baked in a dev default.

### Server-side resolution (`env.py`)

```python
def public_app_url() -> str:
    # DEPLOY_URL → PUBLIC_APP_URL → http://localhost:3000
    deploy = os.getenv("DEPLOY_URL", "").strip().rstrip("/")
    return deploy or os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/") or "http://localhost:3000"
```

Set `DEPLOY_URL=https://enhancement.bio` in production. Everything (OG tags, share
links, sitemap, emails, QR codes) derives from this one value.

### Client-side resolution (split dev mode)

In Reflex split dev, the frontend is `:3000` and the backend static server is
`:8000`, so the browser must not assume one origin. The trick used here:

- A hidden input `<input id="report-canonical-base">` is populated with the
  **explicit** deploy URL — which is **empty in dev** (`_explicit_deploy_url()`
  returns `""` rather than `localhost`).
- Client JS reads it; if empty, it falls back to `window.location.origin`:

```js
function canonicalOrigin() {
  var el = document.getElementById('report-canonical-base');
  var v = el && el.value.trim();
  return v || window.location.origin;   // dev → real current origin, not baked localhost
}
```

> **Pitfall:** if you default the hidden input to `localhost:3000`, every share
> link a dev generates while testing will be a dead `localhost` URL. Default it
> to **empty** and fall back to `window.location.origin`.

### Serving the generated static files

The per-item folders are served as plain static files alongside the app
(`app.py`): `StaticFiles(directory=GENERATED_PUBLIC_DIR)` mounted at
`GENERATED_URL_PREFIX` (default `/generated`), so a report is reachable at
`/generated/reports/{slug}/index.html`. In split dev, the same files are mirrored
into `.web/public/generated/` so the `:3000` frontend can serve them too.

> **`.web/` is wiped on every `reflex run` / `uv run serve` and rebuilt from
> scratch.** The dev mirror under `.web/public/generated/` is a *convenience
> copy*, not storage — the canonical store is `GENERATED_PUBLIC_DIR`
> (`data/output/public`). Never treat `.web/` as durable: re-mirror on each
> publish, and keep all real source under `src/` and all static assets under
> `assets/`. Anything written into `.web/` by hand is lost on the next run.

---

## 7. Generating the per-item preview image in the browser

This app renders the preview card to an image **client-side** (no Python image
deps — a deliberate constraint), then uploads the bytes. The library is
`html-to-image`; the output is WebP at 92% quality, 1080×1080 (square card) or
1200×630 depending on the surface. (The PDF artifact is built client-side too —
see §12 for its mechanics and download UX.)

```js
async function snapshotNode(node, options) {
  var canvas = await htmlToImage.toCanvas(clone, h2iOptions(options));
  return canvas.toDataURL('image/webp', 0.92);
}
```

### `html-to-image` pitfalls we hit (all real, all costly)

- **`skipFonts: true` is mandatory** when any cross-origin stylesheet (here:
  Fomantic UI) embeds thousands of `url(...)` font/emoji references. When
  html-to-image can't read a cross-origin sheet's `cssRules`, it refetches the
  raw CSS and downloads **every** `url()` — thousands of parallel requests that
  hang the tab or abort with `ERR_INSUFFICIENT_RESOURCES`. Skipping webfonts is a
  visual no-op if your card uses system fonts.
- **Move off-screen capture nodes into the viewport** for the snapshot. Nodes at
  `display:none` or far off-screen rasterize blank in Chromium.
- **Use full `opacity: 1` and a high `z-index`** on the capture node; very low
  opacity often rasterizes as blank.
- **Avoid `display:flex` on the snapshot root inside an SVG `foreignObject`** —
  it mis-measures and clips.
- **`await` image loads** before snapshotting (`waitImages()`); un-decoded
  `<img>`s produce gaps.
- **Filter out `<iframe>`/`<script>`** nodes from the clone.

### Uploading large generated bytes: bypass the WebSocket

Reflex state travels over a WebSocket with a message-size cap. A 1–40 MB image+PDF
bundle will blow it. Solution: a **plain HTTP `POST` endpoint** that writes the
files server-side (`app.py → /_api/upload-report-assets`, 40 MB cap), instead of
shipping bytes through state:

```python
_MAX_UPLOAD_BYTES = 40 * 1024 * 1024
# POST base64 png+pdf → decode → write to GENERATED_PUBLIC_DIR/reports/{slug}/
```

> **Guard the build+upload against hanging.** The browser bundle builder
> (`__meBuildReportBundleBase64(timeoutMs, …)`, `me_report.js:1501`) takes an
> **explicit timeout** and wraps generation in error recovery. A stuck
> `html-to-image`/`jspdf` call or a failed POST must **reject**, not spin
> forever — otherwise the "Create public link" button hangs indefinitely with no
> feedback and the user can't tell publishing from a freeze. Always bound
> client-side artifact generation with a timeout and surface the failure.

### 7.1 Channel payload limits & the store-and-link pattern

Every channel that carries an artifact has a size ceiling, and **most fail
silently at the ceiling** — the single most expensive class of bug in this whole
system. This subsection collects the limits and the one pattern that solves all
of them.

> ### ⚠️ The inobvious pitfall: the WebSocket buffer that drops messages without an error
>
> Reflex ships state diffs over a Socket.IO WebSocket whose **default max message
> size is 1 MB**. When a state update exceeds it, the message is **dropped
> silently** — no exception, no toast, no console error; the event handler just
> appears to "do nothing," or the socket disconnects and reconnects. You will
> burn hours looking for a logic bug that isn't there.
>
> The fix is one env var, read in `rxconfig.py:11`:
> ```bash
> # The report publish callback sends base64 PNG+PDF (~3–10 MB) over the WS.
> # Reflex default 1 MB SILENTLY DROPS large messages. 50 MB is safe.
> REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE=50000000
> ```
> Raising it to 50 MB buys headroom, but it is **not** the real solution for big
> payloads — see below. Treat the buffer bump as a safety margin for ordinary
> state, not a transport for files.

**The layered limits in this app:**

| Channel | Limit | Where | Failure mode |
|---|---|---|---|
| Reflex state (WebSocket) | 1 MB default → **50 MB** raised | `REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE`, `rxconfig.py:11` | **silent drop** |
| HTTP POST upload | **40 MB** | `_MAX_UPLOAD_BYTES`, `app.py:81` | `413 Payload too large` |
| Email attachments (zip threshold) | **1.5 MB** → bundle into one zip | `ATTACHMENT_ZIP_THRESHOLD_BYTES`, `email_send.py:36` | n/a (optimisation) |
| Email attachments (hard cap) | **30 MB** (Resend ceiling 40 MB) | `MAX_TOTAL_ATTACHMENT_BYTES`, `email_send.py:40` | `EmailSendError` |

These caps stack: raising one just moves the wall. A 60 MB STL won't fit the
50 MB socket, won't fit the 40 MB upload, and won't fit a 30 MB email. Chasing
ever-larger limits is a losing game.

**The general solution — store the artifact, send the link.**

This is the *same* insight as the Facebook static-landing pattern (§4): a social
crawler can't be handed megabytes of image either, so we store the image on the
instance and put a **URL** in the OG tag. Generalise it to every channel:

> When a payload risks exceeding a channel's limit, **don't push the bytes
> through the channel. Write the artifact to instance storage (served at a stable
> URL) and send the link instead.** The link is a few hundred bytes and fits
> every channel — WebSocket, email body, social post, PDF footer, QR code.

| Instead of pushing bytes through… | …store and link |
|---|---|
| WebSocket state diff | write to `GENERATED_PUBLIC_DIR`, set a `report_public_url` state var (a string) |
| OG image to a crawler (§4) | serve `report.webp`; OG tag carries its URL |
| Email attachment > 30 MB | publish to `/generated/reports/<slug>/` and put `report_public_url` / `share_url` in the **email body** instead of attaching |
| A social post | share the landing-page URL (§8), never the raw file |
| A PDF that must reference the model | embed the **link + QR**, not the STL bytes (`renderShareFooterPage`) |

This app already has the infrastructure for it: the published report folder
(§4), the absolute `report_public_url` / `share_url`, and the in-page/PDF QR
codes (§8) are all "link to the stored artifact" surfaces.

> **Not yet wired for email (known low-priority TODO).** The email path
> *currently* always attaches (zipping ≤ 30 MB, rejecting above via
> `MAX_TOTAL_ATTACHMENT_BYTES`). The store-and-link move for an oversized bundle
> — **send the recreate/public link in the HTML body instead of attaching** — is
> not implemented; `_build_sculpture_email_html` already includes `share_url`, so
> the remaining work is just: when the bundle would exceed the cap, publish to
> `/generated/...` (if not already) and swap the attachment for the link. Tracked
> as a low-priority follow-up, not a current behaviour.

> **Rule of thumb:** inline small payloads (a few hundred KB) over their native
> channel; for anything that *might* be megabytes, store-and-link. Size limits
> are a transport concern — keep them from leaking into your UX by making the
> link, not the bytes, the thing that travels.

---

## 8. Share intents — the actual URLs

"Share to X" buttons are just `window.open` to each network's intent URL with
your **canonical** link (the landing page from §4, not the raw image)
URL-encoded:

```js
function shareIntent(network, rawUrl, text) {
  var u = encodeURIComponent(rawUrl);
  var t = encodeURIComponent(text);
  var target = {
    twitter:  'https://twitter.com/intent/tweet?text=' + t + '&url=' + u,
    facebook: 'https://www.facebook.com/sharer/sharer.php?u=' + u,
    linkedin: 'https://www.linkedin.com/sharing/share-offsite/?url=' + u,
    whatsapp: 'https://api.whatsapp.com/send?text=' + t + '%20' + u,
    telegram: 'https://t.me/share/url?url=' + u + '&text=' + t,
  }[network];
  if (target) window.open(target, '_blank', 'noopener,noreferrer,width=640,height=520');
}
```

Notes:
- **Share the landing-page URL**, never the raw `report.webp`. The networks fetch
  *that* page and read its OG tags; sharing the image directly gives a bare image
  with no title/description/actions.
- Facebook's sharer **ignores any custom text** — it derives everything from the
  page's OG tags. So your OG tags must be right; you can't override per-share.
- `og:url` on the shared page should be the **canonical** copy so re-shares
  collapse to one cached entry.

### Gate the share controls until a link exists

The QR / copy-link / social buttons have nothing to point at until the user has
**published** (clicked "Create public link" → a `report_public_url` exists). The
UX rule learned here:

> Before publish, show **explanatory placeholder text**, not a dead QR or a
> broken share link. Only after publish succeeds do the QR/copy/social controls
> resolve to `report_public_url`.

A half-rendered QR for a not-yet-existent URL reads as broken; an explanatory
placeholder reads as "do this first." (This is the visitor-facing counterpart of
the deterministic `share_url` always being available as a fallback — see the
fallback chain in §12.)

### Pitfall: a QR-painting MutationObserver can freeze the tab

The QR code is painted into the DOM by a `MutationObserver` (it waits for
`#report-qr` to mount, then writes the QR image). If that observer isn't guarded,
its own `innerHTML` write **retriggers itself**, looping until the tab freezes.
Make any repaint observer:

- **idempotent** with a signature guard (skip if the current content already
  matches the intended URL),
- **blind to its own subtree** (ignore mutations inside the node it rewrote),
- **debounced** via `requestAnimationFrame`.

(Same discipline applies to the report-card painter `__mePaintReport`.)

### 8.1 After "Create public link" — the publish state machine & post-publish pathways

§4 covered *what* gets written; this covers the **sender-side control flow** and
what the user can do once it's done.

**The publish chain** — one click → browser render → HTTP upload → server persist:

```
ComposeState.start_report_publish          (state.py:1615-1648; button pages/index.py:8296)
  → report_publishing=True, clears report_public_url / report_publish_error
  → rx.call_script("__meBuildReportBundleBase64(timeoutMs, publishedUrlOverride, slug)")
        (me_report.js:1501)
          → render WebP card + build A4 PDF (client-side)
          → POST base64 bundle to /_api/upload-report-assets   (app.py:84-131, 40 MB cap)
          → resolve → callback ComposeState.receive_report_bundle_and_publish
               (state.py:1650-1792)
                 → write model.stl + params.json + index.html landing page
                 → set report_public_url / report_public_slug, report_publishing=False
                 → switch artifact tab to "share", repaint QR
```

(A sibling callback `receive_report_assets`, `state.py:1794`, acknowledges an
asset-only upload.)

**The gating state vars** — the whole UI keys off these:

| Var | Meaning | Gates |
|---|---|---|
| `report_publishing` | a publish is in flight | spinner; disables the button via `can_publish_report` (`state.py:1530`) |
| `report_public_url` | non-empty ⇒ published | `has_published_report` (`state.py:1538`) → QR / copy / social / links panels |
| `report_publish_error` | last failure message | error banner + the **reset** affordance |
| `report_public_slug` / `report_{model,png,pdf,params}_url` | per-artifact links | the "published report links" panel |

**Failure & recovery — no infinite spinner.** Every error path flips
`report_publishing` back to `False` and sets `report_publish_error`; the browser
bundle builder is bounded by `timeoutMs + 60 s` and **rejects** on timeout, so it
never hangs (§7). If the flag still gets stuck (e.g. the tab was backgrounded
mid-build), `reset_report_publish` (`state.py:1850`, button `pages/index.py:8610`)
clears it so the user can retry.

**Pathways available *after* publish succeeds** (all gated on
`has_published_report`):

- **Copy link / social intents** (`__meCopyShareLink`, `__meShareIntent`) now
  resolve `reportTargetUrl()` to the **public landing URL** instead of the bare
  recreate URL. The swap is transparent — same buttons, better target (§8).
- **QR code** is painted into `#report-qr` (idempotent observer, §8), encoding the
  public URL.
- **Published-report links panel** exposes the PDF, STL, params JSON, and the
  landing page as direct `/generated/...` links.
- **Share card** renders in "model" or "character" mode on demand
  (`show_share_artifact_tab`, `state.py:1305`).
- **Email** (§11) and **ARTEX venue publish** are independent of report-publish
  and can fire before *or* after it.

**Before vs after publish — what the share buttons actually point at:**

| | Copy / social / QR target | Backing artifact |
|---|---|---|
| **Before publish** | `share_url` recreate link (`?report=1&…`) | none yet — the recreate URL *regenerates* on open (§4.1) |
| **After publish** | `report_public_url` landing page | the published folder; the landing then redirects per §4.1 |

So a post-publish share lands the recipient on the **recreate** path — the
landing page redirects to `share_url` — **by design** (§4.1). The published bytes
back the **preview** (the OG image that must persist for crawlers); the delivered
model regenerates deterministically from the seed, always reflecting the current
generator.

---

## 9. Debugging & forcing re-scrapes (you WILL need this)

Previews are cached aggressively (hours to days, sometimes per-device). After any
fix you must force each network to re-fetch, or you'll keep seeing the old (or
empty) preview and conclude your fix didn't work.

### Validators / debuggers (also force a re-scrape)

| Network | Tool |
|---|---|
| Facebook / generic OG | https://developers.facebook.com/tools/debug/ → "Scrape Again" |
| LinkedIn | https://www.linkedin.com/post-inspector/ |
| Twitter/X | Card validator is deprecated; paste into a draft tweet to preview or https://opentweet.io/tools/x-card-validator |
| Telegram | message [@WebpageBot](https://t.me/webpagebot) with the URL to clear its cache |
| Discord | repost the link in a throwaway channel; cache is per-URL |
| Generic | https://opengraph.xyz |

### Command-line: scrape exactly as a bot does

The single most useful debugging move — fetch your page **with the bot's
User-Agent** and inspect the raw bytes the crawler actually sees:

```bash
# Does the OG block exist in the RAW server response (no JS, no WS)?
curl -sL -A "Twitterbot/1.0" https://enhancement.bio/ | grep -i 'og:\|twitter:'

# Does the OG image actually return 200 with an image content-type?
curl -sI "https://enhancement.bio/images/og-preview.png?v=2" | grep -i 'HTTP/\|content-type\|content-length'

# Per-item landing page
curl -sL -A "facebookexternalhit/1.1" \
  https://enhancement.bio/generated/reports/anonymous-s1985/index.html | grep -i 'og:'
```

If `curl -A "Twitterbot"` doesn't show your tags, **no amount of debugger
re-scraping will help** — the tags aren't in the HTML the bot receives. Fix that
first (it's almost always the prerender/`on_load` trap from §1).

> **Testing the share/report/export flow locally needs a populated selection.**
> Use `uv run preselect` (or `uv run preselect --dev`): it boots the server *and*
> opens a URL with genes, categories, and a personal tag pre-filled. With an empty
> selection (plain `uv run start`) there is **nothing to publish, share, or
> export** — the share controls are gated (§8) and there's no per-item artifact to
> scrape. Don't test sharing features from an empty `uv run start`.

### Cache-busting strategy

- **Change the image URL** when the image changes: append `?v=N` (this repo uses
  `?v=2`). LinkedIn and iMessage in particular cache by URL near-permanently.
- For per-item pages, the **slug is unique** so the URL is naturally fresh; the
  only stale risk is the *template*, handled by the version stamp + regeneration
  job (§10.1).

### Bot User-Agents (for allowlists / curl / logs)

```
Twitterbot/1.0
facebookexternalhit/1.1   (Facebook + WhatsApp)
LinkedInBot/1.0
TelegramBot (like TwitterBot)
Slackbot-LinkExpanding 1.0
Discordbot/2.0
```

> **Pitfall:** if a CDN, WAF, or `robots.txt` blocks unknown bots, these crawlers
> get a `403`/empty body and previews silently fail. Allow them. This app's
> `robots.txt` allows all except `/_event/` and `/ping`.

---

## 10. Production serving & metadata generation

Sharing behaves differently in dev vs production because the **serving topology
changes**, and because crawler metadata is **regenerated at boot from the
canonical URL**. Get this wrong and your links preview perfectly on localhost and
break in production (or vice-versa).

### The three run modes

| Command | Mode | Ports | Use for |
|---|---|---|---|
| `uv run start` | Reflex **dev** (`Env.DEV`) | **split**: frontend `:3000`, backend `:8000` | local development; hot reload |
| `uv run serve` | Reflex **production** (`Env.PROD`, `RunningMode.FULLSTACK`) | **single** `APP_PORT` (front = back) | production / staging deploy |
| `uv run preselect` | dev + pre-filled selection | split | testing share/report/model (selection required) |

The defining difference for sharing: **`uv run serve` is single-port unified
mode** — `_run(running_mode=FULLSTACK, frontend_port=port, backend_port=port)`
in `run.py → serve()`. Frontend and backend share **one origin**.

### Why single-port production simplifies sharing

In split dev mode the frontend (`:3000`) and the static/backend server (`:8000`)
are **different origins**, which is exactly why the client needs the
`window.location.origin` fallback and why generated reports get mirrored into
`.web/public/generated/` (§6). In production single-port mode there is **one
origin**, so:

- `/generated/reports/{slug}/index.html`, `/robots.txt`, `og-preview.png`, the
  app routes, and the WebSocket all live on the same host:port.
- The split-origin mirroring and `window.location.origin` gymnastics become
  no-ops — but keep them, because the same code runs in both modes.
- Set **`DEPLOY_URL`** (and a reverse proxy terminating TLS in front of
  `APP_PORT`) so every absolute URL resolves to `https://your-host/...`.

### What `serve()` does at boot (production-only steps)

```python
def serve() -> None:
    _setup()                          # load .env, cd to repo root
    shutil.rmtree(".web")             # wipe stale build so prerender is fresh
    generate_crawler_assets()         # (re)write robots.txt, sitemap.xml, llms.txt
    regenerate_stale_report_landing_pages()  # rewrite landing pages on an old template (§10.1)
    _run(env=PROD, running_mode=FULLSTACK,
         frontend_port=port, backend_port=port)   # port = APP_PORT
```

Two of those steps are pure sharing/SEO hygiene:

- **`generate_crawler_assets()`** regenerates `robots.txt`, `sitemap.xml`,
  `llms.txt` **from the current canonical URL** — so they're correct for
  whatever `DEPLOY_URL` is set at boot.
- **`regenerate_stale_report_landing_pages()`** rewrites already-published report
  `index.html`s whose embedded template version is behind the current one — see
  §10.1 below for the full mechanism.

> **Pitfall:** these files bake in `DEPLOY_URL` **as it was at process start**.
> If you change the canonical host, you must **restart `uv run serve`** (or
> re-run `generate_crawler_assets()`) — editing the env without a restart leaves
> stale absolute URLs in `robots.txt`/`sitemap.xml`/`llms.txt`.

### 10.1 Versioning & on-start upgrade of static artifacts (the template pattern)

This is the most reusable idea in the whole sharing system, and the one a
repo-as-a-template refactor most wants to keep: **published static artifacts
carry a version stamp, and the server migrates stale ones up to the latest
template on every boot.**

The problem it solves: once you've published thousands of per-item landing pages
(§4), a fix to the OG-tag template (new tag, fixed escaping, changed canonical
host) would only apply to *future* items — every already-shared link keeps its
old, possibly-broken preview. The version+migrate pattern fixes them all at the
next deploy, with zero manual intervention.

**The four moving parts** (`state.py`):

1. **A monotonic version constant + the meta name it's stamped under**
   — `state.py:68-69`:
   ```python
   REPORT_LANDING_HTML_VERSION: int = 2
   REPORT_LANDING_HTML_VERSION_META_NAME = "materialized-report-html-version"
   ```
   Bump the integer whenever the landing template changes in a way you want
   back-propagated.

2. **Every generated page embeds its version** in the `<head>`
   — `state.py:492` inside `_build_report_landing_html` (`state.py:465-531`):
   ```html
   <meta name="{REPORT_LANDING_HTML_VERSION_META_NAME}" content="{REPORT_LANDING_HTML_VERSION}">
   ```

3. **Read-back + staleness check** — `_report_landing_html_version`
   (`state.py:534-545`, regex-parses the stamp; returns `0` if absent) and
   `_report_landing_html_needs_regeneration` (`state.py:548-555`, returns `True`
   if the file is missing or its stamp `< REPORT_LANDING_HTML_VERSION`).

4. **The migration sweep** — `regenerate_stale_report_landing_pages()`
   (`state.py:588-662`), called at boot by `run.py:72`. For each
   `data/output/public/reports/<slug>/` directory it:
   - skips dirs already at the latest version (`state.py:608-610`);
   - if `index.html` is stale **and** `params.json` exists, rebuilds the page
     from that saved artifact via `_build_report_landing_html_from_artifact`
     (`state.py:564-585`) and rewrites `index.html` (`state.py:632-642`);
   - if `index.html` is stale **and `params.json` is gone**, deletes the whole
     unrecoverable report dir (`state.py:611-621`);
   - logs a one-line summary (`updated / regenerated / deleted / skipped /
     checked`) to stdout (`state.py:654-661`).

```
checked = every reports/<slug>/ dir
  ├─ stamp == latest   → leave it
  ├─ stamp <  latest   → params.json present? rebuild index.html  : delete dir
  └─ no index.html     → (treated as stale) rebuild or delete
```

**Why `params.json` is the lynchpin.** Each published report writes a machine-
readable `params.json` next to its assets (the recreate/share inputs: name,
categories, gene list, sculpture params). That file is the *durable source of
truth* — the migrator reconstructs the entire landing page from it, so the
template can evolve freely without re-running the (expensive) original
generation. **The template lesson: every static artifact you publish should sit
next to a small, versionless JSON describing how to regenerate it.**

**Generalising the pattern** for a template repo:

| Piece | This repo | Your repo |
|---|---|---|
| Version constant | `REPORT_LANDING_HTML_VERSION` | one per artifact family |
| Embedded stamp | `<meta name="…-version">` | meta tag, JSON field, file header comment |
| Staleness predicate | `_report_landing_html_needs_regeneration` | `stamp < CURRENT` |
| Regeneration source | `params.json` | any sidecar describing the artifact |
| When it runs | `serve()` at boot (`run.py:72`) | server start / deploy hook / cron |

> **Pitfall:** make regeneration **idempotent and fail-soft** — one corrupt
> `params.json` must not abort the whole sweep. The implementation `continue`s
> past unreadable/non-dict artifacts (`state.py:622-631`) and only counts what
> it actually rewrote, so a bad item is skipped and logged, not fatal.

### Generated crawler metadata (`crawler_assets.py`)

All three are written into `assets/` and served by Reflex at the site root.

**`/robots.txt`** — allow everything except internal Reflex paths; advertise the
sitemap and the LLM overview:

```
User-agent: *
Allow: /
Allow: /llms.txt
Disallow: /_event/
Disallow: /ping

Sitemap: https://enhancement.bio/sitemap.xml
# LLM-readable overview: https://enhancement.bio/llms.txt
```

> `/_event/` is the Reflex **WebSocket** endpoint and `/ping` is a health check —
> neither is a document; excluding them keeps crawlers from indexing junk. Note
> social *preview* bots ignore `robots.txt` for unfurling, but **make sure your
> CDN/WAF still lets them through** (§9) — `robots.txt` allowing `/` is not the
> same as a firewall allowing `Twitterbot`.

**`/sitemap.xml`** — one `<url>` per public route with canonical `<loc>`,
`<lastmod>`, `<changefreq>`, `<priority>`, built from `PUBLIC_ROUTES`. Reflex's
built-in `SitemapPlugin` is **disabled** in `rxconfig.py`
(`disable_plugins=[SitemapPlugin]`) so this hand-rolled, canonical-URL-aware
sitemap is the single source.

**`/llms.txt`** — a human/LLM-readable overview (the emerging
[llmstxt.org](https://llmstxt.org) convention): site + repo URLs, public-page
list, **crawl guidance** (e.g. "route HTML contains default visitor text before
websocket hydration"; "don't index `/_event/`"), dataset stats (gene/category/
organism counts pulled live from the loaded data), and tech notes. It is
generated from the **actual loaded data**, so it never drifts from the CSVs.

### Production `rxconfig.py` knobs that affect sharing

```python
os.environ.setdefault("REFLEX_SSR", "true")                          # prerender each route (§1)
os.environ.setdefault("REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE", "50000000")  # 50 MB WS buffer
config = rx.Config(
    disable_plugins=[SitemapPlugin],          # use our canonical sitemap, not Reflex's
    vite_allowed_hosts=["enhancement.bio"],   # production host allowlist
    head_components=[
        ...,
        rx.el.meta(name="google-site-verification", content="…"),  # search-console verification
    ],
)
```

- **`REFLEX_SSR=true`** is what makes prerendered HTML (with the meta tags) exist
  for crawlers — without it, `uv run serve` would still serve an empty shell.
- **`REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE=50 MB`** raises the WebSocket frame cap,
  but the report image/PDF bytes still go over the **separate HTTP POST** channel
  (§7) — the buffer bump is a safety margin, not the upload path.
- **`google-site-verification` meta** is a third metadata surface (alongside
  OG/Twitter and the crawler files) for Search Console ownership.

### Production-governing environment variables (`.env.template`)

`.env.template` is the documented superset; copy it to `.env` and fill in real
values. These are the nodes that **govern production state** for sharing,
serving, and delivery (see `env.py` for defaults and `rxconfig.py` for the two
`REFLEX_*` knobs read at config time):

| Variable | Governs | Production value / note |
|---|---|---|
| `DEPLOY_URL` | **The** canonical base for OG tags, share/report links, QR codes, PDF/email permalinks, sitemap/robots/llms | `https://enhancement.bio`. Comment out for local dev (→ `http://localhost:3000`). The single most important prod var. |
| `REFLEX_API_URL` | Reflex's own API/WebSocket origin | Same host as `DEPLOY_URL` in single-port prod. |
| `REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE` | Max WebSocket frame size | `50000000` (50 MB). Reflex default 1 MB **silently drops** large report messages (§7.1). Read in `rxconfig.py`. |
| `APP_PORT` | The single fullstack port `serve()` binds (front = back) | e.g. `3001`; keep fixed so the reverse proxy (Caddy) mapping is stable. Blank → Reflex default. |
| `GENERATED_PUBLIC_DIR` | Where published report folders are written | defaults to `data/output/public`; served at `GENERATED_URL_PREFIX`. |
| `GENERATED_URL_PREFIX` | URL prefix for generated static artifacts | defaults to `/generated`. |
| `MATERIALIZED_DEV_MODE` | Exposes dev-only UI + dev redirect targets | set by `uv run start --dev`; **unset in prod**. |
| `RESEND_API_KEY` / `RESEND_FROM_EMAIL` / `RESEND_REPLY_TO` | Email sharing (§11) | required for "Send to email"; `FROM` must be a verified sender. |
| `UMAMI_SCRIPT_URL` / `UMAMI_WEBSITE_ID` / `UMAMI_DOMAINS` / `UMAMI_HOST_URL` | Privacy-friendly analytics | both script+id needed to enable; `UMAMI_DOMAINS` keeps localhost out of prod stats. |
| `ARTEX_API_URL` / `ARTEX_API_TOKEN` / `ARTEX_DISPLAY_ID` | Venue/exhibition publish | see `docs/ARTEX_INTEGRATION.md`. |
| `ARTEX_IDLE_URL` / `ARTEX_DEV_REDIRECT_URL` / `IDLE_TIMEOUT_SECONDS` / `IDLE_WARNING_SECONDS` | Kiosk idle redirect (prod kiosk only) | timer active only when `?redirect=` is in the URL. |
| `DISCORD_INVITE_URL` / `DISCORD_COMMUNITY_NAME` / `GITHUB_PROJECT_URL` / `DONATION_URL` | Post-generation community CTAs | set to empty string to hide a given CTA. |

> **Pitfall:** `public_app_url()` reads `DEPLOY_URL` **fresh on every call** (not
> a module constant) — this is deliberate, to avoid the import-time freeze that
> once baked `localhost:3000` into emails when env vars weren't visible at import.
> But `generate_crawler_assets()` runs **once at boot** (§10), so `robots.txt` /
> `sitemap.xml` / `llms.txt` still snapshot `DEPLOY_URL` as-of process start —
> restart after changing it.

---

## 11. Sharing by email (Resend transactional email)

Email is a first-class sharing channel here: the **"Send to email"** button
delivers the same artifacts the Download buttons would write to disk (STL +
params JSON + the report PDF) to the visitor's inbox, plus an HTML body that
mirrors the on-page report card with a share-back link. It is implemented with
[Resend](https://resend.com) and a hand-rolled `urllib` client
(`email_send.py`) — no SDK, no Python image deps.

### Configuration

```bash
RESEND_API_KEY=re_xxxxxxxx                                  # required; starts with re_
RESEND_FROM_EMAIL=Materialized Enhancements <no-reply@longevity-genie.info>
RESEND_REPLY_TO=                                            # optional human inbox
```

- **`RESEND_FROM_EMAIL` must be a verified sender.** While iterating without DNS
  setup, use Resend's shared sandbox sender `onboarding@resend.dev`; switch to a
  domain you own once SPF/DKIM are configured, or mail lands in spam.
- If `RESEND_API_KEY` is empty the "Send to email" button is **disabled**
  (`can_send_email` checks `len(RESEND_API_KEY) > 0`) — the feature degrades
  gracefully in dev rather than erroring.

### The send flow (why it's a 3-hop dance)

The report PDF is built **in the browser** (no server-side PDF/image deps), so
the bytes must come back to the server before Resend can attach them:

```
Click "Send to email"
  → ComposeState.start_email_send()          # validates email + STL exist
      → rx.call_script("__meBuildReportPdfBase64()", callback=receive_pdf_and_send)
  → browser builds the A4 PDF (jspdf) → returns {filename, base64}
  → ComposeState.receive_pdf_and_send(payload)   # stashes pending_pdf_base64
      → yield ComposeState.send_sculpture_email
  → send_sculpture_email()  [@rx.event(background=True)]
      → reads STL bytes, builds params.json, assembles attachments,
        zips if large, renders HTML body, calls Resend in an executor
```

Two deliberate choices worth copying:

- **`@rx.event(background=True)`** for the actual send — the Resend HTTP call can
  take seconds; a background event keeps the UI responsive and lets the handler
  flip `email_sending`/`email_sent`/`email_error` state around it.
- **`run_in_executor`** wraps the blocking `urllib` call so it doesn't block the
  event loop:

```python
loop = asyncio.get_event_loop()
await loop.run_in_executor(None, lambda: send_email_via_resend(
    to=recipient, subject=subject, html=html, attachments=attachments,
))
```

- If the browser PDF build fails, it sends **without** the PDF rather than
  failing the whole email (`receive_pdf_and_send` logs and proceeds).

### Attachment policy

Attachments are raw bytes wrapped in `EmailAttachment(filename, content,
content_type)` and base64-encoded only at send time. Two size rules
(`email_send.py`):

| Threshold | Constant | Behaviour |
|---|---|---|
| **1.5 MB** combined | `ATTACHMENT_ZIP_THRESHOLD_BYTES` | below → send files **separately** (recipient can grab the STL straight from the preview); above → bundle into **one zip** |
| **30 MB** combined (raw) | `MAX_TOTAL_ATTACHMENT_BYTES` | above → **reject** with `EmailSendError` (Resend's hard cap is 40 MB; we leave headroom for base64 + JSON overhead). For oversized bundles the right pattern is store-and-link, not a bigger cap — see §7.1 |

```python
items = [
    EmailAttachment(stl_filename, stl_bytes, "model/stl"),
    EmailAttachment(stem + "_params.json", params_json, "application/json"),
    EmailAttachment(pdf_filename, pdf_bytes, "application/pdf"),   # if PDF built
]
attachments = maybe_zip_attachments(items, zip_name=f"{stem}.zip")
```

### The Resend client (copyable)

`send_email_via_resend()` POSTs JSON to `https://api.resend.com/emails`. The
essential shape:

```python
payload = {
    "from": RESEND_FROM_EMAIL,
    "to": [recipient],
    "subject": subject,
    "html": html,
    "attachments": [
        {"filename": a.filename,
         "content": base64.b64encode(a.content).decode("ascii"),
         "content_type": a.content_type}
        for a in attachments
    ],
    # "reply_to": RESEND_REPLY_TO   # only if set
}
headers = {
    "Authorization": f"Bearer {RESEND_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    # CRITICAL — see pitfall below
    "User-Agent": "materialized-enhancements/0.2 (+https://enhancement.bio)",
}
# urllib POST, 30s timeout → parse JSON → return parsed["id"] (the message id)
```

> **Pitfall (real, cost us a debugging session):** Cloudflare sits in front of
> `api.resend.com` and **`403`s the default `Python-urllib/x.y` User-Agent**
> (Cloudflare error 1010, "banned browser signature"). You must send a neutral
> custom `User-Agent` or every email silently fails with an opaque 403. Any SDK
> sets one for you; a hand-rolled `urllib`/`requests` client must do it
> explicitly.

### The HTML body

`_build_sculpture_email_html()` (in `state.py`) renders an inline-styled HTML
email mirroring the report card: personal tag, categories, traits, included
genes, source organisms, sculpture params, a note about the attached PDF, and a
**share-back link** (`share_url`, the §4 recreate URL) so the recipient can
reopen or remix the exact selection. Keep email HTML **inline-styled** (no
external CSS, no webfonts) — mail clients strip `<style>`/`<link>`.

### Error surfaces

- `EmailSendError` carries the Resend HTTP status + body, surfaced to the user
  via `email_error` state and logged server-side.
- `is_valid_email()` is a cheap syntactic pre-check; Resend does the real
  validation.

---

## 12. PDF generation & download-UX patterns

The shareable artifacts (PDF, STL, params JSON, images) are *downloaded*, and how
you trigger those downloads matters as much as how you build them. This section
covers the **client-side PDF mechanics**, the **0-click download/render-on-
generate** pattern, the **Chrome multi-download trap**, and **lazy download
patterns for Reflex**.

### PDF generation mechanics (one builder, three sinks)

The A4 report PDF is built **entirely in the browser** with jsPDF — no
server-side PDF deps. `buildReportPdf()` (`me_report.js:1323+`) assembles pages
by **drawing text and shapes from the live DOM**, not by rasterizing the page:

- Pages: cover (`renderCoverPageA4`, `me_report.js:882+`), 3D model views
  (`renderModelViewsPage`, `me_report.js:1206+`), gene library
  (`renderGenePages`, `me_report.js:540+`), share footer + QR
  (`renderShareFooterPage`, `me_report.js:1150+`).
- The **3D model views** aren't drawn by jsPDF — they're captured by a headless
  Three.js page (`assets/sculpture_viewer/capture.html`) loaded in a hidden
  iframe with a changing `?nonce=` (cache-bust per generation). It renders
  front/side/back and `postMessage`s the three PNG data URLs to the parent, which
  stashes them in `window.__reportViews`; the cover and model-views pages read
  from there. (Same nonce trick keeps the interactive viewer iframe from serving
  a stale STL.)
- Text is laid out with `pdf.text()` + `pdf.splitTextToSize()` per row.
  **This is deliberate**: rasterizing each A4 page to an image balloons file
  size; vector text keeps the PDF small and selectable.
- jsPDF's built-in fonts are **WinAnsi/Latin-1 only**, so all strings pass
  through `pdfSafeWinAnsi()` (`me_report.js:282+`) which normalizes Unicode
  (smart quotes, em-dashes, accented chars) before drawing — otherwise glyphs
  drop or wrap wrong.

The **same builder feeds three different sinks** depending on what's needed:

| Sink | jsPDF call | Used for | Location |
|---|---|---|---|
| **Download** | `pdf.save(filename)` | "Download PDF" button | `__meDownloadPdf`, `me_report.js:1448-1456` |
| **In-page preview** | `pdf.output('arraybuffer')` → `Blob` → `URL.createObjectURL` → `<iframe>` | render in the report tab | `renderPdfArrayBufferInPage`, `me_report.js:1364-1369` |
| **Email / upload** | `pdf.output('datauristring')` → base64 | attach to Resend / POST to server | `__meBuildReportPdfBase64`, `me_report.js:1477-1499` |

> **Object-URL hygiene:** in-page preview uses `URL.createObjectURL(blob)` and
> **must** `revokeObjectURL` the previous one before creating a new one
> (`clearPdfPreviewObjectUrl`, `me_report.js:1341-1346`) — otherwise each
> re-render leaks a blob handle and memory climbs.

### Always embed a *usable* URL in the PDF (fallback chain)

The share-footer page (`renderShareFooterPage`) carries the link/QR a reader uses
to reopen the character — so it must **never** be blank or `localhost`. Pick it by
a fallback chain so there's always a resolvable URL regardless of publish state:

| Publish state | URL embedded in the PDF |
|---|---|
| **While publishing** | the *pending* public-report URL (the slug folder being written) |
| **After publishing** | `report_public_url` (the live landing page) |
| **Before publishing** | the deterministic `share_url` recreate link (§4) — always available |

The deterministic `share_url` is the floor: even with nothing published, the
recreate URL reproduces the selection, so a downloaded PDF is never a dead end.

### 0-click render/download-on-generate (smoother UX)

Make the artifact appear **without a second click**. Two flavours here:

1. **Auto-render on tab open.** When the report tab opens, the PDF renders into
   the page automatically — no "click to preview" step. The orchestrator
   `__meRenderActiveReportPdfInPage` (`me_report.js:1405-1414`):
   - waits for the preview container to mount (`waitPdfViewerMounted`,
     `me_report.js:1395-1403` — DOM polling because the node mounts async),
   - **prefers the already-published PDF** if one exists
     (`__meUsePublishedPdfInPage`, just points the iframe at the saved file —
     cheap), otherwise **builds inline** (`__meRenderPdfInPage`,
     `me_report.js:1416-1446`).
   - A re-entrancy guard (`window.__mePdfRendering`) prevents overlapping builds.

2. **Build-and-download in one gesture.** The download handlers build the PDF and
   immediately `pdf.save()` in the same click (`__meDownloadPdf`). For data-URL
   artifacts (WebP card), `downloadDataUrl()` (`me_report.js:239-246`) creates a
   transient `<a download>`, clicks it, and removes it on the next tick.

> The general pattern: **the moment the user has "generated" something, surface
> the artifact** (render the preview, or hand them the file) instead of gating it
> behind another button. Pair it with a published-artifact fast path so repeat
> views don't rebuild.

### The Chrome multi-download trap (important)

> If a **single user gesture** (one button click) programmatically triggers
> **more than one file download**, Chrome shows a *"Download multiple files?"*
> permission prompt — and if the user (or enterprise policy) has
> **"Automatic downloads" set to block**, the **2nd and later files are silently
> dropped**. Firefox/Safari have similar heuristics.

So a naive "Download all (STL + PDF + JSON)" button that fires three
`a.click()` / `pdf.save()` / `rx.download()` calls in a row will deliver the
first file and silently lose the rest for many users.

**Mitigations, in order of preference:**

1. **Bundle into one file.** Zip the artifacts and download once — exactly what
   the email path does with `maybe_zip_attachments` (`email_send.py:63-84`).
   One file = one download = no prompt. This is the most robust fix.
2. **One download per gesture.** Keep separate buttons (this app's "Download
   STL", "Download params", "Download PDF" are independent handlers —
   `state.py:1459-1486`), so each download maps to its own click.
3. **Stagger** if you must fire several: sequence them with a short delay between
   downloads so the browser doesn't coalesce them into the multi-file prompt
   (least reliable — still prompts on strict settings).
4. **Hand a link, not a download** for secondary artifacts: publish them to the
   `/generated/...` folder (§4) and link to them, letting the user pull each on
   demand.

### Lazy download patterns for Reflex

"Lazy" = **don't hold large bytes in state or push them over the WebSocket until
the moment they're actually requested.** Reflex gives several tools:

- **`rx.download()` yielded from an event handler.** The handler reads the bytes
  from disk *on click* and streams them to the browser — they never live in a
  state var:
  ```python
  def download_stl(self):
      p = Path(self.stl_download_path)
      if not p.exists():
          yield rx.toast.error("STL file not found on disk.")
          return
      yield rx.download(data=p.read_bytes(), filename=self.stl_filename)
  ```
  (`download_stl` `state.py:1459-1468`; `download_params_json`
  `state.py:1470-1486` builds the JSON on demand; `download_protein_stl`
  `state.py:1517-1527`.) State only ever holds the **path**
  (`stl_download_path`), not the file.

- **Build-in-browser, return via callback** for artifacts the server shouldn't
  hold (the PDF): `rx.call_script("__meBuild…()", callback=...)` →
  the browser builds the bytes → the callback receives base64 → the server uses
  it for one operation (email/publish) and discards it (§7, §11). Heavy bytes
  travel over the **HTTP POST** side-channel (§7), not the state socket.

- **`@rx.event(background=True)` for long work.** The Resend send
  (`send_sculpture_email`, `state.py:1915-1916`) and the sculpture generation are
  background events: they `yield`/flip progress flags
  (`email_sending` / `generating` / `report_publishing`) so the UI stays
  responsive and shows a spinner, and they `run_in_executor` any blocking I/O
  (§11) so the event loop isn't stalled.

- **Disk-backed, regenerable.** Generated files live under
  `GENERATED_PUBLIC_DIR`; state keeps only paths/URLs. Combined with the boot
  migration (§10.1), this means even published artifacts are lazy — rebuilt from
  `params.json` when stale rather than kept hot in memory.

> **Reflex pitfall:** a tempting "preload everything into state so download is
> instant" approach serializes multi-MB blobs into every state diff over the
> WebSocket — slow, and it can exceed `REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE`
> (§10). Keep bytes on disk or in the browser; move them only on the actual
> download/needed event.

---

## 13. Consolidated pitfalls checklist

Run through this before declaring sharing "done":

- [ ] **Tags are in the raw HTML** — `curl -A Twitterbot <url> | grep og:` shows them.
- [ ] **No content depends on `on_load`/WebSocket** for crawlability (Reflex prerenders defaults only).
- [ ] **All OG/Twitter URLs are absolute** and use the **canonical** origin, not `localhost`.
- [ ] **`og:image` is a raster** (PNG/JPEG/WebP), **not SVG**, returns `200` with matching `Content-Type` on a cold `GET`.
- [ ] **Image is ~1200×630**, < 5 MB; site-wide uses PNG/JPEG, per-item WebP is fine for FB/Telegram/Discord/Twitter.
- [ ] **`og:image:type` / `:width` / `:height`** declared and accurate.
- [ ] **Per-item shares use a static landing `index.html`** with `<meta http-equiv="refresh">` into the live app; `og:url` points at the landing page itself.
- [ ] **All interpolated user text is HTML-escaped** in the landing template.
- [ ] **Slugs/paths are sanitised** — no raw user input in filesystem paths or URLs.
- [ ] **Large generated bytes uploaded via plain HTTP POST**, not through state/WebSocket.
- [ ] **`skipFonts: true`** (and the other html-to-image fixes) if rendering images client-side over a webfont-heavy CSS.
- [ ] **Share buttons link the landing page**, not the raw image.
- [ ] **Crawler bots are allowed** through CDN/WAF/`robots.txt`.
- [ ] **Cache-buster (`?v=N`)** on changeable images; **template version stamp** + regeneration for landing pages.
- [ ] **`DEPLOY_URL` is set before `uv run serve` starts** — crawler files bake it in at boot; restart after changing it.
- [ ] **Prerender is on in production** (`REFLEX_SSR=true`) so `uv run serve` emits HTML-with-meta, not an empty shell.
- [ ] **`robots.txt` / `sitemap.xml` / `llms.txt` regenerated at boot** with correct canonical URLs; CDN/WAF still lets preview bots through.
- [ ] **Post-deploy: re-scraped** in Facebook debugger / LinkedIn inspector / Telegram @WebpageBot.
- [ ] **Email sharing**: `RESEND_FROM_EMAIL` is a *verified* sender; hand-rolled HTTP client sets a custom `User-Agent` (Cloudflare 403s `Python-urllib`); attachments zip > 1.5 MB and reject > 30 MB; HTML body is inline-styled.
- [ ] **Downloads**: a single click triggers **one** download (or one zip) — never N programmatic downloads (Chrome blocks the 2nd+ when "automatic downloads" is off); object URLs are `revokeObjectURL`'d; large bytes stay on disk/in-browser, not in Reflex state (§12).
- [ ] **Payload limits**: `REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE` raised above 1 MB (default **silently drops** big state messages); megabyte payloads go via HTTP POST, not state; anything that *might* exceed a channel cap is **store-and-link**, not a bigger cap (§7.1).
- [ ] **Keep the per-item static page thin**: meta tags + version stamp + redirect into **on-the-fly** artifacts. Don't statically store regenerable artifacts (STL/PDF) — only the OG image must persist for crawlers. Shared links redirect into the **deterministic regenerate** path (seed-reproducible, always current), not frozen stored bytes; static-STL sharing is deprecated (§4.1, §8.1).

---

## 14. Implementation index (exact code references)

Every concept in this guide, mapped to the exact symbol and line range that
implements it. Line numbers are accurate as of this writing — when refactoring
this repo into a template, treat the **symbol names** as the stable anchors and
re-grep if the lines have drifted.

### Meta tags & per-item landing pages

| Concept (§) | Symbol | Location |
|---|---|---|
| Site-page OG/Twitter meta (§3) | `_page_meta` | `src/.../pages/index.py:42-66` |
| Site OG image URL + `?v=` buster (§3, §5) | `_page_image_url` | `src/.../pages/index.py:68-69` |
| `index, follow` on public routes (§3) | `_page_meta` robots entry | `src/.../pages/index.py:49` |
| `noindex, nofollow` on gated route (§3) | `materialization_page` meta | `src/.../pages/index.py:9335` |
| Page registration (`@rx.page`, prerendered) (§1) | `index/materialization/about_page` | `src/.../pages/index.py:9321-9360` |
| Per-item landing HTML template (§4) | `_build_report_landing_html` | `src/.../state.py:465-531` |
| Landing meta-refresh redirect (§4) | `<meta http-equiv="refresh">` | `src/.../state.py:493` |
| Rebuild landing from saved artifact (§4) | `_build_report_landing_html_from_artifact` | `src/.../state.py:564-585` |

### Arrival from shared links & the publish flow (§4.1, §8.1)

| Concept | Symbol | Location |
|---|---|---|
| Recreate-path handler (regenerates) | `apply_shared_report` | `src/.../state.py:2303-2367` |
| Saved-artifact handler (loads bytes) | `apply_saved_report` | `src/.../state.py:2231-2302` |
| Shared-visit flags | `is_shared_visit` / `shared_report_slug` | `src/.../state.py:944, 948` |
| "Shared with you" banner + gate | `_shared_report_banner` / `has_loaded_shared_report` | `pages/index.py:4341-4378` / `state.py:1542-1543` |
| Shared-visit UI branches (skip PDF, swap CTA) | `is_shared_visit` conds | `pages/index.py:4237, 8960` |
| Legacy `?tab=` redirect (preserves share params) | `redirect_legacy_tab` | `src/.../state.py:872-887` |
| Slug mint / read-validate / upload-validate | `_safe_report_slug` / `_is_safe_report_slug` / `_SLUG_RE` | `state.py:402-405, 408-410` / `app.py:80` |
| Publish click handler | `start_report_publish` | `src/.../state.py:1615-1648` |
| Publish recovery (clear stuck flag) | `reset_report_publish` | `src/.../state.py:1850` (button `pages/index.py:8610`) |
| Publish gating predicates | `can_publish_report` / `has_published_report` | `src/.../state.py:1530-1531 / 1538-1539` |
| Asset-only upload callback | `receive_report_assets` | `src/.../state.py:1794` |
| Share-tab open / QR repaint | `show_share_artifact_tab` | `src/.../state.py:1305-1321` |

### Versioning & on-start upgrade (§10.1)

| Concept | Symbol | Location |
|---|---|---|
| Version constant + meta name | `REPORT_LANDING_HTML_VERSION` / `…_META_NAME` | `src/.../state.py:68-69` |
| Embedded version stamp | meta tag in template | `src/.../state.py:492` |
| Read stamp from HTML | `_report_landing_html_version` | `src/.../state.py:534-545` |
| Staleness predicate | `_report_landing_html_needs_regeneration` | `src/.../state.py:548-555` |
| Boot migration sweep | `regenerate_stale_report_landing_pages` | `src/.../state.py:588-662` |
| Sweep invoked at boot | `serve()` | `src/.../run.py:72` |

### Canonical URL & static serving

| Concept (§) | Symbol | Location |
|---|---|---|
| Server canonical origin (§6) | `public_app_url` | `src/.../env.py:61-72` |
| Root-relative artifact URL (§6) | `generated_public_url` | `src/.../env.py:92-99` |
| Absolute artifact URL (OG/email) (§6) | `generated_public_absolute_url` | `src/.../env.py:102-108` |
| Generated dirs config (§6) | `GENERATED_PUBLIC_DIR` / `_URL_PREFIX` | `src/.../env.py:75-84` |
| Client origin fallback (§6) | `canonicalOrigin` | `assets/vendor/me_report.js:28-33` |
| Share-link resolution (§6, §8) | `absoluteShareUrl` / `reportTargetUrl` / `publicReportTargetUrl` | `assets/vendor/me_report.js:34-48` |
| Static serve `/generated` (§4, §6) | `normalize_reflex_event_websocket_path` | `src/.../app.py:133-149` |
| `StaticFiles` mount (§4) | `_generated_static` | `src/.../app.py:33` |
| Upload endpoint (bypass WS) (§7) | `_handle_upload_report_assets` | `src/.../app.py:84-131` |
| Upload size cap (§7) | `_MAX_UPLOAD_BYTES` | `src/.../app.py:81, 93` |
| Write `report.webp` server-side (§7) | `(out_dir / "report.webp").write_bytes` | `src/.../app.py:109-113` |

### Share URL, image, PDF, QR, social (client)

| Concept (§) | Symbol | Location |
|---|---|---|
| Recreate/share URL builder (§4) | `_build_materialization_share_url` | `src/.../state.py:413-434` |
| `share_url` computed var (§4) | `ComposeState.share_url` | `src/.../state.py:2219-2225` |
| Slug sanitisation (§4) | `_safe_report_slug` | `src/.../state.py:402-410` |
| Publish callback (server) (§4, §7, §8.1) | `receive_report_bundle_and_publish` | `src/.../state.py:1650-1792` |
| `html-to-image` options + `skipFonts` (§7) | `h2iOptions` (+ rationale comment) | `assets/vendor/me_report.js:312-340` |
| Await image decode (§7) | `waitImages` | `assets/vendor/me_report.js:359-387` |
| Snapshot node → WebP (§5, §7) | `snapshotNode` (`toDataURL('image/webp',0.92)`) | `assets/vendor/me_report.js:388-413` |
| 1080×1080 PNG/WebP card (§5) | `buildReportPngDataUrl` / `__meDownloadPng` | `assets/vendor/me_report.js:441-473` |
| Build A4 PDF (§7, §11) | `buildReportPdf` | `assets/vendor/me_report.js:1323+` |
| PDF base64 for email (§11) | `__meBuildReportPdfBase64` | `assets/vendor/me_report.js:1477-1499` |
| Build+upload bundle (§4) | `__meBuildReportBundleBase64` | `assets/vendor/me_report.js:1501-1570` |
| Copy share link (§8) | `__meCopyShareLink` | `assets/vendor/me_report.js:1572-1589` |
| Social share intents (§8) | `__meShareIntent` | `assets/vendor/me_report.js:1591-1606` |
| On-page QR (§8) | `renderQrInto` | `assets/vendor/me_report.js:115+` |
| QR PNG for PDF (§8) | `qrDataUrlForShare` | `assets/vendor/me_report.js:831+` |

### PDF generation & download UX (§12)

| Concept | Symbol | Location |
|---|---|---|
| Build A4 PDF (vector, from DOM) | `buildReportPdf` | `assets/vendor/me_report.js:1323+` |
| Cover / model / gene / footer pages | `renderCoverPageA4` / `renderModelViewsPage` / `renderGenePages` / `renderShareFooterPage` | `me_report.js:882` / `1206` / `540` / `1150` |
| WinAnsi/Latin-1 normalize | `pdfSafeWinAnsi` | `assets/vendor/me_report.js:282+` |
| Download sink (`pdf.save`) | `__meDownloadPdf` | `assets/vendor/me_report.js:1448-1456` |
| In-page preview (Blob + object URL) | `renderPdfArrayBufferInPage` / `clearPdfPreviewObjectUrl` | `me_report.js:1364-1369` / `1341-1346` |
| Base64 sink (email/upload) | `__meBuildReportPdfBase64` | `assets/vendor/me_report.js:1477-1499` |
| Auto-render-on-tab-open | `__meRenderActiveReportPdfInPage` | `assets/vendor/me_report.js:1405-1414` |
| Prefer published PDF / build inline | `__meUsePublishedPdfInPage` / `__meRenderPdfInPage` | `me_report.js:1376-1393` / `1416-1446` |
| Wait-for-mount poll | `waitPdfViewerMounted` | `assets/vendor/me_report.js:1395-1403` |
| Transient `<a download>` (data URLs) | `downloadDataUrl` | `assets/vendor/me_report.js:239-246` |
| Lazy server download (read on click) | `download_stl` / `download_params_json` / `download_protein_stl` | `src/.../state.py:1459-1468` / `1470-1486` / `1517-1527` |
| Zip-on-large (single download) | `maybe_zip_attachments` | `src/.../email_send.py:63-84` |
| Background long-work event | `@rx.event(background=True)` | `src/.../state.py:1915` (and 1119, 1379, …) |

### Crawler metadata & production config

| Concept (§) | Symbol | Location |
|---|---|---|
| `robots.txt` builder (§10) | `build_robots_txt` | `src/.../crawler_assets.py:79-88` |
| `sitemap.xml` builder (§10) | `build_sitemap_xml` | `src/.../crawler_assets.py:91-108` |
| `llms.txt` builder (§10) | `build_llms_txt` | `src/.../crawler_assets.py:119-165` |
| Write all three (§10) | `generate_crawler_assets` | `src/.../crawler_assets.py:168-180` |
| Public route table (§10) | `PUBLIC_ROUTES` | `src/.../crawler_assets.py:34-66` |
| Robot-excluded paths (§10) | `ROBOT_EXCLUDED_PATHS` | `src/.../crawler_assets.py:19-22` |
| OG image path/size (§5) | `OG_PREVIEW_PATH` / `OG_PREVIEW_SIZE` | `src/.../crawler_assets.py:13-15` |
| Single-port prod serve (§10) | `serve()` | `src/.../run.py:59-87` |
| `.web` wipe before serve (§10) | `shutil.rmtree(web_dir)` | `src/.../run.py:64-66` |
| `APP_PORT` → front=back (§10) | `frontend_port`/`backend_port` | `src/.../run.py:79-87` |
| SSR/prerender + socket buffer (§1, §10) | `os.environ.setdefault(...)` | `rxconfig.py:10-11` |
| Disabled built-in sitemap, host allowlist, site-verification (§10) | `rx.Config(...)` | `rxconfig.py:16-31` |
| Prod env reference (§10) | all vars | `.env.template` (whole file) |

### Email sharing (Resend)

| Concept (§) | Symbol | Location |
|---|---|---|
| Resend env config (§11) | `RESEND_API_KEY` / `_FROM_EMAIL` / `_REPLY_TO` | `src/.../env.py:114-119` |
| Resend HTTP client + Cloudflare-UA fix (§11) | `send_email_via_resend` | `src/.../email_send.py:87-end` |
| Attachment zip/cap thresholds (§11) | `ATTACHMENT_ZIP_THRESHOLD_BYTES` / `MAX_TOTAL_ATTACHMENT_BYTES` | `src/.../email_send.py:36, 40` |
| Attachment zip policy (§11) | `maybe_zip_attachments` | `src/.../email_send.py:63-84` |
| Attachment dataclass (§11) | `EmailAttachment` | `src/.../email_send.py:45-54` |
| Email validity check (§11) | `is_valid_email` | `src/.../email_send.py:58-60` |
| Click handler → JS PDF build (§11) | `start_email_send` | `src/.../state.py:1871-1893` |
| PDF callback → stash (§11) | `receive_pdf_and_send` | `src/.../state.py:1895-1913` |
| Background send + executor (§11) | `send_sculpture_email` | `src/.../state.py:1916-2024` |
| HTML email body (§11) | `_build_sculpture_email_html` | `src/.../state.py:684-758` |
| `can_send_email` gate (§11) | `ComposeState.can_send_email` | `src/.../state.py:1862-1869` |

> Project-specific wiring (handlers, ARTEX, email copy) is also narrated in
> [`docs/SHARING.md`](SHARING.md).

---

## 15. Minimal recipe for a new dynamic app

1. **Pick a canonical-origin resolver** (`DEPLOY_URL` env → fallback to
   `window.location.origin` client-side; never bake `localhost`).
2. **Attach OG + Twitter meta to every public route**, absolute URLs, one
   1200×630 PNG site image with a `?v=N` buster. Verify with
   `curl -A Twitterbot`.
3. **For per-item shares**, on publish:
   - render a 1200×630 (or square) raster preview,
   - write `reports/{slug}/index.html` with item meta + `<meta http-equiv="refresh">`
     into the live route + a human fallback body,
   - write the image next to it, all URLs absolute,
   - serve the folder as static files.
4. **Upload big generated bytes over plain HTTP POST**, not your state channel.
5. **Share the landing-page URL** in intent buttons.
6. **Serve production single-port** behind a TLS proxy with `DEPLOY_URL` set, and
   **regenerate `robots.txt`/`sitemap.xml`/`llms.txt` + stale landing pages at
   boot** (as `uv run serve` does) so all metadata uses the canonical host.
7. **After deploy, re-scrape** in each network's debugger; add `?v=N` when images
   change.

Do those seven and your dynamic app will preview correctly across every major
network.
