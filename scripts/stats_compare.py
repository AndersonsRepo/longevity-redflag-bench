"""Statistical measurement for the eval results (scientist meeting 2): McNemar's test + paired
bootstrap 95% CIs + SEM-based CIs, over the multi-run data. Pure stdlib (no numpy/scipy).

Per (model, task) we majority-vote each item's correctness across the 3 runs (denoises the ~11%
endpoint flips), then:
  - per-condition accuracy ± 95% CI (CI = p ± 1.96·SEM, SEM = sqrt(p(1-p)/n))  [Miller 2024]
  - Δ_recall (geno_pheno − pheno_only): McNemar exact p (paired by genotype) + paired-bootstrap 95% CI
  - two-model comparison on the controlled task: McNemar Longevity-LLM vs Claude per condition
    + bootstrap 95% CI on the accuracy difference  [Dietterich 1998; Berg-Kirkpatrick 2012]
  - format compliance: parse-success rate per condition (separates format failure from task failure)

Refs: Miller 2024 arXiv:2411.00640; Dietterich 1998; Berg-Kirkpatrick 2012; Dror 2018.

    python scripts/stats_compare.py   # -> results/stats.md
"""
import glob
import json
import math
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402

BOOT, SEED = 10000, 1234


def load_runs(model, task):
    """(genotype_id,condition) -> majority-vote correct over runs; + parse-success per condition."""
    files = sorted(glob.glob(os.path.join(config.OUTPUTS_DIR, f"eval_{model}_{task}_run*.jsonl")))
    votes, parse_ok, parse_tot = defaultdict(list), defaultdict(int), defaultdict(int)
    for f in files:
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            key = (r["genotype_id"], r["condition"])
            parse_tot[r["condition"]] += 1
            if r["parse_failure"] is None:
                parse_ok[r["condition"]] += 1
            votes[key].append(r["correct"])               # parse-fail rows have correct=0
    mv = {k: (1 if sum(v) * 2 > len(v) else 0) for k, v in votes.items()}
    return mv, len(files), parse_ok, parse_tot


def acc_ci(correct_list):
    n = len(correct_list)
    if not n:
        return None
    p = sum(correct_list) / n
    sem = math.sqrt(p * (1 - p) / n)
    return {"acc": round(p, 4), "n": n, "sem": round(sem, 4),
            "ci95": [round(max(0, p - 1.96 * sem), 4), round(min(1, p + 1.96 * sem), 4)]}


def mcnemar(pairs):
    """pairs: list of (a_correct, b_correct). Returns discordant b,c and exact two-sided p."""
    b = sum(1 for a, bb in pairs if a == 1 and bb == 0)
    c = sum(1 for a, bb in pairs if a == 0 and bb == 1)
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) * (0.5 ** n))
    return b, c, round(p, 5)


def boot_ci(items, statfn, seed=SEED):
    rng = random.Random(seed)
    n = len(items)
    vals = sorted(statfn([items[rng.randrange(n)] for _ in range(n)]) for _ in range(BOOT))
    return round(vals[int(0.025 * BOOT)], 4), round(vals[int(0.975 * BOOT)], 4)


def within_model(model, task, md):
    """Δ_recall McNemar + bootstrap, paired by genotype across the two conditions."""
    gids = sorted({g for (g, c) in md if c == "geno_pheno"} & {g for (g, c) in md if c == "pheno_only"})
    pairs = [(md[(g, "geno_pheno")], md[(g, "pheno_only")]) for g in gids]
    b, c, p = mcnemar(pairs)
    lo, hi = boot_ci(pairs, lambda s: sum(a for a, _ in s) / len(s) - sum(x for _, x in s) / len(s))
    dr = sum(a for a, _ in pairs) / len(pairs) - sum(x for _, x in pairs) / len(pairs)
    return {"n_pairs": len(pairs), "delta_recall": round(dr, 4), "delta_recall_ci95": [lo, hi],
            "mcnemar_b_genoOnly": b, "mcnemar_c_phenoOnly": c, "mcnemar_p": p}


def main():
    report = ["# Statistical measurement — McNemar + bootstrap CIs (majority-vote over 3 runs)\n",
              "SEM-based 95% CI = p ± 1.96·SEM (Miller 2024). McNemar exact p (Dietterich 1998).",
              "Paired bootstrap 10k resamples of genotypes (Berg-Kirkpatrick 2012). Regenerate: "
              "`python scripts/stats_compare.py`.\n"]

    tasks = [("longevity", "controlled"), ("claude", "controlled"),
             ("longevity", "random"), ("longevity", "pairwise")]
    loaded = {}
    report.append("## Per-condition accuracy ± 95% CI, and Δ_recall (McNemar + bootstrap)\n")
    report.append("| model | task | condition | accuracy ± 95% CI | parse-success |")
    report.append("|---|---|---|---|---|")
    deltas = []
    for model, task in tasks:
        md, nruns, pok, ptot = load_runs(model, task)
        if not md:
            continue
        loaded[(model, task)] = md
        for cond in ("geno_pheno", "pheno_only"):
            cl = [v for (g, c), v in md.items() if c == cond]
            a = acc_ci(cl)
            ps = f"{pok[cond]}/{ptot[cond]} ({100*pok[cond]/ptot[cond]:.0f}%)" if ptot[cond] else "-"
            report.append(f"| {model} | {task} | {cond} | {a['acc']:.3f} [{a['ci95'][0]:.3f}, {a['ci95'][1]:.3f}] | {ps} |")
        wm = within_model(model, task, md)
        deltas.append((model, task, wm))

    report.append("\n## Δ_recall significance (gene-shown vs gene-hidden, paired by genotype)\n")
    report.append("| model | task | Δ_recall [95% CI] | McNemar b/c | exact p | significant? |")
    report.append("|---|---|---|---|---|---|")
    for model, task, wm in deltas:
        sig = "yes" if wm["mcnemar_p"] < 0.05 else "no"
        report.append(f"| {model} | {task} | {wm['delta_recall']:.3f} [{wm['delta_recall_ci95'][0]:.3f}, "
                       f"{wm['delta_recall_ci95'][1]:.3f}] | {wm['mcnemar_b_genoOnly']}/{wm['mcnemar_c_phenoOnly']} "
                       f"| {wm['mcnemar_p']} | {sig} |")

    # two-model comparison on controlled (same items)
    report.append("\n## Two-model comparison — Longevity-LLM vs Claude (controlled, McNemar)\n")
    report.append("| condition | acc Longevity | acc Claude | Δacc [95% CI] | McNemar b/c | exact p | significant? |")
    report.append("|---|---|---|---|---|---|---|")
    L, C = loaded.get(("longevity", "controlled")), loaded.get(("claude", "controlled"))
    if L and C:
        for cond in ("geno_pheno", "pheno_only"):
            gids = sorted({g for (g, c) in L if c == cond} & {g for (g, c) in C if c == cond})
            pairs = [(L[(g, cond)], C[(g, cond)]) for g in gids]   # (longevity, claude)
            b, c, p = mcnemar(pairs)                                # b=L-only-correct, c=Claude-only
            aL = sum(a for a, _ in pairs) / len(pairs)
            aC = sum(x for _, x in pairs) / len(pairs)
            lo, hi = boot_ci(pairs, lambda s: sum(x for _, x in s) / len(s) - sum(a for a, _ in s) / len(s))
            sig = "yes" if p < 0.05 else "no"
            report.append(f"| {cond} | {aL:.3f} | {aC:.3f} | {aC-aL:+.3f} [{lo:+.3f}, {hi:+.3f}] | {b}/{c} | {p} | {sig} |")

    out = os.path.join(config.REPO_ROOT, "results", "stats.md")
    open(out, "w").write("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nwrote -> {out}")


if __name__ == "__main__":
    main()
