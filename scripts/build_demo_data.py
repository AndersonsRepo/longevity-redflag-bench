"""Build a STATIC, pre-computed trace-scorer demo so Ibrahim's reasoning scorer can run entirely
on Lovable (no live API/backend). Selects story-telling ternary examples (the life-extension
blind-spot, a correct lethal, a correct neutral, a gene-shown vs gene-hidden ablation pair), joins
the model's full trace, runs the no-API trace checks (judge/score_trace.py), and bundles everything
into results/demo_data.json for the frontend to replay client-side.

    python scripts/build_demo_data.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import config  # noqa: E402

CLS = {"A": "Shortens", "B": "No effect", "C": "Extends"}
PROMPTS = os.path.join(config.OUTPUTS_DIR, "ternary.jsonl")
EVAL = os.path.join(config.OUTPUTS_DIR, "eval_longevity_ternary.jsonl")


def main():
    by_key = {}
    for l in open(PROMPTS, encoding="utf-8"):
        r = json.loads(l); m = json.loads(r["metadata"])
        by_key[(m["genotype_id"], m["condition"])] = {
            "genes": m["genes"], "prompt_text": r["messages"][1]["content"], "gold_class": m["ternary_class"]}
    ev = {}
    for l in open(EVAL, encoding="utf-8"):
        r = json.loads(l)
        ev[(r["genotype_id"], r["condition"])] = r

    # curate ~6 story-telling examples
    picks, used = [], set()

    def add(pred_filter, story, cond="geno_pheno", want_class=None, n=1):
        c = 0
        for (gid, cd), e in ev.items():
            if cd != cond or (gid, cd) in used:
                continue
            p = by_key.get((gid, cd))
            if not p or not p["genes"]:
                continue
            if want_class and p["gold_class"] != want_class:
                continue
            if pred_filter(e, p):
                picks.append((gid, cd, e, p, story)); used.add((gid, cd)); c += 1
                if c >= n:
                    return

    add(lambda e, p: p["gold_class"] == "extends" and not e["correct"], "Life-extension blind-spot: a longevity mutation the model misreads as harmful/neutral.", want_class="extends", n=2)
    add(lambda e, p: p["gold_class"] == "shortens" and e["correct"], "Correct: identifies a lethal/deleterious mutation.", want_class="shortens")
    add(lambda e, p: p["gold_class"] == "no_effect" and e["correct"], "Correct: identifies a no-effect mutation (uses the neutral option).", want_class="no_effect")

    # ablation pair: take one picked genotype, add its gene-hidden twin
    for gid, cd, e, p, story in list(picks):
        twin = ev.get((gid, "pheno_only"))
        if twin and (gid, "pheno_only") not in used:
            ptw = by_key.get((gid, "pheno_only"))
            picks.append((gid, "pheno_only", twin, ptw, "Ablation: same genotype with the gene name HIDDEN (reasoning vs recall)."))
            used.add((gid, "pheno_only")); break

    # run the no-API trace scorer
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        for gid, cd, e, p, story in picks:
            tf.write(json.dumps({"trace": e["raw"], "answer": e["pred"] or "", "genes_in_prompt": p["genes"]}) + "\n")
        tin = tf.name
    tout = tin.replace(".jsonl", "_scores.jsonl")
    subprocess.run([sys.executable, "judge/score_trace.py", tin, "--no-api", "-o", tout], check=True, cwd=config.REPO_ROOT)
    scores = [json.loads(l) for l in open(tout)]

    demo = []
    for i, ((gid, cd, e, p, story), sc) in enumerate(zip(picks, scores)):
        demo.append({
            "id": i, "genotype_id": gid, "genes": p["genes"], "condition": cd,
            "story": story, "prompt": p["prompt_text"],
            "gold": e["gold"], "gold_label": CLS.get(e["gold"]),
            "pred": e["pred"], "pred_label": CLS.get(e["pred"]), "correct": e["correct"],
            "trace": e["raw"], "trace_score": sc.get("trace_score"), "sub_scores": sc.get("checks", sc),
        })
    out = os.path.join(config.REPO_ROOT, "results", "demo_data.json")
    json.dump({"note": "Pre-computed trace-scorer demo (no live API). Longevity-LLM ternary; scores from judge/score_trace.py --no-api.",
               "examples": demo}, open(out, "w"), indent=2)
    print(f"wrote {len(demo)} demo examples -> {out}")
    for d in demo:
        print(f"  {d['genes']} [{d['condition']}] gold={d['gold_label']} pred={d['pred_label']} "
              f"correct={d['correct']} trace_score={d['trace_score']} :: {d['story'][:40]}")


if __name__ == "__main__":
    main()
