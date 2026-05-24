# Statistical measurement — McNemar + bootstrap CIs (majority-vote over 3 runs)

SEM-based 95% CI = p ± 1.96·SEM (Miller 2024). McNemar exact p (Dietterich 1998).
Paired bootstrap 10k resamples of genotypes (Berg-Kirkpatrick 2012). Regenerate: `python scripts/stats_compare.py`.

## Per-condition accuracy ± 95% CI, and Δ_recall (McNemar + bootstrap)

| model | task | condition | accuracy ± 95% CI | parse-success |
|---|---|---|---|---|
| longevity | controlled | geno_pheno | 0.775 [0.700, 0.850] | 360/360 (100%) |
| longevity | controlled | pheno_only | 0.675 [0.591, 0.759] | 360/360 (100%) |
| claude | controlled | geno_pheno | 0.817 [0.747, 0.886] | 360/360 (100%) |
| claude | controlled | pheno_only | 0.733 [0.654, 0.812] | 360/360 (100%) |
| longevity | random | geno_pheno | 0.775 [0.700, 0.850] | 360/360 (100%) |
| longevity | random | pheno_only | 0.742 [0.663, 0.820] | 360/360 (100%) |
| longevity | pairwise | geno_pheno | 0.885 [0.798, 0.972] | 156/156 (100%) |
| longevity | pairwise | pheno_only | 0.846 [0.748, 0.944] | 156/156 (100%) |

## Δ_recall significance (gene-shown vs gene-hidden, paired by genotype)

| model | task | Δ_recall [95% CI] | McNemar b/c | exact p | significant? |
|---|---|---|---|---|---|
| longevity | controlled | 0.100 [0.025, 0.175] | 17/5 | 0.0169 | yes |
| claude | controlled | 0.083 [-0.008, 0.175] | 20/10 | 0.09874 | no |
| longevity | random | 0.033 [-0.042, 0.108] | 14/10 | 0.54126 | no |
| longevity | pairwise | 0.038 [-0.038, 0.115] | 3/1 | 0.625 | no |

## Two-model comparison — Longevity-LLM vs Claude (controlled, McNemar)

| condition | acc Longevity | acc Claude | Δacc [95% CI] | McNemar b/c | exact p | significant? |
|---|---|---|---|---|---|---|
| geno_pheno | 0.775 | 0.817 | +0.042 [-0.025, +0.117] | 7/12 | 0.35928 | no |
| pheno_only | 0.675 | 0.733 | +0.058 [-0.025, +0.142] | 9/16 | 0.22952 | no |
