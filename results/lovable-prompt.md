# Lovable prompt — LongevityBench-Mouse site (FULLY STATIC, no backend)

Paste this into your existing Lovable project and **attach BOTH files**: `results/dashboard_data.json`
and `results/demo_data.json`. The entire site renders **client-side from these two files — NO API,
no backend, no keys.** This replaces the old version (which had stale single-run numbers and assumed a
live API). After it rebuilds, hit **Publish**.

---

Update this single-page **scientific results site** for a benchmark testing whether an aging-biology
LLM (Longevity-LLM, 9B) can reason from a mouse's genotype+phenotype to a mutation's lifespan effect,
vs Claude Sonnet 4.6. Render **everything from the two attached JSON files** — do not invent numbers,
do not call any API. Clean, modern, credible (for scientists + hackathon judges); light theme;
colorblind-safe; one consistent color for "gene shown" vs "gene hidden" throughout.

## Part A — Results dashboard (from `dashboard_data.json`)

1. **Hero** — `project` + `tagline`; the four `headline_findings` as cards.
2. **Dataset** — the `dataset` block (74,573 genotypes; death/no-mortality/life-extending split; note
   that life-extension is rare and developmental lethality dominates).
3. **Test results** (`tests`) — for each test, gene-shown vs gene-hidden accuracy with **95% CI error
   bars**, and **Δ_recall with its CI + McNemar p + a significance badge** (green only when
   `significant: true`). Build a **forest plot of Δ_recall** with a reference line at 0 (only
   `binary_controlled` for Longevity clears it). Show both `model_under_test` and `sota` where present.
4. **Epistasis story** (`single_gene_epistasis`) — before/after: multi-gene Δ_recall (significant) →
   single-gene Δ_recall (collapses). Headline: "controlling for epistasis removes the apparent
   gene-recall reliance." Give it weight — it's a key result.
5. **Life-extension blind-spot** (`tests.ternary`) — grouped bar of per-class recall
   (shortens / no-effect / **extends**); make the tiny extends bars visually alarming. Caption: both
   models default to "a mutation is harmful or neutral."
6. **Contamination** (`contamination_probe`) — famous vs obscure recall (impairs-YES is the key cell).
7. **Reliability** (`reliability`) — a badge: 100% parsed, risky fallback 0% → errors are task, not format.
8. **Caveats & methods** — list them honestly from `caveats` + `methods`.

## Part B — Reasoning Trace Scorer demo (from `demo_data.json`) — the "extra credit"

A showcase of our reasoning-quality scorer, **pre-computed and replayed client-side** (no live model).
Render `demo_data.examples` as an interactive gallery:
- A selector/dropdown of the examples (label each with `genes` + `story`).
- For the selected example, show: the **prompt**, the model's full **trace** (reveal it with a typed/
  "streaming" animation for a live feel — but it's just replaying the stored `trace`), the model's
  **pred_label** vs the **gold_label** with a correct/incorrect badge, and the scorer's **sub_scores**
  (render each key/value in `sub_scores`: gene-hallucination, think/answer consistency, system
  grounding) plus the overall **trace_score** (0–1) as a gauge.
- Lead the gallery with the **life-extension blind-spot** examples (gold=Extends, pred wrong) — that's
  the most compelling. Include the gene-shown vs gene-hidden ablation pair side by side.
- Caption the section: "Beyond final-answer accuracy, we grade the *quality* of the model's reasoning
  trace against real biological ground truth — gene hallucination, internal consistency, and pathway
  grounding. (Pre-computed; the live scorer + 4th Claude-verification check are in `judge/`.)"

## Must-haves
- Every number/score from the JSON; significance badges from the `significant` field; CIs from the
  `*_ci95` arrays; trace-scorer values from `demo_data.json`.
- No network calls, no API keys, no backend — 100% static from the two attached files.
- Tooltips with exact values; a one-line plain caption under each chart.
- Responsive; PDF-exportable for judges.
- Don't soften the two headline negatives (epistasis-collapse; extension blind-spot) — they're the
  benchmark's most valuable findings.
