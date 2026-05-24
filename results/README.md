# results/ — one scorecard per test

Each test (task × model) is its own committed JSON here, regenerated from the raw eval outputs by
`scripts/eval_scorecard.py` (raw per-item JSONLs stay gitignored in `outputs/`; these compact
scorecards are tracked). Contamination summaries are copied from `data/contamination_probe_summary*.json`.

| file | task | model | gene-shown | gene-hidden | Δ_recall |
|---|---|---|---|---|---|
| `eval_longevity_controlled.json` | survival binary (controlled) | Longevity-LLM | 0.808 | 0.683 | +0.125 |
| `eval_longevity_controlled_run2.json` | survival binary (controlled, run 2) | Longevity-LLM | 0.783 | 0.675 | +0.108 |
| `eval_claude_controlled.json` | survival binary (controlled) | Claude Sonnet 4.6 | 0.825 | 0.692 | +0.133 |
| `eval_longevity_random.json` | survival binary (random baseline) | Longevity-LLM | 0.792 | 0.775 | +0.017 |
| `eval_claude_random.json` | survival binary (random baseline) | Claude Sonnet 4.6 | 0.867 | 0.842 | +0.025 |
| `eval_lifespan_pairwise.json` | pairwise lifespan-extension | Longevity-LLM | 0.885 | 0.827 | +0.058 |
| `eval_claude_pairwise.json` | pairwise lifespan-extension | Claude Sonnet 4.6 | 0.827 | 0.788 | +0.038 |

**Contamination probe (famous/obscure, gene-only — no Δ_recall):**

| file | model | famous | obscure | impairs-YES famous/obscure |
|---|---|---|---|---|
| `contamination_longevity-llm.json` | Longevity-LLM | 0.65 | 0.49 | 0.70 / 0.05 |
| `contamination_claude.json` | Claude Sonnet 4.6 | 0.78 | 0.68 | 0.95 / 0.40 |

Each JSON has per-condition accuracy / sensitivity / specificity / parse-fails + Δ_recall.
Regenerate: `python scripts/eval_scorecard.py`. Full registry + findings: `../docs/EVALS.md`.
