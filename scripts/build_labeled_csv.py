"""Materialize the CORRECTED, labeled view of the MGI dataset for inspection + the
downstream phenotype-system categorization (step c).

Reads  data/mgi_genotype_phenotype.csv   (raw extract; buggy label_impairs_survival)
       data/mp_mortality_classified.csv   (frozen 128-term ground-truth table)
Writes data/mgi_labeled.csv               (raw columns + the derived label columns)

Derived columns appended to every row (NO rows dropped — excluded ones are flagged):
  label_corrected    1 (impairs) | 0 (does NOT, incl. reversed + true-neg) | "" (excluded)
  mortality_category death | reversed | none | contradictory | conditional | reproductive | ambiguous
  lethality_stage    developmental | postnatal | adult_aging | unspecified | na
  eligible           1 if usable in the baseline binary, else 0
  is_famous          1 if any constituent gene is on the GenAge blocklist

The classification logic is imported from src.data.mgi so this file and the loader can
never diverge. Run scripts/classify_mortality_terms.py first if the frozen table is stale.

    python scripts/build_labeled_csv.py
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
csv.field_size_limit(10 ** 7)

from src import config  # noqa: E402
from src.data.mgi import (  # noqa: E402  — reuse the loader's single source of truth
    _classify_genotype, _load_blocklist, _load_mortality_classes, _split_field,
)

SRC = config.DATA_DIR / "mgi_genotype_phenotype.csv"
OUT = config.DATA_DIR / "mgi_labeled.csv"
NEW_COLS = ["label_corrected", "mortality_category", "lethality_stage", "eligible", "is_famous"]


def main():
    classes = _load_mortality_classes()
    blocklist = _load_blocklist()

    cat_counts, stage_counts = Counter(), Counter()
    n = flipped = eligible = 0
    with SRC.open(encoding="utf-8") as fin, OUT.open("w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames) + NEW_COLS
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            n += 1
            # re-partition: pull any mortality-classified term out of the phenotype column (e.g.
            # the bare root "mortality/aging") so it's classified, not shown as a phenotype.
            raw_pheno = _split_field(row.get("phenotype_terms", ""))
            pheno = [p for p in raw_pheno if p not in classes]
            moved = [p for p in raw_pheno if p in classes]
            mort_names = _split_field(row.get("mortality_terms", "")) + moved
            if moved:  # keep the labeled CSV self-consistent
                row["phenotype_terms"] = "|".join(pheno)
                row["n_phenotype_terms"] = len(pheno)
                row["mortality_terms"] = "|".join(_split_field(row.get("mortality_terms", "")) + moved)
            label, category, stage = _classify_genotype(mort_names, classes)
            genes = _split_field(row.get("gene_symbols", ""))
            orig = 1 if str(row.get("label_impairs_survival", "")).strip() in ("1", "True", "true") else 0

            row["label_corrected"] = "" if label is None else label
            row["mortality_category"] = category
            row["lethality_stage"] = stage
            row["eligible"] = 1 if label is not None else 0
            row["is_famous"] = 1 if any(g in blocklist for g in genes) else 0
            writer.writerow(row)

            cat_counts[category] += 1
            if category == "death":
                stage_counts[stage] += 1
            if label is not None:
                eligible += 1
                if label != orig:
                    flipped += 1

    print(f"wrote {n} rows -> {OUT}")
    print("  mortality_category:", dict(cat_counts))
    print("  death lethality_stage:", dict(stage_counts))
    print(f"  eligible (usable in baseline binary): {eligible}")
    print(f"  excluded: {n - eligible}")
    print(f"  labels flipped vs buggy build column: {flipped}")


if __name__ == "__main__":
    main()
