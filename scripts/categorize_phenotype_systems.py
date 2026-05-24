"""Add the deterministic PHENOTYPE-SYSTEM categorization to data/mgi_labeled.csv.

For each genotype, map every phenotype_term (a NON-mortality MP term NAME) to its
top-level MP branch(es) by walking the mp.obo `is_a` tree up to a direct child of the
root MP:0000001, then tag the genotype:
  primary_system : the most-frequent top-level branch among its phenotype terms
                   (ties: higher count, then branch-name alphabetical)
  all_systems    : all distinct top-level branches it touches (pipe-joined, multi-label)

No AI; fully reproducible from the ontology. Idempotent — recomputes from phenotype_terms
each run. Branch labels are the MP branch name minus the trailing " phenotype".

    python scripts/categorize_phenotype_systems.py
"""
import csv
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
csv.field_size_limit(10 ** 7)
from src import config  # noqa: E402

OBO = config.DATA_DIR / "mp.obo"
CSV = config.DATA_DIR / "mgi_labeled.csv"
ROOT = "MP:0000001"
NEW_COLS = ["primary_system", "all_systems"]


def parse_obo(path):
    id2name, parents, cur = {}, defaultdict(list), None
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.rstrip()
        if line == "[Term]":
            cur = {"id": None}
        elif cur is not None and line.startswith("id: MP:"):
            cur["id"] = line[4:]
        elif cur is not None and line.startswith("name:"):
            id2name[cur["id"]] = line[6:]
        elif cur is not None and line.startswith("is_a: MP:"):
            parents[cur["id"]].append(line[6:].split("!")[0].strip())
    return id2name, parents


def label_of(name):
    return name[:-len(" phenotype")] if name.endswith(" phenotype") else name


def main():
    id2name, parents = parse_obo(OBO)
    name2id = {v: k for k, v in id2name.items()}
    top = set(c for c, ps in ((cid, parents[cid]) for cid in parents) if ROOT in ps)
    top |= {c for c in parents if ROOT in parents.get(c, [])}

    # top-level ancestors of an MP id (memoized walk up is_a)
    cache = {}

    def top_levels(mp):
        if mp in cache:
            return cache[mp]
        out, seen, stack = set(), set(), [mp]
        while stack:
            x = stack.pop()
            if x in top:
                out.add(x)
            for p in parents.get(x, []):
                if p not in seen:
                    seen.add(p)
                    stack.append(p)
        cache[mp] = out
        return out

    def split(v):
        return [t.strip() for t in (v or "").split("|") if t.strip()]

    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    fieldnames = [c for c in rows[0].keys() if c not in NEW_COLS] + NEW_COLS if rows else NEW_COLS

    unmatched = Counter()
    matched_terms = total_terms = 0
    primary_dist = Counter()       # over eligible genotypes that HAVE a phenotype profile

    for row in rows:
        branch_counts = Counter()
        for term in split(row.get("phenotype_terms", "")):
            total_terms += 1
            mp = name2id.get(term)
            if mp is None:
                unmatched[term] += 1
                continue
            matched_terms += 1
            for tl in top_levels(mp):
                branch_counts[label_of(id2name[tl])] += 1
        if branch_counts:
            primary = sorted(branch_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            all_systems = "|".join(sorted(branch_counts))
        else:
            primary, all_systems = "", ""
        row["primary_system"] = primary
        row["all_systems"] = all_systems
        if primary and row.get("eligible") == "1":
            primary_dist[primary] += 1

    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"rewrote {len(rows)} rows -> {CSV} (+{NEW_COLS})")
    print(f"phenotype-term name->MP match: {matched_terms}/{total_terms} "
          f"({100*matched_terms/max(total_terms,1):.2f}%); distinct unmatched names: {len(unmatched)}")
    if unmatched:
        print("  top unmatched:", unmatched.most_common(8))
    print("\nprimary_system distribution (eligible genotypes with a phenotype profile):")
    tot = sum(primary_dist.values())
    for sys_, c in primary_dist.most_common():
        print(f"  {c:7}  ({100*c/tot:4.1f}%)  {sys_}")


if __name__ == "__main__":
    main()
