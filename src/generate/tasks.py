"""STUB — owner: Anderson. The NOVEL red-flag task generators. Each returns a list of
BenchmarkRecord (LongevityBench format). >= 50 rows per task (rows of a task share lb_id).
See mock/make_mock.py for worked examples of every record shape.

We do NOT rebuild plain NHANES mortality — those already exist as LB-0042/46/50/54.
Our contribution is counterfactual red-flag robustness + context-vs-keyword reasoning.

  LB-0142 gen_redflag_pairwise   pairwise/accuracy  — A (base) vs B (base+1 red flag)
  LB-0146 gen_redflag_relevance  binary/accuracy    — is THIS flag a real driver here? (traps)
  LB-0150 gen_redflag_setgen     generation/jaccard — which listed factors raise THIS risk?

Gold goes in the trailing assistant message; verifiable GT (direction, matched-cohort
band, should_moderate, split, cycle, base_profile_id) goes in metadata. Tag split by
covariates.cycle (build-plan.md §4). Validate with validate/validate_jsonl.py.
"""

from __future__ import annotations

from typing import List

from schema.records import BenchmarkRecord


def gen_redflag_pairwise(cohort, redflags, effects, n: int = 60) -> List[BenchmarkRecord]:
    """Base profile vs same profile + one injected red flag; gold = higher-risk option.
    Direction from matched_cohort.empirical_effect (fallback: redflags.csv direction)."""
    raise NotImplementedError("Anderson: build pairwise A/B; gold from effect direction.")


def gen_redflag_relevance(cohort, redflags, context_cases, n: int = 60) -> List[BenchmarkRecord]:
    """Is this red flag a clinically significant driver for THIS patient? Include the
    keyword-reactive traps from tasks/context_cases.yaml (gold=No despite scary keyword)."""
    raise NotImplementedError("Anderson: build binary relevance; wire context_cases traps.")


def gen_redflag_setgen(cohort, redflags, context_cases, n: int = 60) -> List[BenchmarkRecord]:
    """Which of the listed factors raise THIS patient's risk? Mix real drivers with
    managed/hereditary distractors; gold_set in metadata; metric=jaccard."""
    raise NotImplementedError("Anderson: build set-generation with distractors.")


ALL_GENERATORS = (gen_redflag_pairwise, gen_redflag_relevance, gen_redflag_setgen)
