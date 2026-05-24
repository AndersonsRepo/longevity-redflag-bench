"""Generate LB-0138 (MGI genotype-survival binary) in BOTH ablation conditions, with the
CORRECTED labels (src.data.mgi.load_mgi re-derives them from the frozen mortality table).

Writes outputs/lb0138_sample.jsonl — one BenchmarkRecord per line (model_dump_json). The same
genotypes are rendered under geno_pheno and pheno_only (matched pairs) so Δ_recall is computed
item-for-item. Run validate/validate_jsonl.py afterwards.

    python scripts/build_lb0138.py [--n 60] [--seed 1234] [--include-famous]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import config
from src.data.mgi import load_mgi, summarize
from src.generate.tasks import CONDITIONS, gen_mgi_survival_binary

OUT = os.path.join(config.OUTPUTS_DIR, "lb0138_sample.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60, help="items per condition")
    ap.add_argument("--seed", type=int, default=config.SEED)
    ap.add_argument("--include-famous", action="store_true")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    rows = load_mgi(include_famous=args.include_famous, balance=True, seed=args.seed)
    s = summarize(rows)
    print("loaded rows:", s["total"], "| categories:", s["mortality_category"],
          "| flipped vs buggy:", s["label_flipped_vs_orig"])
    assert s["gene_overlap_train_test"] == 0, "LEAKAGE: gene spans train/test"

    records = []
    for cond in CONDITIONS:
        recs = gen_mgi_survival_binary(rows, cond, n=args.n, seed=args.seed)
        records.extend(recs)
        print(f"  {cond}: {len(recs)} records")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")
    print(f"wrote {len(records)} records -> {args.out}")


if __name__ == "__main__":
    main()
