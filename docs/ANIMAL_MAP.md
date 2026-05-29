# Animal Map — Species → SVG Silhouette Mapping

**Single source of truth for which SVG represents each species, where it came from, and why.**

| Resource | Path |
|----------|------|
| **Canonical SVGs** | `assets/species_svg/<species_id>.svg` (39 files, one per species) |
| **Attribution** | `docs/species_svg_attribution.md` (single source of truth) |
| Machine-readable map | `data/input/species_svg_map.csv` |
| Species master | `data/input/species.csv` |
| Gene assignments | `data/input/gene_species.csv` |
| Runtime UI map | `src/materialized_enhancements/puzzle.py` → `_SPECIES_PUZZLE_MAP` (derived from CSV) |
| Jigsaw layer map | `src/materialized_enhancements/puzzle.py` → `_SPECIES_LAYER_MAP` (derived from CSV) |

---

## Two source pools

### Pool A — Numbered jigsaw artwork (hand-drawn puzzle pieces)

Original hand-crafted SVGs for the 28-piece jigsaw puzzle, located in `assets/puzzle/`.
Each was derived from a specific PhyloPic image (documented in `animals_phylopic.md`).
These are the preferred source where they exist, because they were made for this project.

### Pool B — PhyloPic downloads

SVGs (and PNGs) downloaded by `scripts/download_phylopic.py` into `assets/puzzle/phylopic/`.
Used for species added after the original 28-piece set, and for the three new SVGs downloaded below.
Attributions recorded in `assets/puzzle/phylopic/ATTRIBUTION.json`.

### Resolution for the `assets/species_svg/` folder

| Case | Source chosen | Reason |
|------|--------------|--------|
| Species has a numbered jigsaw SVG | Pool A (numbered) | Project-original artwork |
| Species added after puzzle v1 | Pool B (phylopic SVG) | No jigsaw piece exists |
| Species had PNG-only in phylopic + vector SVG exists on PhyloPic | Newly downloaded vector SVG | Scalability |
| Two species share same silhouette (both Hydrozoa jellyfish) | Single file, two copies | Taxonomically justified; see notes |

---

## Taxonomy tree

```
Life
├── Bacteria
│   └── Deinococcota · Deinococci
│       └── Deinococcus radiodurans
│
├── Fungi  (Ascomycota · Dothideomycetes)
│   └── Cladosporium sphaerospermum
│
└── Animalia
    ├── Cnidaria · Hydrozoa              ← both share 8_jellyfish.svg
    │   ├── Leptothecata — Aequorea victoria
    │   └── Anthoathecatae — Turritopsis dohrnii
    │
    ├── Platyhelminthes · Rhabditophora · Tricladida
    │   └── Schmidtea mediterranea
    │
    ├── Mollusca
    │   ├── Cephalopoda — Sepia officinalis
    │   └── Bivalvia — Pinctada fucata
    │
    ├── Arthropoda
    │   ├── Insecta · Diptera            ← possible silhouette share
    │   │   ├── Drosophila melanogaster
    │   │   └── Polypedilum vanderplanki
    │   ├── Insecta · Coleoptera — Photinus pyralis
    │   ├── Arachnida · Araneae — Trichonephila clavipes
    │   ├── Arachnida · Scorpiones — Leiurus quinquestriatus
    │   └── Malacostraca · Decapoda — Homarus americanus
    │
    ├── Tardigrada — Ramazzottius varieornatus
    │
    └── Chordata
        ├── Chondrichthyes
        │   ├── Squaliformes — Somniosus microcephalus
        │   └── Rajiformes — Leucoraja erinacea
        ├── Actinopterygii
        │   ├── Gymnotiformes — Electrophorus electricus
        │   └── Pleuronectiformes — Pseudopleuronectes americanus
        ├── Amphibia
        │   ├── Caudata — Ambystoma mexicanum
        │   └── Anura — Cyclorana platycephala
        ├── Reptilia · Squamata
        │   ├── Viperidae — Crotalus atrox
        │   └── Gekkonidae — Gekko japonicus
        ├── Aves
        │   ├── Passeriformes — Erithacus rubecula
        │   └── Psittaciformes — Melopsittacus undulatus
        └── Mammalia
            ├── Rodentia
            │   ├── Muridae — Mus musculus
            │   ├── Deomyidae — Acomys cahirinus
            │   ├── Bathyergidae — Heterocephalus glaber
            │   └── Sciuridae — Urocitellus parryii
            ├── Carnivora
            │   ├── Canidae — Canis familiaris
            │   ├── Felidae — Felis catus
            │   ├── Herpestidae — Herpestes ichneumon
            │   └── Phocidae — Leptonychotes weddellii
            ├── Proboscidea — Loxodonta africana
            ├── Artiodactyla (incl. Cetacea)
            │   ├── Bovidae — Bos taurus
            │   ├── Balaenidae — Balaena mysticetus
            │   └── Delphinidae — Tursiops truncatus
            ├── Chiroptera — Pteropus alecto
            ├── Primates — Homo sapiens
            └── Diprotodontia — Potorous tridactylus
```

---

## Per-species mapping

Columns:
- **svg_file** — filename in `assets/species_svg/`
- **source** — `jigsaw` (Pool A, numbered puzzle piece) or `phylopic` (Pool B/downloaded)
- **jigsaw_origin** — numbered file copied from `assets/puzzle/` (jigsaw only)
- **phylopic_uuid** — PhyloPic image UUID
- **phylopic_url** — PhyloPic image page
- **taxon_used** — what PhyloPic labels the image (may differ from target species)
- **accuracy** — taxonomic resolution of match: `exact` · `subspecies` · `genus` · `family` · `order` · `class` · `phylum`
- **license** — image license
- **notes** — justification when accuracy < exact

### Non-Animalia

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `deinococcus_radiodurans` | Conan the Bacterium | `deinococcus_radiodurans.svg` | jigsaw | `2_Deinococcus.svg` | `40e8c1ed-c133-4930-9a9d-572d9ba8b0d5` | [phylopic](https://www.phylopic.org/images/40e8c1ed-c133-4930-9a9d-572d9ba8b0d5/) | *Deinococcus radiodurans* | **exact** | CC BY-SA 3.0 — Matt Crook | — |
| `cladosporium_sphaerospermum` | Chernobyl fungus | `cladosporium_sphaerospermum.svg` | jigsaw | `4_fungi_true.svg` | `a21310f5-2762-495d-b996-bc0bef7203fd` | [phylopic](https://www.phylopic.org/images/a21310f5-2762-495d-b996-bc0bef7203fd/) | *Schizosaccharomyces pombe* | **class** | CC0 | *Cladosporium* absent from PhyloPic. *S. pombe* (Schizosaccharomycetes, Ascomycota) is in a different class from *Cladosporium* (Dothideomycetes). A generic yeast silhouette is acceptable as a fungal icon; the gene story carries the narrative |

### Animalia — Cnidaria (Hydrozoa)

Both species share `8_jellyfish.svg`. They are in the same class (Hydrozoa) but different orders.
The jigsaw SVG (`8_jellyfish.svg`) was derived from a *Clytia hemisphaerica* image (Joseph Ryan, photo: Patrick Steinmetz; CC BY-SA 3.0). *Clytia* is in order Leptothecata.
The previous phylopic downloads (`aequorea_victoria.png`, `turritopsis_dohrnii.png`) were byte-identical fallbacks to *Narcomedusae* (UUID `ae1697f9`) — a third, unrelated Hydrozoa order — and have been superseded.

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `aequorea_victoria` | Crystal jellyfish | `aequorea_victoria.svg` | jigsaw | `8_jellyfish.svg` | `e4d57d67-c144-457a-877b-34faaaa16ed2` | [phylopic](https://www.phylopic.org/images/e4d57d67-c144-457a-877b-34faaaa16ed2/) | *Clytia hemisphaerica* | **order** | CC BY-SA 3.0 — Joseph Ryan (photo: Patrick Steinmetz) | *A. victoria* (Leptothecata, Aequoreidae) and *C. hemisphaerica* (Leptothecata, Campanulariidae) are in the same order; different family. Silhouette is visually interchangeable — all leptothecate medusae share the bell-and-tentacle body plan |
| `turritopsis_dohrnii` | Immortal jellyfish | `turritopsis_dohrnii.svg` | jigsaw | `8_jellyfish.svg` | `e4d57d67-c144-457a-877b-34faaaa16ed2` | [phylopic](https://www.phylopic.org/images/e4d57d67-c144-457a-877b-34faaaa16ed2/) | *Clytia hemisphaerica* | **class** | CC BY-SA 3.0 — Joseph Ryan (photo: Patrick Steinmetz) | *T. dohrnii* (Anthoathecatae, Oceanidae) and *C. hemisphaerica* (Leptothecata) are in different orders within class Hydrozoa. Artistically acceptable — all small Hydrozoa medusae share the bell-and-tentacle body plan |

### Animalia — Platyhelminthes · Rhabditophora · Tricladida

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `schmidtea_mediterranea` | Planarian | `schmidtea_mediterranea.svg` | jigsaw | `9_planarian.svg` | `fb16134d-47c9-42f0-bafe-f63bccf2d58b` | [phylopic](https://www.phylopic.org/images/fb16134d-47c9-42f0-bafe-f63bccf2d58b/) | *Schmidtea mediterranea* | **exact** | CC0 — Markus A. Grohme | — |

### Animalia — Mollusca

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `sepia_officinalis` | Common cuttlefish | `sepia_officinalis.svg` | jigsaw | `19_octopus.svg` | `6cbff80e-9537-4130-8397-ebbf77464ea4` | [phylopic](https://www.phylopic.org/images/6cbff80e-9537-4130-8397-ebbf77464ea4/) | *Sepia officinalis* | **exact** | CC BY 3.0 — David Sim (photo) & T. Michael Keesey (vectorization) | Note: jigsaw file is named `19_octopus.svg` but the subject is cuttlefish, not octopus — the filename is a misnomer |
| `pinctada_fucata` | Akoya pearl oyster | `pinctada_fucata.svg` | phylopic (new download) | — | `a2a342d0-e77e-4abc-8913-72b15eb9d906` | [phylopic](https://www.phylopic.org/images/a2a342d0-e77e-4abc-8913-72b15eb9d906/pinctada-fucata) | *Pinctada fucata* | **exact** | CC BY-SA 3.0 — Taro Maeda | Previously stored as PNG only; vectorized SVG downloaded directly from PhyloPic. Must credit Taro Maeda, link license, and share derivatives under same license |

### Animalia — Arthropoda · Insecta

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `drosophila_melanogaster` | Fruit fly | `drosophila_melanogaster.svg` | phylopic | — | `b5160ba3-ad86-4123-92a7-1c55122f4a6c` | [phylopic](https://www.phylopic.org/images/b5160ba3-ad86-4123-92a7-1c55122f4a6c/) | *Sophophora melanogaster* | **exact** | CC0 | PhyloPic title uses obsolete synonym *Sophophora* (now subsumed into *Drosophila*); image accurate |
| `polypedilum_vanderplanki` | Sleeping chironomid | `polypedilum_vanderplanki.svg` | phylopic (new download) | — | `af2b4c88-b61d-4343-898a-69741d883a54` | [phylopic](https://www.phylopic.org/images/af2b4c88-b61d-4343-898a-69741d883a54/chironomidae) | Chironomidae | **family** | PDM 1.0 — Melissa Ingala | *P. vanderplanki* absent from PhyloPic; family Chironomidae (non-biting midges) is the closest available silhouette. Midge and *Polypedilum* share the same slender dipteran body plan. PDM = public domain |
| `photinus_pyralis` | Firefly | `photinus_pyralis.svg` | jigsaw | `20._fireflysvg.svg` | `ae83a86e-79a8-46b5-ba0e-9d4b25bd707e` | [phylopic](https://www.phylopic.org/images/ae83a86e-79a8-46b5-ba0e-9d4b25bd707e/) | *Photinus pyralis* | **exact** | CC BY 3.0 — Melissa Broussard | — |

### Animalia — Arthropoda · Arachnida

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `trichonephila_clavipes` | Golden silk orbweaver | `trichonephila_clavipes.svg` | phylopic | — | `f152b5fb-1e9f-4d4b-864c-704a95827129` | [phylopic](https://www.phylopic.org/images/f152b5fb-1e9f-4d4b-864c-704a95827129/) | *Trichonephila clavata* | **genus** | CC BY 4.0 — Gabriela Palomo-Munoz | Congeneric orb-weaver; the genus *Trichonephila* spans similar-looking large spiders. Morphologically equivalent at silhouette resolution. Attribution required |
| `leiurus_quinquestriatus` | Deathstalker scorpion | `leiurus_quinquestriatus.svg` | phylopic (new download) | — | `4133ae32-753e-49eb-bd31-50c67634aca1` | [phylopic](https://www.phylopic.org/images/4133ae32-753e-49eb-bd31-50c67634aca1/heterometrus-laoticus) | *Heterometrus laoticus* | **order** | CC0 — Margot Michaud | *Leiurus* (Buthidae) and *Heterometrus* (Scorpionidae) are in different families but both Scorpiones. Chosen by visual match: the forward-claws + upward-curved tail posture of *Heterometrus* resembles a deathstalker in side-view silhouette. Two CC0 alternatives at same taxonomic distance also available: *Cercophonius squama* (f7c36b60, Bothriuridae) and *Protoischnurus axelrodor* (7742cd64, Hemiscorpiidae) |

### Animalia — Arthropoda · Malacostraca

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `homarus_americanus` | American lobster | `homarus_americanus.svg` | jigsaw | `26_lobster.svg` | `46f3f90b-48ee-4d25-b751-e5070e37532e` | [phylopic](https://www.phylopic.org/images/46f3f90b-48ee-4d25-b751-e5070e37532e/) | *Homarus americanus* | **exact** | CC0 / PDM — Michaël Rabiller | — |

### Animalia — Tardigrada

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `ramazzottius_varieornatus` | Tardigrade | `ramazzottius_varieornatus.svg` | jigsaw | `1_tardigrade.svg` | `1a7ba4da-a5f9-489b-b30e-8cf56d579d8f` | [phylopic](https://www.phylopic.org/images/1a7ba4da-a5f9-489b-b30e-8cf56d579d8f/) | Tardigrada | **phylum** | CC BY-NC-SA 3.0 — Mali'o Kodis (Smithsonian Institution) | No species-level silhouette in PhyloPic; phylum-level is the only option. All tardigrades have the same distinctive barrel-shaped body with 8 stubby legs. **NC-SA license: non-commercial use only; must credit Mali'o Kodis / Smithsonian; derivative works must use the same license.** |

### Animalia — Chordata · Chondrichthyes

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `somniosus_microcephalus` | Greenland shark | `somniosus_microcephalus.svg` | jigsaw | `6_shark.svg` | `081252c0-f3f3-4d9f-84bb-b9f00fcb1f5b` | [phylopic](https://www.phylopic.org/images/081252c0-f3f3-4d9f-84bb-b9f00fcb1f5b/) | *Centroscymnus* | **family** | CC0 — Margot Michaud | *Centroscymnus* (Portuguese dogfish) is in the same family Somniosidae as *Somniosus*. Sleeper shark body plan is close; both are large, deep-water Squaliformes |
| `leucoraja_erinacea` | Little skate | `leucoraja_erinacea.svg` | phylopic | — | `f1c15c22-db53-4753-837e-5bb439c591fa` | [phylopic](https://www.phylopic.org/images/f1c15c22-db53-4753-837e-5bb439c591fa/) | *Leucoraja erinacea* | **exact** | CC0 | — |

### Animalia — Chordata · Actinopterygii

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `electrophorus_electricus` | Electric eel | `electrophorus_electricus.svg` | jigsaw | `21_eel.svg` | `c931ef9c-ff5a-4b7d-96b5-80a6be323b04` | [phylopic](https://www.phylopic.org/images/c931ef9c-ff5a-4b7d-96b5-80a6be323b04/) | *Electrophorus electricus* | **exact** | CC0 — Neil Kelley | — |
| `pseudopleuronectes_americanus` | Winter flounder | `pseudopleuronectes_americanus.svg` | jigsaw | `13_fish.svg` | `83fae06d-c93d-41d6-9080-82734bc59163` | [phylopic](https://www.phylopic.org/images/83fae06d-c93d-41d6-9080-82734bc59163/) | *Pseudopleuronectes americanus* | **exact** | CC0 — Antonarctica | — |

### Animalia — Chordata · Amphibia

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `ambystoma_mexicanum` | Axolotl | `ambystoma_mexicanum.svg` | jigsaw | `10_axolotl.svg` | `575eaa51-6c9b-4d36-9881-b8463c68ebbc` | [phylopic](https://www.phylopic.org/images/575eaa51-6c9b-4d36-9881-b8463c68ebbc/) | *Ambystoma mexicanum* | **exact** | CC0 — Jake Warner | — |
| `cyclorana_platycephala` | Water-holding frog | `cyclorana_platycephala.svg` | phylopic | — | `01a21193-6599-463c-a5f0-75b6fe03189d` | [phylopic](https://www.phylopic.org/images/01a21193-6599-463c-a5f0-75b6fe03189d/) | *Leiopelma archeyi* | **order** | CC BY 3.0 — Auckland Museum & T. Michael Keesey | Direct PhyloPic SVG download. *Cyclorana* (Hylidae) absent from PhyloPic; *L. archeyi* (Leiopelmatidae) is a different family within order Anura; order-level match. Replaces previous jigsaw copy and phylopic PNG (*Litoria raniformis*) |

### Animalia — Chordata · Reptilia

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `crotalus_atrox` | Western diamondback rattlesnake | `crotalus_atrox.svg` | jigsaw | `15_Pit Viper.svg` | `8748e7ab-6dc8-4384-a72b-37361ae8f60b` | [phylopic](https://www.phylopic.org/images/8748e7ab-6dc8-4384-a72b-37361ae8f60b/) | *Crotalus atrox* | **exact** | CC BY 4.0 — Gabriela Palomo-Munoz | Attribution required |
| `gekko_japonicus` | Japanese gecko | `gekko_japonicus.svg` | jigsaw | `23_gecko.svg` | `9aca34d8-4dde-418d-9fdc-2d58b6a7b267` | [phylopic](https://www.phylopic.org/images/9aca34d8-4dde-418d-9fdc-2d58b6a7b267/) | *Gekko gecko* | **genus** | CC0 — Jose Carlos Arenas-Monroy | *G. gecko* (Tokay gecko) is the type species of the genus; same body plan as *G. japonicus* |

### Animalia — Chordata · Aves

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `erithacus_rubecula` | European robin | `erithacus_rubecula.svg` | jigsaw | `17_European Robin.svg` | `3c4ef873-76b5-473d-a740-8fcb4864462b` | [phylopic](https://www.phylopic.org/images/3c4ef873-76b5-473d-a740-8fcb4864462b/) | *Erithacus rubecula* | **exact** | CC BY 3.0 — Rebecca Groom | Attribution required |
| `melopsittacus_undulatus` | Budgerigar | `melopsittacus_undulatus.svg` | phylopic | — | `93400ea7-5b4c-4d5f-92ae-2345f228df08` | [phylopic](https://www.phylopic.org/images/93400ea7-5b4c-4d5f-92ae-2345f228df08/) | *Melopsittacus undulatus* | **exact** | CC0 | — |

### Animalia — Chordata · Mammalia · Rodentia

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `mus_musculus` | Mouse | `mus_musculus.svg` | jigsaw | `25_mouse.svg` | `6b2b98f6-f879-445f-9ac2-2c2563157025` | [phylopic](https://www.phylopic.org/images/6b2b98f6-f879-445f-9ac2-2c2563157025/) | *Mus musculus domesticus* | **subspecies** | CC0 / PDM — Madeleine Price Ball | Domestic house mouse subspecies; exact |
| `acomys_cahirinus` | Cairo spiny mouse | `acomys_cahirinus.svg` | phylopic | — | `720396f4-3d8a-41e5-9505-555964202c0c` | [phylopic](https://www.phylopic.org/images/720396f4-3d8a-41e5-9505-555964202c0c/) | *Acomys cahirinus dimidiatus* | **subspecies** | CC0 | Exact subspecies. Deomyidae (split from Muridae; Steppan & Schenk 2017), same superfamily Muroidea as *Mus musculus* — could share the mouse silhouette if this SVG is ever lost, but own file is preferred |
| `heterocephalus_glaber` | Naked mole-rat | `heterocephalus_glaber.svg` | jigsaw | `3_naked mole rat.svg` | `7a7d8226-aa19-4f6f-8afa-f039cc860d7e` | [phylopic](https://www.phylopic.org/images/7a7d8226-aa19-4f6f-8afa-f039cc860d7e/) | *Heterocephalus glaber* | **exact** | CC0 — Steven Traver | — |
| `urocitellus_parryii` | Arctic ground squirrel | `urocitellus_parryii.svg` | phylopic | — | `f4ca8082-0db0-4130-88eb-04a74e18312d` | [phylopic](https://www.phylopic.org/images/f4ca8082-0db0-4130-88eb-04a74e18312d/) | *Urocitellus beldingi* | **genus** | CC0 | Belding's ground squirrel; same genus, same stout ground-squirrel body plan |

### Animalia — Chordata · Mammalia · Carnivora

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `canis_familiaris` | Dog (Whippet) | `canis_familiaris.svg` | phylopic | — | `3c534a59-fd0c-41bb-80c7-1d18db9bae13` | [phylopic](https://www.phylopic.org/images/3c534a59-fd0c-41bb-80c7-1d18db9bae13/) | *Canis familiaris* dingo | **subspecies** | CC BY 3.0 — Sam Fraser-Smith (vectorized by T. Michael Keesey) | Dingo is *Canis familiaris dingo*, same species as domestic dog. Attribution required |
| `felis_catus` | Cat | `felis_catus.svg` | jigsaw | `18_cat.svg` | `e9f41f59-d708-47aa-a705-ba9b8826ebc6` | [phylopic](https://www.phylopic.org/images/e9f41f59-d708-47aa-a705-ba9b8826ebc6/) | *Felis lybica catus* | **subspecies** | CC0 — Steven Traver | Domestic cat subspecies; exact |
| `herpestes_ichneumon` | Egyptian mongoose | `herpestes_ichneumon.svg` | phylopic | — | `640e09b5-4e1b-4143-90c4-9ea924c8d270` | [phylopic](https://www.phylopic.org/images/640e09b5-4e1b-4143-90c4-9ea924c8d270/) | *Herpestes ichneumon* | **exact** | CC0 | — |
| `leptonychotes_weddellii` | Weddell seal | `leptonychotes_weddellii.svg` | jigsaw | `12_seal.svg` | `81814d17-9379-4358-ad92-32e92dbf35eb` | [phylopic](https://www.phylopic.org/images/81814d17-9379-4358-ad92-32e92dbf35eb/) | *Leptonychotes weddellii* | **exact** | CC BY 4.0 — Gabriela Palomo-Munoz | **Must credit contributor, link license, and indicate any changes.** |

### Animalia — Chordata · Mammalia · Other orders

| species_id | common_name | svg_file | source | jigsaw_origin | phylopic_uuid | phylopic_url | taxon_used | accuracy | license | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `loxodonta_africana` | African elephant | `loxodonta_africana.svg` | jigsaw | `5_elephant.svg` | `62398ac0-f0c3-48f8-8455-53512a05fbc4` | [phylopic](https://www.phylopic.org/images/62398ac0-f0c3-48f8-8455-53512a05fbc4/) | *Loxodonta africana africana* | **subspecies** | CC0 — Steven Traver | Exact subspecies (African bush elephant) |
| `bos_taurus` | Cattle (Belgian Blue) | `bos_taurus.svg` | phylopic | — | `0ebe16cb-4c74-4c77-9643-9e531a0840cc` | [phylopic](https://www.phylopic.org/images/0ebe16cb-4c74-4c77-9643-9e531a0840cc/) | *Bos primigenius* | **species (ancestor)** | CC BY 4.0 — Ivan Iofrida | *Bos primigenius* is the wild aurochs, direct ancestor of *Bos taurus*. Silhouette is indistinguishable at this resolution. Attribution required |
| `balaena_mysticetus` | Bowhead whale | `balaena_mysticetus.svg` | jigsaw | `7_whale.svg` | `18438875-f6e8-4e46-8fda-5a07bd4c1a85` | [phylopic](https://www.phylopic.org/images/18438875-f6e8-4e46-8fda-5a07bd4c1a85/) | *Balaena mysticetus* | **exact** | CC BY-SA 3.0 — Chris Huh | Attribution required; share-alike |
| `tursiops_truncatus` | Bottlenose dolphin | `tursiops_truncatus.svg` | jigsaw | `14_dolphin.svg` | `0b5c6b41-3a44-4c9e-869a-63ed54bf7c65` | [phylopic](https://www.phylopic.org/images/0b5c6b41-3a44-4c9e-869a-63ed54bf7c65/) | *Tursiops truncatus* | **exact** | CC BY-SA 3.0 — Chris Huh | Attribution required; share-alike |
| `pteropus_alecto` | Black flying fox | `pteropus_alecto.svg` | jigsaw | `11_bat.svg` | `e4ab0438-794b-4030-8e2a-7b5c1f23bf03` | [phylopic](https://www.phylopic.org/images/e4ab0438-794b-4030-8e2a-7b5c1f23bf03/) | *Pteropus poliocephalus* | **genus** | CC0 — Margot Michaud | Grey-headed flying fox; same genus, same large fruit bat wing morphology |
| `homo_sapiens` | Human | `homo_sapiens.svg` | jigsaw | `28_homo-longi.svg` | `f46f28c7-b3da-485e-9af0-9839b63138e0` | [phylopic](https://www.phylopic.org/images/f46f28c7-b3da-485e-9af0-9839b63138e0/) | *Homo longi* | **genus** | CC0 — T. Michael Keesey | *Homo longi* (Dragon Man, Ji & Ni 2021) is an archaic *Homo* species; genus-level match. In the UI this file is only used for `epas1_tibetan` via `_GENE_PUZZLE_OVERRIDE`; all other human genes use the base human silhouette |
| `potorous_tridactylus` | Long-nosed potoroo | `potorous_tridactylus.svg` | phylopic | — | `6354f106-3d0f-4525-b958-75bd740a19ee` | [phylopic](https://www.phylopic.org/images/6354f106-3d0f-4525-b958-75bd740a19ee/) | *Potorous tridactylus* | **exact** | CC0 | — |

---

## Taxonomic similarity groups

Species close enough to share a silhouette without materially misleading viewers.

| Shared level | Members | Verdict |
|---|---|---|
| Class Hydrozoa | *Aequorea victoria* + *Turritopsis dohrnii* | **Implemented** — both use `8_jellyfish.svg`; same class, visually interchangeable medusae. *A. victoria* is order-level match; *T. dohrnii* is class-level (different orders) |
| Superfamily Muroidea | *Mus musculus* + *Acomys cahirinus* | Possible fallback — both have own SVGs; sharing only if one is lost. Note: different families (Muridae vs Deomyidae) since Steppan & Schenk 2017 reclassification |
| Order Diptera | *Drosophila melanogaster* + *Polypedilum vanderplanki* | Acceptable — both dipterans now have distinct SVGs; chironomid midge vs fly are noticeably different shapes |
| Class Arachnida | *Trichonephila clavipes* + *Leiurus quinquestriatus* | **Not recommended** — spider vs scorpion are obviously different |
| Class Aves | *Erithacus rubecula* + *Melopsittacus undulatus* | **Not recommended** — robin vs parrot clearly differ; both have exact SVGs |

---

## License summary for required attributions

The following licenses require explicit credit in any public display.

| License | Species | Contributor | Action required |
|---|---|---|---|
| **CC BY-NC-SA 3.0** | `ramazzottius_varieornatus` | Mali'o Kodis / Smithsonian Institution | Credit contributor; **non-commercial only**; derivatives must carry same license |
| **CC BY-SA 3.0** | `deinococcus_radiodurans` | Matt Crook | Credit; share-alike |
| **CC BY-SA 3.0** | `balaena_mysticetus` | Chris Huh | Credit; share-alike |
| **CC BY-SA 3.0** | `aequorea_victoria` + `turritopsis_dohrnii` | Joseph Ryan (photo: Patrick Steinmetz) | Credit; share-alike (both share this image) |
| **CC BY-SA 3.0** | `tursiops_truncatus` | Chris Huh | Credit; share-alike |
| **CC BY-SA 3.0** | `pinctada_fucata` | Taro Maeda | Credit; share-alike; indicate changes |
| **CC BY 4.0** | `crotalus_atrox` | Gabriela Palomo-Munoz | Credit; link license; indicate changes |
| **CC BY 4.0** | `bos_taurus` | Ivan Iofrida | Credit; link license; indicate changes |
| **CC BY 4.0** | `trichonephila_clavipes` | Gabriela Palomo-Munoz | Credit; link license; indicate changes |
| **CC BY 4.0** | `leptonychotes_weddellii` | Gabriela Palomo-Munoz | Credit; link license; **indicate changes** |
| **CC BY 3.0** | `cyclorana_platycephala` | T. Michael Keesey (after Auckland Museum) | Credit; link license |
| **CC BY 3.0** | `erithacus_rubecula` | Rebecca Groom | Credit; link license |
| **CC BY 3.0** | `sepia_officinalis` | David Sim + T. Michael Keesey | Credit both; link license |
| **CC BY 3.0** | `photinus_pyralis` | Melissa Broussard | Credit; link license |
| **CC BY 3.0** | `canis_familiaris` | Sam Fraser-Smith (vectorized by T. Michael Keesey) | Credit; link license |
| **PDM 1.0 (≈ CC0)** | `polypedilum_vanderplanki` | Melissa Ingala | No legal requirement; credit by courtesy |
| **CC0 / PDM** | all others | see table above | No legal requirement; provenance recorded |

---

## Jigsaw-only SVGs (no species in dataset)

These files exist in `assets/puzzle/` and as layers in `ALL_ANIMALS.svg` but have no entry in `data/input/species.csv`. They are not in `assets/species_svg/`.

| File | Layer label | Original subject |
|------|------------|-----------------|
| `16_Mantis Shrimp.svg` | `16_Mantis Shrimp` | Stomatopod (no species in dataset) |
| `22_sea slug.svg` | `22_sea slug` | *Elysia chlorotica* or similar sacoglossan (no species in dataset) |
| `24_worm.svg` | `24_worm` | *Caenorhabditis elegans* roundworm (not in `gene_species.csv`) |

---

*Sources: `data/input/species.csv`, `data/input/gene_species.csv`, `assets/species_svg/ATTRIBUTION.md`, `animals_phylopic.md`, and PhyloPic (phylopic.org). Last updated: 2026-05-28.*
