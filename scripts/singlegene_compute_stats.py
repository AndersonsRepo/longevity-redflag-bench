"""Compute single-gene (epistasis-controlled) LB-0138 stats and compare to the multi-gene
baseline. Self-contained, additive — reads only the single_gene/ eval outputs + the baseline
numbers in web/data/headline.json. Writes results.json + results.md in this folder.

  python outputs/single_gene/compute_stats.py
"""
import json
import math
import os
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CONDS = ("geno_pheno", "pheno_only")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def correctness_by_item(records):
    """{(genotype_id, condition): correct_bool} for a single run."""
    return {(r["genotype_id"], r["condition"]): bool(r["correct"]) for r in records}


def majority_correct(run_maps):
    """Majority-vote `correct` across runs, per (genotype_id, condition)."""
    keys = set().union(*[set(m) for m in run_maps])
    out = {}
    for k in keys:
        votes = [m[k] for m in run_maps if k in m]
        out[k] = sum(votes) > len(votes) / 2
    return out


def acc(cmap, cond):
    vals = [v for (gid, c), v in cmap.items() if c == cond]
    return sum(vals) / len(vals) if vals else float("nan"), len(vals)


def paired(cmap):
    """List of (correct_geno, correct_pheno) for items present in both conditions."""
    gids = {gid for (gid, c) in cmap}
    out = []
    for gid in gids:
        kg, kp = (gid, "geno_pheno"), (gid, "pheno_only")
        if kg in cmap and kp in cmap:
            out.append((cmap[kg], cmap[kp]))
    return out


def mcnemar(pairs):
    b = sum(1 for g, p in pairs if g and not p)   # right when shown, wrong when hidden
    c = sum(1 for g, p in pairs if p and not g)   # the reverse
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) * (0.5 ** n)
    return b, c, min(1.0, 2 * tail)


def bootstrap_delta_ci(pairs, n_boot=5000, seed=1234):
    if not pairs:
        return [float("nan"), float("nan")]
    rng = random.Random(seed)
    deltas = []
    m = len(pairs)
    for _ in range(n_boot):
        sample = [pairs[rng.randrange(m)] for _ in range(m)]
        gp = sum(g for g, _ in sample) / m
        po = sum(p for _, p in sample) / m
        deltas.append(gp - po)
    deltas.sort()
    lo = deltas[int(0.025 * n_boot)]
    hi = deltas[int(0.975 * n_boot)]
    return [round(lo, 3), round(hi, 3)]


def summarize(cmap, label):
    a_gp, n_gp = acc(cmap, "geno_pheno")
    a_po, n_po = acc(cmap, "pheno_only")
    pairs = paired(cmap)
    b, c, p = mcnemar(pairs)
    ci = bootstrap_delta_ci(pairs)
    return {
        "label": label,
        "n_pairs": len(pairs),
        "geno_pheno": {"acc": round(a_gp, 3), "n": n_gp},
        "pheno_only": {"acc": round(a_po, 3), "n": n_po},
        "delta_recall": round(a_gp - a_po, 3),
        "delta_recall_ci95": ci,
        "mcnemar": {"b": b, "c": c, "p": round(p, 4)},
    }


def main():
    # ---- Longevity-LLM: 3 runs -> per-run + majority vote ----
    lvg_runs = []
    for r in (1, 2, 3):
        path = os.path.join(HERE, f"eval_longevity_controlled_singlegene_run{r}.jsonl")
        if os.path.exists(path):
            lvg_runs.append(correctness_by_item(load(path)))
    out = {"task": "LB-0138 survival binary, CONTROLLED, single-gene only (epistasis-controlled)",
           "models": {}}

    if lvg_runs:
        per_run = []
        for i, m in enumerate(lvg_runs, 1):
            a_gp, _ = acc(m, "geno_pheno")
            a_po, _ = acc(m, "pheno_only")
            per_run.append({"run": i, "geno_pheno": round(a_gp, 3),
                            "pheno_only": round(a_po, 3), "delta": round(a_gp - a_po, 3)})
        maj = majority_correct(lvg_runs)
        summ = summarize(maj, "Longevity-LLM (3-run majority vote)")
        summ["per_run"] = per_run
        summ["n_runs"] = len(lvg_runs)
        out["models"]["Longevity-LLM"] = summ

    # ---- Claude: single run ----
    cpath = os.path.join(HERE, "eval_claude_controlled_singlegene.jsonl")
    if os.path.exists(cpath):
        cmap = correctness_by_item(load(cpath))
        out["models"]["Claude Sonnet 4.6"] = summarize(cmap, "Claude Sonnet 4.6 (single run)")

    # ---- baseline (multi-gene controlled) from headline.json ----
    hl = json.load(open(os.path.join(REPO, "web", "data", "headline.json")))
    base = {}
    for e in hl["ablation"]:
        if e["task"] == "controlled":
            base[e["model"]] = {
                "geno_pheno": e["geneShown"]["acc"], "pheno_only": e["geneHidden"]["acc"],
                "delta_recall": e["deltaRecall"]["value"], "delta_ci95": e["deltaRecall"]["ci95"],
                "mcnemar_p": e["mcnemar"]["p"]}
    out["baseline_multigene_controlled"] = base

    # ---- comparison ----
    comp = []
    for model, summ in out["models"].items():
        if model in base:
            d_sg = summ["delta_recall"]
            d_mg = base[model]["delta_recall"]
            comp.append({"model": model, "delta_singlegene": d_sg, "delta_multigene": d_mg,
                         "shift": round(d_sg - d_mg, 3)})
    out["comparison_delta_recall"] = comp

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(out, f, indent=2)

    # ---- markdown ----
    lines = ["# Single-gene (epistasis-controlled) LB-0138 — results", "",
             "Multi-gene & transgene genotypes REMOVED (single-gene only). Same controlled curation, "
             "same 120-genotype structure, both ablation conditions. Compare Delta_recall vs the "
             "(mixed) multi-gene controlled baseline.", "",
             "| model | gene-shown | gene-hidden | Δ_recall [95% CI] | McNemar p | baseline Δ (multi-gene) | shift |",
             "|---|---|---|---|---|---|---|"]
    for model, s in out["models"].items():
        b = base.get(model, {})
        ci = s["delta_recall_ci95"]
        lines.append(
            f"| {model} | {s['geno_pheno']['acc']:.3f} | {s['pheno_only']['acc']:.3f} | "
            f"{s['delta_recall']:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}] | {s['mcnemar']['p']:.4f} | "
            f"{b.get('delta_recall', float('nan')):+.3f} | "
            f"{s['delta_recall'] - b.get('delta_recall', 0):+.3f} |")
    lines += ["", "Caveats: Longevity-LLM = 3-run majority vote; Claude = single run. "
              "n_pairs per model in results.json. CIs = paired bootstrap (5000). "
              "Endpoint non-deterministic at temp=0."]
    open(os.path.join(HERE, "results.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote -> {os.path.join(HERE, 'results.json')} + results.md")


if __name__ == "__main__":
    main()
