# Lovable prompt — LongevityBench-Mouse results dashboard (REFRESH)

Paste this into Lovable and **attach `results/dashboard_data.json`** (the single source of truth —
render every number from it; do NOT invent or round-trip-estimate any figure). Optionally attach the
SVGs in `results/figures/` as fallbacks. This **supersedes the earlier dashboard**, which had stale
single-run numbers and an overstated "both models rely on gene recall" claim — the data below is the
averaged + significance-tested + epistasis-controlled version.

---

Build a clean, modern, single-page **scientific results dashboard** for a benchmark that tests whether
an aging-biology LLM (Longevity-LLM, a 9B model) can reason from a mouse's genotype + phenotype to the
mutation's effect on lifespan — compared against Claude Sonnet 4.6. Render entirely from the attached
`dashboard_data.json`. Light theme, generous whitespace, a serious/credible tone (this is for
scientists + hackathon judges), colorblind-safe palette. Use one consistent color for "gene shown"
and one for "gene hidden" across all charts.

## Sections (top to bottom)

1. **Hero** — `project` + `tagline`, and the four `headline_findings` as punchy cards.

2. **Dataset** — `dataset` block: total genotypes, the death/no-mortality/life-extending split, and
   the note that life-extension is rare (51 usable) and developmental lethality dominates.

3. **Test results** (`tests`) — the core. For each test show gene-shown vs gene-hidden accuracy with
   **95% CI error bars** and the **Δ_recall with its CI + McNemar p + a significance badge**
   (green "significant" only when `significant: true`). Build a **forest plot of Δ_recall** across
   tests with a reference line at 0 — the hero chart (only `binary_controlled` for Longevity clears 0).
   Show both `model_under_test` and `sota` where present.

4. **The epistasis story** (`single_gene_epistasis`) — a before/after: multi-gene Δ_recall (significant)
   → single-gene Δ_recall (collapses, not significant). Headline: "controlling for epistasis removes
   the apparent gene-recall reliance." This is the most important scientific result — give it weight.

5. **Can it recognize life-extension?** (`tests.ternary`) — a grouped bar of **per-class recall**
   (shortens / no-effect / **extends**) for both models. Make the **extends bars visually alarming**
   (they're 3–20/50 vs 46–48/50). Caption: both models default to "a mutation is harmful or neutral."

6. **Contamination** (`contamination_probe`) — famous vs obscure recall (impairs-YES subset is the key
   cell): Longevity 0.67/0.10, Claude 0.83/0.33. Caption: justifies the obscure-gene (retrieval-
   resistant) design.

7. **Reliability** (`reliability`) — a small badge: "100% of responses parsed; risky fallback fired 0%
   → errors are genuine task failures, not formatting."

8. **Caveats & methods** — list `caveats` honestly (wide CIs, endpoint noise, single-run Claude on some
   tasks, irreducible genetic-background confound) and cite `methods`.

## Must-haves
- Every statistic comes from `dashboard_data.json`; significance badges driven by the `significant`
  field; CIs drawn from the `*_ci95` arrays.
- Interactive tooltips with exact values; one-line plain-language caption under each chart.
- Responsive; exportable to PDF for the judges.
- Do not soften the two headline negatives (epistasis-collapse; fails-to-recognize-extension) — they
  are the benchmark's most valuable findings.
