#!/usr/bin/env python3
"""Download species silhouette SVGs from PhyloPic for all species in species.csv."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parents[1]
SPECIES_CSV = REPO_ROOT / "data" / "input" / "species.csv"
PUZZLE_DIR = REPO_ROOT / "data" / "input" / "puzzle"
OUTPUT_DIR = PUZZLE_DIR / "phylopic"

API_BASE = "https://api.phylopic.org"
IMAGES_BASE = "https://images.phylopic.org"

SKIP_SPECIES = {"homo_sapiens"}


def api_get(path: str) -> dict | None:
    url = f"{API_BASE}{path}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def download_file(url: str, dest: Path) -> bool:
    try:
        req = Request(url)
        with urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"  ERROR downloading {url}: {e}")
        return False


def find_node_uuid(name: str) -> str | None:
    """Find a PhyloPic node UUID by scientific name (lowercase)."""
    # First check if there are results
    check_path = f"/nodes?filter_name={name.lower().replace(' ', '+')}&build=538"
    check = api_get(check_path)
    if not check or check.get("totalItems", 0) == 0:
        return None
    # Now fetch with embedded items
    path = f"/nodes?filter_name={name.lower().replace(' ', '+')}&build=538&embed_items=true&page=0"
    data = api_get(path)
    if not data:
        return None
    items = data.get("_embedded", {}).get("items", [])
    if not items:
        return None
    self_href = items[0].get("_links", {}).get("self", {}).get("href", "")
    if "/nodes/" in self_href:
        return self_href.split("/nodes/")[1].split("?")[0]
    return None


def get_images_for_node(node_uuid: str) -> list[dict]:
    """Get all images for a node, with source file info."""
    check_path = f"/images?filter_node={node_uuid}&build=538"
    check = api_get(check_path)
    if not check or check.get("totalItems", 0) == 0:
        return []
    path = f"/images?filter_node={node_uuid}&build=538&embed_items=true&page=0"
    data = api_get(path)
    if not data:
        return []
    return data.get("_embedded", {}).get("items", [])


def get_primary_image(node_uuid: str) -> dict | None:
    """Get the primary image for a node directly."""
    path = f"/nodes/{node_uuid}?build=538&embed_primaryImage=true"
    data = api_get(path)
    if not data:
        return None
    return data.get("_embedded", {}).get("primaryImage")


def get_parent_node(node_uuid: str) -> str | None:
    """Get parent node UUID."""
    path = f"/nodes/{node_uuid}?build=538"
    data = api_get(path)
    if not data:
        return None
    parent = data.get("_links", {}).get("parentNode")
    if not parent:
        return None
    parent_href = parent.get("href", "")
    if "/nodes/" in parent_href:
        return parent_href.split("/nodes/")[1].split("?")[0]
    return None


def find_svg_image(node_uuid: str, max_depth: int = 3) -> tuple[str, str, str] | None:
    """Find an SVG source image for a node, walking up the tree if needed.

    Returns (svg_url, image_title, license_url) or None.
    """
    current_uuid = node_uuid
    for depth in range(max_depth):
        if not current_uuid:
            break
        # Try primary image first
        img = get_primary_image(current_uuid)
        if img:
            source = img.get("_links", {}).get("sourceFile", {})
            if source.get("type") == "image/svg+xml":
                title = img.get("_links", {}).get("self", {}).get("title", "unknown")
                license_url = img.get("_links", {}).get("license", {}).get("href", "")
                return (source["href"], title, license_url)

        # Try all images for this node
        images = get_images_for_node(current_uuid)
        for im in images:
            source = im.get("_links", {}).get("sourceFile", {})
            if source.get("type") == "image/svg+xml":
                title = im.get("_links", {}).get("self", {}).get("title", "unknown")
                license_url = im.get("_links", {}).get("license", {}).get("href", "")
                return (source["href"], title, license_url)

        # Walk up to parent
        if depth < max_depth - 1:
            current_uuid = get_parent_node(current_uuid)
            if current_uuid:
                print(f"    No SVG at this level, trying parent node...")
            time.sleep(0.3)
    return None


def find_best_image(node_uuid: str, max_depth: int = 3) -> tuple[str, str, str, str] | None:
    """Find the best image (SVG preferred, PNG fallback) for a node.

    Returns (url, image_title, license_url, file_type) or None.
    """
    # First try to find SVG
    svg = find_svg_image(node_uuid, max_depth)
    if svg:
        return (svg[0], svg[1], svg[2], "svg")

    # Fallback: try primary image (any format)
    current_uuid = node_uuid
    for depth in range(max_depth):
        if not current_uuid:
            break
        img = get_primary_image(current_uuid)
        if img:
            source = img.get("_links", {}).get("sourceFile", {})
            if source.get("href"):
                title = img.get("_links", {}).get("self", {}).get("title", "unknown")
                license_url = img.get("_links", {}).get("license", {}).get("href", "")
                ext = "svg" if "svg" in source.get("type", "") else "png"
                return (source["href"], title, license_url, ext)
        if depth < max_depth - 1:
            current_uuid = get_parent_node(current_uuid)
            time.sleep(0.3)
    return None


def load_species() -> list[tuple[str, str]]:
    """Load (species_id, scientific_name) pairs from species.csv."""
    lines = SPECIES_CSV.read_text().strip().split("\n")
    # Skip double header if present
    start = 1
    if len(lines) > 1 and lines[1].startswith("species_id,"):
        start = 2
    result = []
    for line in lines[start:]:
        parts = line.split(",")
        species_id = parts[0].strip()
        scientific_name = parts[1].strip()
        if species_id not in SKIP_SPECIES:
            result.append((species_id, scientific_name))
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    species_list = load_species()
    print(f"Found {len(species_list)} species (excluding human)")
    print(f"Output directory: {OUTPUT_DIR}\n")

    results: list[dict] = []
    failed: list[str] = []

    for i, (species_id, sci_name) in enumerate(species_list, 1):
        print(f"[{i}/{len(species_list)}] {species_id} ({sci_name})")

        # Find node
        node_uuid = find_node_uuid(sci_name)
        if not node_uuid:
            # Try genus only
            genus = sci_name.split()[0] if " " in sci_name else sci_name
            print(f"  Not found by full name, trying genus: {genus}")
            node_uuid = find_node_uuid(genus)

        if not node_uuid:
            print(f"  FAILED: No node found on PhyloPic")
            failed.append(species_id)
            time.sleep(0.5)
            continue

        print(f"  Node UUID: {node_uuid}")

        # Find best image
        result = find_best_image(node_uuid, max_depth=4)
        if not result:
            print(f"  FAILED: No image found")
            failed.append(species_id)
            time.sleep(0.5)
            continue

        url, title, license_url, file_type = result
        ext = "svg" if file_type == "svg" else "png"
        dest = OUTPUT_DIR / f"{species_id}.{ext}"

        print(f"  Image: {title} ({file_type})")
        print(f"  License: {license_url}")
        print(f"  URL: {url}")

        if download_file(url, dest):
            print(f"  Saved: {dest.name}")
            results.append({
                "species_id": species_id,
                "scientific_name": sci_name,
                "file": dest.name,
                "type": file_type,
                "source_url": url,
                "title": title,
                "license": license_url,
            })
        else:
            failed.append(species_id)

        time.sleep(0.5)

    # Write attribution log
    attr_file = OUTPUT_DIR / "ATTRIBUTION.json"
    attr_file.write_text(json.dumps(results, indent=2))
    print(f"\n{'='*60}")
    print(f"Downloaded: {len(results)}/{len(species_list)}")
    print(f"Failed: {len(failed)} — {failed}")
    print(f"Attribution log: {attr_file}")


if __name__ == "__main__":
    main()
