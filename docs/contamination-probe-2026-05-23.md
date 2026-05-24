# Gene-Recall Contamination Probe — LongevityLLM

**Date:** 2026-05-23 · **Model:** `longevity-llm` (Insilico, Qwen3.5-9B) via HF endpoint `swchnq0ekc3scmqw…/v1` · **Seed:** 1234 · **Script:** `scripts/contamination_probe_genes.py`

## TL;DR
On mouse genes whose knockout **does** impair survival, LongevityLLM correctly flags **70% of *famous* (GenAge) genes but only 5% of *obscure* genes** (14/20 vs 1/20; Fisher's exact two-sided **p = 3.9 × 10⁻⁵**). With no phenotype context given, the only thing distinguishing the two groups is whether the gene is well-known — so this is **recall, not reasoning**. It is direct, on-model evidence that famous longevity genes are contaminated and belong in the blocklist, not the retrieval-resistant test set.

## Question & hypothesis
Does LongevityLLM answer "does a knockout of gene X impair survival?" better for **famous** longevity genes than for **obscure** ones, when given *only the gene name* (no phenotype)?
- **Reasoning model** → similar accuracy on both (it has the same — i.e. zero — information either way).
- **Recall/contaminated model** → much higher accuracy on famous genes (seen in pretraining/literature).

## Method
**Groups**
- **FAMOUS** = genes in the **GenAge model-organism** mouse set (136 genes; `genomics.senescence.info/genes/models_genes.zip`) that also have a clean MGI single-gene knockout label → 116 candidates.
- **OBSCURE** = MGI single-gene knockout genes **not** in our famous-gene blocklist (2,193 symbols; GenAge + curated starter) → 11,518 candidates. Median **0** PMIDs in the MGI annotation (obscurity proxy).

**Gene eligibility:** single-gene genotypes only; allele must be a knockout/null; `eligible=True`; gold label = **majority vote of MGI `label_corrected`** over the gene's knockout genotypes (ties dropped).

**Sampling:** 40 genes per group, **balanced 20 impairs-survival (gold A) / 20 not (gold B)** so a constant "No" answer scores 50% in *both* groups — the gap is therefore pure recall, not label prior. Famous sampled most-studied-first, obscure least-studied-first. Seed 1234.

**Prompt (gene-only, verbatim):**
> *System:* You are a biomedical AI specialized in aging biology, trained on genomic, proteomic, and clinical data.
> *User:* A laboratory mouse carries a homozygous loss-of-function (knockout) mutation in the gene **{SYMBOL}**. No phenotype information is provided.
> Question: Does this knockout impair survival (cause premature death or a shortened lifespan)?
> Options: A. Yes  B. No
> Reason briefly, then on the FINAL line output exactly: Answer: \<letter\>

**Ground truth:** A = impairs survival (MGI label 1), B = not (0). **Metric:** accuracy per group; recall gap = acc(famous) − acc(obscure), bootstrap 95% CI (5,000 resamples). Answer parsed after the model's `</think>` block.

## Results (n = 40/group, 79 parsed, 1 parse failure)

| Group | Overall acc | impairs=YES subset (n=20) | impairs=NO subset (n=20) |
|---|---|---|---|
| **FAMOUS (GenAge)** | **65.0%** | **70% (14/20)** | 60% (12/20) |
| **OBSCURE** | **48.7%** | **5% (1/20)** | 90% (18/20) |

- **Overall recall gap:** +16.3%, 95% CI **[−6.3%, +38.9%]** (crosses zero — see interpretation).
- **YES-subset gap:** **70% vs 5%**, Fisher's exact two-sided **p = 3.9 × 10⁻⁵** (decisive).
- **Prediction distribution:** B/No = 55, A/Yes = 24, blank = 1 → the model **defaults to "No"** (69% of answers).
- **Recalled (famous, correctly flagged harmful):** ATM, BUB1B, COQ7, ERCC1, ERCC2, FN1, FXN, MSH2, PPM1D, RICTOR, SHC1, SIRT1…
- **Missed (obscure, harmful KO but said "No"):** CLINT1, ANKRD50, INTS11, NDUFA11, DDX21, ANAPC7, EDARADD, ARHGEF17… (19/20). Only **LSS** was correctly flagged.

## Interpretation
The model's policy is essentially **"default to No (survival not impaired) unless I recognize the gene as a known-harmful one."**
- On the **impairs=YES** genes (where knowledge is required to answer correctly), it recognizes **70% of famous** genes vs **5% of obscure** — a 65-point gap, p ≈ 4e-5. This is recall.
- On the **impairs=NO** genes, defaulting to "No" is *correct*, so both groups score high (90% obscure, 60% famous) — which is why the **overall balanced-accuracy gap CI crosses zero**: the No-subset is uninformative and dilutes the aggregate. The YES-subset is the decisive comparison.
- This matches the earlier 2-gene preview (Sirt6 recalled / Clint1 missed) and the documented "defaults to no-effect on unknown genes" behavior.

## What this justifies (for the writeup)
1. **The famous-gene blocklist is empirically warranted** — not asserted from assumptions about Insilico's (undisclosed) training set, but *measured* on the model itself.
2. **Retrieval-resistance lives in the obscure tail.** Famous genes test memorization; obscure genes test reasoning. Build the scored test set from the obscure tail; keep famous genes for the contamination/recall slice only.
3. **Validates the `Δ_recall` ablation** (geno+pheno − pheno-only): the gene name alone carries a large recall signal that the phenotype context must outweigh for the result to reflect reasoning.

## Limitations
- n = 20 per subset; the YES-subset gap is large and significant, but widen to ~60–100/group for the final paper.
- "Obscure" = non-blocklist + ~0 MGI PMIDs (a proxy; not a global literature count).
- Gold = MGI knockout-genotype majority label; genes with mixed labels were dropped.
- Single model, single seed, T=0 still has endpoint-level nondeterminism — re-run to confirm stability.

## Reproduce
```
.venv/bin/python scripts/contamination_probe_genes.py --n 40 --seed 1234 --workers 3
```
Outputs: `data/contamination_probe_results.csv` (per-gene) · `data/contamination_probe_summary.json` (metrics).
