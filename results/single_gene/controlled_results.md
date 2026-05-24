# Single-gene (epistasis-controlled) LB-0138 — results

Multi-gene & transgene genotypes REMOVED (single-gene only). Same controlled curation, same 120-genotype structure, both ablation conditions. Compare Delta_recall vs the (mixed) multi-gene controlled baseline.

| model | gene-shown | gene-hidden | Δ_recall [95% CI] | McNemar p | baseline Δ (multi-gene) | shift |
|---|---|---|---|---|---|---|
| Longevity-LLM | 0.708 | 0.692 | +0.017 [-0.075, +0.108] | 0.8555 | +0.100 | -0.083 |
| Claude Sonnet 4.6 | 0.750 | 0.700 | +0.050 [-0.033, +0.125] | 0.3075 | +0.083 | -0.033 |

Caveats: Longevity-LLM = 3-run majority vote; Claude = single run. n_pairs per model in results.json. CIs = paired bootstrap (5000). Endpoint non-deterministic at temp=0.
