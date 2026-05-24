"""Sample the LONGEVITY benchmark selection in one of two modes, so we can compare a
CONTROLLED (curated/stratified) set against a size-matched TRULY-RANDOM baseline:

  --mode controlled : adult/aging-focused positives across the 12 curated phenotype-system
                      branches (embryo dropped), POS_ADULT adult + POS_DEV developmental per
                      branch + NEG `none` negatives. The "wired" options ON.
  --mode random     : same total size + same pos/neg balance, but drawn RANDOMLY from the whole
                      eligible obscure pool — no category, no stage control. The "wired" options OFF.

Both reuse src.data.mgi.load_mgi (corrected labels + gene-grouped split), are obscure-only +
eligible + must have a phenotype profile, and are deterministic in --seed. primary_system +
lethality_stage are RECORDED in both (so you can see what random drew), but only STEER selection
in controlled mode. Comparing model accuracy across the two = does our curation change the result.

    python scripts/sample_longevity_benchmark.py --mode controlled
    python scripts/sample_longevity_benchmark.py --mode random
Writes data/longevity_sample_<mode>.csv.
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

CURATED = [
    "homeostasis/metabolism", "immune system", "cardiovascular system", "hematopoietic system",
    "nervous system", "growth/size/body region", "skeleton", "digestive/alimentary",
    "liver/biliary system", "renal/urinary system", "respiratory system", "endocrine/exocrine gland",
]
LABELED = config.DATA_DIR / "mgi_labeled.csv"
COLS = ["primary_system", "role", "label", "mortality_category", "lethality_stage",
        "genotype_id", "gene_symbols", "zygosity", "expression_direction", "split",
        "n_phenotype_terms", "pmids", "phenotype_terms"]


def _row(branch, role, r):
    return [branch, role, r.label, r.mortality_category, r.lethality_stage, r.genotype_id,
            "|".join(r.genes), r.zygosity, r.expression_direction, r.split,
            len(r.phenotype_terms), "|".join(r.pmids), "|".join(r.phenotype_terms)]


def controlled(rows, ps_map, rng, a):
    selected, summary = [], []
    for branch in CURATED:
        pool = [r for r in rows if ps_map.get(r.genotype_id) == branch and r.phenotype_terms]
        adult = [r for r in pool if r.mortality_category == "death" and r.lethality_stage == "adult_aging"]
        dev = [r for r in pool if r.mortality_category == "death" and r.lethality_stage == "developmental"]
        negs = [r for r in pool if r.mortality_category == "none"]
        pa = rng.sample(adult, min(a.pos_adult, len(adult)))
        pd = rng.sample(dev, min(a.pos_dev, len(dev)))
        pn = rng.sample(negs, min(a.neg, len(negs)))
        selected += [(branch, "pos_adult", r) for r in pa]
        selected += [(branch, "pos_dev", r) for r in pd]
        selected += [(branch, "neg", r) for r in pn]
        summary.append((branch, len(pa), len(pd), len(pn)))
    return selected, summary


def random_mode(rows, ps_map, rng, n_pos, n_neg):
    pool = [r for r in rows if r.phenotype_terms]
    pos = [r for r in pool if r.mortality_category == "death"]
    neg = [r for r in pool if r.mortality_category == "none"]
    pick = rng.sample(pos, min(n_pos, len(pos))) + rng.sample(neg, min(n_neg, len(neg)))
    return [(ps_map.get(r.genotype_id, ""), "pos" if r.label == 1 else "neg", r) for r in pick]


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
        selected, summary = controlled(rows, ps_map, rng, a)
    else:
        n_pos = (a.pos_adult + a.pos_dev) * len(CURATED)   # match controlled totals
        n_neg = a.neg * len(CURATED)
        selected, summary = random_mode(rows, ps_map, rng, n_pos, n_neg), None

    out = config.DATA_DIR / f"longevity_sample_{a.mode}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for branch, role, r in selected:
            w.writerow(_row(branch, role, r))

    n = len(selected)
    pos = sum(1 for _, role, _ in selected if role.startswith("pos"))
    print(f"[{a.mode}] wrote {n} genotypes -> {out}  | positives {pos} / negatives {n - pos}")
    print(f"  splits: {dict(Counter(r.split for _, _, r in selected))}")
    # stage breakdown of POSITIVES — the headline difference between the two modes
    stages = Counter(r.lethality_stage for _, role, r in selected if role.startswith("pos"))
    print(f"  positive lethality_stage: {dict(stages)}")
    sysd = Counter(ps for ps, role, r in selected if role.startswith("pos"))
    print(f"  positive primary_system spread: {len(sysd)} systems")
    if summary:
        print("  per branch (adult/dev/neg):")
        for b, pa, pd, pn in summary:
            print(f"    {b:26} {pa} {pd} {pn}")


if __name__ == "__main__":
    main()
