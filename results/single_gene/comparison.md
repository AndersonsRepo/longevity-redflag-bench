# Single-gene (epistasis-controlled) vs multi-gene — comparison

Phase B: re-ran the suite single-gene-only (multi-gene/transgene removed) to isolate clean
single-gene mutations. Longevity-LLM on all tasks; Claude on controlled (general-3) + ternary.
Contamination is already single-gene by design. Source: `outputs/single_gene/eval_*`.

## Finding 1 — gene-recall reliance COLLAPSES under epistasis control
Longevity-LLM Δ_recall = acc(gene-shown) − acc(gene-hidden):

| task | multi-gene Δ_recall | single-gene Δ_recall |
|---|---|---|
| controlled | **+0.100** (McNemar p=0.017, SIG) | **+0.017** (p=0.86, n.s.) |
| pairwise | +0.058 | **+0.000** |
| random | +0.017 | +0.075 (single run, noisy) |

→ Controlled and pairwise collapse to ~0 → the apparent gene-recall reliance was **largely a
multi-gene/epistasis confound** (the scientist's concern, confirmed across tasks). Random is noisy
(single run, ±2pt) and inconclusive either way.

## Finding 2 — the life-EXTENSION blind-spot PERSISTS single-gene
Ternary `extends`-recall (n=20/class single-gene vs 50/class multi-gene):

| model | condition | single-gene extends-recall | multi-gene |
|---|---|---|---|
| Longevity-LLM | gene-shown | **1/20** | 3/50 |
| Longevity-LLM | gene-hidden | 10/20 | 17/50 |
| Claude | gene-shown | 9/20 | 17/50 |
| Claude | gene-hidden | 10/20 | 20/50 |

→ Both models STILL fail to recognize life-extension even on clean single-gene mutations with a
neutral option — the "mutation = harmful or neutral" prior is robust to the epistasis control. The
Longevity gene-shown < gene-hidden wrinkle persists (1 vs 10) — showing the gene makes it *worse*.

## Bottom line
Controlling for epistasis **removes the recall-reliance signal** (it was a multi-gene artifact) but
**not the extension blind-spot** (a genuine, robust capability gap).

## Caveats
Single-gene extenders are scarce → ternary is n=20/class, pairwise 51 pairs; single run. Wide CIs —
directional, not definitive. Multi-run + more extenders (e.g. allow famous for the extends class)
would firm these up.
