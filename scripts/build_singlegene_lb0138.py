"""Build the LB-0138 survival-binary benchmark with MULTI-GENE genotypes REMOVED
(single-gene only — controls the epistasis confound; LRN-20260524-405 "Phase B").

This is a NEW, additive script: it does NOT edit data/mgi_labeled.csv, the original
build_longevity_benchmark.py, or any other existing file. It reuses the exact same
loader (src.data.mgi.load_mgi), curation logic (sample_longevity_benchmark.controlled /
random_mode) and record builder (src.generate.tasks.make_survival_record) as the
multi-gene benchmark, then inserts ONE filter: keep only genotypes with len(genes) == 1.

    python scripts/build_singlegene_lb0138.py --mode controlled \
        --out outputs/single_gene/longevity_controlled_singlegene.jsonl

Output is written ONLY to the path given by --out (default under outputs/single_gene/).
The same single-gene genotype is rendered in BOTH ablation conditions (matched pairs),
so Delta_recall stays item-for-item, identical in shape to the multi-gene benchmark.
"""
import argparse
import os
import random
import sys
from collections import Counter
from types import SimpleNamespace

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
    ap.add_argument("--out", default=os.path.join(config.OUTPUTS_DIR, "single_gene",
                                                  "longevity_controlled_singlegene.jsonl"))
    a = ap.parse_args()

    rows = load_mgi(balance=False, include_famous=False, seed=a.seed)
    n_all = len(rows)
    # === the single change vs build_longevity_benchmark.py: drop multi-gene & transgene ===
    rows = [r for r in rows if len(r.genes) == 1]
    print(f"single-gene filter: {len(rows)}/{n_all} rows kept "
          f"({100 * len(rows) / n_all:.0f}% single-gene)")

    ps_map = {r["genotype_id"]: r["primary_system"]
              for r in csv.DictReader(LABELED.open(encoding="utf-8"))}
    rng = random.Random(a.seed)

    if a.mode == "controlled":
        selected, summary = slb.controlled(rows, ps_map, rng, a)
        for b, pa, pd, pn in summary:
            print(f"    {b:26} adult={pa} dev={pd} neg={pn}")
    else:
        n_pos = (a.pos_adult + a.pos_dev) * len(slb.CURATED)
        n_neg = a.neg * len(slb.CURATED)
        selected = slb.random_mode(rows, ps_map, rng, n_pos, n_neg)
    genos = [row for _, _, row in selected]   # render the SAME genotypes in both conditions

    records = []
    for cond in CONDITIONS:
        records.extend(make_survival_record(row, cond) for row in genos)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")

    gold = Counter(r.messages[-1].content for r in records)
    conds = Counter(r.meta()["condition"] for r in records)
    n_genes_all_one = all(len(row.genes) == 1 for row in genos)  # sanity: zero multi-gene
    print(f"[single-gene {a.mode}] {len(genos)} genotypes x {len(CONDITIONS)} conditions "
          f"= {len(records)} records -> {a.out}")
    print(f"  gold balance: {dict(gold)}  | conditions: {dict(conds)}  | all single-gene: {n_genes_all_one}")


if __name__ == "__main__":
    main()
