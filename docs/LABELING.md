# Labeling & categorization — how the ground truth is derived

This documents how the mouse-longevity benchmark turns raw MGI annotations into a clean,
labeled, categorized dataset. **Principle: the ground truth is deterministic and auditable —
no AI in the labeling path.** Sources and file schema are in [`../data/README.md`](../data/README.md).

## Data flow

```
MGI_PhenoGenoMP.rpt  ──build_mgi_dataset.py──►  data/mgi_genotype_phenotype.csv
(genotype → MP terms + PMIDs)                   (74,573 genotypes; buggy label)
        │
mp.obo ─┤ mortality/aging subtree (MP:0010768) = the survival LABEL
        │ everything else                       = the phenotype PROFILE
        ▼
data/mp_mortality_terms.csv (129 terms) ──classify_mortality_terms.py──► data/mp_mortality_classified.csv
        │                                  (per-term: category / label / stage)
        ▼
build_labeled_csv.py + categorize_phenotype_systems.py ──►  data/mgi_labeled.csv  ◄── the canonical dataset
        ▼
build_lb0138.py ──►  outputs/lb0138_sample.jsonl  ──eval_lb0138.py──►  scorecard + Δ_recall
```

## 1. Where the labels come from

- **Phenotype terms + survival outcome = MGI curators.** MGI biologists read published papers
  and tag each genotype with Mammalian Phenotype (MP) ontology terms; the `pmids` column is the
  citation. We did not author these — we *split* them (mortality vs phenotype) and *corrected* the split.
- **Phenotype-system category = the MP ontology itself.** Each phenotype term is walked up its
  `is_a` parents to its top-level branch (a direct child of root `MP:0000001`). The 28 branches are
  the ontology's own groupings.

## 2. The survival label — mortality-term classification

`build_mgi_dataset.py` originally set `label_impairs_survival = 1` for **any** term in the
MP:0010768 (mortality/aging) subtree. That subtree is **bidirectional and heterogeneous**, so this
was wrong. We classify each of the 129 mortality terms once (rules in
`src/data/mortality_classes.py`, frozen to `data/mp_mortality_classified.csv`):

| category | label | handling | examples |
|---|---|---|---|
| `death` | **1** | impairs survival | premature death, embryonic/perinatal lethality, moribund, SUDEP |
| `beneficial` | **0** | longevity-EXTENDING (was mislabeled 1) | extended life span, slow aging, increased tumor-free survival |
| `protective` | **0** | resists death (was mislabeled 1) | decreased susceptibility to … mortality |
| `conditional` | exclude | only dies when challenged | increased susceptibility to viral/xenobiotic … mortality |
| `reproductive` | exclude | not organismal baseline death | premature ovarian failure, early reproductive senescence |
| `ambiguous` | exclude | direction-less | abnormal survival, **mortality/aging (the bare root)** |

**Per-genotype precedence** (`src/data/mgi.py :: _classify_genotype`), since a genotype can carry
several mortality terms:

1. genuine death **+** longevity-extending term → `contradictory`, **excluded** (conflicting GT)
2. any `death` term → label **1**, stage = earliest of {developmental, postnatal, adult_aging, unspecified}
3. `beneficial`/`protective` only → label **0**, tagged `reversed` (kept as a **hard negative**)
4. `conditional` / `reproductive` / `ambiguous` only → **excluded**
5. no mortality term → label **0** (`none`, true negative)

### Three bugs fixed (vs the original build)

1. **407 reversed** — longevity-extending/protective genotypes were labeled "impairs survival." A
   longevity mutant scored as impairs-survival *penalizes a model that reasons correctly*. → label 0.
2. **6 contradictory** — carry both a death term and `extended life span` → excluded as ambiguous GT.
3. **`mortality/aging` root leak** — the build's *descendants-only* walk excluded the subtree root
   (`MP:0010768`) itself, so genotypes annotated with the bare term leaked it into their phenotype
   **profile** and were scored as clean negatives. Now treated as a mortality term (ambiguous);
   `_classify_genotype` / `build_labeled_csv.py` re-partition any mortality-classified term out of
   the profile. (18 profiles cleaned, 16 false-negatives corrected.) See vault `ERR-20260523-406`.

## 3. The phenotype-system category

`categorize_phenotype_systems.py` maps each genotype's phenotype terms to MP top-level branches:

- `primary_system` = most-frequent branch (ties: higher count, then branch-name alphabetical)
- `all_systems` = all distinct branches touched (multi-label)
- 100% of phenotype-term names resolve against `mp.obo` (verified). Mortality terms never map here.

The ~12 **survival-relevant** branches used for sampling: homeostasis/metabolism, immune,
cardiovascular, hematopoietic, nervous, growth/size/body region, skeleton, digestive/alimentary,
liver/biliary, renal/urinary, respiratory, endocrine/exocrine, embryo. (All fill N=10 at 5 pos / 5
neg, obscure-only; `normal` and `taste/olfaction` cannot and are not curated.)

## 4. The benchmark task (LB-0138)

`src/data/mgi.py :: load_mgi` returns corrected, balanced, gene-split rows; `build_lb0138.py`
renders each in **two ablation conditions** (`geno_pheno` shows gene+alleles; `pheno_only` hides
them) → matched pairs. `eval_lb0138.py` scores a model and reports
**Δ_recall = acc(geno_pheno) − acc(pheno_only)**.

**Smoke (Longevity-LLM, n=20/condition):** acc 0.90 / 0.90, Δ_recall ≈ 0 (reasons from phenotype,
not gene recall on obscure genes). Stratified: developmental 14/14, postnatal 4/6, adult/aging 3/4
— weaker on the longevity-relevant cases, which is why we **report by stage**.

## 5. Regenerate end-to-end

```bash
# deps: pip install openai anthropic tiktoken scikit-learn pydantic
curl -L -o data/mp.obo http://purl.obolibrary.org/obo/mp.obo
curl -L -o /tmp/mgi.rpt https://www.informatics.jax.org/downloads/reports/MGI_PhenoGenoMP.rpt

python scripts/build_mgi_dataset.py /tmp/mgi.rpt data/mp.obo   # → data/mgi_genotype_phenotype.csv
python scripts/classify_mortality_terms.py                     # → data/mp_mortality_classified.csv
python scripts/build_labeled_csv.py                            # → data/mgi_labeled.csv (label cols)
python scripts/categorize_phenotype_systems.py                 # → adds primary_system / all_systems
python scripts/build_lb0138.py --n 60                          # → outputs/lb0138_sample.jsonl
python validate/validate_jsonl.py outputs/lb0138_sample.jsonl --min-per-task 50
python scripts/eval_lb0138.py --model longevity --n-per-condition 20
```

## 6. Known caveats / follow-ups

- Raw `MGI_PhenoGenoMP.rpt` is **not** committed (fetch to rebuild step 1).
- LB-0138 sampler should **over-sample `reversed` hard-negatives** (they're the most diagnostic).
- Gene-component train/test split puts ~60% of rows in "test" because a few mega-components dominate
  — split by component **size**, not count, when this matters.
- IMPC viability task (LB-0142) is blocked on a viable/subviable Solr re-pull (current extract is
  lethal-only).
- Hallmark-of-Aging gene tag (MyGene→GO) is a planned **secondary** covariate — not deterministic,
  needs bio review.
