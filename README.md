# Red-Flag Clinical-Reasoning Benchmark

Caltech Longevity Hackathon — **Track 01: LongevityLLM Benchmarking**. We build a
JSONL/ChatML benchmark that tests whether Insilico's **Longevity-LLM (Qwen3.5-9B)**
derives a high-level phenotype (10-yr mortality) from low-level NHANES clinical data —
and whether it reasons about clinical *context* or reacts to scary keywords.

**The deliverable is the dataset** (`benchmark.jsonl`), not a demo. Judged on Utility /
Diversity / Retrieval-Resistance / Statistical-Rigor (20 pts). Full plan in the vault:
`vault/shared/caltech-hackathon-2026/` (build-plan, grading-rubric-spec, task-authoring-worksheet, deck→README).

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill HF_TOKEN (and ANTHROPIC_API_KEY for the bonus judge)

python scripts/smoke_endpoint.py                                   # hour-0: endpoint alive?
python scripts/contamination_probe.py                              # hour-0: model recognize NHANES?
python mock/make_mock.py                                           # build mock records
python validate/validate_jsonl.py mock/mock_records.jsonl --min-per-task 1   # gate works
```

## The contract — LongevityBench format
`schema/records.py :: BenchmarkRecord` mirrors the real LongevityBench row schema
(`lb_id, pool, display_name, display_group, domain, format, metric, units, messages,
task, has_reasoning, metadata`) so our tasks **extend the framework**. Confirmed against
a live `LB-0042` row:
- **gold = the trailing `assistant` message** (e.g. `"B"`); prompt sent = `messages[:-1]`.
- `metadata` is a **JSON string** of provenance; we stash our verifiable GT there
  (`red_flag, expected_direction, magnitude_band, should_moderate, evidence_ids, split, cycle, base_profile_id`).
A submission line is `record.model_dump_json()`. Build against `mock/mock_records.jsonl`.
**Don't change a field without telling the team.**

## Model behavior (verified live 2026-05-23)
Endpoint is **vLLM-served**, model id **`longevity-llm`** (not `tgi`), **28K** real context
(`max_model_len`), ~8s/call. It **ignores JSON formatting** and answers in verbose prose, so:
- End every prompt with `Reason briefly, then on the FINAL line output exactly: Answer: <letter>`
  and call with `max_tokens >= ~400`. `src/model/parse.py` extracts the trailing letter.
- The reasoning prose is a bonus-track asset → set `has_reasoning=True` and feed the scorer.
- Calls need `MODEL_ACCESS_TOKEN` + `LONGEVITY_BASE_URL` (with `/v1`) in `.env`.

## Our tasks (the NOVEL part — we do NOT rebuild plain NHANES mortality)
Plain NHANES mortality/age already ship as **LB-0042/46/50/54** and **LB-0030/34/38** —
rebuilding them = zero novelty. Our contribution is **counterfactual red-flag robustness +
context-vs-keyword reasoning**, which doesn't exist in the benchmark:
- **LB-0142 `nhanes_redflag_pairwise`** (pairwise/accuracy) — A (base) vs B (base + 1 red flag)
- **LB-0146 `nhanes_redflag_relevance`** (binary/accuracy) — is this flag a real driver *for this patient*? (keyword traps)
- **LB-0150 `nhanes_redflag_setgen`** (generation/jaccard) — which listed factors raise *this* patient's risk?
- **bonus** — reasoning-verification scorer (`src/score/deterministic.py` + `judge.py`) over `has_reasoning` traces

Ground truth: relative (red-flag effect) from matched-cohort/epidemiology, in `metadata`.
Contamination is confirmed (NHANES is in LongevityBench) → the perturbation is what makes
these retrieval-resistant. Run `scripts/contamination_probe.py` to document it.

## Who owns what
| Person | Start here | Builds |
|---|---|---|
| **Anderson** | `src/generate/tasks.py` | task generators, profile render/perturb, model run+parse, scorer, `run_all.py` |
| **CS teammate** | `src/nhanes/build_cohort.py` | NHANES acquire/join/**censoring**, baselines, matched-cohort effects |
| **Bio 1** | `tasks/redflags.csv` | red-flag table: direction + HR band + citation (no git) |
| **Bio 2** | `tasks/context_cases.yaml` | keyword-traps + biological-correctness criteria + citations (no git) |

## How we work (lean — co-located, 32h)
- One repo, short-lived per-person branches, merge to `main` freely; **say it out loud** before merging. No required reviews.
- The **schema is the coordination mechanism**, not a board. Lock it; develop against mock.
- Bio teammates edit `tasks/*` in-repo or a shared doc — no git ceremony required.
- **Validate before every freeze:** `python validate/validate_jsonl.py outputs/benchmark.jsonl` must PASS.
- `data/` and `outputs/` are gitignored. **Never commit `.env` / `HF_TOKEN`.**

## Runnable now vs stubbed
- **Runnable:** smoke test, contamination probe, mock generator, validator, model client, parser, metrics, red-flag loader, bonus scorer.
- **Stubs (locked signatures, `# TODO(owner)`):** `src/nhanes/*`, `src/generate/*`, `src/baselines/*`, `run_all.py` wiring.
