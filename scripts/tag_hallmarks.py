"""Tag genes with Hallmark(s) of Aging — a SECONDARY, cited diversity covariate (Lopez-Otin).
NOT part of the ground-truth label: the survival label stays deterministic (MGI + mp.obo);
this is a fuzzy gene-function annotation for slicing/diversity, flagged for bio review.

Method (no AI): query MyGene.info for each gene's GO terms (stdlib urllib), then match the GO
term NAMES against the curated keyword table data/go_hallmark_map.csv. A gene may map to 0, 1,
or several hallmarks (coverage is partial by design — most knockout genes aren't canonical
aging-pathway genes).

Default scope: the genes in data/longevity_sample_controlled.csv (the 120-genotype set).

    python scripts/tag_hallmarks.py [--sample data/longevity_sample_controlled.csv]
Writes data/hallmark_tags.csv (gene_symbol, hallmarks, n_go_terms, status) + a coverage report.
"""
import argparse
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
csv.field_size_limit(10 ** 7)
from src import config  # noqa: E402

MAP = config.DATA_DIR / "go_hallmark_map.csv"
OUT = config.DATA_DIR / "hallmark_tags.csv"
MYGENE = "http://mygene.info/v3/query"


def load_map():
    out = {}
    for r in csv.DictReader(MAP.open(encoding="utf-8")):
        out[r["hallmark"]] = [k.strip().lower() for k in r["keywords"].split("|") if k.strip()]
    return out


def mygene_go(symbols):
    """symbol -> set(lowercased GO term names). Batched POST to MyGene.info."""
    go_by_gene = {}
    for i in range(0, len(symbols), 100):
        batch = symbols[i:i + 100]
        body = urllib.parse.urlencode({
            "q": ",".join(batch), "scopes": "symbol",
            "fields": "go", "species": "mouse",
        }).encode()
        req = urllib.request.Request(MYGENE, data=body,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            hits = json.load(resp)
        for h in hits:
            q = h.get("query")
            if h.get("notfound"):
                go_by_gene.setdefault(q, None)
                continue
            terms = go_by_gene.setdefault(q, set())
            go = h.get("go") or {}
            for cat in ("BP", "MF", "CC"):
                entries = go.get(cat) or []
                if isinstance(entries, dict):
                    entries = [entries]
                for e in entries:
                    t = (e.get("term") or "").lower()
                    if t:
                        terms.add(t)
    return go_by_gene


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default=str(config.DATA_DIR / "longevity_sample_controlled.csv"))
    a = ap.parse_args()

    hmap = load_map()
    genes = []
    seen = set()
    for r in csv.DictReader(open(a.sample, encoding="utf-8")):
        for g in (r.get("gene_symbols") or "").split("|"):
            g = g.strip()
            if g and g not in seen:
                seen.add(g)
                genes.append(g)
    print(f"unique genes in {os.path.basename(a.sample)}: {len(genes)}")

    go_by_gene = mygene_go(genes)

    rows, per_hallmark, n_hit, n_tagged = [], Counter(), 0, 0
    for g in genes:
        terms = go_by_gene.get(g)
        if terms is None:
            rows.append((g, "", 0, "no_mygene_hit"))
            continue
        n_hit += 1
        blob = " || ".join(terms)
        tags = sorted(h for h, kws in hmap.items() if any(k in blob for k in kws))
        if tags:
            n_tagged += 1
            for t in tags:
                per_hallmark[t] += 1
        rows.append((g, "|".join(tags), len(terms), "ok" if tags else "no_hallmark"))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["gene_symbol", "hallmarks", "n_go_terms", "status"])
        w.writerows(rows)

    print(f"wrote {len(rows)} genes -> {OUT}")
    print(f"  MyGene hits: {n_hit}/{len(genes)} | tagged with >=1 hallmark: {n_tagged} "
          f"({100*n_tagged/max(len(genes),1):.0f}%)")
    print("  per hallmark (gene count):")
    for h, c in per_hallmark.most_common():
        print(f"    {c:3}  {h}")
    unmapped = [g for g, t, n, s in rows if s == "no_hallmark"]
    print(f"  genes with GO but NO hallmark match: {len(unmapped)} (e.g. {unmapped[:6]})")


if __name__ == "__main__":
    main()
