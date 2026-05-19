from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

os.environ.setdefault("REFLEX_SSR", "true")
os.environ.setdefault("REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE", "50000000")

import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin
from reflex_components_radix.plugin import RadixThemesPlugin

config = rx.Config(
    app_name="materialized_enhancements",
    plugins=[RadixThemesPlugin(theme=rx.theme(appearance="light"))],
    disable_plugins=[SitemapPlugin],
    stylesheets=[
        "https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.css",
    ],
    head_components=[
        rx.script(src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"),
        rx.script(src="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.4/dist/semantic.min.js"),
        rx.el.meta(name="google-site-verification", content="BoBYqc8A_Xkw0AHGsMrk9Y_Ms3zsltZZtvd8Rltrs4w"),
    ],
    tailwind=None,
    vite_allowed_hosts=["enhancement.bio"],
    show_built_with_reflex=False,
)
