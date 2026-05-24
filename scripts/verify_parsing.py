"""Parse-path verification: do the models actually emit the requested 'Answer: <letter>' format,
or is our parser silently guessing via its last-resort fallback? Re-runs a sample on the FULL
response (stored eval `raw` is truncated, so we can't audit retroactively) and records, per item,
which extraction path fired:

  explicit       -> matched "Answer: X" / "Option X"  (the requested format — reliable)
  leading        -> a bare letter at the start of the answer region (reliable-ish)
  fallback_last  -> NO explicit answer; parser grabbed the LAST standalone A-E (GUESS — risky)
  none           -> no letter at all (true parse failure)

Also flags `explicit_vs_fallback_disagree`: cases where the fallback would pick a DIFFERENT letter
than the explicit answer (i.e., where the lenient fallback would have mis-graded). A high explicit
rate + low/zero disagreement = our accuracy numbers are reliable. Otherwise we tighten the parser.

    python scripts/verify_parsing.py [--n-per-condition 30 --claude-model claude-sonnet-4-6]
Writes results/parse_audit.json. Mirrors src/model/parse.py _letter exactly.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402
from src.model.client import chat, chat_claude  # noqa: E402

_EXPLICIT = re.compile(r"\b(?:answer|option)\s*[:=]?\s*\(?([A-E])\)?", re.I)
_LEADING = re.compile(r"\(?([A-E])\)?[\.\):]?\b", re.I)
_ALL = re.compile(r"\b([A-E])\b")


def audit(text):
    region = text.rsplit("</think>", 1)[-1] if "</think>" in text else text
    e = _EXPLICIT.search(region)
    lead = _LEADING.match(region.strip())
    alll = _ALL.findall(region)
    if e:
        path, letter = "explicit", e.group(1).upper()
    elif lead:
        path, letter = "leading", lead.group(1).upper()
    elif alll:
        path, letter = "fallback_last", alll[-1].upper()
    else:
        path, letter = "none", None
    expl = e.group(1).upper() if e else None
    fb = alll[-1].upper() if alll else None
    return {"path": path, "letter": letter,
            "explicit_vs_fallback_disagree": bool(expl and fb and expl != fb),
            "has_answer_keyword": bool(re.search(r"\banswer\s*[:=]", region, re.I)),
            "resp_chars": len(text)}


def run(model, items, claude_model):
    def one(rec):
        msgs = [{"role": m["role"], "content": m["content"]} for m in rec["messages"][:-1]]
        r = (chat_claude(msgs, model=claude_model, max_tokens=1500) if model == "claude"
             else chat(msgs, max_tokens=600))
        cond = json.loads(rec["metadata"])["condition"]
        if not r.ok:
            return {"path": "api_error", "ok": False, "condition": cond}
        a = audit(r.content)
        a["ok"] = True
        a["condition"] = cond
        return a
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(one, items))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default=os.path.join(config.OUTPUTS_DIR, "longevity_controlled.jsonl"))
    ap.add_argument("--n-per-condition", type=int, default=30)
    ap.add_argument("--claude-model", default="claude-sonnet-4-6")
    a = ap.parse_args()

    recs = [json.loads(l) for l in open(a.jsonl, encoding="utf-8") if l.strip()]
    by_cond = {"geno_pheno": [], "pheno_only": []}
    for r in recs:
        by_cond[json.loads(r["metadata"])["condition"]].append(r)
    items = by_cond["geno_pheno"][:a.n_per_condition] + by_cond["pheno_only"][:a.n_per_condition]

    out = {}
    for model in ("longevity", "claude"):
        res = run(model, items, a.claude_model)
        valid = [r for r in res if r["ok"]]
        paths = Counter(r["path"] for r in res)
        n = len(valid)
        out[model] = {
            "n": len(res), "api_errors": sum(1 for r in res if not r["ok"]),
            "path_counts": dict(paths),
            "explicit_rate": round(paths.get("explicit", 0) / n, 4) if n else None,
            "fallback_rate": round(paths.get("fallback_last", 0) / n, 4) if n else None,
            "none_rate": round(paths.get("none", 0) / n, 4) if n else None,
            "answer_keyword_rate": round(sum(r.get("has_answer_keyword", False) for r in valid) / n, 4) if n else None,
            "fallback_disagreements": sum(r.get("explicit_vs_fallback_disagree", False) for r in valid),
        }
        print(f"[{model}] n={out[model]['n']} explicit={out[model]['explicit_rate']} "
              f"fallback={out[model]['fallback_rate']} none={out[model]['none_rate']} "
              f"answer_kw={out[model]['answer_keyword_rate']} "
              f"fallback_disagreements={out[model]['fallback_disagreements']} paths={out[model]['path_counts']}")

    json.dump(out, open(os.path.join(config.REPO_ROOT, "results", "parse_audit.json"), "w"), indent=2)
    print("\nwrote -> results/parse_audit.json")


if __name__ == "__main__":
    main()
