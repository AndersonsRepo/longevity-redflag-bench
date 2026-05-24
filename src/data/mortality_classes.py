"""Deterministic classification of the MP mortality/aging subtree (MP:0010768) terms.

WHY THIS EXISTS: scripts/build_mgi_dataset.py set label_impairs_survival=1 for ANY term
in the MP:0010768 subtree. That subtree is BIDIRECTIONAL and heterogeneous — it contains
longevity-EXTENDING terms ("extended life span", "slow aging"), PROTECTIVE terms
("decreased susceptibility to ... mortality"), CONDITIONAL challenge-induced terms
("increased susceptibility to viral infection induced mortality"), and REPRODUCTIVE terms
("premature ovarian failure"). Labeling all of those "impairs survival" is wrong — a
longevity mutant tagged impairs=1 actively penalizes a model that reasons correctly.

This module is the SINGLE deterministic source of truth that splits each term into:
  category            : death | beneficial | protective | conditional | reproductive | ambiguous
  label_contribution  : 1 (impairs survival) | 0 (does NOT / reversed) | None (exclude from baseline)
  lethality_stage     : developmental | postnatal | adult_aging | unspecified | na

The rules are pure string logic over the curated MP term NAMES (no ontology walk, no AI).
scripts/classify_mortality_terms.py freezes the output to data/mp_mortality_classified.csv;
src/data/mgi.py consumes that FROZEN TABLE (not these rules) so the ground truth is the
reviewable CSV, not code. Per-genotype aggregation (precedence, contradiction handling)
lives in mgi.py.

Verified against the real 74,573-row CSV: covers all 106 distinct mortality names present
(0 UNCLASSIFIED); reproduces the 407 flat-reversed positives (= 301 protective + 106
beneficial) and the ~18,471 clean death-positives.
"""
from __future__ import annotations

from typing import Optional, Tuple

# category -> baseline-binary handling
LABEL_1_CATS = ("death",)                       # impairs survival
LABEL_0_CATS = ("beneficial", "protective")     # does NOT impair (currently mislabeled 1) -> hard negatives
EXCLUDE_CATS = ("conditional", "reproductive", "ambiguous")  # out of the baseline binary

_BENEFICIAL = {"extended life span", "slow aging", "increased tumor-free survival time"}
_REPRODUCTIVE = {"early reproductive senescence", "premature ovarian failure",
                 "pregnancy-related premature death"}
# "mortality/aging" is the bare ROOT (MP:0010768) — direction-less, and the build script's
# descendants-only walk let it leak into phenotype profiles. Treat it as ambiguous (exclude).
_AMBIGUOUS = {"abnormal survival", "abnormal tumor-free survival time", "mortality/aging"}
_DEATH_DEV_SUBSTR = ("embryonic lethality", "prenatal lethality", "perinatal lethality",
                     "neonatal lethality", "preweaning lethality", "lethality at weaning",
                     "lethality during fetal growth", "lethality throughout fetal growth")
_DEATH_ADULT = {"premature death", "premature aging", "moribund",
                "sudden unexpected death in epilepsy", "decreased tumor-free survival time"}
_DEATH_UNSPEC = {"lethality, complete penetrance", "lethality, incomplete penetrance",
                 "decreased survivor rate"}


def classify_term(name: str) -> Tuple[str, Optional[int], str]:
    """Classify ONE MP mortality-term name. Returns (category, label_contribution, stage)."""
    n = name.strip().strip('"').lower()

    # --- wrong-direction: longevity-EXTENDING / beneficial (currently mislabeled 1) ---
    if n in _BENEFICIAL:
        return ("beneficial", 0, "aging")
    # --- protective: decreased death / decreased susceptibility (currently mislabeled 1) ---
    if n.startswith("decreased susceptibility") or n.startswith("decreased mortality induced"):
        return ("protective", 0, "na")
    # --- conditional / challenge-induced: only dies when challenged (exclude from baseline) ---
    if (n.startswith("increased susceptibility") or n.startswith("increased mortality induced")
            or n.startswith("abnormal susceptibility") or n.startswith("abnormal mortality induced")
            or n in ("abnormal induced morbidity/mortality",
                     "abnormal xenobiotic induced morbidity/mortality")):
        return ("conditional", None, "na")
    # --- reproductive: not organismal baseline death (exclude) ---
    if n in _REPRODUCTIVE:
        return ("reproductive", None, "na")
    # --- ambiguous direction (exclude) ---
    if n in _AMBIGUOUS:
        return ("ambiguous", None, "na")
    # --- DEATH (impairs survival) with a lethality-stage axis ---
    if any(k in n for k in _DEATH_DEV_SUBSTR):
        return ("death", 1, "developmental")
    if n.startswith("postnatal lethality"):
        return ("death", 1, "postnatal")
    if n in _DEATH_ADULT:
        return ("death", 1, "adult_aging")
    if n in _DEATH_UNSPEC:
        return ("death", 1, "unspecified")
    return ("UNCLASSIFIED", None, "na")
