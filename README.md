# Materialized Enhancements

> **Build your post-human character from real genes — tardigrade radiation shields, naked-mole-rat cancer resistance, Greenland shark longevity — backed by scientific evidence tiers and real citations — and 3D-print the result.**

An RPG-style character creator for speculative human enhancement. Spend enhancement credits on real genes from extraordinary organisms, watch your profile light up by category, then materialize the result as a unique 3D-printable artifact and a personal enhancement report.

**[Try it live](https://enhancement.bio/)** · [Project video](https://www.youtube.com/watch?v=adCYIcbR4Gs) · [Open source](https://github.com/winternewt/materialized-enchancements)

---

## Why this exists

Upgrading human DNA is not science fiction — it is already happening in adults today. In alternative jurisdictions like Prospera, medical tourists are actively receiving gene therapies for muscle growth (Follistatin) and blood vessel creation (VEGF). The next decade will bring harder questions about what traits people might choose. Nature has already evolved extreme survival modules: tardigrade radiation shields, whale DNA repair, axolotl regeneration, bat immune tolerance, and cephalopod expression systems.

**Materialized Enhancements** turns that biology into a playful experience. Learn real genetics along the way: every gene card cites peer-reviewed papers with DOIs, shows a tiered evidence grade (T2–T6), and is upfront about contradictions and translational gaps. Pick your favourites, then take home a unique souvenir — a 3D-printable form and a personal report generated from your choices.

---

## How to play

1. **Name your character** — pick a name for your future self.
2. **Spend enhancement credits** — browse the gene library grouped by category (Stress Resistance, Longevity & Genome, Regeneration, Environmental Adaptation, Perception, Expression). Each gene comes from a real organism and costs credits based on evidence strength.
3. **Watch your profile light up** — the human silhouette fills in by category as you build your loadout.
4. **Materialize** — generate a deterministic 3D-printable STL from the selected genes and your name. The geometry is driven by real protein properties (molecular weight, exon count, hydropathy, system size).
5. **Review and share** — inspect front/side/back captures, download STL + params, export a square PNG or A4 PDF report, and optionally create a public report link with social previews.

---

## Gene Library

55 genes · 6 parent categories · 39 source species spanning microbes, animals, fungi, humans, and archaic-human ancestry.

| Category | Genes | Example organisms |
|---|---|---|
| Environmental Adaptation | 12 | Sperm whale, Arctic ground squirrel, Egyptian mongoose |
| Longevity & Genome | 11 | Greenland shark, Bowhead whale, Naked mole-rat |
| Stress Resistance | 8 | Tardigrade, Deinococcus, Sleeping chironomid |
| Regeneration | 8 | Axolotl, Planarian, Spiny mouse |
| Perception | 8 | Little skate, Budgerigar, Pit viper |
| Expression | 8 | Golden silk orbweaver, Deathstalker scorpion, Firefly |

Each gene has an **evidence tier** (T2–T6), a **confidence level**, quantified achievements with citations, and honest notes about limitations, contradictions, and translational gaps.

### Data schema

Gene data lives in six CSV files under `data/input/`, organized like a relational database. Adding or editing genes requires **zero Python changes** — just edit the CSVs.

#### Entity-relationship overview

```
                         ┌────────────────┐
species.csv              │ gene_library   │         gene_properties.csv
┌────────────┐           │────────────────│         ┌─────────────────┐
│ species_id │◄──┐       │ gene_id    (PK)├────────►│ gene_id     (FK)│
│ common_name│   │       │ Gene           │    1:1  │ protein_mass_kda│
│ sci_name   │   │       │ Category       │         │ gene_price      │
│ taxonomy…  │   │       │ Subcategory    │         │ …biophysical    │
│ life-hist… │   │       │ Narrative      │         └─────────────────┘
└────────────┘   │       │ Mechanism      │
       ▲         │       │ Evidence Tier  │         gene_confidence.csv
       │         │       │ References     │         ┌─────────────────┐
gene_species.csv │       │ …              ├ ─ ─ ─ ►│ gene_id     (FK)│
┌────────────┐   │       └────────────────┘  1:N   │ value           │
│ gene_id(FK)├───┤              │ (optional)        │ argument        │
│species_id  ├───┘              │                   └─────────────────┘
│ (many:many)│                  │
└────────────┘                  │                   gene_testing.csv
                                │  (optional)       ┌─────────────────┐
                                └ ─ ─ ─ ─ ─ ─ ─ ─ ►│ gene_id     (FK)│
                                             1:N    │ host, delivery  │
                                                    │ key_result      │
                                                    │ doi, year       │
                                                    └─────────────────┘

─────► = required FK (app fails at startup if missing)
─ ─ ─► = optional FK (app runs without rows for a gene)
```

#### Table: `gene_library.csv` — gene metadata (source of truth)

| Column | Required | Description |
|---|---|---|
| `gene_id` | **PK** | Unique slug, e.g. `dsup`, `has2_nmr`. Used as join key everywhere. |
| `Gene` | yes | Display name, e.g. `Dsup`, `HAS2` |
| `Manipulation` | yes | How the gene is used: `Overexpression`, `Knockout`, `Base editing knockout`, etc. |
| `Category` | yes | One of 6 parent categories: `Stress Resistance`, `Longevity & Genome`, `Regeneration`, `Environmental Adaptation`, `Perception`, `Expression` |
| `Subcategory` | yes | Specific trait within the category, e.g. `Radiation Shielding`, `Hyaluronic Acid` |
| `Narrative` | yes | 150–300 word biological story. Honest about contradictions — not hype. |
| `Short Description` | yes | 1–2 sentence plain-language summary |
| `Mechanism` | yes | Molecular mechanism of action |
| `Achievements (effect sizes)` | yes | Quantified experimental results with citations |
| `Highest Evidence Tier` | yes | `T1`–`T7` (T7 = association only, T6 = ≥4 independent labs, T5 = in-vivo mammal, T4 = in-vivo non-mammal, T3 = cell culture, T2 = computational, T1 = theoretical). Compound tiers like `T4 (human U2OS cell expression) + T3 (cross-species)` are allowed. |
| `Translational Gaps` | yes | What research is still needed |
| `Key References (DOIs)` | yes | Pipe-separated `Author Year URL` entries |
| `Notes (limitations, contradictions, caveats)` | yes | Caveats, contradictions between studies, known failure modes |
| `Secondary Categories` | optional | Pipe-separated additional parent category names for cross-cutting genes |

#### Table: `species.csv` — organism lookup

| Column | Required | Description |
|---|---|---|
| `species_id` | **PK** | Snake_case slug, e.g. `ramazzottius_varieornatus`, `heterocephalus_glaber` |
| `scientific_name` | yes | Binomial name, e.g. `Ramazzottius varieornatus` |
| `common_name` | yes | Display name, e.g. `Tardigrade`, `Naked mole-rat` |
| `genus` | yes | Taxonomic genus |
| `species` | yes | Taxonomic species epithet |
| `kingdom` | yes | e.g. `Animalia` |
| `phylum` | yes | e.g. `Chordata`, `Tardigrada` |
| `class` | yes | Taxonomic class |
| `order` | yes | Taxonomic order |
| `family` | yes | Taxonomic family |
| `max_longevity_years` | optional | Maximum recorded lifespan in years (from [AnAge](https://genomics.senescence.info/species/)) |
| `adult_weight_g` | optional | Typical adult body weight in grams |
| `metabolic_rate_w` | optional | Metabolic rate in watts |
| `body_mass_g` | optional | Body mass used for allometric scaling |
| `temperature_k` | optional | Body temperature in kelvin |
| `female_maturity_days` | optional | Days to female sexual maturity |
| `male_maturity_days` | optional | Days to male sexual maturity |
| `gestation_days` | optional | Gestation period in days |
| `imr_per_year` | optional | Initial mortality rate per year |
| `mrdt_years` | optional | Mortality rate doubling time in years |
| `url` | optional | Wikipedia or reference URL for the species |

#### Table: `gene_species.csv` — many-to-many join

| Column | Required | Description |
|---|---|---|
| `gene_id` | **FK** | References `gene_library.csv → gene_id` |
| `species_id` | **FK** | References `species.csv → species_id` |

One row per gene–species link. Multi-species genes (e.g. a gene studied in both mouse and fly) have multiple rows.

#### Table: `gene_properties.csv` — pricing & biophysical data

| Column | Required | Description |
|---|---|---|
| `gene_id` | **FK** | References `gene_library.csv → gene_id` |
| `gene` | yes | Display name (must match `gene_library.csv → Gene`) |
| `protein_id` | yes | UniProt/NCBI accession |
| `id_type` | yes | `uniprot` or `ncbi` |
| `reference_protein` | yes | Protein name for the reference entry |
| `protein_length_aa` | yes | Protein length in amino acids |
| `protein_mass_kda` | yes | Protein mass in kilodaltons |
| `exon_count` | yes | Number of exons in the gene |
| `genes_in_system` | yes | Gene count in the functional system |
| `recipient_organism_count` | yes | Number of organisms this gene has been tested in |
| `disorder_pct` | yes | Intrinsic disorder percentage (0–100) |
| `isoelectric_point_pI` | yes | Isoelectric point |
| `gravy_score` | yes | GRAVY hydropathy score |
| `key_publication_year` | yes | Year of the key publication |
| `category` | yes | Parent category (must match `gene_library.csv → Category`) |
| `gene_price` | yes | Enhancement credit cost (positive integer) |

#### Table: `gene_confidence.csv` — confidence assessments

| Column | Required | Description |
|---|---|---|
| `gene_id` | **FK** | References `gene_library.csv → gene_id` |
| `value` | yes | Confidence level: `Low`, `Low-Medium`, `Medium-Low`, `Medium`, `Medium-High`, `High`, `Very High`, `N/A`, or `Declining` |
| `argument` | optional | Reasoning for the assessment |
| `description` | optional | Extended explanation |

Multiple rows per gene are allowed (e.g. different assessors or dimensions).

#### Table: `gene_testing.csv` — experimental evidence records

| Column | Required | Description |
|---|---|---|
| `gene_id` | **FK** | References `gene_library.csv → gene_id` |
| `host` | yes | Test organism, e.g. `Human`, `Mouse`, `C. elegans` |
| `tissue_or_system` | yes | Tissue/cell type tested, e.g. `cell_line (HEK293)`, `whole_organism` |
| `intervention` | yes | e.g. `overexpression`, `knockout`, `mRNA delivery` |
| `delivery` | yes | e.g. `stable_transfection`, `LNP`, `AAV` |
| `integration` | yes | `stable`, `transient`, `episomal` |
| `key_result` | yes | Main finding in one sentence |
| `effect_size` | optional | Quantified effect, e.g. `~50% SSB reduction at 10 Gy` |
| `positive` | yes | `true` if the result supports the gene's intended effect |
| `reference_short` | yes | Short citation, e.g. `Hashimoto 2016 Nat Commun` |
| `doi` | yes | DOI URL |
| `year` | yes | Publication year |

Multiple rows per gene — each row is one independent experiment/study.

All files under `data/input/` are local runtime inputs and gitignored.

---

## How the 3D model works

Your name is hashed and XORed with your category bitmask to produce a unique seed. Real protein properties from your selected genes — molecular weight, exon count, GRAVY score, system size — are normalized into parameters that control a Voronoi-based parametric sculpture: radius, layer spacing, surface detail, and extrusion depth. The result is a printable STL that is deterministic and reproducible from the same inputs.

![Materialized Enhancements — process flow from trait input through parametric logic to STL and physical fabrication](assets/images/HOW_IT_WORKS.jpg)

---

## Running

```bash
git lfs install        # one-time: enable Git LFS (PDB + STL files)
git lfs pull           # fetch binary assets if cloned without LFS
uv run start           # development mode (hot-reload)
uv run serve           # production mode (single-port, Reflex 0.9+)
```

Copy `.env.template` to `.env` to override defaults (email delivery, deploy URL, kiosk settings). For production, set `DEPLOY_URL` to your public domain so QR codes, report links, and social shares use absolute URLs.

### Binary assets (Git LFS)

Protein structure files (`assets/structures/*.pdb`) and 3D-printable STL meshes (`assets/stl/*.stl`) are tracked with [Git LFS](https://git-lfs.com/). After cloning, run `git lfs pull` to download them. To regenerate STLs from PDB sources: `uv run stl generate --all`.

---

## App Layout

| Route | Tab | Purpose |
|---|---|---|
| `/` | **Character Profile** | Name your character, spend the 100 cr enhancement budget, browse the gene library |
| `/materialization` | **Materialization** | 3D viewer, STL/params downloads, report customization, PNG/PDF exports, public report link |
| `/about` | **About** | Project story, video, team, support links |

---

## Contributing a New Gene

Scientists and biologists can propose new genes — **no Python code changes needed**. The app reads everything from the CSV files at startup.

### Step-by-step

1. **Choose a `gene_id`** — a unique snake_case slug (e.g. `klotho_overexp`, `p53_elephant`). This is the primary key used across all tables.

2. **Add the source species** to `species.csv` (skip if the species already exists):
   - Use the scientific name in snake_case as `species_id` (e.g. `elephas_maximus`)
   - Fill taxonomy columns from [AnAge](https://genomics.senescence.info/species/) or NCBI Taxonomy
   - Life-history fields are optional but enrich the species card

3. **Add the gene row** to `gene_library.csv`:
   - Assign one of the 6 parent categories and a specific subcategory (trait)
   - Write the `Narrative` (150–300 words): describe the biology, cite the strongest evidence with effect sizes, be honest about contradictions and limitations
   - Set `Highest Evidence Tier`: T7 (association only) → T6 (≥4 independent labs) → T5 (in-vivo mammal) → T4 (in-vivo non-mammal) → T3 (cell culture) → T2 (computational) → T1 (theoretical)
   - Fill all required columns (see schema above)

4. **Link gene to species** in `gene_species.csv`:
   - Add one row per source species: `gene_id,species_id`
   - Multi-species genes get multiple rows

5. **Add pricing & protein data** to `gene_properties.csv`:
   - Look up protein data from UniProt or NCBI
   - Set `gene_price` (positive integer, typically 1–15 cr)

6. **Add confidence assessment** to `gene_confidence.csv`:
   - At minimum: `gene_id,value` (e.g. `klotho_overexp,Medium-High`)

7. **Add experimental evidence** to `gene_testing.csv`:
   - One row per independent experiment/study
   - Include both positive and negative results (`positive` = `true` or `false`)

8. **Test locally**: `uv run start` — the app should show the new gene in the correct category

### Writing guidelines

- Be honest about contradictions and limitations — mention failed replications and tissue-specific effects
- Lead with the strongest experimental evidence and include quantified effect sizes
- End on a realistic assessment, not hype
- Use DOIs for all references

### Integrity checks

The app enforces at startup:
- Every `gene_id` in `gene_library.csv` must have a matching row in `gene_properties.csv` with `gene_price > 0`
- Every `species_id` referenced in `gene_species.csv` must exist in `species.csv`

---

## Generated Reports & Sharing

The Materialization tab has two link types:

- **Recreate URL** — a deterministic `/materialization?report=1&name=<b64>&cats=<bitmask>&genes=<b64-json-list>` URL that rebuilds the same character from the name, selected categories, and exact checked genes.
- **Public report link** — a generated `/generated/reports/<slug>/index.html` landing page with social metadata and downloadable artifacts.

Exports stay local until the visitor clicks **Create public link**. That action writes a public report folder with:

- `index.html` — crawler-friendly page with Open Graph/Twitter metadata
- `model.stl` — the printable sculpture
- `params.json` — strongest saved reproduction artifact, including selected categories, checked genes, sculpture parameters, and the recreate URL
- `report.webp` — square social preview card (WebP for smaller size with transparency)
- `report.pdf` — A4 personal enhancement report

QR, copy, and social sharing buttons use the public report link after it exists. Before publication, the PDF still embeds the recreate URL so the character selection can be opened again. Reports are generated in the browser using vendored JS (`html-to-image`, `jsPDF`, `qrcode`) — no server-side image dependencies.

---

## Email Delivery

The **Send STL + report** feature delivers the artifact bundle to the visitor's inbox via [Resend](https://resend.com). Set `RESEND_API_KEY` in `.env`. See [`.env.template`](.env.template) for full configuration.

---

## Venue & Kiosk Integration

For physical installations, the app supports kiosk mode with ARTEX venue display integration (send sculptures to a physical display wall in real time). See [`docs/ARTEX_INTEGRATION.md`](docs/ARTEX_INTEGRATION.md) for setup, kiosk URL parameters, idle timer configuration, and the full ARTEX pipeline.

---

## Team

- **Newton Winter** — web app, RPG interface, geometry optimization, devops, biology, UI — [GitHub @winternewt](https://github.com/winternewt)
- **Anton Kulaga** — concept, biology, UI design, generative video, 3D printing — [GitHub @antonkulaga](https://github.com/antonkulaga)
- **Livia Zaharia** — parametric geometry, personalized enhancement report, 3D printing — [livia.glucosedao.org](http://livia.glucosedao.org/)
- **Marko Prakhov-Donets** — video editing

Started at CODAME ART+TECH 『 The New Human 』 in Milano, now developed by the joint [GlucoseDAO](https://glucosedao.org) and [Longevity Genie](https://longevity-genie.info) team.

The project is **open source** ([repository](https://github.com/winternewt/materialized-enchancements)) and built so other artists can plug their own generative models into the same biological input engine.

### Gratitudes

- **[hidoba](https://github.com/hidoba)** — interface advice and help with Milan Design Week

---

## Tech Stack

- **Frontend**: [Reflex](https://reflex.dev/) + Fomantic UI (RPG-style character builder)
- **Data**: Polars loaders over CSV gene/species/properties tables
- **3D generation**: Python parametric geometry pipeline (`sculpture.py`)
- **Reports**: browser-side `html-to-image`, `jsPDF`, QR generation
- **Email**: [Resend](https://resend.com) HTTPS API
- **Venue**: [ARTEX Platform API](https://github.com/CODAME/artex-open) (optional)
- **Deps**: uv, python-dotenv

---

## Attributions

Organism silhouette artwork is sourced from [PhyloPic](https://www.phylopic.org/). Silhouettes with specific attribution requirements are listed in [`animals_phylopic.md`](animals_phylopic.md).

Jigsaw prototype tools: [CustomShapeJigsawJs](https://github.com/proceduraljigsaw/CustomShapeJigsawJs) (MIT), [svg_extrude](https://github.com/deffi/svg_extrude) (AGPL-3.0).
