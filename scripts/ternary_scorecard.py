"""Score the LB-0154 ternary (shortens/no_effect/extends) for both models: 3-way accuracy,
macro-F1, per-class recall, and the confusion matrix. Writes results/ternary_results.{json,md}.

    python scripts/ternary_scorecard.py
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402

CLS = {"A": "shortens", "B": "no_effect", "C": "extends"}
FILES = {"Longevity-LLM": "eval_longevity_ternary.jsonl", "Claude-Sonnet-4.6": "eval_claude_ternary.jsonl"}


def score(path):
    rs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    out = {}
    for cond in ("geno_pheno", "pheno_only"):
        sub = [r for r in rs if r["condition"] == cond]
        n = len(sub)
        acc = sum(r["correct"] for r in sub) / n
        recall, f1s = {}, []
        for g in "ABC":
            gc = [r for r in sub if r["gold"] == g]
            tp = sum(1 for r in sub if r["gold"] == g and r["pred"] == g)
            fp = sum(1 for r in sub if r["gold"] != g and r["pred"] == g)
            fn = sum(1 for r in sub if r["gold"] == g and r["pred"] != g)
            prec = tp / (tp + fp) if tp + fp else 0.0
            rec = tp / (tp + fn) if tp + fn else 0.0
            recall[CLS[g]] = {"correct": tp, "n": len(gc), "recall": round(rec, 3)}
            f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
        conf = {f"{CLS[r['gold']]}->{CLS.get(r['pred'], str(r['pred']))}": 0 for r in sub}
        for r in sub:
            conf[f"{CLS[r['gold']]}->{CLS.get(r['pred'], str(r['pred']))}"] += 1
        out[cond] = {"n": n, "accuracy": round(acc, 4), "macro_f1": round(sum(f1s) / 3, 4),
                     "parse_fail": sum(1 for r in sub if r["parse_failure"]),
                     "per_class_recall": recall, "confusion": conf}
    return out


def main():
    data = {m: score(os.path.join(config.OUTPUTS_DIR, f)) for m, f in FILES.items()}
    json.dump(data, open(os.path.join(config.REPO_ROOT, "results", "ternary_results.json"), "w"), indent=2)
    md = ["# LB-0154 ternary — lifespan direction (shortens / no-effect / extends)\n",
          "3-way, chance = 0.33. 50/class (extends-capped), multi-gene allowed (Phase A, no single-gene fix),",
          "single run. Per-class recall + macro-F1 from `outputs/eval_<model>_ternary.jsonl`.\n",
          "| model | condition | accuracy | macro-F1 | recall: shortens / no-effect / **extends** |",
          "|---|---|---|---|---|"]
    for m, d in data.items():
        for cond in ("geno_pheno", "pheno_only"):
            c = d[cond]
            r = c["per_class_recall"]
            md.append(f"| {m} | {cond} | {c['accuracy']:.3f} | {c['macro_f1']:.3f} | "
                      f"{r['shortens']['correct']}/50 / {r['no_effect']['correct']}/50 / "
                      f"**{r['extends']['correct']}/50** |")
    md += ["\n**Headline:** both models largely fail to recognize life-EXTENSION (extends-recall far below",
           "shortens/no-effect) — they default to 'mutation = harmful or neutral'. shortens & no-effect are",
           "handled well. Caveats: single run, n=50/class, extends not single-gene-filtered."]
    open(os.path.join(config.REPO_ROOT, "results", "ternary_results.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("\nwrote results/ternary_results.{json,md}")


if __name__ == "__main__":
    main()
