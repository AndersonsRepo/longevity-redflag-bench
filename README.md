# Mouse-Longevity Benchmark (Caltech Longevity Hackathon — Track 01)

A JSONL/ChatML benchmark that **extends LongevityBench** to mouse genetics: give the model a
mouse **genotype (allele set + zygosity) + the strain's phenotype profile (excluding lifespan)**
and have it **predict the survival/lifespan effect**, scored against the **recorded MGI/IMPC label**.
Mirrors the original NHANES method (measurements → mortality), with an added genotype input.

> Repo name `longevity-redflag-bench` is legacy (we pivoted from an NHANES red-flag idea). Plan + rationale: vault `caltech-hackathon-2026/build-plan.md`.

**The dataset is the deliverable** — judged on Utility / Diversity / Retrieval-Resistance / Statistical-Rigor. No demo/leaderboard score.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # MODEL_ACCESS_TOKEN (endpoint) + HF_TOKEN (dataset) — set a LONG expiry
python scripts/smoke_endpoint.py                              # endpoint alive? (model id: longevity-llm)

# build the labeled dataset + benchmark (see docs/LABELING.md for the full chain)
python scripts/classify_mortality_terms.py                   # → data/mp_mortality_classified.csv
python scripts/build_labeled_csv.py                          # → data/mgi_labeled.csv (corrected labels)
python scripts/categorize_phenotype_systems.py               # → + phenotype-system categories
python scripts/build_lb0138.py --n 60                        # → outputs/lb0138_sample.jsonl
python validate/validate_jsonl.py outputs/lb0138_sample.jsonl --min-per-task 50
python scripts/eval_lb0138.py --model longevity --n-per-condition 20   # first Δ_recall
```
**Dataset & labeling docs:** [`docs/LABELING.md`](docs/LABELING.md) (how labels/categories are derived) · [`data/README.md`](data/README.md) (sources + schema).

## The contract — LongevityBench format (unchanged)
`schema/records.py :: BenchmarkRecord` mirrors the real LongevityBench schema (`lb_id, pool,
display_name, display_group, domain, format, metric, units, messages, task, has_reasoning, metadata`).
Gold = trailing `assistant` turn; our verifiable GT + `condition` (ablation) live in `metadata`.

## Tasks
Input = genotype + phenotype profile → predict survival. Each rendered in **two ablation conditions**
(`metadata.condition`): `geno+pheno` and `pheno-only` (alleles removed) — the reasoning-vs-recall probe.

- **LB-0138 `mgi_survival_binary`** (binary/accuracy) — impairs survival? balanced. **Primary.**
- **LB-0142 `impc_viability`** (multiclass/accuracy) — viable / subviable / lethal (IMPC).
- **LB-0146 `mgi_genotype_pairwise`** (pairwise/accuracy) — which genotype is more deleterious.
- *(stretch)* regression on % lifespan (SynergyAge/MPD), MAE.

## Ground truth & data
- **MGI** `MGI_PhenoGenoMP.rpt` → `data/mgi_genotype_phenotype.csv` → **`data/mgi_labeled.csv`** (74,573 genotypes). Corrected `mortality_category`: **death 18,465 · none 54,741 · reversed 407 · excluded 960** (conditional/reproductive/ambiguous/contradictory). Mortality/aging MP subtree = label (corrected — see below); other MP terms = phenotype input; PubMed IDs = provenance.
- **MP ontology** `mp.obo` does double duty: the mortality/aging subtree (MP:0010768) defines the label, and walking phenotype terms up the `is_a` tree gives the **phenotype-system category** (`primary_system`).
- **IMPC** Solr API (CC-BY-4.0, no token) → viability viable/subviable/lethal (LB-0142, deferred). **GenAge** = famous-gene **blocklist** (contamination control).
- Labels are real lab assays (IMPC) or cited papers (MGI PMID) — **never model-generated**.
- ⚠️ The original build labeled *any* mortality-subtree term "impairs survival"; that was wrong for longevity-extending / protective / conditional terms. The correction (407 reversed, 6 contradictory, 18 root-leak) is deterministic and documented in [`docs/LABELING.md`](docs/LABELING.md).

## Statistical rigor
Split **by gene** (same gene never spans train/test); balance the binary task; report balanced-accuracy/F1/MCC; baselines = majority-class (exposes the model's default-to-no-effect bias) + a phenotype-count classifier.

## Model behavior (verified live)
vLLM-served `longevity-llm`, **28K** context, ignores JSON → end prompts with `Answer: <letter>` + `max_tokens≥400`; emits `<think>` traces; ~8s/call (parallelize). Probe: correct on famous Sirt6 (contamination), wrong/defaults to "no effect" on obscure Clint1 (resistant + measurable).

## Who owns what
| Person | Builds |
|---|---|
| **Anderson** | MGI/IMPC loaders, task generators (both ablation conditions), eval harness, metrics |
| **CS teammate** | IMPC API pull, baselines, split-by-gene, JSONL validator, Δ_recall viz |
| **Bio 1/2** | `tasks/` — GenAge famous-gene blocklist, meaningful-vs-leaky phenotype selection, label sanity, citations |

## Runnable now vs stubbed
- **Runnable:** `smoke_endpoint`, `build_mgi_dataset` (→ CSV), the full labeling pipeline
  (`classify_mortality_terms` → `build_labeled_csv` → `categorize_phenotype_systems`), `src/data/mgi.py`
  loader (corrected labels + gene-split + balance), `build_lb0138` (LB-0138 generator, both ablation
  conditions), `validate_jsonl`, `eval_lb0138` (Longevity-LLM + Claude arms), model client, parser.
- **Stubs (`# TODO`):** `src/data/impc.py` + `gen_impc_viability` (LB-0142, blocked on IMPC re-pull),
  `gen_mgi_genotype_pairwise` (LB-0146), baselines, the per-category sampler, Hallmark-of-Aging tags.
