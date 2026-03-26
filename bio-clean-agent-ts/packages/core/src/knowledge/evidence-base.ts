/**
 * Evidence-based recommendations for data cleaning decisions.
 *
 * Provides scientifically-grounded guidance for:
 * - Missing data handling
 * - Outlier detection and treatment
 * - Duplicate record resolution
 * - Data transformation strategies
 * - Study design considerations
 */

import {
  ConfidenceLevel,
  CONFIDENCE_ORDER,
  EVIDENCE_ORDER,
  EvidenceLevel,
  KnowledgeBase,
  KnowledgeEntry,
  createEntry,
} from "./base.js";

// ============================================================
// RETURN / PARAMETER TYPES
// ============================================================

/**
 * Additional context supplied to {@link EvidenceBase.getCleaningRecommendation}.
 * Keys correspond to conditions and contraindications stored on knowledge entries.
 */
export type CleaningContext = Record<string, unknown>;

// ============================================================
// CLASS
// ============================================================

/**
 * Evidence-based recommendations for common data cleaning scenarios.
 *
 * Organises peer-reviewed guidance into five sections:
 * 1. Missing Data Strategies
 * 2. Outlier Detection and Treatment
 * 3. Duplicate Records
 * 4. Data Transformation
 * 5. Study Design Considerations
 */
export class EvidenceBase extends KnowledgeBase {
  /**
   * Populate the knowledge base with all evidence entries.
   */
  protected buildKnowledgeBase(): void {
    this.buildMissingDataStrategies();
    this.buildOutlierStrategies();
    this.buildDuplicateStrategies();
    this.buildTransformationStrategies();
    this.buildStudyDesignGuidelines();
  }

  // ----------------------------------------------------------
  // Section 1: Missing Data Strategies
  // ----------------------------------------------------------

  private buildMissingDataStrategies(): void {
    this.addEntry(
      createEntry({
        id: "missing_complete_case_analysis",
        category: "missing_data",
        topic: "complete_case_analysis",
        statement:
          "Complete case analysis (listwise deletion) is valid when data is Missing Completely " +
          "At Random (MCAR) and missingness is <5%",
        rationale:
          "Minimal bias when MCAR assumption holds. Loss of power acceptable with low missingness. " +
          "Simple to implement.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Little & Rubin",
            title: "Statistical Analysis with Missing Data, 3rd Ed",
            year: 2019,
          },
          {
            source: "Schafer & Graham",
            title: "Missing Data: Our View of the State of the Art",
            year: 2002,
            doi: "10.1037/1082-989X.7.2.147",
          },
        ],
        conditions: ["missing_rate < 0.05", "mcar_assumption"],
        tags: ["missing_data", "deletion", "statistical_method"],
      })
    );

    this.addEntry(
      createEntry({
        id: "missing_mean_imputation_caution",
        category: "missing_data",
        topic: "mean_imputation_problems",
        statement:
          "Simple mean imputation reduces variance and distorts correlations; use only for preliminary analysis",
        rationale:
          "Mean imputation creates artificial precision by reducing variance. Underestimates standard errors. " +
          "More sophisticated methods (MI, ML) preferred for inference.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Donders et al.",
            title: "Review: A gentle introduction to imputation of missing values",
            year: 2006,
            doi: "10.1016/j.jclinepi.2006.01.014",
          },
        ],
        contraindications: ["inferential_statistics", "final_analysis"],
        tags: ["missing_data", "imputation", "caution"],
      })
    );

    this.addEntry(
      createEntry({
        id: "missing_median_imputation_robust",
        category: "missing_data",
        topic: "median_imputation",
        statement:
          "Median imputation is more robust to outliers than mean imputation for skewed distributions",
        rationale:
          "Median less affected by extreme values. Appropriate for skewed continuous variables. " +
          "Still reduces variance but more resistant to outliers.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "Barnard & Meng",
            title: "Applications of multiple imputation in medical studies",
            year: 1999,
          },
        ],
        conditions: ["skewed_distribution", "descriptive_analysis"],
        tags: ["missing_data", "imputation", "robust_method"],
      })
    );

    this.addEntry(
      createEntry({
        id: "missing_multiple_imputation",
        category: "missing_data",
        topic: "multiple_imputation",
        statement:
          "Multiple Imputation (MI) is the gold standard for missing data when missingness is MAR",
        rationale:
          "MI accounts for uncertainty in imputed values. Provides valid inference under MAR assumption. " +
          "Widely accepted in medical research.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Rubin, D.B.",
            title: "Multiple Imputation for Nonresponse in Surveys",
            year: 1987,
          },
          {
            source: "Sterne et al.",
            title:
              "Multiple imputation for missing data in epidemiological and clinical research",
            year: 2009,
            doi: "10.1136/bmj.b2393",
          },
        ],
        conditions: ["inferential_statistics", "mar_assumption"],
        tags: ["missing_data", "imputation", "gold_standard"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 2: Outlier Detection and Treatment
  // ----------------------------------------------------------

  private buildOutlierStrategies(): void {
    this.addEntry(
      createEntry({
        id: "outlier_biological_plausibility",
        category: "outliers",
        topic: "biological_plausibility_check",
        statement:
          "In medical data, check biological plausibility before statistical outlier methods",
        rationale:
          "Clinically impossible values (e.g., BP 300/200) are data errors. Clinically rare but possible " +
          "values (e.g., height 210 cm) may be true outliers. Domain knowledge trumps statistics.",
        evidenceLevel: EvidenceLevel.EXPERT_OPINION,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "van der Loo & de Jonge",
            title: "Statistical Data Cleaning with Applications in R",
            year: 2018,
          },
        ],
        tags: ["outliers", "validation", "medical_data"],
      })
    );

    this.addEntry(
      createEntry({
        id: "outlier_iqr_method",
        category: "outliers",
        topic: "iqr_outlier_detection",
        statement:
          "IQR method (Q1-1.5*IQR, Q3+1.5*IQR) is robust for outlier detection in skewed data",
        rationale:
          "Non-parametric method resistant to outliers themselves. Tukey's fences widely used. " +
          "Less sensitive than z-score to distributional assumptions.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Tukey, J.W.",
            title: "Exploratory Data Analysis",
            year: 1977,
          },
        ],
        conditions: ["no_normal_assumption"],
        tags: ["outliers", "iqr", "robust_method"],
      })
    );

    this.addEntry(
      createEntry({
        id: "outlier_winsorization",
        category: "outliers",
        topic: "winsorization",
        statement:
          "Winsorization (capping at percentiles) preserves sample size while reducing outlier influence",
        rationale:
          "Cap extreme values at 1st/99th or 5th/95th percentile. Maintains ranking. Less information " +
          "loss than deletion. Common in financial and medical data.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "Wilcox, R.R.",
            title: "Introduction to Robust Estimation and Hypothesis Testing",
            year: 2012,
          },
        ],
        tags: ["outliers", "winsorization", "robust_method"],
      })
    );

    this.addEntry(
      createEntry({
        id: "outlier_deletion_caution",
        category: "outliers",
        topic: "outlier_deletion_considerations",
        statement:
          "Delete outliers only if data entry error confirmed or biologically impossible; " +
          "otherwise flag for sensitivity analysis",
        rationale:
          "Deletion reduces sample size and may introduce bias. True extreme values contain information. " +
          "Better to flag and conduct sensitivity analysis.",
        evidenceLevel: EvidenceLevel.EXPERT_OPINION,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Aguinis et al.",
            title:
              "Best-Practice Recommendations for Defining, Identifying, and Handling Outliers",
            year: 2013,
            doi: "10.1177/1094428112470848",
          },
        ],
        tags: ["outliers", "deletion", "best_practice"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 3: Duplicate Records
  // ----------------------------------------------------------

  private buildDuplicateStrategies(): void {
    this.addEntry(
      createEntry({
        id: "duplicate_exact_matches",
        category: "duplicates",
        topic: "exact_duplicate_handling",
        statement:
          "Exact duplicates (identical across all fields) should be removed, keeping first occurrence",
        rationale:
          "Perfect duplicates provide no additional information and may indicate database errors " +
          "or repeated data entry.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "FDA",
            title: "Data Integrity and Compliance With Drug CGMP",
            year: 2018,
            url: "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/data-integrity-and-compliance-drug-cgmp",
          },
        ],
        tags: ["duplicates", "data_quality"],
      })
    );

    this.addEntry(
      createEntry({
        id: "duplicate_partial_matches",
        category: "duplicates",
        topic: "partial_duplicate_handling",
        statement:
          "Partial duplicates (same key fields, different data) require manual review or merge logic",
        rationale:
          "May represent legitimate repeated measures, data corrections, or errors. " +
          "Cannot automatically delete without understanding context.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "Christen, P.",
            title: "Data Matching: Concepts and Techniques for Record Linkage",
            year: 2012,
          },
        ],
        conditions: ["manual_review_available"],
        tags: ["duplicates", "data_linkage", "manual_review"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 4: Data Transformation Strategies
  // ----------------------------------------------------------

  private buildTransformationStrategies(): void {
    this.addEntry(
      createEntry({
        id: "transform_log_skewed",
        category: "transformation",
        topic: "log_transformation_skewed_data",
        statement:
          "Log transformation can normalize right-skewed continuous data with positive values",
        rationale:
          "Reduces positive skewness. Appropriate for multiplicative processes (e.g., concentrations). " +
          "Cannot handle zero or negative values.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Osborne, J.",
            title: "Improving your data transformations",
            year: 2002,
          },
        ],
        conditions: ["positive_values", "right_skewed"],
        contraindications: ["zero_values", "negative_values"],
        tags: ["transformation", "normalization", "skewness"],
      })
    );

    this.addEntry(
      createEntry({
        id: "transform_standardization",
        category: "transformation",
        topic: "standardization_z_scores",
        statement:
          "Standardization (z-scores) enables comparison across variables with different units",
        rationale:
          "Centers at mean=0, scales to SD=1. Preserves relationships. Useful for combining variables " +
          "or comparing effect sizes.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Cohen, J.",
            title: "Statistical Power Analysis for the Behavioral Sciences",
            year: 1988,
          },
        ],
        tags: ["transformation", "standardization", "statistical_method"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 5: Study Design Considerations
  // ----------------------------------------------------------

  private buildStudyDesignGuidelines(): void {
    this.addEntry(
      createEntry({
        id: "sample_size_guideline",
        category: "study_design",
        topic: "minimum_sample_size",
        statement:
          "Minimum sample size of 30 per group often cited for parametric tests, but depends on " +
          "effect size and variability",
        rationale:
          "Central Limit Theorem approximation. Larger samples needed for small effects or high variability. " +
          "Non-parametric alternatives for small samples.",
        evidenceLevel: EvidenceLevel.EXPERT_OPINION,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "Maxwell & Delaney",
            title: "Designing Experiments and Analyzing Data",
            year: 2017,
          },
        ],
        tags: ["study_design", "sample_size", "statistics"],
      })
    );
  }

  // ----------------------------------------------------------
  // Domain-Specific Methods
  // ----------------------------------------------------------

  /**
   * Get the most applicable evidence-based recommendation for a data cleaning situation.
   *
   * The method:
   * 1. Searches by `situation` (mapped to `category`) with at least MEDIUM confidence.
   * 2. Filters candidates whose `conditions` are all satisfied and whose
   *    `contraindications` are all absent in `context`.
   * 3. Falls back to all candidates when none pass the filter.
   * 4. Sorts by confidence then evidence strength, returning the top result.
   *
   * @param situation Type of situation, e.g. `"missing_data"`, `"outliers"`.
   * @param context   Optional key-value context where truthy values signal presence.
   * @returns The best-matching {@link KnowledgeEntry}, or `undefined` if none found.
   */
  getCleaningRecommendation(
    situation: string,
    context: CleaningContext = {}
  ): KnowledgeEntry | undefined {
    const candidates = this.search({
      category: situation,
      minConfidence: ConfidenceLevel.MEDIUM,
    });

    if (candidates.length === 0) {
      return undefined;
    }

    // Filter by conditions and contraindications
    let applicable: KnowledgeEntry[] = candidates.filter((entry) => {
      // All conditions must be truthy in context
      if (entry.conditions.length > 0) {
        const conditionsMet = entry.conditions.every((cond) =>
          Boolean(context[cond])
        );
        if (!conditionsMet) return false;
      }

      // No contraindication may be truthy in context
      if (entry.contraindications.length > 0) {
        const hasContraindication = entry.contraindications.some((contra) =>
          Boolean(context[contra])
        );
        if (hasContraindication) return false;
      }

      return true;
    });

    // Fall back to all candidates if nothing passed the filter
    if (applicable.length === 0) {
      applicable = candidates;
    }

    // Sort by confidence (primary) then evidence strength (secondary)
    applicable.sort((a, b) => {
      const confidenceDiff =
        CONFIDENCE_ORDER.indexOf(a.confidence) -
        CONFIDENCE_ORDER.indexOf(b.confidence);
      if (confidenceDiff !== 0) return confidenceDiff;

      return (
        EVIDENCE_ORDER.indexOf(a.evidenceLevel) -
        EVIDENCE_ORDER.indexOf(b.evidenceLevel)
      );
    });

    return applicable[0];
  }

  /**
   * Generate a human-readable explanation of a knowledge entry.
   *
   * @param entry           The {@link KnowledgeEntry} to explain.
   * @param includeCitations Whether to append the reference list (default `true`).
   * @returns Formatted plain-text / markdown-compatible explanation string.
   */
  explainRecommendation(
    entry: KnowledgeEntry,
    includeCitations = true
  ): string {
    const evidenceLabel = entry.evidenceLevel
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

    let explanation = `**Recommendation:** ${entry.statement}\n\n`;
    explanation += `**Rationale:** ${entry.rationale}\n\n`;
    explanation += `**Evidence Level:** ${evidenceLabel}\n`;
    explanation += `**Confidence:** ${entry.confidence.toUpperCase()}\n\n`;

    if (entry.conditions.length > 0) {
      explanation += "**Applicable when:**\n";
      for (const cond of entry.conditions) {
        explanation += `  - ${cond}\n`;
      }
      explanation += "\n";
    }

    if (entry.contraindications.length > 0) {
      explanation += "**Do NOT use when:**\n";
      for (const contra of entry.contraindications) {
        explanation += `  - ${contra}\n`;
      }
      explanation += "\n";
    }

    if (includeCitations && entry.citations.length > 0) {
      explanation += "**References:**\n";
      for (const cite of entry.citations) {
        let citationText = `  - ${cite.source}`;
        if (cite.year !== undefined) {
          citationText += ` (${cite.year})`;
        }
        citationText += `: ${cite.title}`;
        if (cite.doi !== undefined) {
          citationText += `\n    DOI: ${cite.doi}`;
        }
        if (cite.url !== undefined) {
          citationText += `\n    URL: ${cite.url}`;
        }
        explanation += citationText + "\n";
      }
    }

    return explanation;
  }
}
