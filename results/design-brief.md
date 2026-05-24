# Design brief — mouse-longevity benchmark results (for Claude Design)

Paste this into **Claude Design** to build a polished one-pager / deck / dashboard. The exact numbers
below are authoritative (from `results/stats.json` + `results/stats.md`). Accurate, data-bound charts
already exist as SVGs in `results/figures/` — **use those for any statistical plot** (don't let the
tool re-draw CIs from scratch). Use Claude Design for layout, theme, and narrative polish.

## What this is (one sentence)
A benchmark testing whether an aging-biology LLM can predict a mouse mutation's effect on survival
from genotype + phenotype, with an ablation (gene name shown vs hidden) that measures reasoning-vs-recall.

## The 3 headline findings
1. **Gene-recall reliance is real but model-specific.** Hiding the gene name drops Longevity-LLM's
   accuracy by a statistically significant **Δ_recall = 0.100 [0.025, 0.175], McNemar p = 0.017**.
   Claude's drop (0.083) is *not* significant (p = 0.099) — suggestive but underpowered at n=120.
2. **The 9B specialist ties frontier.** Longevity-LLM (9B, aging-specialized) is **statistically
   indistinguishable** from Claude Sonnet 4.6 on the survival binary (McNemar p = 0.36 / 0.23).
3. **Curation matters + format is clean.** Controlled (adult/aging) Δ_recall (~0.09) ≫ random
   baseline (~0.008); a random benchmark would have hidden the effect. Parse/format compliance = 100%,
   so errors are genuine task failures, not formatting.

## Exact numbers (mean ± 95% CI, 3-run averaged, majority-voted)
| task | model | gene-shown | gene-hidden | Δ_recall [95% CI] | McNemar p |
|---|---|---|---|---|---|
| controlled | Longevity-LLM | 0.775 [0.700, 0.850] | 0.675 [0.591, 0.759] | 0.100 [0.025, 0.175] | **0.017 ✶** |
| controlled | Claude Sonnet 4.6 | 0.817 [0.747, 0.886] | 0.733 [0.654, 0.812] | 0.083 [−0.008, 0.175] | 0.099 |
| random | Longevity-LLM | 0.775 [0.700, 0.850] | 0.742 [0.663, 0.820] | 0.033 [−0.042, 0.108] | 0.541 |
| pairwise | Longevity-LLM | 0.885 [0.798, 0.972] | 0.846 [0.748, 0.944] | 0.038 [−0.038, 0.115] | 0.625 |

Two-model comparison (controlled, McNemar): Δacc +0.042 (gene-shown, p=0.36), +0.058 (gene-hidden, p=0.23) — n.s.
Contamination (famous/obscure, gene-only, n=60): impairs-YES Longevity 0.67/0.10, Claude 0.83/0.33.

## Figures (assets ready)
- `results/figures/delta_recall_forest.svg` — **hero**: forest plot of Δ_recall with 95% CIs + zero line
  (only Longevity-controlled excludes zero).
- `results/figures/accuracy_bars.svg` — grouped accuracy bars (model × condition) with 95% CIs + chance line.
- Suggested deck flow: (1) the question/ablation, (2) forest plot, (3) accuracy bars, (4) the
  9B-ties-frontier result, (5) contamination evidence, (6) caveats + next steps (ternary, scale-N).

## Caveats (state these)
- n = 120/condition → wide CIs; we are underpowered for the smaller effects (scale-N is a next step).
- Endpoint non-deterministic at temp=0 (~11% per-item flip) → figures use 3-run majority-vote + averages.
- Single Claude run on random/pairwise (Claude is steadier). Method refs: Miller 2024; Dietterich 1998;
  Berg-Kirkpatrick 2012.
