// Auto-generated data module for the LongevityBench-Mouse dashboard (fully static).
// Create this as src/data.ts in the Lovable project; all components import from "@/data".

export const dashboardData = {
  "project": "LongevityBench-Mouse \u2014 Track 01, Caltech Longevity Hackathon 2026",
  "model_under_test": "Longevity-LLM (Insilico, Qwen3.5-9B, 28K ctx)",
  "sota_baseline": "Claude Sonnet 4.6",
  "tagline": "Can an aging-biology LLM reason from genotype+phenotype to a mutation's lifespan effect \u2014 or is it recalling famous genes?",
  "dataset": {
    "source": "MGI mouse genotype\u2192phenotype (Jackson Lab) + MP ontology; labels PMID-backed",
    "total_genotypes": 74573,
    "impairs_survival_death": 18465,
    "no_mortality": 54741,
    "life_extending": 407,
    "usable_life_extending": 51,
    "note": "Developmental lethality dominates the death class; we curate for adult/aging-onset (longevity-relevant) cases."
  },
  "headline_findings": [
    "Gene-recall reliance is a MULTI-GENE/epistasis artifact: significant on the mixed set (Longevity \u0394_recall 0.100, p=0.017) but COLLAPSES to non-significant on clean single-gene mutations (\u0394 0.017, p=0.86).",
    "Both models largely FAIL to recognize life-EXTENSION (ternary extends-recall 3\u201320/50 vs shortens 46\u201348/50) \u2014 they default to 'a mutation is harmful or neutral'.",
    "The 9B specialist is statistically indistinguishable from Claude Sonnet 4.6 on the survival binary (McNemar p=0.36/0.23).",
    "Famous longevity genes are recalled, obscure ones are not (gene-only probe) \u2014 justifying the retrieval-resistant obscure-gene design."
  ],
  "tests": {
    "binary_controlled": {
      "model_under_test": {
        "geno_pheno": 0.775,
        "pheno_only": 0.675,
        "delta_recall": 0.1,
        "delta_recall_ci95": [
          0.025,
          0.175
        ],
        "mcnemar_p": 0.0169,
        "significant": true
      },
      "sota": {
        "geno_pheno": 0.8167,
        "pheno_only": 0.7333,
        "delta_recall": 0.0833,
        "delta_recall_ci95": [
          -0.0083,
          0.175
        ],
        "mcnemar_p": 0.09874,
        "significant": false
      },
      "desc": "Does this genotype impair survival? (deleterious vs neutral), adult/aging-curated"
    },
    "binary_random": {
      "model_under_test": {
        "geno_pheno": 0.775,
        "pheno_only": 0.7417,
        "delta_recall": 0.0333,
        "delta_recall_ci95": [
          -0.0417,
          0.1083
        ],
        "mcnemar_p": 0.54126,
        "significant": false
      },
      "desc": "Same task, unstratified random baseline (control: shows curation exposes the effect)"
    },
    "pairwise_extension": {
      "model_under_test": {
        "geno_pheno": 0.8846,
        "pheno_only": 0.8462,
        "delta_recall": 0.0385,
        "delta_recall_ci95": [
          -0.0385,
          0.1154
        ],
        "mcnemar_p": 0.625,
        "significant": false
      },
      "desc": "Which strain's mutation extends lifespan? (forced choice, chance 0.50)"
    },
    "ternary": {
      "Longevity-LLM": {
        "geno_pheno": {
          "n": 150,
          "accuracy": 0.6,
          "macro_f1": 0.5084,
          "parse_fail": 0,
          "per_class_recall": {
            "shortens": {
              "correct": 46,
              "n": 50,
              "recall": 0.92
            },
            "no_effect": {
              "correct": 41,
              "n": 50,
              "recall": 0.82
            },
            "extends": {
              "correct": 3,
              "n": 50,
              "recall": 0.06
            }
          },
          "confusion": {
            "shortens->shortens": 46,
            "shortens->no_effect": 4,
            "no_effect->no_effect": 41,
            "no_effect->shortens": 8,
            "no_effect->extends": 1,
            "extends->no_effect": 27,
            "extends->shortens": 20,
            "extends->extends": 3
          }
        },
        "pheno_only": {
          "n": 150,
          "accuracy": 0.62,
          "macro_f1": 0.6015,
          "parse_fail": 0,
          "per_class_recall": {
            "shortens": {
              "correct": 46,
              "n": 50,
              "recall": 0.92
            },
            "no_effect": {
              "correct": 30,
              "n": 50,
              "recall": 0.6
            },
            "extends": {
              "correct": 17,
              "n": 50,
              "recall": 0.34
            }
          },
          "confusion": {
            "shortens->no_effect": 4,
            "shortens->shortens": 46,
            "no_effect->no_effect": 30,
            "no_effect->shortens": 18,
            "no_effect->extends": 2,
            "extends->no_effect": 9,
            "extends->shortens": 24,
            "extends->extends": 17
          }
        }
      },
      "Claude-Sonnet-4.6": {
        "geno_pheno": {
          "n": 150,
          "accuracy": 0.6667,
          "macro_f1": 0.6532,
          "parse_fail": 0,
          "per_class_recall": {
            "shortens": {
              "correct": 48,
              "n": 50,
              "recall": 0.96
            },
            "no_effect": {
              "correct": 35,
              "n": 50,
              "recall": 0.7
            },
            "extends": {
              "correct": 17,
              "n": 50,
              "recall": 0.34
            }
          },
          "confusion": {
            "shortens->shortens": 48,
            "shortens->extends": 1,
            "shortens->no_effect": 1,
            "no_effect->no_effect": 35,
            "no_effect->shortens": 12,
            "no_effect->extends": 3,
            "extends->extends": 17,
            "extends->shortens": 32,
            "extends->no_effect": 1
          }
        },
        "pheno_only": {
          "n": 150,
          "accuracy": 0.58,
          "macro_f1": 0.56,
          "parse_fail": 0,
          "per_class_recall": {
            "shortens": {
              "correct": 47,
              "n": 50,
              "recall": 0.94
            },
            "no_effect": {
              "correct": 20,
              "n": 50,
              "recall": 0.4
            },
            "extends": {
              "correct": 20,
              "n": 50,
              "recall": 0.4
            }
          },
          "confusion": {
            "shortens->shortens": 47,
            "shortens->extends": 3,
            "no_effect->extends": 8,
            "no_effect->no_effect": 20,
            "no_effect->shortens": 22,
            "extends->shortens": 25,
            "extends->no_effect": 5,
            "extends->extends": 20
          }
        }
      }
    }
  },
  "single_gene_epistasis": {
    "task": "LB-0138 survival binary, CONTROLLED, single-gene only (epistasis-controlled)",
    "models": {
      "Longevity-LLM": {
        "label": "Longevity-LLM (3-run majority vote)",
        "n_pairs": 120,
        "geno_pheno": {
          "acc": 0.708,
          "n": 120
        },
        "pheno_only": {
          "acc": 0.692,
          "n": 120
        },
        "delta_recall": 0.017,
        "delta_recall_ci95": [
          -0.075,
          0.108
        ],
        "mcnemar": {
          "b": 16,
          "c": 14,
          "p": 0.8555
        },
        "per_run": [
          {
            "run": 1,
            "geno_pheno": 0.708,
            "pheno_only": 0.683,
            "delta": 0.025
          },
          {
            "run": 2,
            "geno_pheno": 0.683,
            "pheno_only": 0.7,
            "delta": -0.017
          },
          {
            "run": 3,
            "geno_pheno": 0.725,
            "pheno_only": 0.692,
            "delta": 0.033
          }
        ],
        "n_runs": 3
      },
      "Claude Sonnet 4.6": {
        "label": "Claude Sonnet 4.6 (single run)",
        "n_pairs": 120,
        "geno_pheno": {
          "acc": 0.75,
          "n": 120
        },
        "pheno_only": {
          "acc": 0.7,
          "n": 120
        },
        "delta_recall": 0.05,
        "delta_recall_ci95": [
          -0.033,
          0.125
        ],
        "mcnemar": {
          "b": 15,
          "c": 9,
          "p": 0.3075
        }
      }
    },
    "baseline_multigene_controlled": {
      "Longevity-LLM": {
        "geno_pheno": 0.775,
        "pheno_only": 0.675,
        "delta_recall": 0.1,
        "delta_ci95": [
          0.025,
          0.175
        ],
        "mcnemar_p": 0.017
      },
      "Claude Sonnet 4.6": {
        "geno_pheno": 0.817,
        "pheno_only": 0.733,
        "delta_recall": 0.083,
        "delta_ci95": [
          -0.008,
          0.175
        ],
        "mcnemar_p": 0.099
      }
    },
    "comparison_delta_recall": [
      {
        "model": "Longevity-LLM",
        "delta_singlegene": 0.017,
        "delta_multigene": 0.1,
        "shift": -0.083
      },
      {
        "model": "Claude Sonnet 4.6",
        "delta_singlegene": 0.05,
        "delta_multigene": 0.083,
        "shift": -0.033
      }
    ]
  },
  "contamination_probe": {
    "longevity_llm": {
      "backend": "longevity",
      "model": "longevity-llm",
      "base_url": "https://swchnq0ekc3scmqw.us-east-2.aws.endpoints.huggingface.cloud/v1",
      "seed": 1234,
      "n_per_group": 60,
      "famous_accuracy": 0.6333333333333333,
      "famous_n": 60,
      "obscure_accuracy": 0.55,
      "obscure_n": 60,
      "recall_gap": 0.08333333333333326,
      "gap_95ci": [
        -0.09999999999999998,
        0.25
      ],
      "famous_yes_subset_acc": 0.6666666666666666,
      "famous_yes_n": 30,
      "obscure_yes_subset_acc": 0.1,
      "obscure_yes_n": 30,
      "pred_distribution": {
        "A": 35,
        "B": 85
      },
      "parse_failures": 0
    },
    "claude": {
      "backend": "claude",
      "model": "claude-sonnet-4-6",
      "base_url": "https://swchnq0ekc3scmqw.us-east-2.aws.endpoints.huggingface.cloud/v1",
      "seed": 1234,
      "n_per_group": 60,
      "famous_accuracy": 0.7333333333333333,
      "famous_n": 60,
      "obscure_accuracy": 0.65,
      "obscure_n": 60,
      "recall_gap": 0.08333333333333326,
      "gap_95ci": [
        -0.08333333333333337,
        0.25
      ],
      "famous_yes_subset_acc": 0.8333333333333334,
      "famous_yes_n": 30,
      "obscure_yes_subset_acc": 0.3333333333333333,
      "obscure_yes_n": 30,
      "pred_distribution": {
        "A": 47,
        "B": 73
      },
      "parse_failures": 0
    },
    "desc": "gene-name-only; famous (GenAge) vs obscure; impairs-YES recall is the decisive cell"
  },
  "reliability": {
    "parse_audit": {
      "longevity": {
        "n": 60,
        "api_errors": 0,
        "path_counts": {
          "leading": 57,
          "explicit": 3
        },
        "explicit_rate": 0.05,
        "fallback_rate": 0.0,
        "none_rate": 0.0,
        "answer_keyword_rate": 0.05,
        "fallback_disagreements": 0
      },
      "claude": {
        "n": 60,
        "api_errors": 0,
        "path_counts": {
          "explicit": 60
        },
        "explicit_rate": 1.0,
        "fallback_rate": 0.0,
        "none_rate": 0.0,
        "answer_keyword_rate": 1.0,
        "fallback_disagreements": 0
      }
    },
    "note": "100% of responses parsed; the risky fallback fired 0% \u2014 errors are task failures, not format."
  },
  "caveats": [
    "n=120/condition \u2192 wide CIs; underpowered for the smaller effects (Claude \u0394_recall, model gaps).",
    "Endpoint non-deterministic at temp=0 (~11% per-item flip) \u2192 binary/pairwise use 3-run averaging/majority-vote.",
    "Claude single-gene + random/pairwise = single run (Claude steadier than the vLLM endpoint).",
    "Genetic background is an irreducible confound (24,224 distinct strings \u2192 no matched controls)."
  ],
  "methods": [
    "Miller 2024 (arXiv:2411.00640) SEM/CI",
    "Dietterich 1998 McNemar",
    "Berg-Kirkpatrick 2012 paired bootstrap",
    "Card 2020 power"
  ],
  "figures": [
    "results/figures/delta_recall_forest.svg",
    "results/figures/accuracy_bars.svg",
    "results/figures/mcnemar_tables.svg"
  ]
} as const;

export const demoData = {
  "note": "Pre-computed trace-scorer demo (no live API). Longevity-LLM ternary; scores from judge/score_trace.py --no-api.",
  "examples": [
    {
      "id": 0,
      "genotype_id": "MGI:5544115",
      "genes": [
        "Apc",
        "Cd44"
      ],
      "condition": "geno_pheno",
      "story": "Life-extension blind-spot: a longevity mutation the model misreads as harmful/neutral.",
      "prompt": "A laboratory mouse strain carries the following mutation:\n\nGene(s): Apc, Cd44\nAllelic composition: Apc<Min>/Apc<+>,Cd44<tm1Mak>/Cd44<tm1Mak>\nZygosity: multi-locus\n\nRecorded phenotype profile (excluding any lifespan/mortality findings):\n- increased enterocyte apoptosis\n- decreased intestinal adenoma incidence\n\nQuestion: What is this genotype's most likely effect on lifespan?\n\nOptions: A. Shortens lifespan (premature death / reduced survival)  B. No clear effect on lifespan  C. Extends lifespan (promotes longevity / slows aging)\n\nReason briefly, then on the FINAL line output exactly: Answer: <letter>",
      "gold": "C",
      "gold_label": "Extends",
      "pred": "B",
      "pred_label": "No effect",
      "correct": false,
      "trace": "The mouse carries a heterozygous Apc<Min> mutation, which typically predisposes to intestinal adenomas and accelerates aging phenotypes through Wnt pathway dysregulation. However, the co-occurring Cd44<tm1Mak>/Cd44<tm1Mak> homozygous mutation introduces a critical counterbalance. Cd44 encodes a hyaluronan receptor essential for cell adhesion and immune modulation; its deletion disrupts tumor microenvironment interactions and may suppress oncogenic signaling. The observed reduction in intestinal adenoma incidence suggests Cd44 loss mitigates Apc<Min>-driven tumorigenesis, likely by impairing tumor cell survival or proliferation. While Apc<Min> alone shortens lifespan via cancer risk, the Cd44 knockout appears to override this effect, aligning with the \"decreased adenoma incidence\" phenotype. This interaction implies a shift toward tumor suppression, potentially extending lifespan. However, Cd44's role in immune regulation and tissue repair could introduce trade-offs, such as chronic inflammation or impaired wound healing, which might offset longevity gains. The decisive factor is the direct suppression of adenomas, a major driver of mortality in Apc<Min> models, suggesting a net lifespan extension.\n</think>\nB",
      "trace_score": 0.25,
      "sub_scores": {
        "trace_score": 0.25,
        "sub_scores": {
          "gene_hallucination": {
            "score": 0.0,
            "mentioned_genes": [
              "Apc",
              "Min",
              "Wnt",
              "Cd44"
            ],
            "real_genes": [],
            "hallucinated_genes": [
              "Min",
              "Wnt"
            ],
            "famous_genes_cited": [],
            "n_checked": 2
          },
          "think_answer_consistency": {
            "score": 0.0,
            "contradicts": true,
            "reason": "answer=no_effect but trace argues impairs survival",
            "trace_says_impairs": true,
            "trace_says_no_effect": false,
            "final_answer": "B"
          },
          "system_grounding": {
            "score": 1.0,
            "claimed_systems": [
              "digestive/alimentary",
              "immune system"
            ],
            "verified": [],
            "unverified": [],
            "n_checked": 0
          }
        },
        "weights_used": {
          "gene_hallucination": 0.4,
          "think_answer_consistency": 0.35,
          "system_grounding": 0.25
        },
        "item_index": 0,
        "item_id": "item-0"
      }
    },
    {
      "id": 1,
      "genotype_id": "MGI:5499846",
      "genes": [
        "Mecp2",
        "Sum2"
      ],
      "condition": "geno_pheno",
      "story": "Life-extension blind-spot: a longevity mutation the model misreads as harmful/neutral.",
      "prompt": "A laboratory mouse strain carries the following mutation:\n\nGene(s): Mecp2, Sum2\nAllelic composition: Mecp2<tm1.1Bird>/Y,Sum2<M1Jus>/Sum2<+>\nZygosity: multi-locus\n\nRecorded phenotype profile (excluding any lifespan/mortality findings):\n- tremors\n- dermatitis\n- abnormal body weight\n- limb grasping\n- eye inflammation\n- lethargy\n\nQuestion: What is this genotype's most likely effect on lifespan?\n\nOptions: A. Shortens lifespan (premature death / reduced survival)  B. No clear effect on lifespan  C. Extends lifespan (promotes longevity / slows aging)\n\nReason briefly, then on the FINAL line output exactly: Answer: <letter>",
      "gold": "C",
      "gold_label": "Extends",
      "pred": "A",
      "pred_label": "Shortens",
      "correct": false,
      "trace": "The mouse carries a Y-linked Mecp2<tm1.1Bird> mutation, which is a well-characterized model of Rett syndrome, a neurodevelopmental disorder caused by loss of MECP2 function. MECP2 is critical for neuronal stability, and its absence leads to progressive neurodegeneration, seizures, and early mortality in humans. The Sum2<+> allele (ubiquitin-conjugating enzyme) is likely a wild-type background, with no compensatory effects on MECP2 function. The observed phenotypes\u2014tremors, lethargy, and abnormal body weight\u2014align with Rett syndrome\u2019s neurological and metabolic dysregulation. While the mouse strain\u2019s sex (Y chromosome) suggests male, MECP2 haploinsufficiency in males is lethal in early development, but this strain survives to exhibit age-related phenotypes, indicating partial MECP2 activity or compensatory mechanisms. However, the presence of tremors and lethargy suggests ongoing neurodegeneration, which would accelerate aging. The lack of clear compensatory alleles (e.g., Sum2<+> does not rescue MECP2 loss) and the severity of Rett-like symptoms point to a shortened lifespan. The most decisive evidence is the MECP2 mutation\u2019s direct link to premature mortality in Rett syndrome models.\n</think>\nA",
      "trace_score": 0.6,
      "sub_scores": {
        "trace_score": 0.6,
        "sub_scores": {
          "gene_hallucination": {
            "score": 0.0,
            "mentioned_genes": [
              "Mecp2",
              "Rett",
              "MECP2",
              "Sum2"
            ],
            "real_genes": [],
            "hallucinated_genes": [
              "Rett"
            ],
            "famous_genes_cited": [],
            "n_checked": 1
          },
          "think_answer_consistency": {
            "score": 1.0,
            "contradicts": false,
            "reason": "consistent",
            "trace_says_impairs": true,
            "trace_says_no_effect": false,
            "final_answer": "A"
          },
          "system_grounding": {
            "score": 1.0,
            "claimed_systems": [],
            "verified": [],
            "unverified": [],
            "n_checked": 0
          }
        },
        "weights_used": {
          "gene_hallucination": 0.4,
          "think_answer_consistency": 0.35,
          "system_grounding": 0.25
        },
        "item_index": 1,
        "item_id": "item-1"
      }
    },
    {
      "id": 2,
      "genotype_id": "MGI:5314644",
      "genes": [
        "Ptpn6"
      ],
      "condition": "geno_pheno",
      "story": "Correct: identifies a lethal/deleterious mutation.",
      "prompt": "A laboratory mouse strain carries the following mutation:\n\nGene(s): Ptpn6\nAllelic composition: Ptpn6<me>/Ptpn6<me>\nZygosity: homozygote\n\nRecorded phenotype profile (excluding any lifespan/mortality findings):\n- decreased limb number\n- abnormal skin condition\n- decreased body weight\n- increased IgM level\n- increased autoantibody level\n- increased splenocyte proliferation\n\nQuestion: What is this genotype's most likely effect on lifespan?\n\nOptions: A. Shortens lifespan (premature death / reduced survival)  B. No clear effect on lifespan  C. Extends lifespan (promotes longevity / slows aging)\n\nReason briefly, then on the FINAL line output exactly: Answer: <letter>",
      "gold": "A",
      "gold_label": "Shortens",
      "pred": "A",
      "pred_label": "Shortens",
      "correct": true,
      "trace": "The Ptpn6 gene encodes a tyrosine phosphatase that negatively regulates immune signaling pathways, including those activated by cytokines like IL-6 and TNF-\u03b1. Its protein product interacts with key signaling molecules such as JAK1, JAK3, and STAT proteins, which are central to inflammatory and immune responses. The homozygous mutation in this gene likely disrupts these regulatory interactions, leading to hyperactivation of downstream signaling cascades. The observed phenotypes\u2014increased autoantibody levels, elevated IgM, and enhanced splenocyte proliferation\u2014strongly suggest a chronic inflammatory state driven by dysregulated immune signaling. Chronic inflammation (inflammaging) is a well-established hallmark of aging that accelerates tissue dysfunction and disease susceptibility. The combination of autoimmune features and immune hyperactivation in this mouse model aligns with a pro-aging phenotype, where persistent immune stimulation contributes to systemic damage and organ dysfunction. Given the direct link between immune dysregulation and age-related pathologies, the most plausible outcome is a shortened lifespan due to premature immune-mediated tissue damage and systemic inflammation.\n</think>\nA",
      "trace_score": 0.6,
      "sub_scores": {
        "trace_score": 0.6,
        "sub_scores": {
          "gene_hallucination": {
            "score": 0.0,
            "mentioned_genes": [
              "Ptpn6",
              "IL",
              "JAK1",
              "JAK3",
              "IgM",
              "Chronic"
            ],
            "real_genes": [],
            "hallucinated_genes": [
              "IL",
              "JAK1",
              "JAK3",
              "IgM",
              "Chronic"
            ],
            "famous_genes_cited": [],
            "n_checked": 5
          },
          "think_answer_consistency": {
            "score": 1.0,
            "contradicts": false,
            "reason": "consistent",
            "trace_says_impairs": false,
            "trace_says_no_effect": false,
            "final_answer": "A"
          },
          "system_grounding": {
            "score": 1.0,
            "claimed_systems": [],
            "verified": [],
            "unverified": [],
            "n_checked": 0
          }
        },
        "weights_used": {
          "gene_hallucination": 0.4,
          "think_answer_consistency": 0.35,
          "system_grounding": 0.25
        },
        "item_index": 2,
        "item_id": "item-2"
      }
    },
    {
      "id": 3,
      "genotype_id": "MGI:3697164",
      "genes": [
        "Vss"
      ],
      "condition": "geno_pheno",
      "story": "Correct: identifies a no-effect mutation (uses the neutral option).",
      "prompt": "A laboratory mouse strain carries the following mutation:\n\nGene(s): Vss\nAllelic composition: Vss/Vss<+>\nZygosity: heterozygote\n\nRecorded phenotype profile (excluding any lifespan/mortality findings):\n- belly spot\n- decreased body size\n\nQuestion: What is this genotype's most likely effect on lifespan?\n\nOptions: A. Shortens lifespan (premature death / reduced survival)  B. No clear effect on lifespan  C. Extends lifespan (promotes longevity / slows aging)\n\nReason briefly, then on the FINAL line output exactly: Answer: <letter>",
      "gold": "B",
      "gold_label": "No effect",
      "pred": "B",
      "pred_label": "No effect",
      "correct": true,
      "trace": "The gene Vss is associated with the VSS protein, which is linked to the Wnt signaling pathway, a critical regulator of development and tissue homeostasis. The Wnt pathway interacts with key aging-related processes such as stem cell maintenance, cellular senescence, and inflammation. While Vss itself is not a well-characterized gene in aging studies, its potential role in Wnt signaling suggests indirect effects on aging. The heterozygous mutation (Vss/Vss<+>) may partially disrupt Wnt pathway activity, which could influence tissue regeneration and cellular senescence. However, the absence of clear evidence linking Vss to longevity or age-related diseases, combined with the lack of dominant-negative effects in heterozygotes, implies a limited impact on lifespan. The observed phenotypes (belly spot, decreased body size) are developmental or morphological traits rather than systemic aging markers. Given the limited functional characterization of Vss and its uncertain role in aging pathways, the most parsimonious conclusion is that this mutation has no clear effect on lifespan.\n</think>\nB",
      "trace_score": 0.6,
      "sub_scores": {
        "trace_score": 0.6,
        "sub_scores": {
          "gene_hallucination": {
            "score": 0.0,
            "mentioned_genes": [
              "Vss",
              "VSS",
              "Wnt"
            ],
            "real_genes": [],
            "hallucinated_genes": [
              "Wnt"
            ],
            "famous_genes_cited": [],
            "n_checked": 1
          },
          "think_answer_consistency": {
            "score": 1.0,
            "contradicts": false,
            "reason": "consistent",
            "trace_says_impairs": false,
            "trace_says_no_effect": false,
            "final_answer": "B"
          },
          "system_grounding": {
            "score": 1.0,
            "claimed_systems": [],
            "verified": [],
            "unverified": [],
            "n_checked": 0
          }
        },
        "weights_used": {
          "gene_hallucination": 0.4,
          "think_answer_consistency": 0.35,
          "system_grounding": 0.25
        },
        "item_index": 3,
        "item_id": "item-3"
      }
    },
    {
      "id": 4,
      "genotype_id": "MGI:5544115",
      "genes": [
        "Apc",
        "Cd44"
      ],
      "condition": "pheno_only",
      "story": "Ablation: same genotype with the gene name HIDDEN (reasoning vs recall).",
      "prompt": "A laboratory mouse strain carries mutations at multiple loci in an undisclosed gene.\n\nRecorded phenotype profile (excluding any lifespan/mortality findings):\n- increased enterocyte apoptosis\n- decreased intestinal adenoma incidence\n\nQuestion: What is this genotype's most likely effect on lifespan?\n\nOptions: A. Shortens lifespan (premature death / reduced survival)  B. No clear effect on lifespan  C. Extends lifespan (promotes longevity / slows aging)\n\nReason briefly, then on the FINAL line output exactly: Answer: <letter>",
      "gold": "C",
      "gold_label": "Extends",
      "pred": "B",
      "pred_label": "No effect",
      "correct": false,
      "trace": "The mouse strain exhibits increased enterocyte apoptosis and reduced intestinal adenoma incidence, suggesting a complex interplay between tissue homeostasis and cancer suppression. The heightened apoptosis in intestinal epithelial cells indicates a potential compensatory mechanism to eliminate damaged or dysplastic cells, which could mitigate tumor formation. This aligns with the observed decrease in adenoma incidence, a hallmark of aging-related neoplastic progression. However, excessive apoptosis in regenerative tissues like the intestine may impair tissue renewal, leading to functional decline and systemic effects. The balance between these opposing forces\u2014cancer suppression versus tissue degeneration\u2014depends on the extent of apoptosis and its downstream consequences. In aging biology, chronic inflammation and stem cell exhaustion are key drivers of tissue dysfunction. If the increased apoptosis reflects a heightened immune surveillance or DNA damage response, it might counteract age-related clonal expansion of mutated cells, thereby delaying cancer onset. Conversely, persistent apoptosis could deplete stem cell pools, accelerating organ failure. The absence of other aging-related phenotypes (e.g., frailty, metabolic dysregulation) suggests the primary impact is localized to the intestine. Given the trade-off between tumor suppression and tissue maintenance, the most decisive factor is the potential for apoptosis to drive stem cell exhaustion, a primary hallmark of aging. This would likely outweigh the benefit of reduced adenoma incidence, tipping the balance toward accelerated aging.\n</think>\nB",
      "trace_score": 0.6,
      "sub_scores": {
        "trace_score": 0.6,
        "sub_scores": {
          "gene_hallucination": {
            "score": 0.0,
            "mentioned_genes": [
              "In",
              "If"
            ],
            "real_genes": [],
            "hallucinated_genes": [
              "In",
              "If"
            ],
            "famous_genes_cited": [],
            "n_checked": 2
          },
          "think_answer_consistency": {
            "score": 1.0,
            "contradicts": false,
            "reason": "consistent",
            "trace_says_impairs": false,
            "trace_says_no_effect": false,
            "final_answer": "B"
          },
          "system_grounding": {
            "score": 1.0,
            "claimed_systems": [],
            "verified": [],
            "unverified": [],
            "n_checked": 0
          }
        },
        "weights_used": {
          "gene_hallucination": 0.4,
          "think_answer_consistency": 0.35,
          "system_grounding": 0.25
        },
        "item_index": 4,
        "item_id": "item-4"
      }
    }
  ]
} as const;
