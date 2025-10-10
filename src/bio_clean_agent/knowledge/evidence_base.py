"""Evidence-based recommendations for data cleaning decisions."""

from typing import Any, Dict, List, Optional

from .base import (
    Citation,
    ConfidenceLevel,
    EvidenceLevel,
    KnowledgeBase,
    KnowledgeEntry,
)


class EvidenceBase(KnowledgeBase):
    """
    Evidence-based recommendations for common data cleaning scenarios.

    Provides scientifically-grounded guidance for:
    - Missing data handling
    - Outlier treatment
    - Duplicate resolution
    - Data transformation
    """

    def _build_knowledge_base(self) -> None:
        """Build evidence-based recommendations."""

        # ========================================
        # MISSING DATA STRATEGIES
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="missing_complete_case_analysis",
                category="missing_data",
                topic="complete_case_analysis",
                statement="Complete case analysis (listwise deletion) is valid when data is Missing Completely At Random (MCAR) and missingness is <5%",
                rationale="Minimal bias when MCAR assumption holds. Loss of power acceptable with low missingness. Simple to implement.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Little & Rubin",
                        title="Statistical Analysis with Missing Data, 3rd Ed",
                        year=2019,
                    ),
                    Citation(
                        source="Schafer & Graham",
                        title="Missing Data: Our View of the State of the Art",
                        year=2002,
                        doi="10.1037/1082-989X.7.2.147",
                    ),
                ],
                conditions=["missing_rate < 0.05", "mcar_assumption"],
                tags=["missing_data", "deletion", "statistical_method"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="missing_mean_imputation_caution",
                category="missing_data",
                topic="mean_imputation_problems",
                statement="Simple mean imputation reduces variance and distorts correlations; use only for preliminary analysis",
                rationale="Mean imputation creates artificial precision by reducing variance. Underestimates standard errors. More sophisticated methods (MI, ML) preferred for inference.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Donders et al.",
                        title="Review: A gentle introduction to imputation of missing values",
                        year=2006,
                        doi="10.1016/j.jclinepi.2006.01.014",
                    ),
                ],
                contraindications=["inferential_statistics", "final_analysis"],
                tags=["missing_data", "imputation", "caution"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="missing_median_imputation_robust",
                category="missing_data",
                topic="median_imputation",
                statement="Median imputation is more robust to outliers than mean imputation for skewed distributions",
                rationale="Median less affected by extreme values. Appropriate for skewed continuous variables. Still reduces variance but more resistant to outliers.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="Barnard & Meng",
                        title="Applications of multiple imputation in medical studies",
                        year=1999,
                    ),
                ],
                conditions=["skewed_distribution", "descriptive_analysis"],
                tags=["missing_data", "imputation", "robust_method"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="missing_multiple_imputation",
                category="missing_data",
                topic="multiple_imputation",
                statement="Multiple Imputation (MI) is the gold standard for missing data when missingness is MAR",
                rationale="MI accounts for uncertainty in imputed values. Provides valid inference under MAR assumption. Widely accepted in medical research.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Rubin, D.B.",
                        title="Multiple Imputation for Nonresponse in Surveys",
                        year=1987,
                    ),
                    Citation(
                        source="Sterne et al.",
                        title="Multiple imputation for missing data in epidemiological and clinical research",
                        year=2009,
                        doi="10.1136/bmj.b2393",
                    ),
                ],
                conditions=["inferential_statistics", "mar_assumption"],
                tags=["missing_data", "imputation", "gold_standard"],
            )
        )

        # ========================================
        # OUTLIER DETECTION AND TREATMENT
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="outlier_biological_plausibility",
                category="outliers",
                topic="biological_plausibility_check",
                statement="In medical data, check biological plausibility before statistical outlier methods",
                rationale="Clinically impossible values (e.g., BP 300/200) are data errors. Clinically rare but possible values (e.g., height 210cm) may be true outliers. Domain knowledge trumps statistics.",
                evidence_level=EvidenceLevel.EXPERT_OPINION,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="van der Loo & de Jonge",
                        title="Statistical Data Cleaning with Applications in R",
                        year=2018,
                    ),
                ],
                tags=["outliers", "validation", "medical_data"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="outlier_iqr_method",
                category="outliers",
                topic="iqr_outlier_detection",
                statement="IQR method (Q1-1.5*IQR, Q3+1.5*IQR) is robust for outlier detection in skewed data",
                rationale="Non-parametric method resistant to outliers themselves. Tukey's fences widely used. Less sensitive than z-score to distributional assumptions.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Tukey, J.W.",
                        title="Exploratory Data Analysis",
                        year=1977,
                    ),
                ],
                conditions=["no_normal_assumption"],
                tags=["outliers", "iqr", "robust_method"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="outlier_winsorization",
                category="outliers",
                topic="winsorization",
                statement="Winsorization (capping at percentiles) preserves sample size while reducing outlier influence",
                rationale="Cap extreme values at 1st/99th or 5th/95th percentile. Maintains ranking. Less information loss than deletion. Common in financial and medical data.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="Wilcox, R.R.",
                        title="Introduction to Robust Estimation and Hypothesis Testing",
                        year=2012,
                    ),
                ],
                tags=["outliers", "winsorization", "robust_method"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="outlier_deletion_caution",
                category="outliers",
                topic="outlier_deletion_considerations",
                statement="Delete outliers only if data entry error confirmed or biologically impossible; otherwise flag for sensitivity analysis",
                rationale="Deletion reduces sample size and may introduce bias. True extreme values contain information. Better to flag and conduct sensitivity analysis.",
                evidence_level=EvidenceLevel.EXPERT_OPINION,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Aguinis et al.",
                        title="Best-Practice Recommendations for Defining, Identifying, and Handling Outliers",
                        year=2013,
                        doi="10.1177/1094428112470848",
                    ),
                ],
                tags=["outliers", "deletion", "best_practice"],
            )
        )

        # ========================================
        # DUPLICATE RECORDS
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="duplicate_exact_matches",
                category="duplicates",
                topic="exact_duplicate_handling",
                statement="Exact duplicates (identical across all fields) should be removed, keeping first occurrence",
                rationale="Perfect duplicates provide no additional information and may indicate database errors or repeated data entry.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="FDA",
                        title="Data Integrity and Compliance With Drug CGMP",
                        year=2018,
                        url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/data-integrity-and-compliance-drug-cgmp",
                    ),
                ],
                tags=["duplicates", "data_quality"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="duplicate_partial_matches",
                category="duplicates",
                topic="partial_duplicate_handling",
                statement="Partial duplicates (same key fields, different data) require manual review or merge logic",
                rationale="May represent legitimate repeated measures, data corrections, or errors. Cannot automatically delete without understanding context.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="Christen, P.",
                        title="Data Matching: Concepts and Techniques for Record Linkage",
                        year=2012,
                    ),
                ],
                conditions=["manual_review_available"],
                tags=["duplicates", "data_linkage", "manual_review"],
            )
        )

        # ========================================
        # DATA TRANSFORMATION
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="transform_log_skewed",
                category="transformation",
                topic="log_transformation_skewed_data",
                statement="Log transformation can normalize right-skewed continuous data with positive values",
                rationale="Reduces positive skewness. Appropriate for multiplicative processes (e.g., concentrations). Cannot handle zero or negative values.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Osborne, J.",
                        title="Improving your data transformations",
                        year=2002,
                    ),
                ],
                conditions=["positive_values", "right_skewed"],
                contraindications=["zero_values", "negative_values"],
                tags=["transformation", "normalization", "skewness"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="transform_standardization",
                category="transformation",
                topic="standardization_z_scores",
                statement="Standardization (z-scores) enables comparison across variables with different units",
                rationale="Centers at mean=0, scales to SD=1. Preserves relationships. Useful for combining variables or comparing effect sizes.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Cohen, J.",
                        title="Statistical Power Analysis for the Behavioral Sciences",
                        year=1988,
                    ),
                ],
                tags=["transformation", "standardization", "statistical_method"],
            )
        )

        # ========================================
        # STUDY DESIGN CONSIDERATIONS
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="sample_size_guideline",
                category="study_design",
                topic="minimum_sample_size",
                statement="Minimum sample size of 30 per group often cited for parametric tests, but depends on effect size and variability",
                rationale="Central Limit Theorem approximation. Larger samples needed for small effects or high variability. Non-parametric alternatives for small samples.",
                evidence_level=EvidenceLevel.EXPERT_OPINION,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="Maxwell & Delaney",
                        title="Designing Experiments and Analyzing Data",
                        year=2017,
                    ),
                ],
                tags=["study_design", "sample_size", "statistics"],
            )
        )

    def get_cleaning_recommendation(
        self,
        situation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[KnowledgeEntry]:
        """
        Get evidence-based recommendation for a data cleaning situation.

        Args:
            situation: Type of situation (e.g., "missing_data", "outliers")
            context: Additional context (missingness rate, data type, etc.)

        Returns:
            Most relevant high-confidence recommendation
        """
        context = context or {}

        # Search for relevant recommendations
        candidates = self.search(category=situation, min_confidence=ConfidenceLevel.MEDIUM)

        if not candidates:
            return None

        # Filter by context
        applicable = []
        for entry in candidates:
            # Check if conditions are met
            if entry.conditions:
                conditions_met = all(
                    context.get(cond, False) for cond in entry.conditions
                )
                if not conditions_met:
                    continue

            # Check for contraindications
            if entry.contraindications:
                has_contraindication = any(
                    context.get(contra, False)
                    for contra in entry.contraindications
                )
                if has_contraindication:
                    continue

            applicable.append(entry)

        if not applicable:
            # Return highest confidence even if conditions unclear
            applicable = candidates

        # Sort by confidence and evidence level
        applicable.sort(
            key=lambda e: (
                [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW].index(e.confidence),
                [
                    EvidenceLevel.SYSTEMATIC_REVIEW,
                    EvidenceLevel.RANDOMIZED_TRIAL,
                    EvidenceLevel.COHORT_STUDY,
                    EvidenceLevel.BEST_PRACTICE,
                    EvidenceLevel.EXPERT_OPINION,
                ].index(e.evidence_level),
            )
        )

        return applicable[0]

    def explain_recommendation(
        self,
        entry: KnowledgeEntry,
        include_citations: bool = True,
    ) -> str:
        """
        Generate human-readable explanation of a recommendation.

        Args:
            entry: Knowledge entry to explain
            include_citations: Whether to include citations

        Returns:
            Formatted explanation with evidence
        """
        explanation = f"**Recommendation:** {entry.statement}\n\n"
        explanation += f"**Rationale:** {entry.rationale}\n\n"
        explanation += f"**Evidence Level:** {entry.evidence_level.value.replace('_', ' ').title()}\n"
        explanation += f"**Confidence:** {entry.confidence.value.upper()}\n\n"

        if entry.conditions:
            explanation += f"**Applicable when:**\n"
            for cond in entry.conditions:
                explanation += f"  - {cond}\n"
            explanation += "\n"

        if entry.contraindications:
            explanation += f"**⚠ Do NOT use when:**\n"
            for contra in entry.contraindications:
                explanation += f"  - {contra}\n"
            explanation += "\n"

        if include_citations and entry.citations:
            explanation += "**References:**\n"
            for cite in entry.citations:
                citation_text = f"  - {cite.source}"
                if cite.year:
                    citation_text += f" ({cite.year})"
                citation_text += f": {cite.title}"
                if cite.doi:
                    citation_text += f"\n    DOI: {cite.doi}"
                if cite.url:
                    citation_text += f"\n    URL: {cite.url}"
                explanation += citation_text + "\n"

        return explanation
