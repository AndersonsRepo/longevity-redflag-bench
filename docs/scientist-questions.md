# Questions for the company scientist — mouse-strain longevity benchmark

**Goal restated:** *MGI provides detailed murine strain annotations (phenotype + allele profiles).
Can a model identify the effect of a mutation on murine lifespan?*

## Where we are (so the meeting can skip the settled parts)
We've built `LB-0138`: genotype + phenotype profile → **does this genotype impair survival? (Yes/No)**,
scored against corrected MGI labels, rendered in two ablation conditions (gene name shown vs hidden).
**Spec-compliant already:** split **by gene** (no gene spans train/test), verifiable ground truth
(MGI PMIDs), binary format with balanced-accuracy/F1/MCC, ≤30K cl100k tokens, JSONL ChatML, no
sequence modality, N=240 (≥50). First eval: gene-shown 0.81 vs gene-hidden 0.68 (Δ_recall +0.125).

So the open questions below are **scientific/design judgment calls**, not format issues.

---

## A. Scope & framing of "lifespan effect"

1. **Developmental lethality vs adult/aging death.** ~67–79% of MGI "impairs survival" genotypes
   die *developmentally* (embryonic/neonatal); only ~20% are adult/aging-onset. The goal says
   "lifespan." Should the benchmark (a) scope to **adult/aging-onset** effects = true longevity,
   (b) treat developmental viability as a **separate task**, or (c) keep both? *(We currently lead
   with adult/aging + one developmental anchor per category.)*

2. **Healthspan vs lifespan.** Many phenotypes impair health without changing lifespan. For "effect
   on lifespan" specifically, should healthspan-only phenotypes be excluded, or are they fair input?

## B. Ground-truth validity (we fixed a labeling bug — please sanity-check)

The original build labeled *any* MP mortality/aging-subtree term as "impairs survival." That's wrong
for several term types; we re-classified the 128 terms. Please check the edge calls:

3. **`decreased tumor-free survival time`** → we count as survival-impairing (earlier cancer death).
   Correct, or is it a healthspan/tumor metric, not lifespan?
4. **Challenge-induced mortality** (e.g. `increased susceptibility to viral infection induced
   mortality`) → we **exclude** from the baseline survival task (the animal dies only when
   challenged). Should this instead be its own **"stress-survival"** task?
5. **Reproductive** (`premature ovarian failure`, `pregnancy-related premature death`) → excluded as
   not-organismal-lifespan. Agree?
6. **Conflicting annotations.** 6 genotypes carry BOTH a death term and `extended life span` (from
   different studies). We exclude them as ambiguous — is there a principled resolution instead?

7. **"Too-telling" phenotypes (leakage).** The model infers survival from the *non-mortality*
   phenotypes. Some are near-deterministic for lethality (e.g. `failure of gastrulation`, `absent
   heartbeat`). **Which phenotype classes effectively give away the answer**, and should we exclude
   them to force subtler reasoning rather than pattern-spotting an obviously-lethal phenotype?

## C. The scarce but most-interesting class: life EXTENSION

8. Genuine life-**extending** genotypes are rare: ~51 usable (`extended life span`/`slow aging`) vs
   ~3,300 shortening. The sharpest longevity question is "does this mutation **extend** lifespan?"
   How would you prioritize capturing it — a dedicated **diagnostic slice**, broadening to
   **protective** effects, or pulling **quantitative %-lifespan** data (OpenGenes/SynergyAge)?
9. Are MGI's `extended life span` annotations **reliable enough** as ground truth, or do you trust a
   quantitative source (SynergyAge/OpenGenes %-change) more for the extension direction?

## D. Confounders & rigor

10. **Genetic background.** MGI genotypes sit on different strain backgrounds. For "effect of *the
    mutation*," how much does background confound the survival outcome? Should we restrict to
    **matched-background** comparisons or **allelic series on the same gene** for a clean causal read?
11. **Split covariate.** Spec wants leakage-safe splits; we split **by gene**. Is gene right, or
    should it be **gene family / pathway / genetic background**? (What's the mouse-genotype analog of
    the spec's "protein family"?)
12. **Direction of effect (mechanism).** Loss-of-function (knockout) vs gain-of-function
    (overexpression) of the *same* gene can have **opposite** lifespan effects. Is a task that tests
    whether the model reasons about the **direction** of the perturbation — rather than defaulting to
    "mutation = bad" — the most valuable probe of genuine reasoning? (We have an
    `expression_direction` field to support this.)
13. **Zygosity / dominance.** Does the lifespan effect commonly depend on zygosity (recessive vs
    dominant)? Worth a task pairing the same allele homozygous vs heterozygous?

## E. Additional formats & data sources (Diversity)

14. **Quantitative regression.** OpenGenes has ~424 mouse genetic experiments with numeric %-lifespan
    change. Worth a **regression** task? Are cross-study %-changes comparable enough (different
    strains/conditions) to be fair ground truth?
15. **IMPC viability.** IMPC has systematic homozygous viability (viable/subviable/lethal). Is IMPC's
    **systematic screen** cleaner ground truth than MGI's literature-curated annotations for a
    **ternary** viability task?

## F. What's most useful to YOU

16. **What capability do you most want this benchmark to measure** about your aging LLM —
    survival/viability prediction, mechanism/direction reasoning, intervention/longevity prediction,
    or something else? Is "genotype + phenotype → lifespan effect" the framing you'd choose, or would
    you reframe it?
17. **Is the ablation valid?** We measure reasoning-vs-recall by hiding the gene name (Δ_recall). Does
    the gene name carry *legitimate* mechanistic information a researcher would use — i.e., does hiding
    it remove genuine reasoning signal, not just memorized facts?

---

## If short on time — the top 5
**16** (what do you want measured / is the framing right) · **1** (developmental vs adult/aging
scope) · **7** (which phenotypes are too-telling) · **8** (how to handle the rare life-extension
class) · **12** (direction-of-effect as the deepest reasoning probe).
