/**
 * @file quality.ts
 * @description Zod schemas for data quality assessment: dimensional scoring,
 * per-dimension assessments, and full dataset quality reports.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

/**
 * ISO 8000 / DAMA-aligned quality dimensions assessed during data profiling.
 */
export const QualityDimensionSchema = z
  .enum([
    "completeness",
    "validity",
    "consistency",
    "uniqueness",
    "timeliness",
    "accuracy",
  ])
  .describe("Data quality dimension being assessed");

export type QualityDimension = z.infer<typeof QualityDimensionSchema>;

/**
 * Qualitative label derived from a numeric dimension score.
 *
 * | Label     | Score range |
 * |-----------|-------------|
 * | excellent | >= 95 %     |
 * | good      | 80 – 94 %   |
 * | fair      | 60 – 79 %   |
 * | poor      | < 60 %      |
 */
export const DimensionScoreSchema = z
  .enum(["excellent", "good", "fair", "poor"])
  .describe("Qualitative quality level derived from a numeric score");

export type DimensionScore = z.infer<typeof DimensionScoreSchema>;

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

/**
 * Converts a numeric score in the range [0, 1] to its qualitative
 * {@link DimensionScore} label.
 *
 * @param score - A value between 0 (worst) and 1 (best).
 * @returns The corresponding {@link DimensionScore}.
 *
 * @example
 * ```ts
 * scoreToDimensionLevel(0.97); // "excellent"
 * scoreToDimensionLevel(0.82); // "good"
 * scoreToDimensionLevel(0.70); // "fair"
 * scoreToDimensionLevel(0.45); // "poor"
 * ```
 */
export function scoreToDimensionLevel(score: number): DimensionScore {
  if (score >= 0.95) return "excellent";
  if (score >= 0.80) return "good";
  if (score >= 0.60) return "fair";
  return "poor";
}

// ---------------------------------------------------------------------------
// DimensionAssessment
// ---------------------------------------------------------------------------

/**
 * Assessment result for a single quality dimension.
 */
export const DimensionAssessmentSchema = z
  .object({
    /** The quality dimension being assessed. */
    dimension: QualityDimensionSchema,

    /**
     * Numeric score in the closed interval [0, 1].
     * A score of 1 means the dimension is fully satisfied.
     */
    score: z
      .number()
      .min(0)
      .max(1)
      .describe("Numeric quality score in [0, 1]"),

    /** Qualitative label derived from the numeric score. */
    level: DimensionScoreSchema,

    /**
     * List of specific data quality issues detected for this dimension
     * (e.g. "Column 'age' has 12 % missing values").
     */
    issues: z
      .array(z.string())
      .default([])
      .describe("Detected quality issues for this dimension"),

    /**
     * Actionable recommendations to improve the dimension score
     * (e.g. "Impute missing 'age' values with median").
     */
    recommendations: z
      .array(z.string())
      .default([])
      .describe("Recommended remediation actions"),

    /**
     * Arbitrary diagnostic metrics produced during assessment
     * (e.g. `{ missing_rate: 0.12, null_count: 340 }`).
     */
    metrics: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Detailed diagnostic metrics for this dimension"),
  })
  .describe("Quality assessment result for one data quality dimension");

export type DimensionAssessment = z.infer<typeof DimensionAssessmentSchema>;

// ---------------------------------------------------------------------------
// DataQualityReport
// ---------------------------------------------------------------------------

/**
 * Aggregated quality report for an entire dataset.
 * Mandatory dimensions mirror the six core DAMA dimensions;
 * `timeliness` and `accuracy` are optional because not all datasets
 * carry sufficient metadata to evaluate them.
 */
export const DataQualityReportSchema = z
  .object({
    /** Name or identifier of the assessed dataset. */
    dataset_name: z
      .string()
      .min(1)
      .describe("Name or identifier of the assessed dataset"),

    /** Total number of data records (rows) in the dataset. */
    total_records: z
      .number()
      .int()
      .nonnegative()
      .describe("Total number of records (rows)"),

    /** Total number of data fields (columns) in the dataset. */
    total_fields: z
      .number()
      .int()
      .nonnegative()
      .describe("Total number of fields (columns)"),

    // ---- Mandatory dimensions ----

    /** Assessment for the completeness dimension. */
    completeness: DimensionAssessmentSchema.describe(
      "Completeness dimension assessment"
    ),

    /** Assessment for the validity dimension. */
    validity: DimensionAssessmentSchema.describe(
      "Validity dimension assessment"
    ),

    /** Assessment for the consistency dimension. */
    consistency: DimensionAssessmentSchema.describe(
      "Consistency dimension assessment"
    ),

    /** Assessment for the uniqueness dimension. */
    uniqueness: DimensionAssessmentSchema.describe(
      "Uniqueness dimension assessment"
    ),

    // ---- Optional dimensions ----

    /**
     * Assessment for the timeliness dimension.
     * Omit when the dataset does not contain temporal metadata.
     */
    timeliness: DimensionAssessmentSchema.nullable()
      .optional()
      .describe("Timeliness dimension assessment (optional)"),

    /**
     * Assessment for the accuracy dimension.
     * Omit when no ground-truth reference is available.
     */
    accuracy: DimensionAssessmentSchema.nullable()
      .optional()
      .describe("Accuracy dimension assessment (optional)"),

    // ---- Aggregate scores ----

    /**
     * Weighted or arithmetic mean of all dimension scores.
     * Value in [0, 1].
     */
    overall_score: z
      .number()
      .min(0)
      .max(1)
      .describe("Aggregate quality score across all assessed dimensions (0–1)"),

    /** Qualitative label for the overall score. */
    overall_level: DimensionScoreSchema.describe(
      "Qualitative label for the overall quality score"
    ),
  })
  .describe("Comprehensive data quality report for a dataset");

export type DataQualityReport = z.infer<typeof DataQualityReportSchema>;
