"""Build LB-0150: pairwise lifespan-EXTENSION task. Each item pairs a life-EXTENDING genotype
against a survival-SHORTENING (adult/aging death) genotype matched on phenotype-system, and asks
which is more likely to EXTEND lifespan. Forced choice → base-rate-robust (the rare extender class
can't be gamed by a default). gold = the extender's letter.

Extenders = aging_direction.csv `direction==extends`, obscure, eligible, n_phenotype_terms >= MIN.
Each extender is paired with K same-system shorteners (→ clears the N>=50 floor from ~31 extenders).
Position (A/B) randomized; gene-grouped split via union-find over each pair's genes (no gene spans
train/test). Rendered in both ablation conditions. Reuses src.generate.tasks.make_pairwise_lifespan_record.

    python scripts/build_pairwise_lifespan.py [--min-pheno 2 --per-extender 2 --seed 1234]
Writes outputs/lifespan_pairwise.jsonl.
"""
import argparse
import csv
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
csv.field_size_limit(10 ** 7)

from src import config  # noqa: E402
from src.data.mgi import load_mgi  # noqa: E402
from src.generate.profiles import CONDITIONS  # noqa: E402
from src.generate.tasks import make_pairwise_lifespan_record  # noqa: E402

LABELED = config.DATA_DIR / "mgi_labeled.csv"
AGING = config.DATA_DIR / "aging_direction.csv"


class _UF:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b): self.p[self.find(a)] = self.find(b)


def _keys(row):
    return list(row.genes) if row.genes else [f"_nogene:{row.genotype_id}"]


# Curation: drop extenders whose phenotype profile shows disease WORSENING that contradicts the
# "extends lifespan" label (e.g. compound Apc tumor-model genotypes whose static profile carries
# pro-neoplasia phenotypes from the base model). Keep tumor-DECREASE/latency-INCREASE (those
# legitimately signal extension). Deterministic keyword rule; v1 — flag for bio review.
_NEO = ("tumor", "carcinoma", "adenoma", "neoplas", "lymphoma", "sarcoma", "leukemia",
        "metasta", "cancer", "malignan")


def _contradicts_extension(terms):
    for t in terms:
        tl = t.lower()
        if not any(w in tl for w in _NEO):
            continue
        protective = ("latency" in tl) or ("free survival" in tl) or ("free interval" in tl)
        if tl.startswith(("increased", "accelerated", "early", "premature")) and not protective:
            return True            # more/earlier neoplasia -> worsening
        if tl.startswith("decreased") and "latency" in tl:
            return True            # shorter tumor latency -> worsening
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pheno", type=int, default=2, help="min non-mortality phenotype terms")
    ap.add_argument("--per-extender", type=int, default=2, help="shorteners paired per extender")
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument("--keep-contradictions", action="store_true",
                    help="keep extenders whose profile contradicts the extends label (default: drop)")
    ap.add_argument("--single-gene", action="store_true", help="single-gene genotypes only (epistasis control)")
    ap.add_argument("--out", default=None, help="output path (default outputs/lifespan_pairwise.jsonl)")
    ap.add_argument("--seed", type=int, default=config.SEED)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    rows = load_mgi(balance=False, include_famous=False, seed=a.seed)
    by_id = {r.genotype_id: r for r in rows}
    ps_map = {r["genotype_id"]: r["primary_system"]
              for r in csv.DictReader(LABELED.open(encoding="utf-8"))}

    ext_ids = {r["genotype_id"] for r in csv.DictReader(AGING.open(encoding="utf-8"))
               if r["direction"] == "extends" and r["is_famous"] == "0" and r["eligible"] == "1"
               and int(r["n_phenotype_terms"] or 0) >= a.min_pheno}
    extenders = [by_id[i] for i in ext_ids if i in by_id and len(by_id[i].phenotype_terms) >= a.min_pheno
                 and (len(by_id[i].genes) == 1 if a.single_gene else True)]
    if not a.keep_contradictions:
        dropped = [e for e in extenders if _contradicts_extension(e.phenotype_terms)]
        extenders = [e for e in extenders if not _contradicts_extension(e.phenotype_terms)]
        print(f"curation: dropped {len(dropped)} extenders whose profile contradicts 'extends' "
              f"(e.g. {[d.genotype_id for d in dropped[:5]]})")

    shorteners_by_sys = defaultdict(list)
    for r in rows:
        if (r.mortality_category == "death" and r.lethality_stage == "adult_aging"
                and len(r.phenotype_terms) >= a.min_pheno
                and (len(r.genes) == 1 if a.single_gene else True)):
            shorteners_by_sys[ps_map.get(r.genotype_id, "")].append(r)
    all_short = [r for lst in shorteners_by_sys.values() for r in lst]

    # build pairs: each extender vs K same-system shorteners (fallback any-system)
    pairs = []   # (extender_row, shortener_row)
    for ext in extenders:
        sysname = ps_map.get(ext.genotype_id, "")
        pool = [r for r in shorteners_by_sys.get(sysname, []) if r.genotype_id != ext.genotype_id]
        if len(pool) < a.per_extender:
            pool = [r for r in all_short if r.genotype_id != ext.genotype_id]
        for sho in rng.sample(pool, min(a.per_extender, len(pool))):
            pairs.append((ext, sho))

    # gene-grouped split: union each pair's genes; pairs sharing a gene → same component → same split
    uf = _UF()
    for ext, sho in pairs:
        ks = _keys(ext) + _keys(sho)
        for k in ks[1:]:
            uf.union(ks[0], k)
    pair_comp = [uf.find(_keys(ext)[0]) for ext, _ in pairs]
    comps = sorted(set(pair_comp))
    rng.shuffle(comps)
    n_test = max(1, round(len(comps) * a.test_frac))
    test_comps = set(comps[:n_test])

    records = []
    gold_counter = Counter()
    for (ext, sho), comp in zip(pairs, pair_comp):
        split = "test" if comp in test_comps else "train"
        if rng.random() < 0.5:        # randomize position; gold = extender's letter
            row_a, row_b, gold = ext, sho, "A"
        else:
            row_a, row_b, gold = sho, ext, "B"
        gold_counter[gold] += 1
        for cond in CONDITIONS:
            records.append(make_pairwise_lifespan_record(row_a, row_b, gold, cond, split))

    # leakage check: no gene in both train & test pairs
    train_g, test_g = set(), set()
    for (ext, sho), comp in zip(pairs, pair_comp):
        tgt = test_g if comp in test_comps else train_g
        tgt |= set(ext.genes) | set(sho.genes)
    overlap = train_g & test_g

    out = a.out or os.path.join(config.OUTPUTS_DIR, "lifespan_pairwise.jsonl")
    os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")

    print(f"extenders (nP>={a.min_pheno}): {len(extenders)} | pairs: {len(pairs)} | "
          f"records: {len(records)} ({len(pairs)} pairs x {len(CONDITIONS)} conditions)")
    print(f"  gold balance: {dict(gold_counter)}  | gene overlap train/test: {len(overlap)} (must be 0)")
    splits = Counter("test" if c in test_comps else "train" for c in pair_comp)
    print(f"  pair splits: {dict(splits)}")
    print(f"  wrote -> {out}")
    assert not overlap, f"LEAKAGE: genes span splits: {list(overlap)[:5]}"


if __name__ == "__main__":
    main()
