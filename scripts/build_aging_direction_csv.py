"""Isolate the ADULT/AGING lifespan-DIRECTION question into its own CSV, so we can see
whether there are enough life-EXTENDING ("positive") genotypes to compare against the
life-SHORTENING ("negative") ones. The original experiment idea was this comparison; the
full dataset is dominated by developmental lethality, which is NOT an aging signal.

Direction (from the frozen term classification, data/mp_mortality_classified.csv):
  extends    = a `beneficial` term  (extended life span | slow aging | increased tumor-free survival)
  shortens   = a `death` term at the adult_aging stage (premature death/aging, moribund, SUDEP,
                                                          decreased tumor-free survival time)
  protective = a `protective` term  (decreased susceptibility/mortality — conditional, kept separate)
  mixed      = both extends AND shortens (contradictory annotation)
Genotypes with none of these are not aging-direction-relevant and are dropped.
`also_developmental` flags genotypes that ALSO carry a developmental-lethality term.

Reads  data/mgi_labeled.csv, data/mp_mortality_classified.csv
Writes data/aging_direction.csv

    python scripts/build_aging_direction_csv.py
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
csv.field_size_limit(10 ** 7)
from src import config  # noqa: E402

LABELED = config.DATA_DIR / "mgi_labeled.csv"
CLASSES = config.DATA_DIR / "mp_mortality_classified.csv"
OUT = config.DATA_DIR / "aging_direction.csv"

KEEP_COLS = ["genotype_id", "gene_symbols", "zygosity", "expression_direction",
             "genetic_background", "primary_system", "n_phenotype_terms", "is_famous",
             "eligible", "phenotype_terms", "pmids"]
NEW_COLS = ["direction", "aging_terms", "also_developmental"]


def load_classes():
    cat, stage = {}, {}
    for r in csv.DictReader(CLASSES.open(encoding="utf-8")):
        cat[r["name"]] = r["category"]
        stage[r["name"]] = r["lethality_stage"]
    return cat, stage


def main():
    cat, stage = load_classes()

    def split(v):
        return [t.strip() for t in (v or "").split("|") if t.strip()]

    rows_out = []
    dist = Counter()                 # direction over ALL kept rows
    usable_pos = Counter()           # extends/protective that are obscure+eligible+have-profile

    for row in csv.DictReader(LABELED.open(encoding="utf-8")):
        mterms = split(row.get("mortality_terms", ""))
        ext = [t for t in mterms if cat.get(t) == "beneficial"]
        sht = [t for t in mterms if cat.get(t) == "death" and stage.get(t) == "adult_aging"]
        pro = [t for t in mterms if cat.get(t) == "protective"]
        dev = any(cat.get(t) == "death" and stage.get(t) == "developmental" for t in mterms)
        if not (ext or sht or pro):
            continue
        if ext and sht:
            direction = "mixed"
        elif ext:
            direction = "extends"
        elif sht:
            direction = "shortens"
        else:
            direction = "protective"

        out = {k: row.get(k, "") for k in KEEP_COLS}
        out["direction"] = direction
        out["aging_terms"] = "|".join(ext + sht + pro)
        out["also_developmental"] = 1 if dev else 0
        rows_out.append(out)

        dist[direction] += 1
        testable = (row.get("is_famous") == "0" and row.get("eligible") == "1"
                    and int(row.get("n_phenotype_terms") or 0) > 0)
        if direction in ("extends", "protective") and testable:
            usable_pos[direction] += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KEEP_COLS + NEW_COLS)
        w.writeheader()
        w.writerows(rows_out)

    print(f"wrote {len(rows_out)} aging-direction genotypes -> {OUT}")
    print("\ndirection (all genes):")
    for d in ("extends", "shortens", "protective", "mixed"):
        print(f"  {d:11} {dist.get(d, 0)}")
    print("\nUSABLE positives (obscure + eligible + has phenotype profile):")
    print(f"  extends    {usable_pos.get('extends', 0)}")
    print(f"  protective {usable_pos.get('protective', 0)}")
    # how many usable shortens, for the balance picture
    us_sht = sum(1 for r in rows_out if r["direction"] == "shortens"
                 and r["is_famous"] == "0" and r["eligible"] == "1"
                 and int(r["n_phenotype_terms"] or 0) > 0)
    print(f"  (usable shortens, for comparison: {us_sht})")


if __name__ == "__main__":
    main()
