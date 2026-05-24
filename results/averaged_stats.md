# Averaged eval statistics (mean ± std over repeated runs)

Endpoint is non-deterministic at temp=0 (~±2pt); these average it out. Source: repeated
`outputs/eval_<model>_<task>_run<N>.jsonl`; regenerate with `python scripts/aggregate_runs.py`.

| group | runs | geno_pheno | pheno_only | Δ_recall | per-item flip rate |
|---|---|---|---|---|---|
| eval_claude_controlled | 3 | 0.811 ± 0.004 | 0.739 ± 0.032 | 0.072 ± 0.028 | 0.1083 |
| eval_longevity_controlled | 3 | 0.764 ± 0.028 | 0.675 ± 0.007 | 0.089 ± 0.024 | 0.1083 |
| eval_longevity_pairwise | 3 | 0.878 ± 0.009 | 0.833 ± 0.024 | 0.045 ± 0.018 | 0.0481 |
| eval_longevity_random | 3 | 0.753 ± 0.004 | 0.744 ± 0.010 | 0.008 ± 0.007 | 0.1125 |
