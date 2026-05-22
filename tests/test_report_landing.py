from __future__ import annotations

import json
from html import escape
from pathlib import Path

import pytest

from materialized_enhancements.gene_data import UNIQUE_CATEGORIES
from materialized_enhancements.state import (
    REPORT_LANDING_HTML_VERSION,
    REPORT_LANDING_HTML_VERSION_META_NAME,
    _build_materialization_share_url,
    _build_report_landing_html,
    _report_landing_html_version,
    regenerate_stale_report_landing_pages,
)


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
    assert _report_landing_html_version(html) == REPORT_LANDING_HTML_VERSION
    assert f'<meta name="{REPORT_LANDING_HTML_VERSION_META_NAME}" content="{REPORT_LANDING_HTML_VERSION}">' in html
    assert f'<meta property="og:url" content="{landing_url}">' in html
    assert 'http-equiv="refresh"' not in html
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


def test_report_landing_migration_regenerates_missing_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEPLOY_URL", "https://enhancement.bio")
    monkeypatch.setattr(
        "materialized_enhancements.state.generated_public_path",
        lambda *parts: tmp_path.joinpath(*parts),
    )
    report_dir = tmp_path / "reports" / "anonymous-s1985"
    report_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<!doctype html><title>old</title>", encoding="utf-8")
    (report_dir / "params.json").write_text(
        json.dumps(
            {
                "name": "",
                "selected_categories": [UNIQUE_CATEGORIES[0]],
                "included_genes": [],
                "share_url": "",
                "sculpture_params": {"seed": 1985},
                "pipeline_stats": {},
            }
        ),
        encoding="utf-8",
    )

    result = regenerate_stale_report_landing_pages()
    html = (report_dir / "index.html").read_text(encoding="utf-8")

    assert result == {"checked": 1, "latest": 1, "regenerated": 1, "deleted": 0, "skipped": 0, "updated": 1}
    assert _report_landing_html_version(html) == REPORT_LANDING_HTML_VERSION
    assert "https://enhancement.bio/generated/reports/anonymous-s1985/report.webp" in html
    assert "https://enhancement.bio/materialization?report=1" in html
    assert 'http-equiv="refresh"' not in html


def test_report_landing_migration_skips_current_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "materialized_enhancements.state.generated_public_path",
        lambda *parts: tmp_path.joinpath(*parts),
    )
    report_dir = tmp_path / "reports" / "current-s1"
    report_dir.mkdir(parents=True)
    html_path = report_dir / "index.html"
    html_path.write_text(
        f'<meta name="{REPORT_LANDING_HTML_VERSION_META_NAME}" content="{REPORT_LANDING_HTML_VERSION}">',
        encoding="utf-8",
    )

    result = regenerate_stale_report_landing_pages()

    assert result == {"checked": 1, "latest": 1, "regenerated": 0, "deleted": 0, "skipped": 0, "updated": 0}


def test_report_landing_migration_deletes_report_without_params_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "materialized_enhancements.state.generated_public_path",
        lambda *parts: tmp_path.joinpath(*parts),
    )
    report_dir = tmp_path / "reports" / "anonymous-s2025"
    report_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<!doctype html><title>old</title>", encoding="utf-8")
    (report_dir / "report.webp").write_text("stale", encoding="utf-8")

    result = regenerate_stale_report_landing_pages()

    assert result == {"checked": 1, "latest": 0, "regenerated": 0, "deleted": 1, "skipped": 0, "updated": 1}
    assert not report_dir.exists()
