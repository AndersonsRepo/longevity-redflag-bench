"""Assemble the CANONICAL dashboard feed from the current result files (supersedes general-3's
stale single-run web/results.json). Reads results/stats.json (averaged + McNemar), ternary_results,
single_gene, contamination, parse_audit -> results/dashboard_data.json. Re-run after new results.

    python scripts/build_dashboard_feed.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402

R = os.path.join(config.REPO_ROOT, "results")


def load(p, default=None):
    fp = os.path.join(R, p)
    return json.load(open(fp)) if os.path.exists(fp) else default


def main():
    stats = load("stats.json", {})          # per task: conditions(acc/ci) + delta_recall(+McNemar p)
    tern = load("ternary_results.json", {})
    sg = load("single_gene/controlled_results.json", {})
    cont_l = load("contamination_n60_longevity-llm.json", {})
    cont_c = load("contamination_n60_claude.json", {})
    parse = load("parse_audit.json", {})

    def dr(key):
        d = stats.get(key, {})
        c, drr = d.get("conditions", {}), d.get("delta_recall", {})
        return {
            "geno_pheno": c.get("geno_pheno", {}).get("acc"),
            "pheno_only": c.get("pheno_only", {}).get("acc"),
            "delta_recall": drr.get("delta_recall"),
            "delta_recall_ci95": drr.get("delta_recall_ci95"),
            "mcnemar_p": drr.get("mcnemar_p"),
            "significant": (drr.get("mcnemar_p") is not None and drr["mcnemar_p"] < 0.05),
        }

    feed = {
        "project": "LongevityBench-Mouse — Track 01, Caltech Longevity Hackathon 2026",
        "model_under_test": "Longevity-LLM (Insilico, Qwen3.5-9B, 28K ctx)",
        "sota_baseline": "Claude Sonnet 4.6",
        "tagline": "Can an aging-biology LLM reason from genotype+phenotype to a mutation's lifespan effect — or is it recalling famous genes?",
        "dataset": {
            "source": "MGI mouse genotype→phenotype (Jackson Lab) + MP ontology; labels PMID-backed",
            "total_genotypes": 74573, "impairs_survival_death": 18465, "no_mortality": 54741,
            "life_extending": 407, "usable_life_extending": 51,
            "note": "Developmental lethality dominates the death class; we curate for adult/aging-onset (longevity-relevant) cases.",
        },
        "headline_findings": [
            "Gene-recall reliance is a MULTI-GENE/epistasis artifact: significant on the mixed set (Longevity Δ_recall 0.100, p=0.017) but COLLAPSES to non-significant on clean single-gene mutations (Δ 0.017, p=0.86).",
            "Both models largely FAIL to recognize life-EXTENSION (ternary extends-recall 3–20/50 vs shortens 46–48/50) — they default to 'a mutation is harmful or neutral'.",
            "The 9B specialist is statistically indistinguishable from Claude Sonnet 4.6 on the survival binary (McNemar p=0.36/0.23).",
            "Famous longevity genes are recalled, obscure ones are not (gene-only probe) — justifying the retrieval-resistant obscure-gene design.",
        ],
        "tests": {
            "binary_controlled": {"model_under_test": dr("longevity_controlled"), "sota": dr("claude_controlled"),
                                  "desc": "Does this genotype impair survival? (deleterious vs neutral), adult/aging-curated"},
            "binary_random": {"model_under_test": dr("longevity_random"),
                              "desc": "Same task, unstratified random baseline (control: shows curation exposes the effect)"},
            "pairwise_extension": {"model_under_test": dr("longevity_pairwise"),
                                   "desc": "Which strain's mutation extends lifespan? (forced choice, chance 0.50)"},
            "ternary": tern,
        },
        "single_gene_epistasis": sg,
        "contamination_probe": {"longevity_llm": cont_l, "claude": cont_c,
                                "desc": "gene-name-only; famous (GenAge) vs obscure; impairs-YES recall is the decisive cell"},
        "reliability": {"parse_audit": parse,
                        "note": "100% of responses parsed; the risky fallback fired 0% — errors are task failures, not format."},
        "caveats": [
            "n=120/condition → wide CIs; underpowered for the smaller effects (Claude Δ_recall, model gaps).",
            "Endpoint non-deterministic at temp=0 (~11% per-item flip) → binary/pairwise use 3-run averaging/majority-vote.",
            "Claude single-gene + random/pairwise = single run (Claude steadier than the vLLM endpoint).",
            "Genetic background is an irreducible confound (24,224 distinct strings → no matched controls).",
        ],
        "methods": ["Miller 2024 (arXiv:2411.00640) SEM/CI", "Dietterich 1998 McNemar",
                    "Berg-Kirkpatrick 2012 paired bootstrap", "Card 2020 power"],
        "figures": ["results/figures/delta_recall_forest.svg", "results/figures/accuracy_bars.svg",
                    "results/figures/mcnemar_tables.svg"],
    }
    out = os.path.join(R, "dashboard_data.json")
    json.dump(feed, open(out, "w"), indent=2)
    print(f"wrote {out}")
    print("  tests:", list(feed["tests"].keys()), "| single_gene:", bool(sg), "| contamination:", bool(cont_l))


if __name__ == "__main__":
    main()
