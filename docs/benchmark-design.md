# LB-0138 (curated "longevity" set) — design choices & rationale

The controlled benchmark = `scripts/sample_longevity_benchmark.py --mode controlled` →
`scripts/build_longevity_benchmark.py`. Each choice below maps to the task goal ("can a model
identify the effect of a mutation on murine lifespan?") and the spec (covariate split, verifiable
GT, preferred format, formal metric, ≤30K tokens, JSONL ChatML, no sequence modality, N≥50).

| # | Choice | Why |
|---|--------|-----|
| 1 | **Task = binary "does this genotype impair survival? (Yes/No)"** | Matches the goal; a preferred spec format; data-rich; scoreable with balanced-acc/F1/MCC. |
| 2 | **Input = genotype (gene + allele + zygosity) + non-mortality phenotype profile** | Mirrors the "low-level data → high-level phenotype (lifespan)" task. Phenotype carries the reasoning load; genotype adds gene identity + mechanism. |
| 3 | **Label = corrected MP mortality/aging subtree** | Deterministic, MGI-curator + PMID-backed ground truth; we fixed the directional bug (longevity-extending/protective were mislabeled "impairs"). |
| 4 | **Positive = adult/aging-onset death (NOT developmental)** | The goal is *lifespan*. ~67–79% of MGI deaths are developmental lethality (a different question = viability); without scoping, the benchmark degenerates into an embryo-viability test. Adult/aging = the longevity-relevant signal. |
| 5 | **+1 developmental anchor per category (4 adult + 1 dev)** | Keeps one "obvious" calibration case per category so the set isn't only hard items, and preserves some developmental representation. |
| 6 | **Negative = `none` (no mortality phenotype)** | Clean, abundant "does not impair survival" contrast. *(Note: this is "no effect," NOT life-extension — see the open gap below.)* |
| 7 | **Drop the `embryo` phenotype-system branch** | Embryo phenotype is inherently developmental (only 3 adult/aging deaths) — can't fill an adult/aging positive quota and isn't a longevity category. |
| 8 | **12 curated survival-relevant phenotype-system branches** | Diversity across biologically survival-relevant systems; per-category sampling → covariate balance (Diversity + Statistical-Rigor). |
| 9 | **Obscure genes only (GenAge famous-gene blocklist filtered)** | Retrieval-resistance: famous longevity genes (Sirt6, mTOR) are memorized; obscure genes force reasoning from the phenotype. |
| 10 | **Split by gene (union-find over gene components)** | Spec-required leakage prevention — a gene never spans train/test; multi-gene genotypes handled by connected components. |
| 11 | **Both ablation conditions (gene shown / gene hidden), matched pairs** | The Δ_recall reasoning-vs-recall probe (retrieval-resistance), computed item-for-item. |
| 12 | **N=10/category (4 adult + 1 dev + 5 neg) → 120 genotypes → 240 prompts** | First-cut size; clears the ≥50 floor; balanced 50/50; scalable via knobs. |
| 13 | **Balanced classes; report balanced-accuracy / F1 / MCC** | Spec requires a formal statistic; balanced so the majority-class baseline = 50%. |
| 14 | **Controlled/random toggle** | Methodology lever: demonstrates curation matters (controlled Δ_recall +0.125 vs random +0.017). |

## Open gap (important): the negative class is "no effect," not "life-extension"
The negatives are `mortality_category == none` — genotypes MGI recorded with phenotypes but **no
survival/mortality effect**. We have **not** tested whether the model recognizes life-*extending*
genotypes: there are **0** life-extenders in the controlled set. The "Yes/No" task conflates
"no effect" and "extends lifespan" under "No," but we populated "No" only with "no effect." Options
to close this (data: ~51 usable life-extenders, `data/aging_direction.csv`): a life-extension
**diagnostic slice**, a **ternary** task (shortens / no-effect / extends — a preferred spec format),
or a **regression** on %-lifespan change (OpenGenes/SynergyAge). Pending the scientist's input
(`docs/scientist-questions.md` Q8).
