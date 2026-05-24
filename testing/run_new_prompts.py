#!/usr/bin/env python3
"""Test the 12 new benchmark prompts (4 categories) against Longevity-LLM + judge scorer.

Sends each prompt to the model endpoint, captures the <think> trace,
runs programmatic checks + Claude Haiku verification, saves everything to
testing/new_prompts_results.json.

Usage:  python testing/run_new_prompts.py
"""

import json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src import config

PROMPTS = [
    {
        "id": "MM-001", "category": "multi_mutant", "title": "Arv1 × Cry1 double knockout",
        "format": "binary", "difficulty": "medium", "genes": ["Arv1", "Cry1"],
        "answer": "A",
        "prompt": (
            "Based on the known individual effects of the two gene knockouts listed below, "
            "predict whether the double-knockout organism will exhibit premature death compared to wild type.\n\n"
            "Options:\n  A. Yes — premature death expected\n  B. No — normal lifespan expected\n\n"
            "Mutant 1:\n  Gene: Arv1 | Zygosity: homozygote | Expression: decreased\n"
            "  Phenotypes: decreased circulating HDL cholesterol level | abnormal liver physiology | "
            "decreased circulating triglyceride level | increased insulin sensitivity | seizures | "
            "impaired coordination | decreased brown adipose tissue amount\n"
            "  Single-mutant outcome: premature adult death\n\n"
            "Mutant 2:\n  Gene: Cry1 | Zygosity: homozygote | Expression: decreased\n"
            "  Phenotypes: increased leukocyte cell number | decreased circulating serum albumin level | "
            "decreased fasting circulating glucose level\n"
            "  Single-mutant outcome: no premature death\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "MM-002", "category": "multi_mutant", "title": "Fas × Ctla4 double knockout",
        "format": "pairwise", "difficulty": "hard", "genes": ["Fas", "Ctla4"],
        "answer": "A",
        "prompt": (
            "Which organism has a longer mean lifespan?\n\n"
            "Options:\n  A. Fas single-knockout mouse\n  B. Fas;Ctla4 double-knockout mouse\n\n"
            "Mutant 1:\n  Gene: Fas | Zygosity: homozygote | Expression: decreased\n"
            "  Phenotypes: enlarged spleen | enlarged lymph nodes | enlarged thymus | skin lesions | "
            "blood vessel inflammation | salivary gland inflammation | increased autoantibody level | "
            "abnormal T cell number | abnormal immune system physiology | abnormal thyroid gland morphology\n"
            "  Single-mutant outcome: premature adult death (lymphoproliferative autoimmune disease)\n\n"
            "Mutant 2:\n  Gene: Ctla4 | Zygosity: homozygote | Expression: decreased\n"
            "  Phenotypes: increased acute inflammation\n"
            "  Single-mutant outcome: premature adult death (systemic inflammatory infiltration)\n\n"
            "GO context:\n  FAS: death receptor mediating activation-induced T cell apoptosis — peripheral tolerance.\n"
            "  CTLA4: inhibitory co-receptor dampening T cell activation at priming — central checkpoint.\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "MM-003", "category": "multi_mutant", "title": "Col4a3 × Slc2a4 double knockout",
        "format": "pairwise", "difficulty": "hard", "genes": ["Col4a3", "Slc2a4"],
        "answer": "B",
        "prompt": (
            "Which organism reaches fatal phenotype threshold earlier?\n\n"
            "Options:\n  A. Col4a3 single-knockout mouse\n  B. Col4a3;Slc2a4 double-knockout mouse\n"
            "  C. Both show equivalent time to fatal phenotype\n\n"
            "Mutant 1:\n  Gene: Col4a3 | Zygosity: homozygote | Expression: decreased\n"
            "  Phenotypes: glomerulonephritis | albuminuria | increased urine protein level | "
            "renal interstitial fibrosis | kidney failure | glomerulosclerosis | "
            "increased circulating creatinine level | increased blood urea nitrogen level\n"
            "  Primary system: renal/urinary\n  Single-mutant outcome: premature adult death via progressive renal failure\n\n"
            "Mutant 2:\n  Gene: Slc2a4 | Zygosity: homozygote | Expression: decreased\n"
            "  Phenotypes: abnormal circulating glucose level | cardiac hypertrophy | postnatal growth retardation | "
            "increased circulating insulin level | abnormal muscle physiology | insulin resistance | "
            "decreased circulating free fatty acids level | increased heart weight\n"
            "  Primary system: homeostasis/metabolism\n  Single-mutant outcome: premature adult death via cardiac and metabolic failure\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "SG-001", "category": "synthetic_gene", "title": "Lgvx3 knockout — late-endosomal lipid trafficking",
        "format": "binary", "difficulty": "medium", "genes": ["Lgvx3"],
        "answer": "A",
        "prompt": (
            "A novel gene, Lgvx3 (Lipid Globule Vesicle X-3), encodes a late-endosomal lipid transfer protein "
            "involved in intracellular cholesterol export, expressed predominantly in hepatocytes and macrophages.\n\n"
            "Based solely on the homozygous knockout phenotype profile below, predict whether this mutant "
            "exhibits premature death.\n\n"
            "Options:\n  A. Yes — premature death expected\n  B. No — normal lifespan expected\n\n"
            "Phenotypes: increased liver cholesterol level | foam cell reticulosis | hepatic steatosis | "
            "increased circulating triglyceride level | decreased circulating HDL cholesterol level | "
            "abnormal macrophage physiology | liver inflammation | progressive weight loss\n\n"
            "Constraint: Lgvx3 is a hypothetical gene. No experimental lifespan data exists. "
            "Reason from phenotype profile alone. Do not infer from gene name.\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "SG-002", "category": "synthetic_gene", "title": "Hspk2 knockout — proteotoxic stress kinase",
        "format": "binary", "difficulty": "easy", "genes": ["Hspk2"],
        "answer": "B",
        "prompt": (
            "A novel gene, Hspk2 (Heat Shock Protein Kinase 2), encodes a serine/threonine kinase that "
            "phosphorylates HSP70-family chaperones during proteotoxic stress, ubiquitously expressed.\n\n"
            "Based solely on the homozygous knockout phenotype profile below, predict whether this mutant "
            "exhibits premature death.\n\n"
            "Options:\n  A. Yes — premature death expected\n  B. No — normal lifespan expected\n\n"
            "Phenotypes: increased anxiety-related response | decreased locomotor activity | "
            "abnormal social investigation | increased grooming behavior | abnormal object recognition memory | "
            "decreased exploration in new environment\n\n"
            "Constraint: Hspk2 is a hypothetical gene. No experimental lifespan data exists. "
            "Reason from phenotype profile alone. Do not infer from gene name.\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "SG-003", "category": "synthetic_gene", "title": "Tmfc5 overexpression — cardiac matrix connector",
        "format": "multiclass", "difficulty": "medium", "genes": ["Tmfc5"],
        "answer": "C",
        "prompt": (
            "A novel gene, Tmfc5 (Transmembrane Fibronectin Connector 5), encodes a transmembrane adaptor "
            "linking extracellular matrix to cardiomyocyte cytoskeleton, expressed at high levels in cardiac muscle.\n\n"
            "Based solely on the hemizygous overexpression phenotype profile below, select the most likely "
            "mortality category.\n\n"
            "Options:\n  A. No premature death — normal lifespan\n  B. Premature death, developmental onset\n"
            "  C. Premature death, adult-aging onset (gradual deterioration)\n  D. Perinatal lethality\n\n"
            "Phenotypes: cardiac hypertrophy | increased myocardial fiber size | cardiac interstitial fibrosis | "
            "decreased cardiac muscle contractility | thick ventricular wall | abnormal heart echocardiography feature\n\n"
            "Constraint: Tmfc5 is a hypothetical gene. No experimental lifespan data exists. "
            "Reason from phenotype profile alone.\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "RP-001", "category": "reverse_lookup", "title": "Identify gene: cerebellar + lipid storage",
        "format": "multiple_choice", "difficulty": "easy", "genes": ["Npc1", "Arv1", "Slc2a4", "Hnf1b"],
        "answer": "B",
        "prompt": (
            "A homozygous knockout mouse exhibits the following phenotype profile. "
            "Which gene was most likely knocked out?\n\n"
            "Phenotypes: decreased Purkinje cell number | weight loss | ataxia | abnormal lipid level | "
            "increased liver cholesterol level | tremors | foam cell reticulosis | decreased body weight\n\n"
            "Options:\n  A. Arv1 — lipid transfer protein, HDL biogenesis, liver and brain\n"
            "  B. Npc1 — NPC intracellular cholesterol transporter, late endosomal\n"
            "  C. Slc2a4 — GLUT4, insulin-stimulated glucose transporter, muscle and adipose\n"
            "  D. Hnf1b — hepatocyte nuclear factor 1-beta, liver/kidney/pancreas\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "RP-002", "category": "reverse_lookup", "title": "Identify gene: glucose transport + cardiac",
        "format": "multiple_choice", "difficulty": "medium", "genes": ["Slc2a4", "Npc1", "Arv1", "Col4a3"],
        "answer": "C",
        "prompt": (
            "A homozygous knockout mouse (decreased expression) exhibits the following phenotype profile. "
            "Which gene was most likely knocked out?\n\n"
            "Phenotypes: abnormal circulating glucose level | cardiac hypertrophy | postnatal growth retardation | "
            "increased circulating insulin level | insulin resistance | decreased circulating free fatty acids level | "
            "increased heart weight | decreased circulating ketone body level\n\n"
            "Options:\n  A. Npc1 — NPC intracellular cholesterol transporter\n"
            "  B. Arv1 — ARV1 lipid transfer protein, HDL biogenesis\n"
            "  C. Slc2a4 — GLUT4, insulin-stimulated glucose uptake in muscle and adipose\n"
            "  D. Col4a3 — type IV collagen alpha-3 chain, basement membrane structure\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "RP-003", "category": "reverse_lookup", "title": "Identify gene: lymphoproliferative multi-organ",
        "format": "multiple_choice", "difficulty": "hard", "genes": ["Fas", "Smad3", "Ctla4", "Bcl2l11"],
        "answer": "D",
        "prompt": (
            "A homozygous knockout mouse (decreased expression) exhibits the following phenotype profile. "
            "Which gene was most likely knocked out?\n\n"
            "Phenotypes: enlarged spleen | enlarged lymph nodes | enlarged thymus | blood vessel inflammation | "
            "salivary gland inflammation | skin lesions | increased autoantibody level | abnormal T cell number | "
            "abnormal immune system physiology | abnormal thyroid gland morphology\n\n"
            "Options:\n  A. Smad3 — TGF-beta signal transducer, immune and epithelial homeostasis\n"
            "  B. Ctla4 — CTLA-4, T cell co-inhibitory receptor at priming stage\n"
            "  C. Bcl2l11 — BIM, pro-apoptotic BCL-2 family member in lymphocytes\n"
            "  D. Fas — FAS death receptor, activation-induced T cell peripheral deletion\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "GC-001", "category": "gene_complement", "title": "Complement to Ctla4 KO — dual T-cell checkpoint",
        "format": "multiple_choice", "difficulty": "hard", "genes": ["Ctla4", "Fas", "Cry1", "Gatm", "Npc2"],
        "answer": "A",
        "prompt": (
            "Gene A has been identified as Ctla4 (homozygous knockout, decreased expression). "
            "The observed combined phenotype is substantially broader than Ctla4 KO alone. "
            "Which additional gene knockout (Gene B) most likely produces the full observed phenotype?\n\n"
            "Ctla4 KO alone: increased acute inflammation (rapid systemic T cell activation)\n\n"
            "Combined observed phenotype: enlarged spleen | increased autoantibody level | lymphoproliferation | "
            "abnormal T cell number | blood vessel inflammation | salivary gland inflammation | skin lesions | "
            "abnormal thyroid gland morphology | multi-organ immune infiltration\n\n"
            "Options:\n  A. Fas — FAS death receptor, peripheral T cell activation-induced apoptosis\n"
            "  B. Cry1 — Cryptochrome 1, core circadian clock component\n"
            "  C. Gatm — glycine amidinotransferase, creatine biosynthesis\n"
            "  D. Npc2 — NPC intracellular cholesterol transporter 2\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "GC-002", "category": "gene_complement", "title": "Complement to Arv1 KO — atherogenic lipid axis",
        "format": "multiple_choice", "difficulty": "medium", "genes": ["Arv1", "Ddr1", "Ldlr", "Proc", "Nherf1", "Sun3"],
        "answer": "A",
        "prompt": (
            "Gene A has been identified as Arv1 (homozygous knockout, decreased expression). "
            "The combined phenotype includes vascular pathology absent from Arv1 KO alone. "
            "Which additional gene knockout (Gene B) most likely contributes the vascular component?\n\n"
            "Arv1 KO alone: decreased circulating HDL | abnormal liver physiology | decreased circulating "
            "triglyceride level | increased insulin sensitivity | seizures | impaired coordination\n\n"
            "Combined observed phenotype: decreased circulating HDL | hepatic steatosis | abnormal lipid "
            "homeostasis | atherosclerotic lesions | decreased macrophage cell number | increased liver "
            "cholesterol level | abnormal blood vessel morphology\n\n"
            "Options:\n  A. Ddr1;Ldlr (multi-locus) — collagen receptor DDR1 + LDL receptor\n"
            "  B. Proc — Protein C, anticoagulant serine protease\n"
            "  C. Nherf1 — Na+/H+ exchanger regulatory factor, phosphate reabsorption\n"
            "  D. Sun3 — SUN domain protein 3, nuclear envelope architecture\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
    {
        "id": "GC-003", "category": "gene_complement", "title": "Complement to Col4a3 KO — immune-mediated nephropathy",
        "format": "multiple_choice", "difficulty": "hard", "genes": ["Col4a3", "Was", "Proc", "Foxo4", "Tgm3"],
        "answer": "A",
        "prompt": (
            "Gene A has been identified as Col4a3 (homozygous knockout, decreased expression). "
            "The combined phenotype includes immune-complex glomerular pathology absent from Col4a3 KO alone. "
            "Which additional gene knockout (Gene B) most likely adds the immune-mediated component?\n\n"
            "Col4a3 KO alone: glomerulonephritis | albuminuria | increased urine protein | renal interstitial "
            "fibrosis | kidney failure | glomerulosclerosis | increased circulating creatinine | increased BUN\n\n"
            "Combined observed phenotype: glomerulonephritis | albuminuria | renal interstitial fibrosis | "
            "kidney failure | abnormal glomerular mesangium | increased mesangial cell number | expanded mesangial "
            "matrix | increased IgM level | increased IgA level | renal glomerular immunoglobulin deposits\n\n"
            "Options:\n  A. Was — Wiskott-Aldrich syndrome protein, actin cytoskeleton in hematopoietic cells\n"
            "  B. Proc — Protein C, anticoagulant, coagulation cascade\n"
            "  C. Foxo4 — FOXO4 transcription factor, hemizygous, urinary bladder\n"
            "  D. Tgm3 — Transglutaminase 3, kidney morphology\n\n"
            "Think step by step, then answer with the option letter.\nAnswer: "
        ),
    },
]


def call_model(prompt_text):
    """Try Longevity-LLM first; fall back to Claude via existing client."""
    from src.model.client import chat, chat_claude

    msgs = [{"role": "user", "content": prompt_text}]
    res = chat(msgs, max_tokens=400, retries=1, backoff=(2,))
    if res.ok:
        return res.content, res.latency_s, "longevity-llm", None

    res2 = chat_claude(msgs, max_tokens=600, retries=2, backoff=(2, 5))
    if res2.ok:
        return res2.content, res2.latency_s, "claude-sonnet", None

    return None, 0, "none", res2.error


def extract_answer(text):
    if not text:
        return "?"
    region = text.rsplit("</think>", 1)[-1] if "</think>" in text else text
    m = re.search(r"\b(?:answer|option)\s*[:=]?\s*\(?([A-D])\)?", region, re.I)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-D])\b", region[-50:])
    return m.group(1).upper() if m else "?"


def main():
    sys.path.insert(0, str(ROOT / "judge"))
    from score_trace import score_trace

    results = []
    correct = 0
    total = len(PROMPTS)

    print(f"\n{'='*65}")
    print(f"  TESTING 12 NEW PROMPTS — Longevity-LLM + Judge Scorer")
    print(f"{'='*65}\n")

    for i, p in enumerate(PROMPTS, 1):
        print(f"[{i}/{total}] {p['id']} — {p['title']}")
        print(f"  Category: {p['category']} | Difficulty: {p['difficulty']} | Gold: {p['answer']}")

        raw, latency, model_used, err = call_model(p["prompt"])
        if err:
            print(f"  ERROR: {err}")
            results.append({"id": p["id"], "error": err})
            continue

        pred = extract_answer(raw)
        is_correct = pred == p["answer"]
        if is_correct:
            correct += 1
        print(f"  Model: {model_used} | Predicted: {pred} | Correct: {is_correct} | Latency: {latency:.1f}s")

        trace_result = score_trace(raw, pred, p["genes"], use_api=True)
        print(f"  Trace score: {trace_result['trace_score']:.3f}")

        for key, sub in trace_result["sub_scores"].items():
            s = sub.get("score")
            if s is not None:
                label = key.replace("_", " ").title()
                print(f"    {label}: {s:.3f}")
                if sub.get("hallucinated_genes"):
                    print(f"      Hallucinated: {sub['hallucinated_genes']}")
                if sub.get("contradicts"):
                    print(f"      Contradiction: {sub['reason']}")
                if sub.get("unverified"):
                    print(f"      Ungrounded: {sub['unverified']}")

        results.append({
            "id": p["id"],
            "category": p["category"],
            "title": p["title"],
            "format": p["format"],
            "difficulty": p["difficulty"],
            "genes": p["genes"],
            "gold_answer": p["answer"],
            "predicted_answer": pred,
            "correct": is_correct,
            "raw_response": raw,
            "model_used": model_used,
            "latency_s": round(latency, 2),
            "trace_score": trace_result["trace_score"],
            "sub_scores": {
                k: {kk: vv for kk, vv in v.items() if kk != "mentioned_genes"}
                for k, v in trace_result["sub_scores"].items()
            },
            "weights_used": trace_result["weights_used"],
        })
        print()

    print(f"{'='*65}")
    print(f"  ACCURACY: {correct}/{total} ({correct/total*100:.1f}%)")
    scores = [r["trace_score"] for r in results if "trace_score" in r]
    if scores:
        print(f"  MEAN TRACE SCORE: {sum(scores)/len(scores):.3f}")
    print(f"{'='*65}\n")

    out_path = ROOT / "testing" / "new_prompts_results.json"
    summary = {
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": config.LONGEVITY_MODEL,
        "endpoint": config.LONGEVITY_BASE_URL,
        "judge_model": config.JUDGE_MODEL,
        "total_prompts": total,
        "correct": correct,
        "accuracy": round(correct / total, 3),
        "mean_trace_score": round(sum(scores) / len(scores), 3) if scores else None,
        "results": results,
    }
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {out_path}\n")


if __name__ == "__main__":
    main()
