#set page(width: 8.5in, height: 11in, margin: 0.46in)
#set text(font: "Helvetica", size: 8.15pt, fill: rgb("#17202a"))
#set par(leading: 0.48em)

#let ink = rgb("#17202a")
#let soft = rgb("#52606d")
#let accent = rgb("#1f6f78")
#let pale = rgb("#eaf4f4")
#let rule = rgb("#d0d5dd")
#let good = rgb("#1f7a4d")
#let warn = rgb("#b54708")

#show heading.where(level: 1): it => [
  #set text(size: 17pt, weight: "bold", fill: ink)
  #it.body
  #v(-0.25em)
]
#show heading.where(level: 2): it => [
  #v(0.22em)
  #set text(size: 9.2pt, weight: "bold", fill: accent)
  #it.body
  #v(-0.35em)
]

#let chip(body) = box(inset: (x: 5pt, y: 2.5pt), fill: pale, radius: 2pt)[#text(size: 7.2pt, weight: "bold", fill: accent)[#body]]
#let card(title, value, detail, color: accent) = box(width: 100%, inset: 5pt, stroke: 0.45pt + rule, radius: 3pt)[
  #text(size: 6.8pt, weight: "bold", fill: soft)[#title] \
  #text(size: 13.5pt, weight: "bold", fill: color)[#value] \
  #text(size: 7pt, fill: soft)[#detail]
]
#let tight-list(items) = {
  for item in items [
    #text(fill: accent, weight: "bold")[•] #item \
  ]
}

= LongevityBench-Mouse
#text(size: 9pt, fill: soft)[A mouse-genetics benchmark for testing whether aging LLMs reason from phenotype evidence or lean on memorized gene names.]

#v(0.06in)
#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 5pt)[
  #card("Dataset", "74,573", "MGI mouse genotypes")
][
  #card("Main eval", "240", "controlled binary prompts")
][
  #card("Single-gene control", "120", "epistasis removed")
][
  #card("Extra credit", "12", "reasoning stress-test prompts", color: warn)
]

#grid(columns: (1.08fr, 0.92fr), gutter: 0.2in)[
  == Problem
  Aging-biology LLMs can look good when an eval rewards recall of famous genes. Track 01 asks for verifiable benchmark tasks; our question was: *can a model infer a mouse mutation's lifespan effect from genotype, zygosity, and phenotype profile?*

  == Solution
  We built ChatML/JSONL tasks from mouse genotype-phenotype annotations. Mortality/aging MP terms become the label; all non-mortality phenotype terms become the prompt. Each item is rendered twice: gene shown and gene hidden. The difference, `Delta_recall`, measures how much the model benefits from seeing the gene name.

  == Ground Truth
  Labels are deterministic and auditable. MGI curators assign phenotype terms from published papers; MP ontology defines the mortality/aging subtree; we corrected bidirectional label bugs before scoring. No model-generated labels are used.
][
  == Data Sources
  #tight-list((
    [*MGI* `MGI_PhenoGenoMP.rpt`: genotype, allele, zygosity, MP terms, PMIDs.],
    [*MP ontology* `mp.obo`: survival label boundary and phenotype-system categories.],
    [*GenAge/HAGR*: famous-gene blocklist for contamination control.],
    [*SynergyAge/OpenGenes*: explored for quantitative lifespan, but too sparse for the main task.]
  ))

  == Tech Stack
  Python, pandas, Pydantic, OpenAI-compatible Longevity-LLM endpoint, Claude Sonnet 4.6, Claude Haiku judge, Typst, Lovable/TanStack/Vite/React dashboard, static JSON feeds.

  == Team
  Anderson Edmond, Ibrahim, CS teammate, biology teammates.
]

#v(0.04in)
#line(length: 100%, stroke: 0.6pt + rule)

#grid(columns: (1fr, 1fr), gutter: 0.2in)[
  == Tests We Built
  #tight-list((
    [*LB-0138 binary survival:* Does this genotype impair survival? Controlled adult/aging curation across 12 phenotype systems; balanced yes/no; gene-shown vs gene-hidden matched pairs.],
    [*Random baseline:* Same binary format without curation, proving why random MGI sampling hides the effect.],
    [*LB-0150 pairwise extension:* Which mutation is more likely to extend lifespan?],
    [*LB-0154 ternary:* Shortens / no-effect / extends, added after scientist feedback so the model can choose neutral.]
  ))
][
  == Extra Credit
  #tight-list((
    [*Reasoning trace scorer* (`judge/score_trace.py`): checks gene hallucination, think/answer consistency, and pathway/system grounding against MGI-derived facts; optional Claude Haiku biological verification.],
    [*Live/demo API* (`api_server.py`, `judge/live_scorer.py`): streams Longevity-LLM reasoning plus scorer output for the frontend.],
    [*12-prompt stress test* (`testing/run_new_prompts.py`): multi-mutant, synthetic-gene, reverse-lookup, and gene-complement prompts. Result: 9/12 accuracy, mean trace score 0.682.]
  ))
]

#v(0.02in)
#grid(columns: (1fr, 1fr, 1fr), gutter: 5pt)[
  #card("Mixed controlled Delta_recall", "+0.100", "Longevity-LLM, p=0.017", color: good)
][
  #card("Single-gene Delta_recall", "+0.017", "not significant, p=0.86", color: accent)
][
  #card("Life-extension recall", "1/20", "Longevity gene-shown extenders", color: warn)
]

#grid(columns: (1fr, 1fr), gutter: 0.2in)[
  == Key Findings
  #tight-list((
    [*Gene-name reliance was mostly an epistasis artifact.* The mixed controlled set showed significant `Delta_recall`, but after removing multi-gene/transgene cases it collapsed to non-significant.],
    [*The life-extension blind spot persisted.* In ternary tests, both models recognized shortens/no-effect far better than extends; they default toward "mutation is harmful or neutral."],
    [*The 9B specialist tied frontier on binary survival.* Longevity-LLM was statistically indistinguishable from Claude Sonnet 4.6 on the controlled binary task.],
    [*Famous genes are memorized.* Gene-only contamination probes showed famous >> obscure recall, validating the obscure-gene design.]
  ))
][
  == Why It Meets Track 01
  #tight-list((
    [Preferred formats: binary, ternary, pairwise MCQ.],
    [Verifiable ground truth: MGI + PMIDs + MP ontology.],
    [Leakage control: train/test split by gene components; single-gene control for epistasis.],
    [Formal metrics: accuracy, macro-F1, McNemar exact tests, paired bootstrap CIs, `Delta_recall`.],
    [No sequence modality and no free-text expert scoring required for final answers.]
  ))
]

#v(0.02in)
#box(width: 100%, inset: 6pt, fill: rgb("#f8fafc"), stroke: 0.45pt + rule, radius: 3pt)[
  #text(size: 7.25pt, fill: soft)[
    Primary artifacts: `docs/LABELING.md`, `docs/EVALS.md`, `results/stats.json`,
    `results/single_gene/comparison.md`, `results/ternary_results.md`,
    `testing/new_prompts_results.json`, `judge/score_trace.py`, and the live Lovable dashboard backed by `results/dashboard_data.json`.
  ]
]
