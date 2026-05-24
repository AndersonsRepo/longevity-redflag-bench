"""Aggregate repeated eval runs into mean ± std (the endpoint is non-deterministic at temp=0,
~±2pt — vault LRN-20260523-432). Groups outputs/eval_<model>_<task>_run<N>.jsonl by (model,task),
computes per-condition accuracy mean±std and Δ_recall mean±std across runs, plus the per-item flip
rate (the empirical noise). Writes one JSON per group to results/averaged/ and a combined
results/averaged_stats.md.

    python scripts/aggregate_runs.py     # scans outputs/eval_*_run*.jsonl
"""
import glob
import json
import os
import re
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402

AVG = os.path.join(config.REPO_ROOT, "results", "averaged")


def run_metrics(path):
    rs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    out = {}
    for c in ("geno_pheno", "pheno_only"):
        sub = [r for r in rs if r["condition"] == c and r["parse_failure"] is None]
        out[c] = sum(r["correct"] for r in sub) / len(sub) if sub else None
    out["delta_recall"] = (out["geno_pheno"] - out["pheno_only"]
                           if out.get("geno_pheno") is not None and out.get("pheno_only") is not None else None)
    # per-item preds for flip-rate
    out["_preds"] = {(r["genotype_id"], r["condition"]): r["pred"] for r in rs}
    return out


def ms(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {"mean": round(statistics.mean(vals), 4),
            "std": round(statistics.pstdev(vals), 4) if len(vals) > 1 else 0.0,
            "n_runs": len(vals), "runs": [round(v, 4) for v in vals]}


def main():
    files = sorted(glob.glob(os.path.join(config.OUTPUTS_DIR, "eval_*_run*.jsonl")))
    groups = defaultdict(list)
    for f in files:
        m = re.match(r"(.*)_run\d+\.jsonl$", os.path.basename(f))
        if m:
            groups[m.group(1)].append(f)
    os.makedirs(AVG, exist_ok=True)
    md = ["# Averaged eval statistics (mean ± std over repeated runs)\n",
          "Endpoint is non-deterministic at temp=0 (~±2pt); these average it out. Source: repeated",
          "`outputs/eval_<model>_<task>_run<N>.jsonl`; regenerate with `python scripts/aggregate_runs.py`.\n",
          "| group | runs | geno_pheno | pheno_only | Δ_recall | per-item flip rate |",
          "|---|---|---|---|---|---|"]
    for prefix in sorted(groups):
        runs = [run_metrics(f) for f in sorted(groups[prefix])]
        gp, po, dr = ms([r["geno_pheno"] for r in runs]), ms([r["pheno_only"] for r in runs]), ms([r["delta_recall"] for r in runs])
        # flip rate: fraction of items whose pred is not identical across all runs
        keys = set().union(*[set(r["_preds"]) for r in runs])
        flips = sum(1 for k in keys if len({r["_preds"].get(k) for r in runs}) > 1)
        flip_rate = round(flips / len(keys), 4) if keys else None
        agg = {"group": prefix, "n_runs": len(runs),
               "geno_pheno": gp, "pheno_only": po, "delta_recall": dr,
               "per_item_flip_rate": flip_rate, "source_runs": [os.path.basename(f) for f in sorted(groups[prefix])]}
        json.dump(agg, open(os.path.join(AVG, prefix + ".json"), "w"), indent=2)

        def cell(x):
            return f"{x['mean']:.3f} ± {x['std']:.3f}" if x else "-"
        md.append(f"| {prefix} | {len(runs)} | {cell(gp)} | {cell(po)} | {cell(dr)} | {flip_rate} |")
        print(f"{prefix:38} runs={len(runs)}  gp={cell(gp)}  po={cell(po)}  Δ={cell(dr)}  flip={flip_rate}")

    with open(os.path.join(config.REPO_ROOT, "results", "averaged_stats.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"\nwrote {len(groups)} averaged scorecards -> {AVG}/ + results/averaged_stats.md")


if __name__ == "__main__":
    main()
