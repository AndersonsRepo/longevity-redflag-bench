# data/ — sources, provenance, and the labeled dataset

This benchmark is built from **mouse genetics**, not NHANES (the repo pivoted; the old
NHANES notes are in git history). Everything here traces to public, citable sources —
**no labels are model-generated**. The labeling/categorization logic is documented in
[`../docs/LABELING.md`](../docs/LABELING.md).

## Source files

| File | What it is | Source | License | In repo? |
|---|---|---|---|---|
| `MGI_PhenoGenoMP.rpt` | genotype → MP phenotype terms + PubMed IDs (the curated annotations) | [MGI](https://www.informatics.jax.org/downloads/reports/index.html) (Jackson Lab) | free, attribution | **no** (large; fetch to build) |
| `MGI_PhenotypicAllele.rpt` | allele → curated attributes (drives `expression_direction`) | MGI | free, attribution | yes |
| `mp.obo` | Mammalian Phenotype ontology (the `is_a` tree) | [MGI / OBO Foundry](http://purl.obolibrary.org/obo/mp.obo) | CC-BY | yes (release 2026-04-22) |
| `mp_mortality_terms.csv` | the 129 MP terms under the mortality/aging root MP:0010768 | derived from `mp.obo` | — | yes |
| `famous_gene_blocklist.csv` | GenAge "famous" aging genes (contamination control) | [GenAge/HAGR](https://genomics.senescence.info/genes/) | academic | yes |
| `impc_viability.csv` | IMPC homozygous viability (for the deferred LB-0142 task; currently lethal-only) | [IMPC Solr](https://www.mousephenotype.org/) | CC-BY-4.0 | yes |

## Derived files (this is the dataset)

| File | Built by | What it is |
|---|---|---|
| `mgi_genotype_phenotype.csv` | `scripts/build_mgi_dataset.py` | one row per genotype: genes, alleles, zygosity, mortality terms, phenotype profile, PMIDs, and the **original (buggy) `label_impairs_survival`** |
| `mp_mortality_classified.csv` | `scripts/classify_mortality_terms.py` | each of the 129 mortality terms → `category`, `label_contribution`, `lethality_stage` (the frozen ground-truth verdicts) |
| **`mgi_labeled.csv`** | `scripts/build_labeled_csv.py` + `scripts/categorize_phenotype_systems.py` | **the canonical labeled dataset** — see schema below |

## `mgi_labeled.csv` column schema

Raw columns (from `mgi_genotype_phenotype.csv`): `genotype_id`, `allelic_composition`,
`gene_symbols`, `zygosity`, `expression_direction`, `allele_attributes`,
`genetic_background`, `label_impairs_survival` (**original, buggy** — kept for audit),
`mortality_terms`, `n_phenotype_terms`, `phenotype_terms`, `pmids`.

Derived columns (added by this repo's pipeline):

| Column | Values | Meaning |
|---|---|---|
| `label_corrected` | `1` / `0` / `""` | 1 = impairs survival, 0 = does not (incl. reversed + true-neg), `""` = excluded |
| `mortality_category` | death · none · reversed · conditional · reproductive · ambiguous · contradictory | how the genotype's mortality terms were judged (see docs/LABELING.md) |
| `lethality_stage` | developmental · postnatal · adult_aging · unspecified · na | stage axis for death-positives (stratify on this — see below) |
| `eligible` | `1` / `0` | usable in the baseline binary (1) vs excluded (0) |
| `is_famous` | `1` / `0` | any constituent gene on the GenAge blocklist |
| `primary_system` | MP top-level branch | most-frequent phenotype-system (e.g. `cardiovascular system`) |
| `all_systems` | `\|`-joined branches | all phenotype-system branches the genotype touches (multi-label) |

## Current contents (74,573 genotypes)

- **mortality_category:** death 18,465 · none 54,741 · conditional 807 · reversed 407 · reproductive 72 · ambiguous 75 · contradictory 6
- **eligible:** 73,613 · **excluded:** 960 · **labels corrected vs the buggy build:** 407
- **death lethality_stage:** developmental 12,445 · postnatal 2,178 · adult_aging 3,640 · unspecified 202
  - ⚠️ developmental dominates — **stratify by `lethality_stage`** or you get an embryo-viability benchmark, not a longevity one.

## How to obtain the source files

```bash
# MP ontology (in repo, but to refresh):
curl -L -o data/mp.obo http://purl.obolibrary.org/obo/mp.obo
# MGI genotype→phenotype report (NOT in repo; ~large):
curl -L -o /tmp/mgi.rpt https://www.informatics.jax.org/downloads/reports/MGI_PhenoGenoMP.rpt
```

Then run the pipeline in [`../docs/LABELING.md`](../docs/LABELING.md).
