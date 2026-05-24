"""Render the LONGEVITY benchmark to prompts: take the categorized selection (controlled or
random) and emit each selected genotype in BOTH ablation conditions as LB-0138 BenchmarkRecords.

Reuses the selection logic in scripts/sample_longevity_benchmark.py (controlled = 12 curated
branches, 4 adult/aging + 1 developmental + 5 `none` per branch; random = size-matched, no
stratification) and the shared record builder src.generate.tasks.make_survival_record — so these
prompts are identical in shape to the rest of the benchmark and the same genotypes appear in both
conditions (matched pairs → Δ_recall is item-for-item).

    python scripts/build_longevity_benchmark.py --mode controlled    # -> outputs/longevity_controlled.jsonl
    python scripts/build_longevity_benchmark.py --mode random
"""
import argparse
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(__file__))  # import the sibling sampler

import csv  # noqa: E402

import sample_longevity_benchmark as slb  # noqa: E402
from src import config  # noqa: E402
from src.data.mgi import load_mgi  # noqa: E402
from src.generate.profiles import CONDITIONS  # noqa: E402
from src.generate.tasks import make_survival_record  # noqa: E402

csv.field_size_limit(10 ** 7)
LABELED = config.DATA_DIR / "mgi_labeled.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["controlled", "random"], default="controlled")
    ap.add_argument("--pos-adult", type=int, default=4)
    ap.add_argument("--pos-dev", type=int, default=1)
    ap.add_argument("--neg", type=int, default=5)
    ap.add_argument("--seed", type=int, default=config.SEED)
    a = ap.parse_args()

    rows = load_mgi(balance=False, include_famous=False, seed=a.seed)
    ps_map = {r["genotype_id"]: r["primary_system"]
              for r in csv.DictReader(LABELED.open(encoding="utf-8"))}
    rng = random.Random(a.seed)

    if a.mode == "controlled":
        selected, _ = slb.controlled(rows, ps_map, rng, a)
    else:
        n_pos = (a.pos_adult + a.pos_dev) * len(slb.CURATED)
        n_neg = a.neg * len(slb.CURATED)
        selected = slb.random_mode(rows, ps_map, rng, n_pos, n_neg)
    genos = [row for _, _, row in selected]   # render the SAME genotypes in both conditions

    records = []
    for cond in CONDITIONS:
        records.extend(make_survival_record(row, cond) for row in genos)

    out = os.path.join(config.OUTPUTS_DIR, f"longevity_{a.mode}.jsonl")
    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")

    gold = Counter(r.messages[-1].content for r in records)
    conds = Counter(r.meta()["condition"] for r in records)
    print(f"[{a.mode}] {len(genos)} genotypes x {len(CONDITIONS)} conditions = {len(records)} records -> {out}")
    print(f"  gold balance: {dict(gold)}  | conditions: {dict(conds)}")


if __name__ == "__main__":
    main()
