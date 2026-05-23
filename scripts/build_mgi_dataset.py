"""Build the MGI genotype+phenotype -> survival SOURCE CSV for the mouse-longevity benchmark.

Groups MGI_PhenoGenoMP.rpt by genotype; splits each genotype's MP terms into the
mortality/aging branch (MP:0010768 subtree = the LABEL) vs the rest (the phenotype
profile we show the model); derives zygosity from the allelic composition.

Inputs (default /tmp; pass paths as argv):
  - mp.obo                  (MP ontology; descendants of MP:0010768)
  - MGI_PhenoGenoMP.rpt     (genotype -> MP annotations)
Output: data/mgi_genotype_phenotype.csv  (one row per genotype)

Usage: python scripts/build_mgi_dataset.py [mgi.rpt] [mp.obo]
"""

import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MGI = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mgi.rpt"
OBO = sys.argv[2] if len(sys.argv) > 2 else "/tmp/mp.obo"
OUT = os.path.join(REPO, "data", "mgi_genotype_phenotype.csv")
MORTALITY_ROOT = "MP:0010768"  # mortality/aging


def load_mp(obo):
    """Return (id->name, set(descendants of MORTALITY_ROOT))."""
    name, isa, cur = {}, defaultdict(list), None
    for line in open(obo, encoding="utf-8", errors="ignore"):
        line = line.rstrip()
        if line == "[Term]":
            cur = {"id": None}
        elif cur is not None and line.startswith("id: MP:"):
            cur["id"] = line[4:]
        elif cur is not None and line.startswith("name:"):
            name[cur["id"]] = line[6:]
        elif cur is not None and line.startswith("is_a: MP:"):
            isa[cur["id"]].append(line[6:].split("!")[0].strip())
    children = defaultdict(list)
    for c, parents in isa.items():
        for p in parents:
            children[p].append(c)
    seen, stack = set(), [MORTALITY_ROOT]
    while stack:
        x = stack.pop()
        for c in children.get(x, []):
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return name, seen


def zygosity(allelic_comp):
    parts = [p.strip() for p in allelic_comp.split("/")]
    if "," in allelic_comp:
        return "multi-locus"
    if len(parts) == 2:
        if parts[0] == parts[1]:
            return "homozygote"
        if "<+>" in parts[1] or parts[1] in ("+", ""):
            return "heterozygote"
        if parts[1] in ("Y", "0", "-"):
            return "hemizygote"
        return "compound/other"
    return "other"


def genes_from(allelic_comp):
    # gene symbol is the text before each "<allele>"
    return sorted(set(re.findall(r"([A-Za-z0-9_.\-]+)<", allelic_comp)))


def main():
    if not os.path.exists(MGI) or not os.path.exists(OBO):
        sys.exit(f"missing input(s): {MGI} / {OBO}")
    id2name, mortality = load_mp(OBO)

    geno = {}  # genotype_acc -> dict
    with open(MGI, encoding="utf-8", errors="ignore") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 5:
                continue  # skip header/partial last line
            allelic, _allele, background, mp, pmid = cols[0], cols[1], cols[2], cols[3], cols[4]
            gacc = cols[6] if len(cols) > 6 and cols[6] else allelic + "|" + background
            if not mp.startswith("MP:"):
                continue
            g = geno.setdefault(gacc, {"allelic": allelic, "background": background,
                                       "mp": set(), "pmids": set()})
            g["mp"].add(mp)
            if pmid:
                g["pmids"].add(pmid)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n_pos = n_neg = n_usable = 0
    with open(OUT, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["genotype_id", "allelic_composition", "gene_symbols", "zygosity",
                    "genetic_background", "label_impairs_survival", "mortality_terms",
                    "n_phenotype_terms", "phenotype_terms", "pmids"])
        for gacc, g in geno.items():
            mort = sorted(g["mp"] & mortality)
            pheno = sorted(g["mp"] - mortality)
            label = 1 if mort else 0
            n_pos += label
            n_neg += (1 - label)
            if pheno:
                n_usable += 1
            w.writerow([
                gacc, g["allelic"], "|".join(genes_from(g["allelic"])), zygosity(g["allelic"]),
                g["background"], label,
                "|".join(id2name.get(m, m) for m in mort),
                len(pheno),
                "|".join(id2name.get(p, p) for p in pheno),
                "|".join(sorted(g["pmids"])),
            ])

    print(f"genotypes: {len(geno)}")
    print(f"  impairs-survival (label=1): {n_pos}")
    print(f"  no-mortality (label=0):     {n_neg}")
    print(f"  with >=1 phenotype term (usable for genotype+phenotype task): {n_usable}")
    print(f"  mortality/aging MP terms in ontology subtree: {len(mortality)}")
    print(f"wrote -> {OUT}")


if __name__ == "__main__":
    main()
