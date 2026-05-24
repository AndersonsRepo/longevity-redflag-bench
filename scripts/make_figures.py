"""Render publication-quality static figures from the multi-run eval data + emit results/stats.json
(the machine-readable feed for Claude Design / the web dashboard). The figures are DATA-BOUND
(plotted from the computed numbers) so they're faithful + reproducible — the hybrid approach:
accurate charts here, polish/layout in Claude Design.

Figures (results/figures/): forest plot of Δ_recall with 95% CIs (+ zero line), grouped accuracy
bar chart with 95% CIs. Reuses scripts/stats_compare.py helpers (single source of the numbers).

    python scripts/make_figures.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import stats_compare as sc  # noqa: E402
from src import config  # noqa: E402

FIG = os.path.join(config.REPO_ROOT, "results", "figures")
plt.rcParams.update({
    "figure.dpi": 150, "savefig.bbox": "tight", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.alpha": 0.3, "axes.axisbelow": True,
})
BLUE, ORANGE, GREEN, GREY = "#2c6fbb", "#e08214", "#1b7837", "#999999"

TASKS = [("longevity", "controlled"), ("claude", "controlled"),
         ("longevity", "random"), ("longevity", "pairwise")]
NICE = {"longevity": "Longevity-LLM", "claude": "Claude Sonnet 4.6"}


def main():
    os.makedirs(FIG, exist_ok=True)
    data, forest, bars = {}, [], []
    for model, task in TASKS:
        md, nruns, pok, ptot = sc.load_runs(model, task)
        if not md:
            continue
        conds = {}
        for cond in ("geno_pheno", "pheno_only"):
            conds[cond] = sc.acc_ci([v for (g, c), v in md.items() if c == cond])
        wm = sc.within_model(model, task, md)
        label = f"{NICE[model]}\n{task}"
        data[f"{model}_{task}"] = {"n_runs": nruns, "conditions": conds, "delta_recall": wm,
                                   "parse_success": {c: f"{pok[c]}/{ptot[c]}" for c in ptot}}
        sig = wm["delta_recall_ci95"][0] > 0 or wm["delta_recall_ci95"][1] < 0
        forest.append((label, wm["delta_recall"], wm["delta_recall_ci95"], wm["mcnemar_p"], sig))
        bars.append((label, conds))
    json.dump(data, open(os.path.join(config.REPO_ROOT, "results", "stats.json"), "w"), indent=2)

    # --- Figure 1: forest plot of Δ_recall ---
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ys = list(range(len(forest)))[::-1]
    for y, (label, dr, ci, p, sig) in zip(ys, forest):
        ax.errorbar(dr, y, xerr=[[dr - ci[0]], [ci[1] - dr]], fmt="o", color=GREEN if sig else GREY,
                    capsize=4, markersize=7, lw=2)
        ax.annotate(f" p={p:.3f}{' *' if sig else ''}", (ci[1], y), va="center", fontsize=9, color="#444")
    ax.axvline(0, color="#cc3333", lw=1.2, ls="--")
    ax.set_yticks(ys)
    ax.set_yticklabels([f[0] for f in forest], fontsize=9)
    ax.set_xlabel("Δ_recall  =  acc(gene shown) − acc(gene hidden)   [95% CI]")
    ax.set_title("Gene-recall reliance by task & model (significant = CI excludes 0)", fontsize=11)
    fig.savefig(os.path.join(FIG, "delta_recall_forest.png"))
    fig.savefig(os.path.join(FIG, "delta_recall_forest.svg"))
    plt.close(fig)

    # --- Figure 2: grouped accuracy bars with 95% CI ---
    fig, ax = plt.subplots(figsize=(8, 4))
    x = list(range(len(bars)))
    w = 0.38
    for i, cond, color, off in [(0, "geno_pheno", BLUE, -w / 2), (1, "pheno_only", ORANGE, w / 2)]:
        accs = [b[1][cond]["acc"] for b in bars]
        errs = [[b[1][cond]["acc"] - b[1][cond]["ci95"][0] for b in bars],
                [b[1][cond]["ci95"][1] - b[1][cond]["acc"] for b in bars]]
        ax.bar([xi + off for xi in x], accs, w, yerr=errs, capsize=4, color=color,
               label="gene shown" if cond == "geno_pheno" else "gene hidden")
    ax.axhline(0.5, color="#cc3333", lw=1, ls="--", label="chance (0.50)")
    ax.set_xticks(x)
    ax.set_xticklabels([b[0] for b in bars], fontsize=9)
    ax.set_ylabel("accuracy  [95% CI]")
    ax.set_ylim(0, 1)
    ax.set_title("Accuracy by task, model, and ablation condition", fontsize=11)
    ax.legend(fontsize=9, loc="lower right")
    fig.savefig(os.path.join(FIG, "accuracy_bars.png"))
    fig.savefig(os.path.join(FIG, "accuracy_bars.svg"))
    plt.close(fig)

    print(f"wrote results/stats.json + {FIG}/delta_recall_forest.{{png,svg}} + accuracy_bars.{{png,svg}}")


if __name__ == "__main__":
    main()
