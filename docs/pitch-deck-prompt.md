# Claude Design prompt — LongevityBench-Mouse pitch deck

Paste everything below the line into **Claude Design** (the Claude Max design feature). Optionally
**attach** `docs/hackathon-submission-one-page.pdf` and `results/dashboard_data.json` so it can pull
exact numbers and mirror the dashboard's visual language. All numbers needed are already inline below,
so it works without attachments too.

---

Create a **12-slide pitch deck (16:9, presentation-ready)** for a hackathon project. Audience:
scientists + technical judges at the **Caltech Longevity Hackathon 2026, Track 01**. The deck should
be **clean, credible, and scientific** — not a marketing deck. Think Nature-figure restraint, not
startup gradients.

## Design system (apply throughout)
- Light theme, generous whitespace, one accent color (teal `#1f6f78`); ink `#17202a`, soft gray
  `#52606d`. Avoid neon/gradients/emoji.
- **One consistent visual encoding for the core contrast**: "gene SHOWN" vs "gene HIDDEN" must use the
  same two colors on every chart. Colorblind-safe palette.
- Use real bar charts / forest plots with **95% CI error bars** where numbers appear — don't fake
  precision, don't decorate. Each chart gets a one-line plain-language caption.
- Sans-serif for body, a serif or mono accent for numbers is fine. Numbers are the hero.
- Footer on every slide: `LongevityBench-Mouse · Caltech Longevity Hackathon 2026 · Track 01`.

## The narrative (this is the spine — don't lose it)
We tested whether an aging-biology LLM **reasons** from a mouse's genotype+phenotype to its lifespan
effect, or just **recalls famous gene names**. Two headline findings, both slightly uncomfortable and
therefore valuable: (1) the apparent "gene-recall reliance" was mostly an **epistasis artifact** that
**collapses** once you control for multi-gene confounds; (2) both models share a **life-extension
blind spot** — they assume a mutation is harmful or neutral and rarely recognize life-extending ones.
A 9B specialist ties frontier Claude on the binary task. Don't soften the two negatives — they're the
benchmark's most valuable contribution.

## Slides

**1 — Title.**
- Title: **LongevityBench-Mouse**
- Subtitle: *Can an aging-biology LLM reason from genotype + phenotype to a mutation's lifespan effect — or is it recalling famous genes?*
- Model under test: **Longevity-LLM** (Insilico, Qwen3.5-9B, 28K ctx). Baseline: **Claude Sonnet 4.6**.
- Track 01, Caltech Longevity Hackathon 2026. Team: Anderson Edmond, Ibrahim, CS teammate, biology teammates.
- Links (make them visible): Live dashboard `mouse-pathfinder-data.lovable.app` · Code `github.com/AndersonsRepo/longevity-redflag-bench`.

**2 — The problem.**
Aging-biology LLMs can score well when an eval rewards recall of famous longevity genes (Sirt6, Foxo3…).
Track 01 wants *verifiable* benchmark tasks. Our question: can a model infer a mouse mutation's lifespan
effect from **genotype, zygosity, and phenotype profile** — the evidence — rather than the gene's fame?

**3 — Our approach: the ablation.**
Every task item is rendered **twice**: once with the gene name **SHOWN**, once with it **HIDDEN**
(phenotype only). The accuracy difference is **Δ_recall = acc(gene shown) − acc(gene hidden)** — a direct
measure of how much the model leans on the name vs the biology. Show a simple two-panel diagram (same
prompt, gene masked) → Δ_recall.

**4 — Dataset & ground truth (verifiable, deterministic).**
- **74,573** MGI mouse genotypes (Jackson Lab) + MP ontology; every label PMID-backed.
- Class split: **18,465** impairs-survival (death) · **54,741** no-mortality · **407** life-extending
  (**~51 usable** after curation) · 960 excluded (conditional/reproductive/ambiguous).
- Labels are **deterministic and auditable — never model-generated**. We corrected a bidirectional
  label bug (407 reversed) before scoring. Note honestly: developmental lethality dominates the death
  class, so we curate for adult/aging-onset cases.

**5 — Tasks we built.**
- **LB-0138 binary survival** — does this genotype impair survival? Balanced, curated across 12
  phenotype systems. *(Primary.)*
- **Random baseline** — same format, no curation, to show why naive MGI sampling hides the effect.
- **LB-0150 pairwise** — which mutation more likely extends lifespan?
- **LB-0154 ternary** — Shortens / No-effect / Extends (added after scientist feedback, so the model
  can pick neutral).

**6 — Finding 1 (the big one): gene-recall reliance is an epistasis artifact.**
Before/after, side by side, as a forest plot of Δ_recall with CIs and a reference line at 0:
- Mixed (multi-gene allowed): **Longevity Δ_recall = +0.100, 95% CI [0.025, 0.175], McNemar p = 0.017 → SIGNIFICANT.**
- Single-gene only (epistasis removed): **Δ_recall = +0.017, p = 0.86 → NOT significant** (shift −0.083).
- Claude shifts the same direction (+0.083 → +0.05).
- Headline caption: **"Controlling for epistasis removes the apparent gene-recall reliance — it was a multi-gene confound."**

**7 — Finding 2: the life-extension blind spot.**
Grouped bar of ternary per-class recall (shortens / no-effect / **extends**); make the tiny extends bars
visually alarming:
- Extends-recall (gene shown, n=50): **Longevity 3/50 (0.06)**, **Claude 17/50 (0.34)** — vs shortens
  recall ~46–48/50 for both.
- Persists single-gene (n=20): Longevity **1/20** gene-shown (10/20 hidden — showing the gene makes it
  *worse*); Claude 9/20.
- Caption: **"Both models default to 'a mutation is harmful or neutral.' Recognizing life-extension is the open capability gap."**

**8 — Finding 3: a 9B specialist ties the frontier.**
On the controlled binary survival task, **Longevity-LLM (9B) is statistically indistinguishable from
Claude Sonnet 4.6** (model-vs-model McNemar p = 0.36 / 0.23). Controlled accuracy: Longevity 0.775
(shown)/0.675 (hidden); Claude 0.817/0.733. Small specialized models are competitive here.

**9 — Contamination probe (retrieval-resistance check).**
Gene-only prompts, famous vs obscure genes. The key cell is the impairs-YES subset:
- Longevity: famous-YES **0.67** vs obscure-YES **0.10** (n=30 each).
- Claude: famous-YES **0.83** vs obscure-YES **0.33**.
- Caption: **"Famous longevity genes are memorized; obscure ones aren't — which is exactly why the benchmark uses obscure genes."**

**10 — Extra credit: reasoning trace scorer + live dashboard.**
Beyond final-answer accuracy, a **programmatic scorer** (`judge/score_trace.py`) grades the model's
`<think>` trace against real biology: **gene hallucination**, **think/answer consistency**, **pathway/
system grounding** (no API key), plus an optional Claude Haiku biological-verification check. On a
12-prompt reasoning stress test: **9/12 correct, mean trace score 0.682**. Live, fully-static dashboard
replays scored traces — `mouse-pathfinder-data.lovable.app`. (Show a screenshot placeholder.)

**11 — Why it meets Track 01.**
- Preferred formats: binary, ternary, pairwise MCQ.
- Verifiable ground truth: MGI + PMIDs + MP ontology (no model-generated labels).
- Leakage control: split by gene; single-gene control for epistasis; obscure-gene design.
- Formal rigor: accuracy, macro-F1, **McNemar exact tests, paired bootstrap CIs**, Δ_recall.
  Methods cited: Miller 2024 (SEM/CI), Dietterich 1998 (McNemar), Berg-Kirkpatrick 2012 (bootstrap), Card 2020 (power).
- Honest caveats: n=120/condition (wide CIs); temp-0 non-determinism (≈11% flip → 3-run majority vote);
  genetic background is an irreducible confound.

**12 — Closing.**
One line: *A verifiable mouse-genetics benchmark that separates reasoning from recall — and surfaces a
real capability gap (life-extension) that frontier and specialist models share.*
Repeat the two links big: **mouse-pathfinder-data.lovable.app** · **github.com/AndersonsRepo/longevity-redflag-bench**.

## Rules
- Every number above is verified against `results/dashboard_data.json` / `results/single_gene/comparison.md`
  / `testing/new_prompts_results.json`. Do **not** invent or round-trip-change them.
- Significance language must match: only Finding-1 mixed Δ_recall and the contamination gaps are "significant";
  single-gene Δ_recall is explicitly **not** significant. Never call life-extension a "positive" outcome.
- Keep it to **12 slides**. Tight. One idea per slide.
