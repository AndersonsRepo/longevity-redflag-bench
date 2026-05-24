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
O = os.path.join(config.REPO_ROOT, "outputs")
TERN_CLS = {"A": "shortens", "B": "no_effect", "C": "extends"}


def load(p, default=None):
    fp = os.path.join(R, p)
    return json.load(open(fp)) if os.path.exists(fp) else default


def _recs(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()] if os.path.exists(path) else []


def tern_per_class(path):
    """Per-class recall (shortens/no_effect/extends) by condition for one ternary eval file."""
    recs = _recs(path)
    out = {}
    for cond in ("geno_pheno", "pheno_only"):
        sub = [r for r in recs if r["condition"] == cond]
        cell = {}
        for code, name in TERN_CLS.items():
            gold = [r for r in sub if r["gold"] == code]
            cor = sum(1 for r in gold if r["pred"] == code)
            cell[name] = {"correct": cor, "n": len(gold),
                          "recall": round(cor / len(gold), 4) if gold else None}
        out[cond] = {"n": len(sub), "per_class_recall": cell}
    return out


def pairwise_delta(path):
    """acc(gene-shown) - acc(gene-hidden) for a pairwise eval file."""
    recs = _recs(path)
    by = {"geno_pheno": [], "pheno_only": []}
    for r in recs:
        if r["condition"] in by:
            by[r["condition"]].append(bool(r["correct"]))
    g = sum(by["geno_pheno"]) / len(by["geno_pheno"]) if by["geno_pheno"] else None
    p = sum(by["pheno_only"]) / len(by["pheno_only"]) if by["pheno_only"] else None
    return {"geno_pheno": round(g, 4) if g is not None else None,
            "pheno_only": round(p, 4) if p is not None else None,
            "delta_recall": round(g - p, 4) if (g is not None and p is not None) else None,
            "n_pairs": len(by["geno_pheno"])}


def stress_test_block():
    """Summarize testing/new_prompts_results.json (12 adversarial reasoning prompts)."""
    import ast
    fp = os.path.join(config.REPO_ROOT, "testing", "new_prompts_results.json")
    if not os.path.exists(fp):
        return None
    d = json.load(open(fp))

    def parse_genes(g):
        try:
            return ast.literal_eval(g) if isinstance(g, str) else (g or [])
        except Exception:
            return []

    def is_true(v):
        return str(v).lower() == "true"

    by_cat = {}
    prompts = []
    for r in d["results"]:
        cat = r.get("category", "other")
        ok = is_true(r.get("correct"))
        ts = float(r.get("trace_score") or 0)
        by_cat.setdefault(cat, {"correct": 0, "n": 0, "trace_sum": 0.0})
        by_cat[cat]["n"] += 1
        by_cat[cat]["correct"] += 1 if ok else 0
        by_cat[cat]["trace_sum"] += ts
        prompts.append({"id": r.get("id"), "category": cat, "title": r.get("title"),
                        "format": r.get("format"), "difficulty": r.get("difficulty"),
                        "genes": parse_genes(r.get("genes")), "gold": r.get("gold_answer"),
                        "pred": r.get("predicted_answer"), "correct": ok,
                        "trace_score": round(ts, 3)})
    cats = {c: {"correct": v["correct"], "n": v["n"],
                "mean_trace_score": round(v["trace_sum"] / v["n"], 3) if v["n"] else None}
            for c, v in by_cat.items()}
    return {
        "total": d["total_prompts"], "correct": d["correct"], "accuracy": d["accuracy"],
        "mean_trace_score": d["mean_trace_score"], "model": d.get("model"),
        "judge_model": d.get("judge_model"),
        "desc": "12 adversarial reasoning prompts (multi-mutant, synthetic-gene, reverse-lookup, gene-complement), scored by judge/score_trace.py against MGI-derived facts.",
        "by_category": cats, "prompts": prompts,
    }


def main():
    stats = load("stats.json", {})          # per task: conditions(acc/ci) + delta_recall(+McNemar p)
    tern = load("ternary_results.json", {})
    sg = load("single_gene/controlled_results.json", {})
    cont_l = load("contamination_n60_longevity-llm.json", {})
    cont_c = load("contamination_n60_claude.json", {})
    parse = load("parse_audit.json", {})

    # additive: single-gene ternary + pairwise (completes the epistasis story on the dashboard)
    if sg is not None:
        sg["ternary"] = {
            "Longevity-LLM": tern_per_class(os.path.join(O, "single_gene/eval_longevity_ternary_singlegene.jsonl")),
            "Claude-Sonnet-4.6": tern_per_class(os.path.join(O, "single_gene/eval_claude_ternary_singlegene.jsonl")),
        }
        sg["pairwise"] = {
            "Longevity-LLM": pairwise_delta(os.path.join(O, "single_gene/eval_longevity_pairwise_singlegene.jsonl")),
        }
        sg["extension_blindspot_note"] = (
            "The extension blind-spot PERSISTS single-gene: Longevity extends-recall stays ~1/20 gene-shown "
            "(vs 10/20 gene-hidden — showing the gene makes it worse); pairwise Δ_recall collapses to 0. "
            "Epistasis control removes the recall artifact but not the genuine capability gap."
        )

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
        "reasoning_stress_test": stress_test_block(),
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
