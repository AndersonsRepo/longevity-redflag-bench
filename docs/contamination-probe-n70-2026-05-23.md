# Gene-Recall Contamination Probe — LongevityLLM (n=70 confirmation run)

**Date:** 2026-05-23 · **Model:** `longevity-llm` (Insilico, Qwen3.5-9B) · **This is the scaled-up confirmation of the n=40 pilot** (`docs/contamination-probe-2026-05-23.md`). Same method, larger sample.

## TL;DR
At the maximum balanced sample the famous set allows (**70/group**), the recall signal holds: on knockouts that **do** impair survival, LongevityLLM flags **54% of famous (GenAge) genes vs 9% of obscure genes** (19/35 vs 3/35; Fisher's exact two-sided **p = 6.7 × 10⁻⁵**). Famous recall **scales with fame** — the top-20 most-studied genes (pilot) scored 70%, the broader 35 score 54%, obscure stays near floor. Direct, on-model evidence of contamination on the famous set.

## Run provenance (documented run)
| | |
|---|---|
| Command | `.venv/bin/python scripts/contamination_probe_genes.py --n 70 --seed 1234 --workers 3 --tag n70` |
| Start → End | 2026-05-23 **20:50:58 → 20:57:45 PDT** (≈ 6m47s) |
| Endpoint | `https://swchnq0ekc3scmqw.us-east-2.aws.endpoints.huggingface.cloud/v1` (live) |
| Calls / workers | 140 / 3 (≈ 2.9 s/call effective) |
| Parse failures | **0 / 140** |
| Sample | famous 70 (35 impairs / 35 not), obscure 70 (35 / 35) — exact balance |
| Outputs | `data/contamination_probe_results_n70.csv`, `data/contamination_probe_summary_n70.json` |

Reproduces deterministically (seed 1234) modulo endpoint-level T=0 nondeterminism.

## Method (unchanged from the pilot — summary)
Gene-only prompt ("a mouse has a homozygous knockout of gene X; does it impair survival? A/B", no phenotype). Gold = MGI `label_corrected` majority over the gene's single-gene knockout genotypes. **FAMOUS** = GenAge mouse ∩ MGI-KO-clean-label; **OBSCURE** = MGI-KO-clean-label not in the famous-gene blocklist (median 0 PMIDs). Both groups balanced 35/35 on the label so a constant "No" scores 50% in each — the gap is pure recall. Full methodology + verbatim prompt: `docs/contamination-probe-2026-05-23.md`.

**Note on max n:** the famous set is capped — only **35 GenAge mouse genes** have an impairs-survival MGI knockout label — so 70/group (35+35) is the largest *balanced* design possible without changing the gene-eligibility rule.

## Results (n=70/group, 140/140 parsed)

| Group | Overall | impairs=YES (n=35) | impairs=NO (n=35) |
|---|---|---|---|
| **FAMOUS (GenAge)** | **62.9%** (44/70) | **54%** (19/35) | 71% (25/35) |
| **OBSCURE** | **52.9%** (37/70) | **9%** (3/35) | 97% (34/35) |

- **YES-subset gap:** 54% vs 9%, Fisher's exact two-sided **p = 6.7 × 10⁻⁵** (decisive).
- **Overall recall gap:** +10.0%, 95% CI **[−5.7%, +25.7%]** (crosses zero — same default-"No" dilution as the pilot; see below).
- **Prediction distribution:** B/No = 107, A/Yes = 33 → model defaults to "No" (**76%** of answers).
- **Recalled (famous, harmful KO correctly flagged):** ATM, ATR, BUB1B, CDK7, CISD2, COQ7, ERCC1, ERCC2, FXN, HTRA2, MSH2, POLG, POU1F1, PPM1D, RICTOR, SHC1, SIRT1, SIRT6 (+1).
- **Missed (famous, harmful KO but said "No"):** SOD2, KL (Klotho), GH, FGF23, FN1, TRP73, BUB3, MSRA, STUB1, TXN1, TOP3B, CDC14B, EEF1E1, MTBP, RBM38, ARHGAP1.
- **Obscure correct (3/35):** EDARADD, IPO7, LSS. The other 32 obscure harmful-KO genes → defaulted "No."

## Interpretation
1. **Recall scales with fame** — a clean dose-response: famous-YES accuracy 70% (top-20 pilot) → 54% (top-35) as less-studied famous genes enter, while obscure stays ~5–9%. Exactly what contamination-by-memorization predicts.
2. **YES-subset is the decisive metric.** The model **defaults to "No"** (76%), which is correct on no-impair genes, so both groups score high there (97% obscure / 71% famous) and the no-impair column dilutes the balanced aggregate → overall CI crosses zero. Knowledge only shows where "Yes" is required, and there the gap is large and significant at both sample sizes.
3. **Consistent across n.** Pilot (n=20/subset): 70% vs 5%, p=3.9e-5. This run (n=35/subset): 54% vs 9%, p=6.7e-5. The effect is robust to sample size; the absolute famous number depends on how deep into the fame-ranked list you go.

## What it justifies (writeup)
- The **famous-gene blocklist is empirically warranted**, measured on the model — not inferred from Insilico's undisclosed training data.
- **Retrieval-resistance lives in the obscure tail** (recall ~floor there); score the benchmark on it, keep famous genes for the contamination slice.
- Validates the **`Δ_recall`** ablation: gene name alone carries a large recall signal the phenotype must outweigh.

## Limitations
- Famous-YES capped at 35 by GenAge∩MGI availability (can't go larger without relaxing eligibility).
- "Obscure" = non-blocklist + ~0 MGI PMIDs (proxy, not a global literature count).
- Single model, single seed; endpoint nondeterministic at T=0 — a repeat run would confirm stability of the absolute numbers (the *direction/significance* is robust).
- The model's default-"No" behavior means balanced-accuracy understates recall; report the YES-subset as primary.

## Reproduce
```
.venv/bin/python scripts/contamination_probe_genes.py --n 70 --seed 1234 --workers 3 --tag n70
```
