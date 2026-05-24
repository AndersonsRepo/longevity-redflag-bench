"""Freeze the deterministic per-term classification of the MP mortality subtree.

Reads  data/mp_mortality_terms.csv   (mp_id, name)  — the 128 curated MP:0010768 terms
Writes data/mp_mortality_classified.csv (mp_id, name, category, label_contribution,
       lethality_stage) — the auditable ground-truth table src/data/mgi.py consumes.

Rules live in src/data/mortality_classes.classify_term (no AI, no ontology walk).
Run after any edit to mp_mortality_terms.csv; review the printed summary before committing.

    python scripts/classify_mortality_terms.py
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.data.mortality_classes import classify_term  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO, "data", "mp_mortality_terms.csv")
OUT = os.path.join(REPO, "data", "mp_mortality_classified.csv")


def main():
    rows = []
    with open(SRC, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cat, lab, stage = classify_term(r["name"])
            rows.append((r["mp_id"], r["name"], cat, "" if lab is None else lab, stage))

    unclassified = [r for r in rows if r[2] == "UNCLASSIFIED"]
    if unclassified:
        print("ERROR: UNCLASSIFIED terms (extend classify_term):", file=sys.stderr)
        for r in unclassified:
            print("  ", r[0], r[1], file=sys.stderr)
        sys.exit(1)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mp_id", "name", "category", "label_contribution", "lethality_stage"])
        w.writerows(rows)

    cats = Counter(r[2] for r in rows)
    stages = Counter(r[4] for r in rows if r[2] == "death")
    print(f"classified {len(rows)} terms -> {OUT}")
    print("  by category:", dict(cats))
    print("  death stages:", dict(stages))
    print("  label=1 terms:", sum(1 for r in rows if r[3] == 1))
    print("  label=0 terms (reversed/protective):", sum(1 for r in rows if r[3] == 0))
    print("  excluded terms (conditional/reproductive/ambiguous):",
          sum(1 for r in rows if r[3] == ""))


if __name__ == "__main__":
    main()
