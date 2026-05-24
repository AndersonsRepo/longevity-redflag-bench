# Tests, prompt files, and eval outputs — what produced what

Registry of every benchmark task/variant, the script that builds it, the prompt file, the eval
output, the metric, and the latest result. **Prompt + eval files live in `outputs/` (gitignored,
regenerable)** — this doc is the source of truth for what each one is.

## Naming convention
- Prompts: `outputs/<task>_<variant>.jsonl`
- Eval results: `outputs/eval_<promptstem>.jsonl` (one row per item: pred, gold, correct, condition, …)
- Eval command: `python scripts/eval_lb0138.py --model longevity --jsonl <prompts> --out <eval> --n-per-condition <N>`
  (the script scores any binary/pairwise letter task, not just LB-0138.)

## Tasks

### LB-0138 — survival binary ("does this genotype impair survival? Yes/No")
Positive = `death` (impairs, gold A); negative = `none` (gold B). Metric: balanced accuracy / F1 /
MCC, plus **Δ_recall = acc(gene shown) − acc(gene hidden)**. Both ablation conditions, gene-split.

| variant | builder | prompts | eval output | result (Longevity-LLM) |
|---|---|---|---|---|
| **controlled** (curated: 12 systems, adult/aging + 1 dev anchor) | `build_longevity_benchmark.py --mode controlled` | `longevity_controlled.jsonl` (240) | `eval_longevity_controlled.jsonl` | gp **0.808** / po **0.683** · **Δ +0.125** · MCC 0.62/0.37 |
| controlled — **run 2** (reproducibility) | same | same | `eval_longevity_controlled_run2.jsonl` | gp 0.783 / po 0.675 · Δ +0.108 (18/240 flips; endpoint ±2pt) |
| **random** (unstratified baseline, size-matched) | `build_longevity_benchmark.py --mode random` | `longevity_random.jsonl` (240) | `eval_longevity_random.jsonl` | gp 0.792 / po 0.775 · **Δ +0.017** |

**Key finding:** controlled Δ_recall (+0.125) ≫ random (+0.017) → curation EXPOSES the gene-recall
reliance that random sampling masks; reliance is concentrated in adult/aging cases. (vault LRN-20260523-430.)

### LB-0150 — lifespan-extension pairwise ("which strain's mutation is more likely to EXTEND lifespan?")
Each item: a life-EXTENDING genotype vs a survival-SHORTENING (adult/aging death) genotype, matched
on phenotype-system. gold = the extender's letter. Forced choice → base-rate-robust (chance = 0.50).
Metric: accuracy + Δ_recall. Curated: drops extenders whose profile contradicts the "extends" label
(pro-neoplasia phenotypes — 5 dropped).

| variant | builder | prompts | eval output | result (Longevity-LLM) |
|---|---|---|---|---|
| curated (26 extenders, 52 pairs) | `build_pairwise_lifespan.py` | `lifespan_pairwise.jsonl` (104) | `eval_lifespan_pairwise.jsonl` | gp **0.885** / po **0.827** · **Δ +0.058** |

**Key finding:** model recognizes extenders vs shorteners well (~0.83 even gene-hidden) with a small
recall boost — distinguishing extend-vs-shorten leans on phenotype reasoning more than the absolute
survival call does. n=52 pairs (directional).

### Contamination / recall probe (retrieval-resistance evidence — not a scored task)
Asks "does a knockout of gene X impair survival?" with **gene name only, no phenotype** — so a
correct answer can only come from prior knowledge. Compares famous (GenAge) vs obscure genes.

| builder | outputs | result (Longevity-LLM) |
|---|---|---|
| `scripts/contamination_probe_genes.py` | `data/contamination_probe_results.csv` + `_summary.json`; writeup `docs/contamination-probe-2026-05-23.md` | impairs-YES subset: **famous 70% vs obscure 5%** (Fisher p=3.9e-5); overall gap +16.3% |

**Key finding:** the model recalls famous longevity genes but not obscure ones → empirically
justifies the famous-gene blocklist and validates the Δ_recall ablation. (Run with `--n 40 --seed 1234`.)

### Deferred / not built
- **LB-0142** IMPC viability (viable/subviable/lethal) — data-blocked (lethal-only extract).
- **Ternary** shortens/no-effect/extends, **regression** (OpenGenes/SynergyAge %-change) — candidates.

## Source / selection files (not prompts)
| file | what it is |
|---|---|
| `data/mgi_labeled.csv` | canonical labeled dataset (corrected label + stage + system) |
| `data/longevity_sample_{controlled,random}.csv` | the genotype selections behind LB-0138 |
| `data/aging_direction.csv` | extends/shortens/protective analysis; source of the 51 extenders |
| `data/hallmark_tags.csv` | Hallmark-of-Aging gene tags (PARKED, v1 over-tags) |

## Caveats that apply to ALL results
- **Endpoint non-deterministic at temp=0** (~±2 pt, ~7.5% per-item flips; vault LRN-20260523-432) →
  for final numbers, **average ≥3 runs and report mean ± std**.
- Single model so far (**Longevity-LLM**); the **Claude SOTA arm** is pending (needed to call
  memorization vs capability).
- Legacy: `outputs/eval_lb0138_longevity.jsonl` = a duplicate of controlled run 1 (pre `--out` flag);
  `outputs/lb0138_sample.jsonl` = old random-balanced 120-rec sample, superseded by `longevity_controlled`.
