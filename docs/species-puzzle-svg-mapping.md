# Species ↔ silhouette art (current state)

How species silhouette art is mapped and served **today**, after consolidation
to a single source of truth. This describes what the code and tree actually do —
no migration history.

---

## Single source of truth

- **Canonical art:** one SVG per species at **`assets/species_svg/<species_id>.svg`**
  (39 files). Reflex ships `assets/`, so these are served at **`/species_svg/<species_id>.svg`**
  (and mirrored into `.web/public/species_svg/` at build time).
- **Mapping CSV:** **`data/input/species_svg_map.csv`** — the only species→art map.
  `puzzle.py` reads it at import; no silhouette mapping is hardcoded in Python.
- **Provenance & licensing:** **`docs/species_svg_attribution.md`** (human-readable),
  backed by the `phylopic_uuid` / `phylopic_title` / `license` columns of the CSV.

There is exactly one copy of each silhouette and one layered jigsaw composite
(`data/input/puzzle/ALL_ANIMALS.svg`, below). No `phylopic/` subtrees, no
duplicate `assets/` ↔ `data/input/` art folders, no per-species PNGs.

---

## `data/input/species_svg_map.csv`

One row per species. Columns:

| Column | Role |
|---|---|
| `species_id` | snake_case slug; primary key, also the SVG basename |
| `common_name`, `scientific_name` | display names |
| `kingdom`, `phylum`, `class`, `order`, `family` | taxonomy (for grouping/justification) |
| `ui_svg_path` | documented canonical path (`assets/species_svg/<id>.svg`) |
| `ui_svg_type` | provenance kind — `phylopic` for all 39 (every silhouette is now sourced from PhyloPic) |
| `jigsaw_layer` | Inkscape layer label inside `ALL_ANIMALS.svg` (or `0_base` for human) |
| `phylopic_uuid`, `phylopic_title` | PhyloPic source image (every row has one) |
| `license` | CC license of the silhouette |
| `similar_to` | species sharing a near-identical silhouette (informational) |
| `flag` | `ok` for all 39 (the former `special` mark on `homo_sapiens` was retired) |
| `notes` | per-mapping rationale |

The code derives the served path as `species_svg/{species_id}.svg`; it does not
read `ui_svg_path` (that column documents the same fact for humans).

---

## `puzzle.py` — what the CSV becomes

Loaded once at import from `data/input/species_svg_map.csv`:

- **`SPECIES_SVG_DF`** / **`SPECIES_SVG_MAP`** — the raw frame and a `species_id → row` dict.
- **`_SPECIES_PUZZLE_MAP`** — `species_id → "species_svg/<id>.svg"` for every row not
  flagged `special` (none are now, so **all 39** including `homo_sapiens` are mapped).
  The `flag != "special"` filter is kept as a defensive guard.
- **`_GENE_PUZZLE_OVERRIDE`** — gene-level override, currently
  `{"epas1_tibetan": "species_svg/homo_sapiens.svg"}` (now resolves to the same file
  the species walk would return; kept explicit).
- **`_SPECIES_LAYER_MAP`** — `species_id → jigsaw_layer` for rows with a non-empty
  `jigsaw_layer` other than `0_base`; used only by the jigsaw composer. `homo_sapiens`
  (`0_base`) is excluded here — that is the puzzle's only human exception.

**`resolve_puzzle_svg(gene_id, species_ids)`**:

1. If `gene_id` is in `_GENE_PUZZLE_OVERRIDE`, return that path immediately.
2. Otherwise walk `species_ids` in order; return the first `"species_svg/<id>.svg"`
   found in `_SPECIES_PUZZLE_MAP`.
3. Return `""` only if no species matches. Human-only genes now resolve to
   `species_svg/homo_sapiens.svg` (the Homo longi silhouette) like any other species.

---

## How art reaches the UI / reports

1. **`gene_data.py`** calls `resolve_puzzle_svg(gene_id, species_ids)` — with
   `species_ids` taken from `gene_species.csv` in row order — and stores the result
   as **`puzzle_svg`** on every `GeneEntry` and per-species animal row.
2. **`state.py`** exposes **`puzzle_src`** = `"/" + quote(puzzle_svg)` when
   `puzzle_svg` is non-empty → e.g. **`/species_svg/mus_musculus.svg`**. (No `/puzzle/`
   prefix anymore.)
3. **`pages/index.py`** renders `puzzle_src` directly in `<img src=...>` for gene
   cards and animal rows, and passes it through as the `data-puzzle-src` attribute
   on report rows (≈ `index.py:8089`).
4. **`assets/vendor/me_report.js`** reads `data-puzzle-src`, runs it through
   `localAssetUrl()` (`window.location.origin + puzzleSrc`), and rasterizes it for
   the PDF/PNG export.

All four steps use the single `assets/species_svg/` file; nothing reads art from
`data/input/`.

---

## Layered jigsaw composite (dormant)

- **`data/input/puzzle/ALL_ANIMALS.svg`** is the single master SVG with one Inkscape
  layer per species plus a `0_base` human silhouette. `puzzle.py` reads it via
  **`ALL_ANIMALS_SVG_PATH`** into module-level **`_ALL_ANIMALS_SVG_RAW`**.
- **`build_jigsaw_svg(selected_species_ids, bold_base=False)`** returns a filtered SVG
  keeping `0_base` + the layers named in `_SPECIES_LAYER_MAP` for the selected species.
  It does **not** touch `assets/species_svg/`.
- **Status: dormant.** The only browser reference is `_jigsaw_artifact_preview()` in
  `pages/index.py` (`src="/puzzle/ALL_ANIMALS.svg"`), and that function is defined but
  never called. Note: `ALL_ANIMALS.svg` lives under `data/input/`, which Reflex does
  **not** serve, so that `/puzzle/...` URL will not resolve until the jigsaw is rewired
  (serving the file from `assets/` or pointing the `<img>` elsewhere).

---

## Join CSVs

- **`data/input/species.csv`** — `species_id` (primary key) + display/taxonomy metadata.
  No art path; linkage to art is only via `species_id`.
- **`data/input/gene_species.csv`** — `gene_id, species_id` many-to-many. `gene_data.py`
  builds `gene_id → [species_id, …]` in CSV row order, which sets the precedence used by
  `resolve_puzzle_svg` for multi-species genes.

---

## Tests

- **`tests/test_puzzle_organisms.py`** — non-human animals have a non-empty `puzzle_svg`;
  any `jigsaw_layer` referenced is present in `ALL_ANIMALS.svg`; and `homo_sapiens` both
  carries the `species_svg/homo_sapiens.svg` silhouette and composes to only the `0_base`
  layer in the jigsaw.

---

## `scripts/download_phylopic.py` (CSV-driven regeneration)

A Typer CLI that regenerates **the entire** silhouette set from
`data/input/species_svg_map.csv`. For each row with `ui_svg_type == "phylopic"` (all 39)
it downloads the recorded `phylopic_uuid` — trying the contributor's `source.svg` first,
then the potrace `vector.svg` — into `assets/species_svg/<species_id>.svg`. The
`flag == "special"` and `ui_svg_type != "phylopic"` filters remain as defensive guards
but currently exclude nothing.

- `uv run python scripts/download_phylopic.py` — write into `assets/species_svg/`
- `uv run python scripts/download_phylopic.py --check` — download to a scratch dir and
  diff against the committed set without overwriting
- `uv run python scripts/download_phylopic.py --species <id>` — single species

`--check` reproduces **all 39** files byte-identically. The hand-drawn jigsaw pieces that
formerly backed 25 of these species are not lost — they survive as the named layers inside
`ALL_ANIMALS.svg`, and each row's `notes`/`jigsaw_layer` records which layer.
