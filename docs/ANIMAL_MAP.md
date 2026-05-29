# Animal Map — species → silhouette mapping

Which PhyloPic silhouette represents each species, and the taxonomic reasoning behind matches that are not exact. Provenance and licensing obligations are in [`docs/species_svg_attribution.md`](species_svg_attribution.md).

| Resource | Path |
|---|---|
| Canonical SVGs | `assets/species_svg/<species_id>.svg` (39, one per species) |
| Machine-readable map | `data/input/species_svg_map.csv` |
| Attribution / licensing | `docs/species_svg_attribution.md` |
| Runtime maps | `puzzle.py` → `_SPECIES_PUZZLE_MAP` (cards/reports) and `_SPECIES_LAYER_MAP` (jigsaw) — both derived from the CSV |

**Sourcing.** Every silhouette is a direct [PhyloPic](https://www.phylopic.org/) download — contributor `source.svg`, falling back to the potrace `vector.svg`. `scripts/download_phylopic.py` reproduces the full set byte-for-byte from the CSV. The hand-drawn jigsaw pieces that once backed 25 of these species are retained as named layers inside `data/input/puzzle/ALL_ANIMALS.svg` (the `jigsaw layer` column below); the per-species cards/reports use the PhyloPic silhouette uniformly. `homo_sapiens` is mapped like any other species (Homo longi); the puzzle's only human exception is its `0_base` layer.

---
## Per-species mapping

`taxon depicted` is what PhyloPic labels the image (may be a relative of the target species; the rationale explains any gap). `jigsaw layer` is the retained layer in `ALL_ANIMALS.svg`.


### Animalia · Chordata · Actinopterygii

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `electrophorus_electricus` | Electric eel | `electrophorus_electricus.svg` | [`c931ef9c`](https://www.phylopic.org/images/c931ef9c-ff5a-4b7d-96b5-80a6be323b04/) | *Electrophorus electricus* | CC0 | `21_eel` | Exact species |
| `pseudopleuronectes_americanus` | Winter flounder | `pseudopleuronectes_americanus.svg` | [`83fae06d`](https://www.phylopic.org/images/83fae06d-c93d-41d6-9080-82734bc59163/) | *Pseudopleuronectes americanus* | CC0 | `13_fish` | Exact species |

### Animalia · Chordata · Amphibia

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `cyclorana_platycephala` | Water-holding frog | `cyclorana_platycephala.svg` | [`01a21193`](https://www.phylopic.org/images/01a21193-6599-463c-a5f0-75b6fe03189d/) | *Leiopelma archeyi* | CC BY 3.0 | `27_frog` | Direct PhyloPic SVG download (Auckland Museum & T. Michael Keesey). Cyclorana absent from PhyloPic; L. archeyi (Leiopelmatidae) is a different family within order Anura; order-level match. Replaces previous jigsaw copy and phylopic PNG (Litoria raniformis) |
| `ambystoma_mexicanum` | Axolotl | `ambystoma_mexicanum.svg` | [`575eaa51`](https://www.phylopic.org/images/575eaa51-6c9b-4d36-9881-b8463c68ebbc/) | *Ambystoma mexicanum* | CC0 | `10_axolotl` | Exact species |

### Animalia · Chordata · Aves

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `erithacus_rubecula` | European robin | `erithacus_rubecula.svg` | [`3c4ef873`](https://www.phylopic.org/images/3c4ef873-76b5-473d-a740-8fcb4864462b/) | *Erithacus rubecula* | CC BY 3.0 | `17_european robin` | Exact species; attribution required |
| `melopsittacus_undulatus` | Budgerigar | `melopsittacus_undulatus.svg` | [`93400ea7`](https://www.phylopic.org/images/93400ea7-5b4c-4d5f-92ae-2345f228df08/) | *Melopsittacus undulatus* | CC0 | `32_budgerigar` | Exact species; monotypic genus |

### Animalia · Chordata · Chondrichthyes

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `leucoraja_erinacea` | Little skate | `leucoraja_erinacea.svg` | [`f1c15c22`](https://www.phylopic.org/images/f1c15c22-db53-4753-837e-5bb439c591fa/) | *Leucoraja erinacea* | CC0 | `33_skate` | Exact species |
| `somniosus_microcephalus` | Greenland shark | `somniosus_microcephalus.svg` | [`081252c0`](https://www.phylopic.org/images/081252c0-f3f3-4d9f-84bb-b9f00fcb1f5b/) | *Centroscymnus* | CC0 | `6_shark` | Family-level fallback; Centroscymnus (Portuguese dogfish) is same family Somniosidae as Somniosus; sleeper shark body plan close |

### Animalia · Chordata · Mammalia

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `balaena_mysticetus` | Bowhead whale | `balaena_mysticetus.svg` | [`18438875`](https://www.phylopic.org/images/18438875-f6e8-4e46-8fda-5a07bd4c1a85/) | *Balaena mysticetus* | CC BY-SA 3.0 | `7_whale` | Exact species; attribution required |
| `bos_taurus` | Cattle (Belgian Blue) | `bos_taurus.svg` | [`0ebe16cb`](https://www.phylopic.org/images/0ebe16cb-4c74-4c77-9643-9e531a0840cc/) | *Bos primigenius* | CC BY 4.0 | `31_cattle` | PhyloPic uses wild aurochs ancestor; silhouette indistinguishable from domestic cattle; attribution required |
| `tursiops_truncatus` | Bottlenose dolphin | `tursiops_truncatus.svg` | [`0b5c6b41`](https://www.phylopic.org/images/0b5c6b41-3a44-4c9e-869a-63ed54bf7c65/) | *Tursiops truncatus* | CC BY-SA 3.0 | `14_dolphin` | Exact species; attribution required |
| `canis_familiaris` | Dog (Whippet) | `canis_familiaris.svg` | [`3c534a59`](https://www.phylopic.org/images/3c534a59-fd0c-41bb-80c7-1d18db9bae13/) | *Canis familiaris dingo* | CC BY 3.0 | `30_dog` | PhyloPic uses dingo (C. familiaris dingo); same species; attribution required |
| `felis_catus` | Cat | `felis_catus.svg` | [`e9f41f59`](https://www.phylopic.org/images/e9f41f59-d708-47aa-a705-ba9b8826ebc6/) | *Felis lybica catus* | CC0 | `18_cat` | Exact subspecies (domestic cat) |
| `herpestes_ichneumon` | Egyptian mongoose | `herpestes_ichneumon.svg` | [`640e09b5`](https://www.phylopic.org/images/640e09b5-4e1b-4143-90c4-9ea924c8d270/) | *Herpestes ichneumon* | CC0 | `39_mongoose` | Exact species |
| `leptonychotes_weddellii` | Weddell seal | `leptonychotes_weddellii.svg` | [`81814d17`](https://www.phylopic.org/images/81814d17-9379-4358-ad92-32e92dbf35eb/) | *Leptonychotes weddellii* | CC BY 4.0 | `12_seal` | Exact species; must credit Gabriela Palomo-Munoz and indicate changes |
| `pteropus_alecto` | Black flying fox | `pteropus_alecto.svg` | [`e4ab0438`](https://www.phylopic.org/images/e4ab0438-794b-4030-8e2a-7b5c1f23bf03/) | *Pteropus poliocephalus* | CC0 | `11_bat` | Same genus; grey-headed flying fox; wing morphology equivalent at silhouette resolution |
| `potorous_tridactylus` | Long-nosed potoroo | `potorous_tridactylus.svg` | [`6354f106`](https://www.phylopic.org/images/6354f106-3d0f-4525-b958-75bd740a19ee/) | *Potorous tridactylus* | CC0 | `38_potoroo` | Exact species |
| `homo_sapiens` | Human | `homo_sapiens.svg` | [`f46f28c7`](https://www.phylopic.org/images/f46f28c7-b3da-485e-9af0-9839b63138e0/) | *Homo longi* | CC0 | `0_base` | H. longi (Ji & Ni 2021) is an archaic Homo species; genus-level match. Shown in gene cards/reports like any other species; the puzzle's outer human silhouette is the separate 0_base layer in ALL_ANIMALS.svg. |
| `loxodonta_africana` | African elephant | `loxodonta_africana.svg` | [`62398ac0`](https://www.phylopic.org/images/62398ac0-f0c3-48f8-8455-53512a05fbc4/) | *Loxodonta africana africana* | CC0 | `5_elephant` | Exact subspecies |
| `heterocephalus_glaber` | Naked mole-rat | `heterocephalus_glaber.svg` | [`7a7d8226`](https://www.phylopic.org/images/7a7d8226-aa19-4f6f-8afa-f039cc860d7e/) | *Heterocephalus glaber* | CC0 | `3_naked mole rat` | Exact species |
| `acomys_cahirinus` | Cairo spiny mouse | `acomys_cahirinus.svg` | [`720396f4`](https://www.phylopic.org/images/720396f4-3d8a-41e5-9505-555964202c0c/) | *Acomys cahirinus dimidiatus* | CC0 | `29_spiny mouse` | Exact genus+species in PhyloPic; subspecies dimidiatus is morphologically identical |
| `mus_musculus` | Mouse | `mus_musculus.svg` | [`6b2b98f6`](https://www.phylopic.org/images/6b2b98f6-f879-445f-9ac2-2c2563157025/) | *Mus musculus domesticus* | CC0 / PDM | `25_mouse` | Exact subspecies (domestic house mouse) |
| `urocitellus_parryii` | Arctic ground squirrel | `urocitellus_parryii.svg` | [`f4ca8082`](https://www.phylopic.org/images/f4ca8082-0db0-4130-88eb-04a74e18312d/) | *Urocitellus beldingi* | CC0 | `40_ground squirrel` | Same genus; Belding's ground squirrel; same stout ground-squirrel body plan at silhouette resolution |

### Animalia · Chordata · Reptilia

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `gekko_japonicus` | Japanese gecko | `gekko_japonicus.svg` | [`9aca34d8`](https://www.phylopic.org/images/9aca34d8-4dde-418d-9fdc-2d58b6a7b267/) | *Gekko gecko* | CC0 | `23_gecko` | Same genus; Tokay gecko body plan identical at silhouette resolution |
| `crotalus_atrox` | Western diamondback rattlesnake | `crotalus_atrox.svg` | [`8748e7ab`](https://www.phylopic.org/images/8748e7ab-6dc8-4384-a72b-37361ae8f60b/) | *Crotalus atrox* | CC BY 4.0 | `15_pit viper` | Exact species; attribution required |

### Animalia · Arthropoda

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `trichonephila_clavipes` | Golden silk orbweaver | `trichonephila_clavipes.svg` | [`f152b5fb`](https://www.phylopic.org/images/f152b5fb-1e9f-4d4b-864c-704a95827129/) | *Trichonephila clavata* | CC BY 4.0 | `34_spider` | Congeneric orb-weaver (T. clavata); morphologically equivalent at silhouette resolution; attribution required |
| `leiurus_quinquestriatus` | Deathstalker scorpion | `leiurus_quinquestriatus.svg` | [`4133ae32`](https://www.phylopic.org/images/4133ae32-753e-49eb-bd31-50c67634aca1/) | *Heterometrus laoticus* | CC0 | `35_scorpion` | New SVG download from PhyloPic (Margot Michaud CC0). Heterometrus laoticus (Scorpionidae) is different family from Leiurus (Buthidae) but same order Scorpiones; forward-claws + upward-curved tail posture visually matches deathstalker in side view |
| `photinus_pyralis` | Firefly | `photinus_pyralis.svg` | [`ae83a86e`](https://www.phylopic.org/images/ae83a86e-79a8-46b5-ba0e-9d4b25bd707e/) | *Photinus pyralis* | CC BY 3.0 | `20_firefly` | Exact species; attribution required |
| `polypedilum_vanderplanki` | Sleeping chironomid | `polypedilum_vanderplanki.svg` | [`af2b4c88`](https://www.phylopic.org/images/af2b4c88-b61d-4343-898a-69741d883a54/) | *Chironomidae* | PDM 1.0 | `24_chironomid` | New SVG download (Melissa Ingala PDM 1.0). P. vanderplanki absent from PhyloPic; family Chironomidae is closest match. Replaces previous CC BY-NC 3.0 PNG — PDM removes the non-commercial restriction |
| `drosophila_melanogaster` | Fruit fly | `drosophila_melanogaster.svg` | [`b5160ba3`](https://www.phylopic.org/images/b5160ba3-ad86-4123-92a7-1c55122f4a6c/) | *Sophophora melanogaster* | CC0 | `36_fruit fly` | PhyloPic title uses obsolete synonym Sophophora (now synonymised into Drosophila); image accurate |
| `homarus_americanus` | American lobster | `homarus_americanus.svg` | [`46f3f90b`](https://www.phylopic.org/images/46f3f90b-48ee-4d25-b751-e5070e37532e/) | *Homarus americanus* | CC0 / PDM | `26_lobster` | Exact species |

### Animalia · Cnidaria

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `turritopsis_dohrnii` | Immortal jellyfish | `turritopsis_dohrnii.svg` | [`e4d57d67`](https://www.phylopic.org/images/e4d57d67-c144-457a-877b-34faaaa16ed2/) | *Clytia hemisphaerica* | CC BY-SA 3.0 | `8_jellyfish` | T. dohrnii (Anthoathecatae) and C. hemisphaerica (Leptothecata) are in different orders within class Hydrozoa; class-level match. All small Hydrozoa medusae share bell-and-tentacle body plan. Supersedes previous byte-identical Narcomedusae PNG (ae1697f9) |
| `aequorea_victoria` | Crystal jellyfish | `aequorea_victoria.svg` | [`e4d57d67`](https://www.phylopic.org/images/e4d57d67-c144-457a-877b-34faaaa16ed2/) | *Clytia hemisphaerica* | CC BY-SA 3.0 | `8_jellyfish` | A. victoria (Leptothecata) and C. hemisphaerica (Leptothecata) are in the same order; order-level match. Medusa body plan interchangeable across Hydrozoa. Supersedes previous byte-identical Narcomedusae PNG (ae1697f9) |

### Animalia · Mollusca

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `pinctada_fucata` | Akoya pearl oyster | `pinctada_fucata.svg` | [`a2a342d0`](https://www.phylopic.org/images/a2a342d0-e77e-4abc-8913-72b15eb9d906/) | *Pinctada fucata* | CC BY-SA 3.0 | `37_oyster` | New SVG download from PhyloPic; exact species. Previously stored as PNG only. Must credit Taro Maeda; share-alike |
| `sepia_officinalis` | Common cuttlefish | `sepia_officinalis.svg` | [`6cbff80e`](https://www.phylopic.org/images/6cbff80e-9537-4130-8397-ebbf77464ea4/) | *Sepia officinalis* | CC BY 3.0 | `19_cuttlefish` | Exact species; attribution required |

### Animalia · Platyhelminthes

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `schmidtea_mediterranea` | Planarian | `schmidtea_mediterranea.svg` | [`fb16134d`](https://www.phylopic.org/images/fb16134d-47c9-42f0-bafe-f63bccf2d58b/) | *Schmidtea mediterranea* | CC0 | `9_planarian` | Exact species |

### Animalia · Tardigrada

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `ramazzottius_varieornatus` | Tardigrade | `ramazzottius_varieornatus.svg` | [`1a7ba4da`](https://www.phylopic.org/images/1a7ba4da-a5f9-489b-b30e-8cf56d579d8f/) | *Tardigrada* | CC BY-NC-SA 3.0 | `1_tardigrade` | Phylum-level fallback; no species silhouette in PhyloPic; NC-SA license: non-commercial only; must credit Mali'o Kodis / Smithsonian Institution; derivative works must carry same license |

### Bacteria

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `deinococcus_radiodurans` | Conan the Bacterium | `deinococcus_radiodurans.svg` | [`40e8c1ed`](https://www.phylopic.org/images/40e8c1ed-c133-4930-9a9d-572d9ba8b0d5/) | *Deinococcus radiodurans* | CC BY-SA 3.0 | `2_Deinococcus` | Exact species; attribution required |

### Fungi

| species_id | common name | SVG | PhyloPic | taxon depicted | license | jigsaw layer | rationale |
|---|---|---|---|---|---|---|---|
| `cladosporium_sphaerospermum` | Chernobyl fungus | `cladosporium_sphaerospermum.svg` | [`a21310f5`](https://www.phylopic.org/images/a21310f5-2762-495d-b996-bc0bef7203fd/) | *Schizosaccharomyces pombe* | CC0 | `4_fungi` | higher-taxon fallback (Ascomycota); S. pombe is Schizosaccharomycetes (different class from Cladosporium Dothideomycetes) but closest available fungal silhouette; acceptable as icon |

---
## Shared / similar silhouettes

Species close enough to share art without materially misleading (from the CSV `similar_to` column).

| Members | Same UUID? | Note |
|---|---|---|
| `erithacus_rubecula` ↔ `melopsittacus_undulatus` | no | Distinct images; close enough to swap if one is lost. |
| `acomys_cahirinus` ↔ `mus_musculus` | no | Distinct images; close enough to swap if one is lost. |
| `polypedilum_vanderplanki` ↔ `drosophila_melanogaster` | no | Distinct images; close enough to swap if one is lost. |
| `turritopsis_dohrnii` ↔ `aequorea_victoria` | yes | Same PhyloPic image — both render identically. |

---
## Jigsaw-only layers (no species in dataset)

Layers present in `ALL_ANIMALS.svg` with no matching row in `species.csv`/`gene_species.csv`, so they have no `assets/species_svg/` file:

| Layer label | Original subject |
|---|---|
| `16_Mantis Shrimp` | Stomatopod (no species in dataset) |
| `22_sea slug` | *Elysia chlorotica* or similar sacoglossan (no species in dataset) |
| `24_worm` | *Caenorhabditis elegans* roundworm (not in `gene_species.csv`) |

---

*Generated from `data/input/species_svg_map.csv`. Licensing obligations: `docs/species_svg_attribution.md`. Last updated: 2026-05-29.*
