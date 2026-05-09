"""Resolve and validate UniProt IDs and AlphaFold availability for all genes.

Reads gene_properties.csv + gene_species.csv + species.csv, queries UniProt and
AlphaFold REST APIs, and writes validated protein_id / id_type back to
gene_properties.csv.  Genes whose UniProt accession cannot be confirmed get
their protein_id cleared so the UI hides the link instead of showing a broken
text-search URL.

Usage::

    uv run resolve-proteins            # resolve & validate, update CSV
    uv run resolve-proteins --dry-run  # show what would change, don't write
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import httpx
import polars as pl
import typer

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "input"
GENE_PROPS_PATH = DATA_DIR / "gene_properties.csv"
SPECIES_PATH = DATA_DIR / "species.csv"
GENE_SPECIES_PATH = DATA_DIR / "gene_species.csv"

UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_ENTRY = "https://rest.uniprot.org/uniprotkb/{accession}.json"
ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction/{accession}"

_GENE_NAME_OVERRIDES: dict[str, list[str]] = {
    "smedwi": ["Smedwi-2", "piwi"],
    "ppri_ppra": ["PprI"],
    "pot1_turritopsis": ["POT1"],
    "clock_bmal1_dolphin": ["CLOCK"],
    "mb_seal": ["MB"],
    "tp53_rtg9": ["p53"],
    "greenland_shark_repair": ["TP53", "p53"],
    "hsf1_pv": ["HSF1"],
    "tps_pv": ["TPS1", "trehalose-6-phosphate synthase"],
    "cbp_gecko": ["CREBBP", "CBP"],
    "prestin_echo": ["SLC26A5", "Prestin"],
    "sting_bat": ["STING", "STING1", "TMEM173"],
    "cry4a_robin": ["CRY4", "CRY4a"],
    "pvlea": ["PvLEA", "LEA"],
    "pvpimt": ["PvPIMT", "PIMT"],
    "tdr1": ["TDR1"],
    "reflectin": ["Reflectin", "reflectin A"],
}

_SKIP_GENES: set[str] = {
    "melanin_pathway",
    "tapetum",
    "acomys_regen",
}


def _load_species_lookup() -> dict[str, str]:
    """species_id → scientific_name."""
    df = pl.read_csv(SPECIES_PATH).select(["species_id", "scientific_name"])
    return {r["species_id"]: r["scientific_name"] for r in df.to_dicts()}


def _load_gene_species() -> dict[str, list[str]]:
    """gene_id → [species_id, ...]."""
    df = pl.read_csv(GENE_SPECIES_PATH)
    result: dict[str, list[str]] = {}
    for r in df.to_dicts():
        result.setdefault(r["gene_id"].strip(), []).append(r["species_id"].strip())
    return result


def _validate_uniprot(client: httpx.Client, accession: str) -> bool:
    """Return True if a UniProt accession resolves to a real entry."""
    url = UNIPROT_ENTRY.format(accession=accession)
    resp = client.get(url, follow_redirects=True)
    return resp.status_code == 200


def _check_alphafold(client: httpx.Client, accession: str) -> bool:
    """Return True if AlphaFold has a predicted structure for this UniProt accession."""
    url = ALPHAFOLD_API.format(accession=accession)
    resp = client.get(url, follow_redirects=True)
    return resp.status_code == 200


def _search_uniprot(
    client: httpx.Client,
    gene_name: str,
    scientific_name: str,
    use_gene_field: bool = True,
) -> str | None:
    """Search UniProt for a gene+organism and return the best accession, or None.

    When *use_gene_field* is True, searches the ``gene:`` field specifically.
    When False, does a full-text search (catches protein names, synonyms, etc.).
    """
    if use_gene_field:
        query = f'(gene:"{gene_name}") AND (organism_name:"{scientific_name}")'
    else:
        query = f'{gene_name} AND (organism_name:"{scientific_name}")'
    params = {
        "query": query,
        "format": "json",
        "size": "5",
        "fields": "accession,gene_names,organism_name,protein_existence",
    }
    resp = client.get(UNIPROT_SEARCH, params=params, follow_redirects=True)
    if resp.status_code != 200:
        log.warning("UniProt search HTTP %d for %s / %s", resp.status_code, gene_name, scientific_name)
        return None
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None

    reviewed = [r for r in results if r.get("entryType") == "UniProtKB reviewed (Swiss-Prot)"]
    best = reviewed[0] if reviewed else results[0]
    return best.get("primaryAccession")


def _gene_search_names(gene_id: str, gene_display: str) -> list[str]:
    """Return a list of gene name variants to try, in priority order."""
    if gene_id in _GENE_NAME_OVERRIDES:
        return _GENE_NAME_OVERRIDES[gene_id]
    name = gene_display.strip()
    primary = name.split("/")[0].strip().split("(")[0].strip()
    return [primary]


app = typer.Typer()


@app.command()
def resolve(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print changes without writing CSV"),
) -> None:
    """Resolve and validate UniProt protein IDs for all genes."""
    props_df = pl.read_csv(GENE_PROPS_PATH)
    species_lookup = _load_species_lookup()
    gene_species = _load_gene_species()

    rows = props_df.to_dicts()
    changes: list[str] = []

    with httpx.Client(timeout=15.0, headers={"User-Agent": "materialized-enhancements/1.0"}) as client:
        for row in rows:
            gene_id = row["gene_id"].strip()
            gene_display = str(row.get("gene", "")).strip()
            existing_pid = str(row.get("protein_id") or "").strip()
            existing_idt = str(row.get("id_type") or "").strip()

            if gene_id in _SKIP_GENES:
                log.info("%-30s SKIP (non-protein gene)", gene_id)
                continue

            sids = gene_species.get(gene_id, [])
            sci_names = [species_lookup[s] for s in sids if s in species_lookup]

            if existing_pid and existing_idt == "uniprot":
                valid = _validate_uniprot(client, existing_pid)
                if valid:
                    has_af = _check_alphafold(client, existing_pid)
                    log.info("%-30s VALID  %s  alphafold=%s", gene_id, existing_pid, has_af)
                else:
                    log.warning("%-30s INVALID UniProt %s — clearing", gene_id, existing_pid)
                    changes.append(f"{gene_id}: cleared invalid UniProt {existing_pid}")
                    row["protein_id"] = ""
                    row["id_type"] = ""
                time.sleep(0.3)
                continue

            search_names = _gene_search_names(gene_id, gene_display)
            resolved = None
            winning_query = ""
            for name_variant in search_names:
                for sci_name in sci_names:
                    resolved = _search_uniprot(client, name_variant, sci_name, use_gene_field=True)
                    if resolved:
                        winning_query = f"gene:{name_variant}"
                        break
                    time.sleep(0.2)
                if resolved:
                    break

            if not resolved:
                for name_variant in search_names:
                    for sci_name in sci_names:
                        resolved = _search_uniprot(client, name_variant, sci_name, use_gene_field=False)
                        if resolved:
                            winning_query = f"text:{name_variant}"
                            break
                        time.sleep(0.2)
                    if resolved:
                        break

            if resolved:
                valid = _validate_uniprot(client, resolved)
                if valid:
                    has_af = _check_alphafold(client, resolved)
                    log.info("%-30s RESOLVED %s via %s (%s)  alphafold=%s",
                             gene_id, resolved, winning_query, sci_names[0] if sci_names else "?", has_af)
                    changes.append(f"{gene_id}: resolved → {resolved}")
                    row["protein_id"] = resolved
                    row["id_type"] = "uniprot"
                else:
                    log.warning("%-30s resolved %s but validation failed", gene_id, resolved)
            else:
                log.warning("%-30s NOT FOUND (tried %s in %s)", gene_id, search_names, sci_names)
                row["protein_id"] = ""
                row["id_type"] = ""

            time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"Changes: {len(changes)}")
    for c in changes:
        print(f"  {c}")

    if not dry_run and changes:
        out_df = pl.DataFrame(rows, schema=props_df.schema)
        out_df.write_csv(GENE_PROPS_PATH)
        print(f"\nWritten to {GENE_PROPS_PATH}")
    elif dry_run:
        print("\n(dry-run mode — no files written)")


def main() -> None:
    app()
