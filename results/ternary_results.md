# LB-0154 ternary — lifespan direction (shortens / no-effect / extends)

3-way, chance = 0.33. 50/class (extends-capped), multi-gene allowed (Phase A, no single-gene fix),
single run. Per-class recall + macro-F1 from `outputs/eval_<model>_ternary.jsonl`.

| model | condition | accuracy | macro-F1 | recall: shortens / no-effect / **extends** |
|---|---|---|---|---|
| Longevity-LLM | geno_pheno | 0.600 | 0.508 | 46/50 / 41/50 / **3/50** |
| Longevity-LLM | pheno_only | 0.620 | 0.602 | 46/50 / 30/50 / **17/50** |
| Claude-Sonnet-4.6 | geno_pheno | 0.667 | 0.653 | 48/50 / 35/50 / **17/50** |
| Claude-Sonnet-4.6 | pheno_only | 0.580 | 0.560 | 47/50 / 20/50 / **20/50** |

**Headline:** both models largely fail to recognize life-EXTENSION (extends-recall far below
shortens/no-effect) — they default to 'mutation = harmful or neutral'. shortens & no-effect are
handled well. Caveats: single run, n=50/class, extends not single-gene-filtered.
