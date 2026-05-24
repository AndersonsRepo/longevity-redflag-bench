"""Build a unified, de-duplicated QUANTITATIVE mouse genotype->lifespan dataset
from OpenGenes (API) + SynergyAge (bulk download), and correlate it against the
MGI categorical dataset (data/mgi_genotype_phenotype.csv).

Deterministic, no AI in the ground-truth path. Stdlib only (urllib/json/csv).

Outputs:
  data/quant_lifespan_mouse.csv   -- one row per source experiment, normalized,
                                      with dedup flags + MGI-overlap columns.
  data/quant_mgi_overlap.csv      -- per matched mouse gene: MGI genotype count +
                                      direction agreement (knockout<->decreased).

Run: .venv/bin/python scripts/build_quant_lifespan.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import threading
import urllib.request
import urllib.error
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
OG_BASE = "https://open-genes.com/api"
SA_MODELS = "https://www.synergyage.info/static/curation/download/models.json"
MGI_CSV = os.path.join(DATA, "mgi_genotype_phenotype.csv")
BLOCKLIST_CSV = os.path.join(DATA, "famous_gene_blocklist.csv")
OUT_CSV = os.path.join(DATA, "quant_lifespan_mouse.csv")
OVERLAP_CSV = os.path.join(DATA, "quant_mgi_overlap.csv")
OG_CACHE = os.path.join(DATA, ".cache_opengenes_mouse.json")  # {symbol: [records]} — resumable

UA = {"User-Agent": "longevity-bench/1.0 (research; +caltech-hackathon)"}


# ---------------------------------------------------------------- http helpers
def _get(url: str, tries: int = 4, timeout: int = 12, backoff=(2, 5, 12)):
    """GET JSON with retry + backoff. Raises on final failure."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            if i < tries - 1:
                time.sleep(backoff[min(i, len(backoff) - 1)])
    raise last


# ---------------------------------------------------------------- direction map
def norm_direction(text: str | None) -> str:
    t = (text or "").lower()
    if "increase" in t and "decreased lifespan" in t:
        return "conditional_increase"  # "increases lifespan in animals with decreased lifespans"
    if "increase" in t or "improves" in t:
        return "increase"
    if "decrease" in t or "reduces" in t:
        return "decrease"
    if "no change" in t:
        return "no_change"
    return "unknown"


def intervention_expr_direction(method: str | None, allele_code: str | None = None) -> str:
    """Map an intervention to the expression direction MGI would record."""
    s = " ".join(filter(None, [(method or "").lower(), (allele_code or "").lower()]))
    if any(k in s for k in ["knockout", "ko", "null", "deletion", "knockdown", "hypomorph", "loss", "deficien"]):
        return "decreased"
    if any(k in s for k in ["overexpress", "oe", "additional cop", "transgen", "gain", "constitutively active"]):
        return "increased"
    return "unknown"


def pick_pct(median, mean, mx):
    for v, name in [(median, "median"), (mean, "mean"), (mx, "max")]:
        if v is not None:
            try:
                return float(v), name
            except (TypeError, ValueError):
                pass
    return None, None


# ---------------------------------------------------------------- OpenGenes
def fetch_opengenes() -> list[dict]:
    # Resumable cache: {symbol: [records]}. Lets a throttled crawl pick up where it left off.
    cache: dict[str, list] = {}
    if os.path.exists(OG_CACHE):
        try:
            cache = json.load(open(OG_CACHE))
            print(f"[OpenGenes] loaded cache: {len(cache)} genes already fetched", flush=True)
        except Exception:  # noqa: BLE001
            cache = {}

    # Fast health probe — never start a long crawl against a throttled/down API.
    healthy = True
    try:
        _get(f"{OG_BASE}/gene/GHR", tries=1, timeout=8)
    except Exception as e:  # noqa: BLE001
        healthy = False
        print(f"[OpenGenes] health probe FAILED ({type(e).__name__}) — API unreachable right now. "
              f"Skipping crawl; using cache only ({len(cache)} genes). Re-run when it recovers.", flush=True)

    symbols = list(cache.keys())
    if healthy:
        print("[OpenGenes] healthy; fetching gene list ...", flush=True)
        try:
            listing = _get(f"{OG_BASE}/gene/search?pageSize=3000")
            symbols = [it["symbol"] for it in listing.get("items", []) if it.get("symbol")]
        except Exception as e:  # noqa: BLE001
            print(f"[OpenGenes] gene-list fetch FAILED ({e}); using cache only.", flush=True)
            symbols = list(cache.keys())

    to_fetch = [s for s in symbols if s not in cache] if healthy else []
    print(f"[OpenGenes] {len(symbols)} genes total; {len(to_fetch)} to fetch, {len(cache)} cached. "
          f"Gentle crawl (4 workers + backoff) ...", flush=True)

    lock = threading.Lock()
    state = {"done": 0, "fails": 0, "consec_fail": 0, "aborted": False}

    def one(sym):
        d = _get(f"{OG_BASE}/gene/{sym}")
        out = []
        # mouse ortholog symbol (for MGI matching), else case-fold fallback
        mouse_orth = None
        for o in (d.get("ortholog") or []):
            if (o.get("species") or {}).get("latinName") == "Mus musculus" and o.get("symbol"):
                mouse_orth = o["symbol"]
                break
        for e in d.get("researches", {}).get("increaseLifespan", []):
            if e.get("modelOrganism") != "mouse":
                continue
            pct, field = pick_pct(e.get("lifespanMedianChangePercent"),
                                  e.get("lifespanMeanChangePercent"),
                                  e.get("lifespanMaxChangePercent"))
            exps = (e.get("interventions") or {}).get("experiment") or [{}]
            method = exps[0].get("interventionMethod")
            way = exps[0].get("interventionWay")
            out.append({
                "source": "opengenes",
                "record_id": f"og:{e.get('id')}",
                "gene_human": d.get("symbol"),
                "gene_mouse": mouse_orth or (d.get("symbol") or ""),
                "n_genes": 1,
                "intervention": method or way or "",
                "expr_direction": intervention_expr_direction(method, way),
                "direction": norm_direction(e.get("interventionResultForLifespan")),
                "pct_change": pct,
                "pct_field": field or "",
                "pct_median": e.get("lifespanMedianChangePercent"),
                "pct_mean": e.get("lifespanMeanChangePercent"),
                "pct_max": e.get("lifespanMaxChangePercent"),
                "abs_control": e.get("lifespanMedianControl") or e.get("lifespanMeanControl"),
                "abs_experiment": e.get("lifespanMedianExperiment") or e.get("lifespanMeanExperiment"),
                "strain": e.get("organismLine") or "",
                "sex": e.get("sex") or "",
                "significance": e.get("lMedianChangeStatSignificance") or e.get("lMeanChangeStatSignificance") or "",
                "citation": e.get("doi") or (("PMID:" + e["pmid"]) if e.get("pmid") else ""),
            })
        return out

    def save_cache():
        tmp = OG_CACHE + ".tmp"
        json.dump(cache, open(tmp, "w"))
        os.replace(tmp, OG_CACHE)

    if to_fetch and not state["aborted"]:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(one, s): s for s in to_fetch}
            for fut in as_completed(futs):
                sym = futs[fut]
                with lock:
                    state["done"] += 1
                    try:
                        cache[sym] = fut.result()
                        state["consec_fail"] = 0
                    except Exception:  # noqa: BLE001
                        state["fails"] += 1
                        state["consec_fail"] += 1
                    if state["done"] % 200 == 0:
                        print(f"  ... {state['done']}/{len(to_fetch)} "
                              f"(fails {state['fails']})", flush=True)
                        save_cache()
                    # circuit breaker: API is clearly down/blocking — stop hammering it
                    if state["consec_fail"] >= 25 and not state["aborted"]:
                        state["aborted"] = True
                        print(f"[OpenGenes] ABORTING crawl after {state['consec_fail']} consecutive "
                              f"failures — API unreachable. Cached {len(cache)} genes so far; "
                              f"re-run later to resume.", flush=True)
                        for f2 in futs:
                            f2.cancel()
        save_cache()

    # build rows from everything we have in cache
    rows: list[dict] = []
    for recs in cache.values():
        rows.extend(recs)
    status = "PARTIAL (API throttled — re-run to complete)" if state["aborted"] else "complete"
    print(f"[OpenGenes] mouse lifespan experiments: {len(rows)} from {len(cache)} genes "
          f"[{status}] (failed fetches: {state['fails']})", flush=True)
    return rows


# ---------------------------------------------------------------- SynergyAge
def fetch_synergyage() -> list[dict]:
    print("[SynergyAge] downloading models.json ...", flush=True)
    try:
        data = _get(SA_MODELS, timeout=40)
    except Exception as e:  # noqa: BLE001
        print(f"[SynergyAge] download failed: {e}", flush=True)
        return []
    models = data if isinstance(data, list) else data.get("data") or data.get("models") or []
    rows = []
    import re
    for m in models:
        tax = str(m.get("tax_id") or m.get("taxon") or "")
        if tax != "10090":  # mouse
            continue
        genes_raw = (m.get("genes") or "").strip()
        name = (m.get("name") or "").strip()
        if genes_raw in ("", "-") or name.lower() == "wild type":
            continue  # WT controls
        genes = [g.strip() for g in genes_raw.replace(",", ";").split(";") if g.strip()]
        # allele codes (KO/OE/...) live in the name, e.g. "bax(KO);Ku70(KO)"
        allele_codes = " ".join(re.findall(r"\(([^)]*)\)", name))
        interv = name  # genotype string is the most informative intervention label
        effect = m.get("effect")
        try:
            effect = float(effect) if effect not in (None, "", "NULL") else None
        except (TypeError, ValueError):
            effect = None
        direction = "unknown"
        if effect is not None:
            direction = "increase" if effect > 0 else ("decrease" if effect < 0 else "no_change")
        pmid = m.get("pmid")
        rows.append({
            "source": "synergyage",
            "record_id": f"sa:{m.get('id') or name}",
            "gene_human": "",
            "gene_mouse": genes[0] if len(genes) == 1 else "|".join(genes),
            "n_genes": len(genes),
            "intervention": interv,
            "expr_direction": intervention_expr_direction(None, allele_codes),
            "direction": direction,
            "pct_change": effect,
            "pct_field": "effect" if effect is not None else "",
            "pct_median": None, "pct_mean": None, "pct_max": None,
            "abs_control": None,
            "abs_experiment": m.get("lifespan"),
            "strain": m.get("strain") or m.get("background") or "",
            "sex": m.get("sex") or "",
            "significance": "",
            "citation": (("PMID:" + str(pmid)) if pmid else name),
            "_genes_list": genes,
        })
    print(f"[SynergyAge] mouse genotype rows: {len(rows)}", flush=True)
    return rows


# ---------------------------------------------------------------- MGI index
def load_mgi_index():
    print("[MGI] indexing gene_symbols -> genotypes ...", flush=True)
    gene_to_geno = defaultdict(list)   # UPPER mouse symbol -> [(genotype_id, expr_direction)]
    with open(MGI_CSV, newline="") as f:
        for row in csv.DictReader(f):
            ed = (row.get("expression_direction") or "").strip().lower()
            for g in (row.get("gene_symbols") or "").split("|"):
                g = g.strip().upper()
                if g:
                    gene_to_geno[g].append((row["genotype_id"], ed))
    print(f"[MGI] {len(gene_to_geno)} distinct genes indexed", flush=True)
    return gene_to_geno


def main():
    og = fetch_opengenes()
    sa = fetch_synergyage()
    records = og + sa

    # famous-gene blocklist (uppercased)
    famous = set()
    if os.path.exists(BLOCKLIST_CSV):
        with open(BLOCKLIST_CSV, newline="") as f:
            for row in csv.DictReader(f):
                famous.add((row.get("gene_symbol") or "").strip().upper())

    mgi = load_mgi_index()

    # ---- dedup + cross-source flagging + MGI correlation
    # dup signature: source-agnostic (mouse gene set, direction, rounded pct)
    seen_exact = set()
    dup_group_sources = defaultdict(set)   # (geneset, direction) -> {sources}
    for r in records:
        gs = "|".join(sorted(g.upper() for g in
                             (r.get("_genes_list") or [r["gene_mouse"]]) if g))
        r["_geneset"] = gs
        dup_group_sources[(gs, r["direction"])].add(r["source"])

    final = []
    n_exact_dropped = 0
    for r in records:
        sig = (r["_geneset"], r["direction"],
               round(r["pct_change"], 1) if r["pct_change"] is not None else None,
               r["citation"])
        if sig in seen_exact:
            n_exact_dropped += 1
            continue
        seen_exact.add(sig)

        srcs = dup_group_sources[(r["_geneset"], r["direction"])]
        r["cross_source_dup"] = len(srcs) > 1

        # famous?
        gene_set = set(g.upper() for g in (r.get("_genes_list") or [r["gene_mouse"]]) if g)
        r["is_famous"] = bool(gene_set & famous)

        # MGI correlation (gene-level + mutation-direction agreement)
        matched, dir_match, mgi_ids = [], False, []
        for g in gene_set:
            if g in mgi:
                matched.append(g)
                genos = mgi[g]
                mgi_ids.extend(gid for gid, _ in genos[:3])
                if r["expr_direction"] != "unknown":
                    if any(ed == r["expr_direction"] for _, ed in genos):
                        dir_match = True
        r["in_mgi"] = bool(matched)
        r["mgi_genes_matched"] = "|".join(sorted(matched))
        r["mgi_direction_consistent"] = dir_match if matched else ""
        r["mgi_genotype_ids"] = "|".join(mgi_ids[:5])
        final.append(r)

    # ---- write main CSV
    cols = ["source", "record_id", "gene_human", "gene_mouse", "n_genes",
            "intervention", "expr_direction", "direction",
            "pct_change", "pct_field", "pct_median", "pct_mean", "pct_max",
            "abs_control", "abs_experiment", "strain", "sex", "significance",
            "citation", "is_famous", "cross_source_dup",
            "in_mgi", "mgi_genes_matched", "mgi_direction_consistent", "mgi_genotype_ids"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in final:
            w.writerow(r)

    # ---- write overlap CSV (per matched mouse gene)
    gene_rows = {}
    for r in final:
        if not r["in_mgi"]:
            continue
        for g in r["mgi_genes_matched"].split("|"):
            if not g:
                continue
            gr = gene_rows.setdefault(g, {"gene": g, "sources": set(),
                                          "n_quant_records": 0, "mgi_genotypes": len(mgi.get(g, [])),
                                          "dir_consistent": False, "is_famous": g in famous})
            gr["sources"].add(r["source"])
            gr["n_quant_records"] += 1
            if r["mgi_direction_consistent"] is True:
                gr["dir_consistent"] = True
    with open(OVERLAP_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gene_mouse", "quant_sources", "n_quant_records",
                    "mgi_genotype_count", "mgi_direction_consistent", "is_famous"])
        for g, gr in sorted(gene_rows.items()):
            w.writerow([g, "+".join(sorted(gr["sources"])), gr["n_quant_records"],
                        gr["mgi_genotypes"], gr["dir_consistent"], gr["is_famous"]])

    # ---- summary
    n_og = sum(1 for r in final if r["source"] == "opengenes")
    n_sa = sum(1 for r in final if r["source"] == "synergyage")
    n_numeric = sum(1 for r in final if r["pct_change"] is not None)
    n_combo = sum(1 for r in final if r["n_genes"] > 1)
    n_xsrc = sum(1 for r in final if r["cross_source_dup"])
    n_inmgi = sum(1 for r in final if r["in_mgi"])
    n_dirok = sum(1 for r in final if r["mgi_direction_consistent"] is True)
    genesets = {r["_geneset"] for r in final}

    print("\n================ SUMMARY ================")
    print(f"records written          : {len(final)}  ({n_og} OpenGenes + {n_sa} SynergyAge)")
    print(f"exact duplicates dropped : {n_exact_dropped}")
    print(f"with numeric pct_change  : {n_numeric}")
    print(f"combination genotypes    : {n_combo}")
    print(f"unique gene-set+direction: {len(genesets)} gene-sets")
    print(f"cross-source overlaps    : {n_xsrc} records share a gene-set+direction across both sources")
    print(f"--- MGI correlation ---")
    print(f"records whose gene(s) hit MGI         : {n_inmgi} / {len(final)}")
    print(f"  ...with mutation-direction agreement: {n_dirok}")
    print(f"distinct mouse genes overlapping MGI  : {len(gene_rows)}")
    print(f"\nwrote: {OUT_CSV}")
    print(f"wrote: {OVERLAP_CSV}")


if __name__ == "__main__":
    main()
