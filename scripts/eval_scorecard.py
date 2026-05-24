"""Turn each eval JSONL into a compact, committed per-test SCORECARD (so every test is its own
tellable file in the repo, instead of living only in the gitignored raw outputs or one big doc).

Reads eval outputs (one row per item: condition/gold/pred/correct/parse_failure) and writes one
JSON per file to results/<stem>.json with: per-condition accuracy / sensitivity / specificity /
parse-fails, Δ_recall, n. Raw per-item JSONLs stay gitignored; these scorecards are tracked.

    python scripts/eval_scorecard.py                 # all outputs/eval_*.jsonl (skips legacy dup)
    python scripts/eval_scorecard.py outputs/eval_claude_random.jsonl
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402

RESULTS = os.path.join(config.REPO_ROOT, "results")


def scorecard(path):
    rs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    stem = os.path.splitext(os.path.basename(path))[0]
    model = "claude" if "claude" in stem else ("longevity-llm" if "longevity" in stem or "lifespan" in stem else "?")
    task = ("pairwise_lifespan_extension" if "pairwise" in stem
            else "survival_binary_random" if "random" in stem
            else "survival_binary_controlled" if "controlled" in stem else stem)
    conds = {}
    for c in sorted({r["condition"] for r in rs if r.get("condition")}):
        sub = [r for r in rs if r["condition"] == c]
        parsed = [r for r in sub if r["parse_failure"] is None]
        pos = [r for r in parsed if r["gold"] == "A"]
        neg = [r for r in parsed if r["gold"] == "B"]
        conds[c] = {
            "n": len(sub), "parsed": len(parsed), "parse_fail": len(sub) - len(parsed),
            "accuracy": round(sum(r["correct"] for r in parsed) / len(parsed), 4) if parsed else None,
            "sensitivity_pos": round(sum(r["correct"] for r in pos) / len(pos), 4) if pos else None,
            "specificity_neg": round(sum(r["correct"] for r in neg) / len(neg), 4) if neg else None,
        }
    dr = None
    if all(k in conds and conds[k]["accuracy"] is not None for k in ("geno_pheno", "pheno_only")):
        dr = round(conds["geno_pheno"]["accuracy"] - conds["pheno_only"]["accuracy"], 4)
    return {"source_file": os.path.basename(path), "model": model, "task": task,
            "n_records": len(rs), "delta_recall": dr, "conditions": conds}


def main():
    paths = sys.argv[1:] or [p for p in sorted(glob.glob(os.path.join(config.OUTPUTS_DIR, "eval_*.jsonl")))
                             if "lb0138_longevity" not in p]  # skip the legacy controlled-run1 dup
    os.makedirs(RESULTS, exist_ok=True)
    print(f"{'scorecard':40} {'task':30} {'gp':>6} {'po':>6} {'Δ_recall':>9}")
    for p in paths:
        sc = scorecard(p)
        out = os.path.join(RESULTS, os.path.splitext(os.path.basename(p))[0] + ".json")
        json.dump(sc, open(out, "w"), indent=2)
        gp = sc["conditions"].get("geno_pheno", {}).get("accuracy")
        po = sc["conditions"].get("pheno_only", {}).get("accuracy")
        print(f"{os.path.basename(out):40} {sc['task']:30} "
              f"{gp if gp is not None else '-':>6} {po if po is not None else '-':>6} "
              f"{sc['delta_recall'] if sc['delta_recall'] is not None else '-':>9}")
    print(f"\nwrote {len(paths)} scorecards -> {RESULTS}/")


if __name__ == "__main__":
    main()
