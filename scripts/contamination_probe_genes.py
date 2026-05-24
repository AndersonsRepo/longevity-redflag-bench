"""GENE-RECALL CONTAMINATION PROBE (Caltech Track 01, retrieval-resistance evidence).

QUESTION: does the model answer "does a knockout of gene X impair survival?" better for
FAMOUS longevity genes (GenAge model-organism set) than for OBSCURE genes (in MGI, NOT in
the famous-gene blocklist)? We give the GENE ONLY — no phenotype context — so a correct
answer can only come from prior knowledge of that gene. A large famous-vs-obscure accuracy
gap = the model is RECALLING, not reasoning => those genes are contaminated and belong in
the blocklist, not the retrieval-resistant test set.

GROUND TRUTH: MGI's corrected `label_impairs_survival` for the gene's single-gene
knockout/null genotype(s) (majority vote per gene). A = impairs survival (Yes), B = No.

DESIGN CONTROLS:
  - Gene-only prompt (no phenotype) isolates recall from reasoning.
  - Both groups balanced on the gold label so "always answer No" scores ~50% in BOTH
    groups (the model's known default) -> the GAP is what reveals recall.
  - We also report accuracy on the impairs=YES subset per group (the sharpest recall signal,
    since the model defaults to "No" on the unknown).
  - Bootstrap 95% CI on the gap. Seeded sampling for reproducibility.

OUTPUTS:
  data/contamination_probe_results.csv  -- per-gene: group, gene, gold, pred, correct, raw
  data/contamination_probe_summary.json -- aggregate metrics (feeds the markdown report)

Run: .venv/bin/python scripts/contamination_probe_genes.py [--n 40] [--seed 1234] [--workers 3]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import random
import re
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config
from src.model.client import chat

DATA = config.DATA_DIR
MGI_LABELED = os.path.join(DATA, "mgi_labeled.csv")
BLOCKLIST = os.path.join(DATA, "famous_gene_blocklist.csv")
GENAGE_CACHE = os.path.join(DATA, ".cache_genage_mouse.json")
OUT_CSV = os.path.join(DATA, "contamination_probe_results.csv")
OUT_JSON = os.path.join(DATA, "contamination_probe_summary.json")

SYS_PROMPT = ("You are a biomedical AI specialized in aging biology, "
             "trained on genomic, proteomic, and clinical data.")


def genage_mouse_symbols() -> set[str]:
    if os.path.exists(GENAGE_CACHE):
        return set(json.load(open(GENAGE_CACHE)))
    raw = urllib.request.urlopen(urllib.request.Request(
        "https://genomics.senescence.info/genes/models_genes.zip",
        headers={"User-Agent": "longevity-bench/1.0"}), timeout=40).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    syms = {r["symbol"].upper() for r in csv.DictReader(
        io.TextIOWrapper(z.open("genage_models.csv"), encoding="utf-8", errors="replace"))
        if "mus" in r["organism"].lower()}
    json.dump(sorted(syms), open(GENAGE_CACHE, "w"))
    return syms


def blocklist_symbols() -> set[str]:
    out = set()
    with open(BLOCKLIST, newline="") as f:
        for r in csv.DictReader(f):
            out.add((r.get("gene_symbol") or "").strip().upper())
    return out


def per_gene_labels():
    """gene(UPPER) -> {label: 0/1 majority over single-gene knockout/null genotypes,
    pmids: total distinct, n: genotype count}. Only single-gene, eligible, KO/null rows."""
    agg = defaultdict(lambda: {"labels": [], "pmids": set()})
    with open(MGI_LABELED, newline="") as f:
        for row in csv.DictReader(f):
            genes = [g for g in (row.get("gene_symbols") or "").split("|") if g.strip()]
            if len(genes) != 1:
                continue  # single-gene only
            attrs = (row.get("allele_attributes") or "").lower()
            if not any(k in attrs for k in ["null", "knockout", "knock out", "knock-out"]):
                continue  # require a loss-of-function/knockout allele
            if str(row.get("eligible", "")).strip().lower() not in ("true", "1"):
                continue
            lab = row.get("label_corrected", row.get("label_impairs_survival", ""))
            try:
                lab = int(float(lab))
            except (TypeError, ValueError):
                continue
            g = genes[0].strip().upper()
            agg[g]["labels"].append(lab)
            for p in (row.get("pmids") or "").replace("|", ",").split(","):
                if p.strip():
                    agg[g]["pmids"].add(p.strip())
    out = {}
    for g, d in agg.items():
        if not d["labels"]:
            continue
        ones = sum(d["labels"])
        # majority vote; require a clear majority (skip 50/50 ties)
        if ones * 2 == len(d["labels"]):
            continue
        out[g] = {"label": 1 if ones * 2 > len(d["labels"]) else 0,
                  "pmids": len(d["pmids"]), "n": len(d["labels"])}
    return out


def balanced_sample(cands: dict, n: int, seed: int, prefer="desc"):
    """cands: gene->meta. Balance on label, sort within class by pmids (desc=most-studied
    first for famous, asc=most-obscure first for obscure). Return up to n genes."""
    rng = random.Random(seed)
    by = {0: [], 1: []}
    for g, m in cands.items():
        by[m["label"]].append((g, m))
    for lab in by:
        by[lab].sort(key=lambda x: x[1]["pmids"], reverse=(prefer == "desc"))
        # light shuffle within the same pmid count to avoid alphabetic bias
        rng.shuffle(by[lab])
        by[lab].sort(key=lambda x: x[1]["pmids"], reverse=(prefer == "desc"))
    half = n // 2
    picked = by[1][:half] + by[0][:n - half]
    return [(g, m["label"], m["pmids"], m["n"]) for g, m in picked]


def ask_gene(symbol: str) -> tuple[str | None, str]:
    user = (f"A laboratory mouse carries a homozygous loss-of-function (knockout) mutation "
            f"in the gene {symbol}. No phenotype information is provided.\n\n"
            f"Question: Does this knockout impair survival (cause premature death or a "
            f"shortened lifespan)?\n\nOptions: A. Yes  B. No\n\n"
            f"Reason briefly, then on the FINAL line output exactly: Answer: <letter>")
    r = chat([{"role": "system", "content": SYS_PROMPT},
              {"role": "user", "content": user}], max_tokens=500)
    if not r.ok:
        return None, f"ERROR: {r.error}"
    return parse_letter(r.content), r.content


def parse_letter(text: str) -> str | None:
    t = (text or "").strip()
    if "</think>" in t:
        t = t.rsplit("</think>", 1)[1].strip() or t
    m = re.search(r"answer\s*[:=]?\s*\(?([AB])\)?", t, re.I)
    if m:
        return m.group(1).upper()
    # last standalone A/B in the (post-think) tail
    found = re.findall(r"\b([AB])\b", t)
    return found[-1].upper() if found else None


def bootstrap_gap(fam_correct, obs_correct, iters=5000, seed=0):
    rng = random.Random(seed)
    gaps = []
    for _ in range(iters):
        f = [rng.choice(fam_correct) for _ in fam_correct]
        o = [rng.choice(obs_correct) for _ in obs_correct]
        gaps.append(sum(f) / len(f) - sum(o) / len(o))
    gaps.sort()
    return gaps[int(0.025 * iters)], gaps[int(0.975 * iters)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="genes per group")
    ap.add_argument("--seed", type=int, default=config.SEED)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--tag", default="", help="suffix for output files (keeps prior runs)")
    args = ap.parse_args()

    global OUT_CSV, OUT_JSON
    if args.tag:
        OUT_CSV = os.path.join(DATA, f"contamination_probe_results_{args.tag}.csv")
        OUT_JSON = os.path.join(DATA, f"contamination_probe_summary_{args.tag}.json")

    print("[probe] loading gene sets ...", flush=True)
    genage = genage_mouse_symbols()
    block = blocklist_symbols()
    labels = per_gene_labels()
    print(f"[probe] GenAge mouse: {len(genage)} | blocklist: {len(block)} | "
          f"MGI single-gene KO genes with clean label: {len(labels)}", flush=True)

    famous_c = {g: m for g, m in labels.items() if g in genage}
    obscure_c = {g: m for g, m in labels.items() if g not in block}  # not famous at all
    fam = balanced_sample(famous_c, args.n, args.seed, prefer="desc")
    obs = balanced_sample(obscure_c, args.n, args.seed, prefer="asc")
    print(f"[probe] sampled famous={len(fam)} obscure={len(obs)}", flush=True)
    print(f"        famous label balance: {Counter(l for _,l,_,_ in fam)}", flush=True)
    print(f"        obscure label balance: {Counter(l for _,l,_,_ in obs)}", flush=True)

    items = [("famous", g, l, p) for g, l, p, _ in fam] + \
            [("obscure", g, l, p) for g, l, p, _ in obs]

    results = []

    def run(it):
        group, gene, gold_lab, pmids = it
        pred, raw = ask_gene(gene)
        gold = "A" if gold_lab == 1 else "B"
        return {"group": group, "gene": gene, "gold": gold, "gold_label": gold_lab,
                "pred": pred or "", "correct": int(pred == gold) if pred else 0,
                "parsed": pred is not None, "pmids": pmids,
                "raw": (raw or "").replace("\n", " ")[:300]}

    print(f"[probe] querying LongevityLLM ({len(items)} calls, {args.workers} workers) ...", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run, it) for it in items]
        done = 0
        for fut in as_completed(futs):
            results.append(fut.result())
            done += 1
            if done % 10 == 0:
                print(f"   ... {done}/{len(items)}", flush=True)

    # per-gene CSV
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["group", "gene", "gold", "gold_label", "pred",
                                          "correct", "parsed", "pmids", "raw"])
        w.writeheader()
        for r in sorted(results, key=lambda x: (x["group"], x["gene"])):
            w.writerow(r)

    # metrics
    def acc(group, subset=None):
        rs = [r for r in results if r["group"] == group and (subset is None or r["gold_label"] == subset)]
        rs = [r for r in rs if r["parsed"]]
        return (sum(r["correct"] for r in rs) / len(rs), len(rs)) if rs else (None, 0)

    fam_acc, fam_n = acc("famous")
    obs_acc, obs_n = acc("obscure")
    fam_yes, fam_yes_n = acc("famous", 1)
    obs_yes, obs_yes_n = acc("obscure", 1)
    fam_correct = [r["correct"] for r in results if r["group"] == "famous" and r["parsed"]]
    obs_correct = [r["correct"] for r in results if r["group"] == "obscure" and r["parsed"]]
    gap = (fam_acc - obs_acc) if (fam_acc is not None and obs_acc is not None) else None
    ci = bootstrap_gap(fam_correct, obs_correct) if (fam_correct and obs_correct) else (None, None)
    n_pred_no = Counter(r["pred"] for r in results)

    summary = {
        "model": config.LONGEVITY_MODEL, "base_url": config.LONGEVITY_BASE_URL,
        "seed": args.seed, "n_per_group": args.n,
        "famous_accuracy": fam_acc, "famous_n": fam_n,
        "obscure_accuracy": obs_acc, "obscure_n": obs_n,
        "recall_gap": gap, "gap_95ci": list(ci),
        "famous_yes_subset_acc": fam_yes, "famous_yes_n": fam_yes_n,
        "obscure_yes_subset_acc": obs_yes, "obscure_yes_n": obs_yes_n,
        "pred_distribution": dict(n_pred_no),
        "parse_failures": sum(1 for r in results if not r["parsed"]),
    }
    json.dump(summary, open(OUT_JSON, "w"), indent=2)

    print("\n================ CONTAMINATION PROBE SUMMARY ================")
    print(f"model: {config.LONGEVITY_MODEL}")
    print(f"FAMOUS (GenAge)  accuracy: {fam_acc:.1%} (n={fam_n})" if fam_acc is not None else "famous: n/a")
    print(f"OBSCURE          accuracy: {obs_acc:.1%} (n={obs_n})" if obs_acc is not None else "obscure: n/a")
    print(f"RECALL GAP (famous - obscure): {gap:+.1%}  95% CI [{ci[0]:+.1%}, {ci[1]:+.1%}]" if gap is not None else "gap: n/a")
    print(f"  impairs=YES subset: famous {fam_yes:.0%} (n={fam_yes_n}) vs obscure {obs_yes:.0%} (n={obs_yes_n})"
          if (fam_yes is not None and obs_yes is not None) else "")
    print(f"  prediction distribution: {dict(n_pred_no)} | parse failures: {summary['parse_failures']}")
    print(f"\nwrote: {OUT_CSV}\nwrote: {OUT_JSON}")


if __name__ == "__main__":
    main()
