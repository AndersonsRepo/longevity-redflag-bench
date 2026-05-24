# Parse-path audit — is our answer extraction reliable?

**Date:** 2026-05-24 · **Script:** `scripts/verify_parsing.py` · **Data:** `results/parse_audit.json`

## Question
Our eval reported ~100% "parse success," but the parser (`src/model/parse.py`) has a **lenient
last-resort fallback** ("grab the LAST standalone A–E in the answer region"). 100% non-failure could
therefore mean *"a letter was always extractable"* rather than *"the model gave a clean answer"* —
and a fallback guess could silently mis-grade. So: how often does each extraction path fire?

## Method
Re-ran a sample (30 geno_pheno + 30 pheno_only = 60 items/model) on the controlled set with the FULL
response (stored eval `raw` is truncated, so retroactive audit is impossible). For each response we
record which path the parser used: **explicit** (`Answer: X`), **leading** (bare letter at the start
of the post-`</think>` region), **fallback_last** (low-confidence guess), or **none** (failure). We
also flag `explicit_vs_fallback_disagree` — cases where the fallback would pick a *different* letter.

## Results
| model | explicit | leading | **fallback_last** | none | fallback disagreements |
|---|---|---|---|---|---|
| **Claude Sonnet 4.6** | **100%** (60/60) | 0% | **0%** | 0% | 0 |
| **Longevity-LLM** | 5% (3/60) | **95%** (57/60) | **0%** | 0% | 0 |

## Conclusion — measurement is RELIABLE
- The **risky fallback fired 0% of the time**, with **0 disagreements** and **0 true failures**. Every
  answer was captured by a reliable path.
- **Claude** follows the requested `Answer: <letter>` format exactly (100%).
- **Longevity-LLM** does *not* write "Answer:" — it emits the **bare verdict letter immediately after
  `</think>`**, captured by the *leading-letter* path. (So "format compliance" differs by model, but
  the answer is extracted reliably either way.)
- Therefore the earlier "errors are task failures, not format failures" claim **holds**: the parser is
  not guessing, so wrong answers reflect the task, not extraction artifacts.

## Fix (so this is provable on EVERY future run, not just this audit)
- `src/model/parse.py` now records the extraction **`path`** on every `ParsedAnswer`
  (explicit | leading | fallback_last | none); `fallback_last` is documented as low-confidence.
- `scripts/eval_lb0138.py` stores **`parse_path`** in each eval record → any future fallback guess is
  visible in the data, never silent. Re-audit anytime: `python scripts/verify_parsing.py`.

## Caveat
Sample = 60 items/model on the controlled set; format behavior is a stable per-model habit, so this
generalizes, but the `parse_path` field now makes per-run verification automatic going forward.
