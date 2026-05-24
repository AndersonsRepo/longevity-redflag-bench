"""Eval smoke for LB-0138: run a model over the matched geno_pheno / pheno_only pairs and
report accuracy per condition + the headline Delta_recall = acc(geno_pheno) - acc(pheno_only).

Models:
  --model longevity  Longevity-LLM HF endpoint (free; src.model.client.chat)
  --model claude     Claude SOTA arm (spends the $50 credit; needs `anthropic` + ANTHROPIC_API_KEY)

    python scripts/eval_lb0138.py --model longevity --n-per-condition 20 --workers 8
    python scripts/eval_lb0138.py --model claude --claude-model claude-sonnet-4-6 --n-per-condition 20

Writes outputs/eval_lb0138_<model>.jsonl (per-item predictions) and prints the scorecard.
Gold: A = impairs survival (label 1), B = does NOT (label 0).
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from schema.records import Format
from src import config
from src.model.parse import parse


def _call_longevity(messages, max_tokens):
    from src.model.client import chat
    r = chat(messages, temperature=0.0, max_tokens=max_tokens)
    return r.content, r.ok, r.error, r.latency_s


def _call_claude(messages, max_tokens, model):
    import time
    from anthropic import Anthropic
    client = Anthropic(api_key=config.require("ANTHROPIC_API_KEY", config.ANTHROPIC_API_KEY))
    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    convo = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    t0 = time.time()
    try:
        resp = client.messages.create(model=model, max_tokens=max_tokens, temperature=0.0,
                                       system=system, messages=convo)
        txt = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return txt, True, None, time.time() - t0
    except Exception as e:  # noqa: BLE001
        return "", False, str(e), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default=os.path.join(config.OUTPUTS_DIR, "lb0138_sample.jsonl"))
    ap.add_argument("--model", choices=["longevity", "claude"], default="longevity")
    ap.add_argument("--claude-model", default="claude-sonnet-4-6")
    ap.add_argument("--n-per-condition", type=int, default=20)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=600)
    ap.add_argument("--out", default=None, help="output path (default outputs/eval_lb0138_<model>.jsonl)")
    args = ap.parse_args()

    records = [json.loads(l) for l in open(args.jsonl, encoding="utf-8") if l.strip()]
    by_cond = defaultdict(list)
    for r in records:
        by_cond[json.loads(r["metadata"])["condition"]].append(r)
    items = []
    for cond, recs in by_cond.items():
        items.extend(recs[:args.n_per_condition])
    print(f"model={args.model}{'/'+args.claude_model if args.model=='claude' else ''}  "
          f"items={len(items)} ({args.n_per_condition}/condition)  workers={args.workers}")

    def run_one(rec):
        meta = json.loads(rec["metadata"])
        prompt_msgs = [{"role": m["role"], "content": m["content"]} for m in rec["messages"][:-1]]
        if args.model == "longevity":
            content, ok, err, lat = _call_longevity(prompt_msgs, args.max_tokens)
        else:
            content, ok, err, lat = _call_claude(prompt_msgs, args.max_tokens, args.claude_model)
        pa = parse(content, Format.binary)
        gold = rec["messages"][-1]["content"].strip().upper()
        pred = pa.answer if pa.ok else None
        return {
            "genotype_id": meta.get("genotype_id") or meta.get("base_profile_id", ""),
            "condition": meta.get("condition"),
            "mortality_category": meta.get("mortality_category"),
            "lethality_stage": meta.get("lethality_stage"),
            "gold": gold, "pred": pred, "correct": (pred == gold),
            "parse_failure": pa.failure_type, "parse_path": pa.path,
            "ok": ok, "error": err, "latency_s": round(lat, 1),
            "raw": content,        # FULL model reply (not truncated) — for the judges / evidence
        }

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(run_one, items))

    outp = args.out or os.path.join(config.OUTPUTS_DIR, f"eval_lb0138_{args.model}.jsonl")
    with open(outp, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # ---- scorecard ----
    per_cond = defaultdict(lambda: {"n": 0, "correct": 0, "parse_fail": 0, "api_fail": 0})
    for r in results:
        c = per_cond[r["condition"]]
        c["n"] += 1
        c["correct"] += int(r["correct"])
        c["parse_fail"] += int(r["parse_failure"] is not None)
        c["api_fail"] += int(not r["ok"])
    print("\n--- scorecard ---")
    accs = {}
    for cond in ("geno_pheno", "pheno_only"):
        c = per_cond.get(cond)
        if not c or not c["n"]:
            continue
        acc = c["correct"] / c["n"]
        accs[cond] = acc
        print(f"  {cond:11} acc={acc:.3f}  ({c['correct']}/{c['n']})  "
              f"parse_fail={c['parse_fail']}  api_fail={c['api_fail']}")
    if "geno_pheno" in accs and "pheno_only" in accs:
        print(f"\n  Delta_recall = acc(geno_pheno) - acc(pheno_only) = "
              f"{accs['geno_pheno'] - accs['pheno_only']:+.3f}")
    # reversed-hard-negative slice (longevity-extending strains)
    rev = [r for r in results if r["mortality_category"] == "reversed"]
    if rev:
        rc = sum(int(r["correct"]) for r in rev)
        print(f"  reversed hard-negatives: {rc}/{len(rev)} correct "
              f"(model should answer B=does-not-impair)")
    print(f"\nwrote -> {outp}")


if __name__ == "__main__":
    main()
