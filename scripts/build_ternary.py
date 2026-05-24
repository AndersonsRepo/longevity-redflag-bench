"""Build LB-0154: ternary lifespan-direction task — Shortens / No-effect / Extends. Adds the
neutral option the scientist asked for and tests the rare 'extends' direction. Balanced ~N/class
(extends-capped, ~50). Both ablation conditions. gene-grouped split (from the loader).

  shortens  = death @ adult_aging      (gold A)
  no_effect = none (no mortality term)  (gold B)
  extends   = beneficial (extended lifespan/slow aging; from data/aging_direction.csv) (gold C)

  --single-gene : restrict to single-gene genotypes (controls epistasis — Phase B). Default OFF
                  (Phase A "without the fix" keeps multi-gene). --out sets the output path.

    python scripts/build_ternary.py                       # Phase A (multi-gene allowed)
    python scripts/build_ternary.py --single-gene --out outputs/single_gene/ternary.jsonl
"""
import argparse
import csv
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
csv.field_size_limit(10 ** 7)

from src import config  # noqa: E402
from src.data.mgi import load_mgi  # noqa: E402
from src.generate.profiles import CONDITIONS  # noqa: E402
from src.generate.tasks import make_ternary_record  # noqa: E402

AGING = config.DATA_DIR / "aging_direction.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-class", type=int, default=50)
    ap.add_argument("--single-gene", action="store_true")
    ap.add_argument("--seed", type=int, default=config.SEED)
    ap.add_argument("--out", default=os.path.join(config.OUTPUTS_DIR, "ternary.jsonl"))
    a = ap.parse_args()
    rng = random.Random(a.seed)

    rows = load_mgi(balance=False, include_famous=False, seed=a.seed)
    ext_ids = {r["genotype_id"] for r in csv.DictReader(AGING.open(encoding="utf-8"))
               if r["direction"] == "extends" and r["is_famous"] == "0" and r["eligible"] == "1"}

    def keep(r):
        return bool(r.phenotype_terms) and (len(r.genes) == 1 if a.single_gene else True)

    pools = {
        "shortens": [r for r in rows if r.mortality_category == "death"
                     and r.lethality_stage == "adult_aging" and keep(r)],
        "no_effect": [r for r in rows if r.mortality_category == "none" and keep(r)],
        "extends": [r for r in rows if r.genotype_id in ext_ids and keep(r)],
    }
    n = min(a.max_per_class, *(len(p) for p in pools.values()))
    print(f"single_gene={a.single_gene} | pool sizes: "
          + ", ".join(f"{k}={len(v)}" for k, v in pools.items()) + f" | N/class={n}")

    records = []
    for klass, pool in pools.items():
        for row in rng.sample(pool, n):
            for cond in CONDITIONS:
                records.append(make_ternary_record(row, klass, cond, row.split))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")

    import json
    gold = Counter(json.loads(r.metadata)["gold"] for r in records)
    splits = Counter(json.loads(r.metadata)["split"] for r in records)
    print(f"wrote {len(records)} records ({n}/class x 3 classes x {len(CONDITIONS)} conditions) -> {a.out}")
    print(f"  gold balance: {dict(gold)} | splits: {dict(splits)}")


if __name__ == "__main__":
    main()
