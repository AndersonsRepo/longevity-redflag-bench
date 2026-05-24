# Frontend data — LongevityBench-Mouse (Caltech Longevity Hackathon 2026, Track 01)

Everything the Lovable frontend needs is in this folder. Drop the whole folder into the app's
`/public/data/` and point the loaders at the two JSON indexes below. **Two layers:**

| Layer | File(s) | Used by |
|---|---|---|
| **Static source of truth** | `headline.json` | Hero, dataset strip, the 3 findings, the ablation forest/significance table, ternary, contamination, caveats. |
| **Interactive explorer** | `manifest.json` + the `eval_*.jsonl` files | The in-browser data explorer: recomputes accuracy / Δ_recall / McNemar live and shows each model's full reasoning trace. |

> Rule: **static sections read `headline.json`; the explorer reads the JSONL via `manifest.json`.**
> The explorer recomputes per-run and may differ slightly from the headline numbers — that's
> expected (the endpoint is non-deterministic at temp 0). `headline.json` is the citable set.

---

## 1. `headline.json` — the authoritative numbers
3-run **majority-voted** binary/pairwise results with paired-bootstrap 95% CIs and exact McNemar
p-values (from `results/stats.json`), plus dataset stats, the 3 findings, the ternary table, the
contamination probe, the quantitative-arm strip, and caveats. Render the static page entirely from
this — never hardcode a number in JSX. Key fields: `dataset`, `ablation[]`, `ternary`,
`contamination`, `findings[]`, `caveats[]`, `quantDataset`.

## 2. `manifest.json` — the explorer file map
Lists every per-item `eval_*.jsonl` with its `{model, split, run, pairs}` label (filenames don't
self-describe — use this map), the record schema, and the exact compute recipe. Three blocks:
- `files[]` + `groups[]` — the **binary** Δ_recall set (the explorer's main view).
- `ternary` — the 3-class LB-0154 files (see §4).
- `single_gene` — the epistasis-controlled rebuild (see §5).

## 3. Binary eval files (the Δ_recall explorer)
14 files: Longevity-LLM × {controlled, random, pairwise} × 3 runs, Claude × controlled × 3 runs,
Claude × {random, pairwise} × 1 run. Each line = one evaluated item:
`{ genotype_id, condition (geno_pheno=gene SHOWN | pheno_only=gene HIDDEN), mortality_category,
lethality_stage, gold, pred, correct, parse_path, latency_s, raw }`. `raw` is the model's **full**
response (reasoning trace + final `Answer: X`) — the payoff for the item drawer.
Compute: `accuracy = mean(correct)`; `Δ_recall = acc(geno_pheno) − acc(pheno_only)`; pair by
`genotype_id` for McNemar. Default aggregation = 3-run majority vote.

## 4. Ternary (LB-0154) — `eval_{longevity,claude}_ternary.jsonl` + `ternary_prompts.jsonl`
**A separate 3-class task: A = shortens, B = no-effect, C = extends (chance 0.33, 50/class, 1 run).**
Do **not** run the binary Δ_recall/McNemar logic on these — compute overall accuracy + per-class
recall + macro-F1 (authoritative aggregates already in `headline.json → ternary`). The item drawer
(gold / pred / correct / raw) works unchanged since A/B/C parse the same way.

**The story to tell:** both models handle *shortens* and *no-effect* well but **largely fail to
recognize life-EXTENSION** — extends-recall is far below the others (Longevity 0.06 / Claude 0.34
with the gene shown). They default to "mutation = harmful or neutral." A striking detail: showing
the gene name *hurts* Longevity-LLM's extends-recall (0.34 → 0.06) — even named famous longevity
genes get read as harmful. Suggested render: a small grouped bar of per-class recall (3 classes ×
2 conditions) per model, with the collapsing `extends` bar as the visual hook.

## 5. `single_gene/` — epistasis-controlled rebuild (multi-gene removed)
The controlled binary task rebuilt with **multi-gene & transgene genotypes removed** (single-gene
only), isolating each mutation's effect from masking by a second gene. Same 120-genotype structure,
same two ablation conditions. Its own `manifest.json` + `headline.json` + `results.json` live in the
subfolder. Use it for a **single-gene vs multi-gene Δ_recall comparison** — does removing the
epistasis confound change the gene-recall signal? (See `single_gene/results.md` for the headline
shift.)

---

### Design reminder
Editorial / Nature / Our-World-in-Data feel — muted ink-on-paper, one accent, serif headings, mono
for IDs/p-values, Recharts styled flat. No gradients, glassmorphism, emoji, default-blue, fake
testimonials, or fade-up-on-scroll. The Δ_recall forest plot and the gene-shown-vs-hidden gap are
the visual hero. Numbers regenerated 2026-05-24; endpoint non-deterministic at temp 0 (~±2 pts).
