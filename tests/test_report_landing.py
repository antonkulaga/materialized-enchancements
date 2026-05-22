from __future__ import annotations

from html import escape

import pytest

from materialized_enhancements.gene_data import UNIQUE_CATEGORIES
from materialized_enhancements.state import _build_materialization_share_url, _build_report_landing_html


def test_report_landing_redirects_to_interactive_page_while_keeping_og_url() -> None:
    landing_url = "https://enhancement.bio/generated/reports/anonymous-s1985/index.html"
    recreate_url = "https://enhancement.bio/materialization?report=1&name=anonymous&cats=3"

    html = _build_report_landing_html(
        title="Materialized Enhancements - anonymous",
        description="A generated personal enhancement report.",
        page_url=landing_url,
        image_url="https://enhancement.bio/generated/reports/anonymous-s1985/report.webp",
        pdf_url="https://enhancement.bio/generated/reports/anonymous-s1985/report.pdf",
        stl_url="https://enhancement.bio/generated/reports/anonymous-s1985/model.stl",
        params_url="https://enhancement.bio/generated/reports/anonymous-s1985/params.json",
        recreate_url=recreate_url,
        make_own_url="https://enhancement.bio/",
    )

    escaped_recreate_url = escape(recreate_url, quote=True)
    assert f'<meta property="og:url" content="{landing_url}">' in html
    assert f'<meta http-equiv="refresh" content="0;url={escaped_recreate_url}">' in html
    assert f'<a class="primary" href="{escaped_recreate_url}">Open shared materialization</a>' in html
    assert f'<a href="{escaped_recreate_url}">Recreate this character</a>' in html
    assert f'<a class="primary" href="{landing_url}">' not in html


def test_anonymous_materialization_share_url_does_not_fall_back_to_homepage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEPLOY_URL", "https://enhancement.bio")

    url = _build_materialization_share_url(
        personal_tag="",
        selected_categories=[UNIQUE_CATEGORIES[0]],
        included_genes=[],
    )

    assert url.startswith("https://enhancement.bio/materialization?report=1&")
    assert "name=YW5vbnltb3Vz" in url
    assert "cats=1" in url


def test_materialization_share_url_requires_a_category(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEPLOY_URL", "https://enhancement.bio")

    assert _build_materialization_share_url(personal_tag="", selected_categories=[], included_genes=[]) == ""
