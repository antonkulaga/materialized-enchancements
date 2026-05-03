# Umami Analytics — Implementation Guide

Self-hosted, privacy-friendly analytics for a Reflex SPA served behind Caddy.

---

## Env vars (`prod .env`)

```
UMAMI_SCRIPT_URL=https://your-app.example.com/stats/script.js
UMAMI_WEBSITE_ID=<uuid from Umami Settings → Websites>
UMAMI_DOMAINS=your-app.example.com,example.com   # comma-sep, no spaces
UMAMI_HOST_URL=https://your-app.example.com/stats  # same-domain proxy; blank = direct to Umami
```

`UMAMI_DOMAINS` silently suppresses tracking on every unlisted hostname — keeps localhost dev
runs out of prod stats without any code change.  
`UMAMI_HOST_URL` blank is safe and correct until the Caddy proxy is confirmed working.

---

## Python wiring

**`env.py`** — four constants read from env at import time.  
**`app.py`** — injected into `head_components` at startup:

```python
if UMAMI_SCRIPT_URL and UMAMI_WEBSITE_ID:
    _umami_attrs: dict[str, str] = {"data-website-id": UMAMI_WEBSITE_ID}
    if UMAMI_DOMAINS:
        _umami_attrs["data-domains"] = UMAMI_DOMAINS
    if UMAMI_HOST_URL:
        _umami_attrs["data-host-url"] = UMAMI_HOST_URL
    _head_components.append(
        rx.script(src=UMAMI_SCRIPT_URL, custom_attrs=_umami_attrs)
    )
```

Use `rx.script(src=..., custom_attrs={...})` — not `rx.el.script(...)`.  
`custom_attrs` is the documented Reflex way to pass `data-*` attributes through `next/script`.

---

## Caddy — same-domain proxy (ad-blocker bypass)

Add **inside** your app's `handle` block, **before** the catch-all `reverse_proxy`:

```caddy
@art host your-app.example.com example.com
handle @art {
    handle_path /stats/* {          # ← handle_path, NOT handle (strips prefix before proxying)
        reverse_proxy localhost:3300
    }
    reverse_proxy localhost:3001    # app catch-all — must be last
}
```

`handle_path /stats/*` strips `/stats` before forwarding, so
`/stats/script.js` → `localhost:3300/script.js` and
`/stats/api/send` → `localhost:3300/api/send`.

Using `handle` (without `_path`) passes the full URL to Umami → 404.

---

## SPA navigation

Umami v2 patches `history.pushState` / `replaceState` natively.  
**Do not** add a custom SPA tracker — it causes double page views.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Counter stuck at 0 | `head_components` baked with stale env | Delete `.web/`, full restart (`uv run start`) |
| 404 on `/stats/script.js` | `handle` instead of `handle_path` in Caddy | Change to `handle_path`, reload Caddy |
| 404 on `/stats/script.js` | Caddy not reloaded | `caddy reload --config /etc/caddy/Caddyfile` |
| Adblock still blocking | Proxy not on same origin as app | Script URL must match the page's hostname exactly |
| Localhost visits in prod stats | `UMAMI_DOMAINS` missing or wrong | List every prod hostname; omit localhost |
| My own visits not counted | Firefox ETP / adblock | ETP alone rarely blocks custom subdomains; adblock needs same-domain proxy |
| `data-host-url` pointing nowhere | Proxy not live when env was set | Set `UMAMI_HOST_URL=` blank until proxy is confirmed with `curl -I` |

---

## Reflex-specific notes

- `head_components` and `rx.script` props are **compiled into the Next.js bundle at Reflex startup**.
  Changing `.env` alone is not enough — the frontend must be rebuilt.
  Quick check: `curl https://your-app.example.com | grep umami` to see what's actually live.
- Umami `data-domains` is matched against `window.location.hostname` — must be exact (no `https://`, no paths).
- Umami CORS is permissive (`Access-Control-Allow-Origin: *`) — cross-origin POSTs work fine.
  The same-domain proxy is for ad-blocker bypass only, not a CORS fix.
