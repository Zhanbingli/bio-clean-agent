/**
 * @file quality/assessor.ts
 * @description ISO 8000-aligned data quality assessor.
 *
 * Implements {@link DataQualityAssessor}, a lightweight, Danfo.js-free module
 * that works directly on `Record<string, unknown>[]` row arrays and uses
 * `simple-statistics` for all numerical computations.
 *
 * Six DAMA dimensions are assessed:
 * - Completeness  – missing and empty cell rates
 * - Validity       – range checks, negative-value guards, IQR outlier detection
 * - Consistency    – BMI, date-pair, age/birthdate coherence
 * - Uniqueness     – exact, key-field, and composite key duplicates
 * - Timeliness     – future dates, data age
 * - (Statistical)  – skewness / kurtosis based normality proxy
 */

import * as ss from "simple-statistics";

import {
  DimensionAssessment,
  DataQualityReport,
  scoreToDimensionLevel,
} from "../schemas/quality.js";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/**
 * Field-level reference ranges for validity checks.
 * Each key is a field name; the value is `[min, max]`.
 *
 * @example
 * ```ts
 * const ranges: QualityReferenceRange = {
 *   systolic_bp: [70, 200],
 *   heart_rate:  [30, 220],
 * };
 * ```
 */
export interface QualityReferenceRange {
  [field: string]: [number, number];
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Returns `true` when `value` is a finite JavaScript number.
 * Filters out `null`, `undefined`, `NaN`, and `Infinity`.
 */
function isNumeric(value: unknown): value is number {
  return typeof value === "number" && isFinite(value);
}

/**
 * Count elements that are `null`, `undefined`, `NaN`, or the empty string.
 */
function countMissing(values: unknown[]): number {
  return values.filter(
    (v) =>
      v === null ||
      v === undefined ||
      (typeof v === "number" && isNaN(v)) ||
      v === ""
  ).length;
}

/**
 * Collect the names of fields whose non-missing values are all numeric.
 */
function getNumericColumns(data: Record<string, unknown>[]): string[] {
  if (data.length === 0) return [];
  const fields = Object.keys(data[0]);
  return fields.filter((field) => {
    const nonMissing = data
      .map((row) => row[field])
      .filter(
        (v) =>
          v !== null &&
          v !== undefined &&
          !(typeof v === "number" && isNaN(v)) &&
          v !== ""
      );
    return (
      nonMissing.length > 0 && nonMissing.every((v) => isNumeric(v))
    );
  });
}

/**
 * Collect the names of fields whose non-missing values are all strings.
 */
function getObjectColumns(data: Record<string, unknown>[]): string[] {
  if (data.length === 0) return [];
  const fields = Object.keys(data[0]);
  return fields.filter((field) => {
    const nonMissing = data
      .map((row) => row[field])
      .filter(
        (v) =>
          v !== null &&
          v !== undefined &&
          !(typeof v === "number" && isNaN(v)) &&
          v !== ""
      );
    return (
      nonMissing.length > 0 && nonMissing.every((v) => typeof v === "string")
    );
  });
}

/**
 * Safe quantile wrapper – returns `null` when the array is too small.
 */
function safeQuantile(values: number[], p: number): number | null {
  if (values.length < 4) return null;
  return ss.quantile(values, p);
}

// ---------------------------------------------------------------------------
// DataQualityAssessor
// ---------------------------------------------------------------------------

/**
 * ISO 8000 / DAMA-aligned data quality assessor.
 *
 * Operates on plain row-oriented data (`Record<string, unknown>[]`) without
 * any external dataframe library.  Statistical computations are delegated to
 * `simple-statistics`.
 *
 * @example
 * ```ts
 * const assessor = new DataQualityAssessor({ age: [0, 120] });
 * const report = assessor.assess(rows, "patients", ["patient_id"], ["visit_date"]);
 * console.log(report.overall_level); // "good"
 * ```
 */
export class DataQualityAssessor {
  /** Per-field reference ranges used by the validity check. */
  private readonly referenceRanges: QualityReferenceRange;

  constructor(referenceRanges: QualityReferenceRange = {}) {
    this.referenceRanges = referenceRanges;
  }

  // -------------------------------------------------------------------------
  // Public entry point
  // -------------------------------------------------------------------------

  /**
   * Run all quality dimensions and aggregate into a {@link DataQualityReport}.
   *
   * @param data        Row-oriented dataset.
   * @param datasetName Optional human-readable name (defaults to `"dataset"`).
   * @param keyFields   Columns that form a logical primary key for uniqueness checks.
   * @param dateFields  Columns that contain date-like values for timeliness checks.
   */
  assess(
    data: Record<string, unknown>[],
    datasetName = "dataset",
    keyFields: string[] = [],
    dateFields: string[] = []
  ): DataQualityReport {
    const totalRecords = data.length;
    const totalFields =
      data.length > 0 ? Object.keys(data[0]).length : 0;

    const completeness = this._assessCompleteness(data);
    const validity = this._assessValidity(data);
    const consistency = this._assessConsistency(data);
    const uniqueness = this._assessUniqueness(data, keyFields);
    const timeliness =
      dateFields.length > 0
        ? this._assessTimeliness(data, dateFields)
        : null;

    // Weighted average: completeness 30%, validity 30%, consistency 20%, uniqueness 20%
    const dimensionScores = [
      completeness.score * 0.3,
      validity.score * 0.3,
      consistency.score * 0.2,
      uniqueness.score * 0.2,
    ];
    if (timeliness !== null) {
      // Re-weight when timeliness is present: add 10 %, reduce consistency/uniqueness
      const baseScore =
        completeness.score * 0.25 +
        validity.score * 0.25 +
        consistency.score * 0.2 +
        uniqueness.score * 0.2 +
        timeliness.score * 0.1;
      const overallScore = Math.min(1, Math.max(0, baseScore));

      return {
        dataset_name: datasetName,
        total_records: totalRecords,
        total_fields: totalFields,
        completeness,
        validity,
        consistency,
        uniqueness,
        timeliness,
        overall_score: overallScore,
        overall_level: scoreToDimensionLevel(overallScore),
      };
    }

    const overallScore = Math.min(
      1,
      Math.max(0, dimensionScores.reduce((a, b) => a + b, 0))
    );

    return {
      dataset_name: datasetName,
      total_records: totalRecords,
      total_fields: totalFields,
      completeness,
      validity,
      consistency,
      uniqueness,
      timeliness: null,
      overall_score: overallScore,
      overall_level: scoreToDimensionLevel(overallScore),
    };
  }

  // -------------------------------------------------------------------------
  // Dimension: Completeness
  // -------------------------------------------------------------------------

  /**
   * Measure what fraction of cells are non-missing.
   *
   * "Missing" means: `null`, `undefined`, `NaN`, or the empty string `""`.
   */
  _assessCompleteness(data: Record<string, unknown>[]): DimensionAssessment {
    const issues: string[] = [];
    const recommendations: string[] = [];
    const metrics: Record<string, unknown> = {};

    if (data.length === 0) {
      return {
        dimension: "completeness",
        score: 0,
        level: "poor",
        issues: ["Dataset is empty"],
        recommendations: ["Provide at least one data record"],
        metrics: {},
      };
    }

    const fields = Object.keys(data[0]);
    const totalCells = data.length * fields.length;
    let totalMissing = 0;
    const missingByField: Record<string, number> = {};
    const missingRateByField: Record<string, number> = {};

    for (const field of fields) {
      const values = data.map((row) => row[field]);
      const missingCount = countMissing(values);
      totalMissing += missingCount;
      missingByField[field] = missingCount;
      const rate = missingCount / data.length;
      missingRateByField[field] = rate;

      if (rate > 0.2) {
        issues.push(
          `Column '${field}' has ${(rate * 100).toFixed(1)}% missing values`
        );
        recommendations.push(
          `Investigate '${field}': >20% missing – consider multiple imputation or exclusion`
        );
      } else if (rate > 0.05) {
        issues.push(
          `Column '${field}' has ${(rate * 100).toFixed(1)}% missing values`
        );
        recommendations.push(`Impute missing '${field}' values with median/mode`);
      }
    }

    const score =
      totalCells > 0 ? Math.max(0, 1 - totalMissing / totalCells) : 1;

    metrics["total_missing"] = totalMissing;
    metrics["total_cells"] = totalCells;
    metrics["overall_missing_rate"] = totalCells > 0 ? totalMissing / totalCells : 0;
    metrics["missing_by_field"] = missingByField;
    metrics["missing_rate_by_field"] = missingRateByField;

    return {
      dimension: "completeness",
      score,
      level: scoreToDimensionLevel(score),
      issues,
      recommendations,
      metrics,
    };
  }

  // -------------------------------------------------------------------------
  // Dimension: Validity
  // -------------------------------------------------------------------------

  /**
   * Validate values against reference ranges, domain rules (no negative
   * anthropometrics, no impossible vital signs), and IQR-based outlier
   * detection (threshold: 3× IQR).
   */
  _assessValidity(data: Record<string, unknown>[]): DimensionAssessment {
    const issues: string[] = [];
    const recommendations: string[] = [];
    const metrics: Record<string, unknown> = {};

    if (data.length === 0) {
      return {
        dimension: "validity",
        score: 1,
        level: "excellent",
        issues: [],
        recommendations: [],
        metrics: {},
      };
    }

    const numericCols = getNumericColumns(data);
    let totalInvalid = 0;
    const invalidByField: Record<string, number> = {};
    const outliersByField: Record<string, number> = {};

    // --- Reference range checks ---
    for (const [field, range] of Object.entries(this.referenceRanges)) {
      const [minVal, maxVal] = range as [number, number];
      if (!numericCols.includes(field)) continue;
      const values = data
        .map((row) => row[field])
        .filter(isNumeric) as number[];
      const outCount = values.filter((v) => v < minVal || v > maxVal).length;
      if (outCount > 0) {
        invalidByField[field] = (invalidByField[field] ?? 0) + outCount;
        totalInvalid += outCount;
        issues.push(
          `Column '${field}': ${outCount} values outside reference range [${minVal}, ${maxVal}]`
        );
        recommendations.push(
          `Review '${field}' values outside [${minVal}, ${maxVal}]; verify or flag for correction`
        );
      }
    }

    // --- Domain rules: negative checks for bio-medical fields ---
    const mustBePositive = [
      "age",
      "weight",
      "height",
      "bmi",
      "systolic_bp",
      "diastolic_bp",
      "heart_rate",
    ];
    for (const field of mustBePositive) {
      if (!numericCols.includes(field)) continue;
      const values = data
        .map((row) => row[field])
        .filter(isNumeric) as number[];
      const negCount = values.filter((v) => v < 0).length;
      if (negCount > 0) {
        invalidByField[field] = (invalidByField[field] ?? 0) + negCount;
        totalInvalid += negCount;
        issues.push(
          `Column '${field}': ${negCount} negative values (biologically impossible)`
        );
        recommendations.push(
          `Correct or remove negative '${field}' values`
        );
      }
    }

    // --- IQR outlier detection (3× IQR fence) ---
    for (const field of numericCols) {
      const values = data
        .map((row) => row[field])
        .filter(isNumeric) as number[];
      if (values.length < 4) continue;

      const q1 = safeQuantile(values, 0.25);
      const q3 = safeQuantile(values, 0.75);
      if (q1 === null || q3 === null) continue;

      const iqr = q3 - q1;
      const lowerFence = q1 - 3 * iqr;
      const upperFence = q3 + 3 * iqr;

      const extremeCount = values.filter(
        (v) => v < lowerFence || v > upperFence
      ).length;
      if (extremeCount > 0) {
        outliersByField[field] = extremeCount;
        issues.push(
          `Column '${field}': ${extremeCount} extreme outliers (outside 3× IQR fence)`
        );
        recommendations.push(
          `Investigate '${field}' extreme outliers – check for data entry errors`
        );
      }
    }

    const totalOutliers = Object.values(outliersByField).reduce(
      (a, b) => a + b,
      0
    );
    const allInvalidCount = totalInvalid + totalOutliers;
    const score =
      data.length > 0
        ? Math.max(0, 1 - allInvalidCount / (data.length * Math.max(1, numericCols.length)))
        : 1;

    metrics["total_invalid"] = totalInvalid;
    metrics["total_outliers"] = totalOutliers;
    metrics["invalid_by_field"] = invalidByField;
    metrics["outliers_by_field"] = outliersByField;

    return {
      dimension: "validity",
      score,
      level: scoreToDimensionLevel(score),
      issues,
      recommendations,
      metrics,
    };
  }

  // -------------------------------------------------------------------------
  // Dimension: Consistency
  // -------------------------------------------------------------------------

  /**
   * Detect logical inconsistencies within rows:
   * - BMI vs. weight/height coherence
   * - Date-pair ordering (enrollment before visit, etc.)
   * - Age vs. birthdate plausibility
   */
  _assessConsistency(data: Record<string, unknown>[]): DimensionAssessment {
    const issues: string[] = [];
    const recommendations: string[] = [];
    const metrics: Record<string, unknown> = {};

    if (data.length === 0) {
      return {
        dimension: "consistency",
        score: 1,
        level: "excellent",
        issues: [],
        recommendations: [],
        metrics: {},
      };
    }

    let inconsistentCount = 0;

    // --- BMI consistency: bmi ≈ weight(kg) / height(m)^2 ---
    const hasBmi =
      data[0] !== undefined &&
      "bmi" in data[0] &&
      "weight" in data[0] &&
      "height" in data[0];
    if (hasBmi) {
      let bmiErrors = 0;
      for (const row of data) {
        const bmi = row["bmi"];
        const weight = row["weight"];
        const height = row["height"];
        if (!isNumeric(bmi) || !isNumeric(weight) || !isNumeric(height)) continue;
        if (height <= 0) continue;
        // height assumed cm if > 3 (common in clinical data)
        const heightM = height > 3 ? height / 100 : height;
        const computedBmi = weight / (heightM * heightM);
        if (Math.abs(computedBmi - bmi) > 2) {
          bmiErrors++;
        }
      }
      if (bmiErrors > 0) {
        inconsistentCount += bmiErrors;
        issues.push(
          `BMI inconsistency: ${bmiErrors} rows where computed BMI deviates >2 units from stored BMI`
        );
        recommendations.push(
          "Recompute BMI from weight and height to resolve discrepancies"
        );
      }
      metrics["bmi_inconsistencies"] = bmiErrors;
    }

    // --- Date-pair consistency ---
    const datePairs: Array<[string, string]> = [
      ["enrollment_date", "visit_date"],
      ["enrollment_date", "completion_date"],
      ["birth_date", "enrollment_date"],
    ];
    for (const [earlier, later] of datePairs) {
      const hasFields =
        data[0] !== undefined &&
        earlier in data[0] &&
        later in data[0];
      if (!hasFields) continue;

      let pairErrors = 0;
      for (const row of data) {
        const earlyVal = row[earlier];
        const lateVal = row[later];
        if (earlyVal === null || earlyVal === undefined || earlyVal === "") continue;
        if (lateVal === null || lateVal === undefined || lateVal === "") continue;
        const earlyDate = new Date(String(earlyVal));
        const lateDate = new Date(String(lateVal));
        if (isNaN(earlyDate.getTime()) || isNaN(lateDate.getTime())) continue;
        if (lateDate < earlyDate) pairErrors++;
      }
      if (pairErrors > 0) {
        inconsistentCount += pairErrors;
        issues.push(
          `Date inconsistency: ${pairErrors} rows where '${later}' is before '${earlier}'`
        );
        recommendations.push(
          `Verify date ordering: '${earlier}' must precede '${later}'`
        );
      }
      metrics[`date_pair_errors_${earlier}_${later}`] = pairErrors;
    }

    // --- Age vs. birth_date coherence ---
    const hasAgeBirth =
      data[0] !== undefined &&
      "age" in data[0] &&
      "birth_date" in data[0];
    if (hasAgeBirth) {
      let ageErrors = 0;
      const now = Date.now();
      for (const row of data) {
        const age = row["age"];
        const birthDateRaw = row["birth_date"];
        if (!isNumeric(age) || birthDateRaw === null || birthDateRaw === undefined || birthDateRaw === "") continue;
        const birthDate = new Date(String(birthDateRaw));
        if (isNaN(birthDate.getTime())) continue;
        const computedAge = (now - birthDate.getTime()) / (365.25 * 24 * 3600 * 1000);
        if (Math.abs(computedAge - age) > 2) {
          ageErrors++;
        }
      }
      if (ageErrors > 0) {
        inconsistentCount += ageErrors;
        issues.push(
          `Age/birthdate inconsistency: ${ageErrors} rows where age does not match birth_date`
        );
        recommendations.push("Recompute age from birth_date to ensure accuracy");
        metrics["age_birthdate_inconsistencies"] = ageErrors;
      }
    }

    const totalRowsChecked = data.length;
    const score =
      totalRowsChecked > 0
        ? Math.max(0, 1 - inconsistentCount / totalRowsChecked)
        : 1;

    metrics["total_inconsistencies"] = inconsistentCount;

    return {
      dimension: "consistency",
      score,
      level: scoreToDimensionLevel(score),
      issues,
      recommendations,
      metrics,
    };
  }

  // -------------------------------------------------------------------------
  // Dimension: Uniqueness
  // -------------------------------------------------------------------------

  /**
   * Detect duplicates at three levels:
   * 1. Exact full-row duplicates
   * 2. Duplicates on individually specified key fields
   * 3. Composite duplicates across all key fields combined
   */
  _assessUniqueness(
    data: Record<string, unknown>[],
    keyFields: string[] = []
  ): DimensionAssessment {
    const issues: string[] = [];
    const recommendations: string[] = [];
    const metrics: Record<string, unknown> = {};

    if (data.length === 0) {
      return {
        dimension: "uniqueness",
        score: 1,
        level: "excellent",
        issues: [],
        recommendations: [],
        metrics: {},
      };
    }

    // --- Exact row duplicates ---
    const rowSigs = data.map((row) => JSON.stringify(row));
    const uniqueRowSigs = new Set(rowSigs);
    const exactDuplicates = data.length - uniqueRowSigs.size;
    if (exactDuplicates > 0) {
      issues.push(`${exactDuplicates} exact duplicate rows detected`);
      recommendations.push(
        "Remove exact duplicate rows – they provide no additional information"
      );
    }
    metrics["exact_duplicates"] = exactDuplicates;

    // --- Per-key-field duplicates ---
    let maxKeyDuplicates = 0;
    const keyDuplicatesByField: Record<string, number> = {};
    for (const field of keyFields) {
      if (!(field in (data[0] ?? {}))) continue;
      const values = data.map((row) => String(row[field] ?? ""));
      const uniq = new Set(values);
      const dups = values.length - uniq.size;
      keyDuplicatesByField[field] = dups;
      if (dups > 0) {
        maxKeyDuplicates = Math.max(maxKeyDuplicates, dups);
        issues.push(
          `Key field '${field}': ${dups} duplicate values (expected unique)`
        );
        recommendations.push(
          `Investigate duplicate values in key field '${field}'`
        );
      }
    }
    metrics["key_duplicates_by_field"] = keyDuplicatesByField;

    // --- Composite key duplicates ---
    let compositeKeyDuplicates = 0;
    const presentKeyFields = keyFields.filter(
      (f) => f in (data[0] ?? {})
    );
    if (presentKeyFields.length > 1) {
      const compositeSigs = data.map((row) =>
        presentKeyFields.map((f) => String(row[f] ?? "")).join("|")
      );
      const uniqComposite = new Set(compositeSigs);
      compositeKeyDuplicates = compositeSigs.length - uniqComposite.size;
      if (compositeKeyDuplicates > 0) {
        issues.push(
          `${compositeKeyDuplicates} composite key duplicates on [${presentKeyFields.join(", ")}]`
        );
        recommendations.push(
          `Resolve composite key duplicates on [${presentKeyFields.join(", ")}]`
        );
      }
    }
    metrics["composite_key_duplicates"] = compositeKeyDuplicates;

    const totalDuplicates = exactDuplicates + compositeKeyDuplicates;
    const score =
      data.length > 0
        ? Math.max(0, 1 - totalDuplicates / data.length)
        : 1;

    return {
      dimension: "uniqueness",
      score,
      level: scoreToDimensionLevel(score),
      issues,
      recommendations,
      metrics,
    };
  }

  // -------------------------------------------------------------------------
  // Dimension: Timeliness
  // -------------------------------------------------------------------------

  /**
   * Evaluate timeliness of date-containing fields:
   * - Count future dates (data that hasn't happened yet)
   * - Compute mean data age in days (large ages may indicate stale data)
   */
  _assessTimeliness(
    data: Record<string, unknown>[],
    dateFields: string[]
  ): DimensionAssessment {
    const issues: string[] = [];
    const recommendations: string[] = [];
    const metrics: Record<string, unknown> = {};

    if (data.length === 0) {
      return {
        dimension: "timeliness",
        score: 1,
        level: "excellent",
        issues: [],
        recommendations: [],
        metrics: {},
      };
    }

    const now = Date.now();
    const nowDate = new Date();
    let totalFutureDates = 0;
    const futureByField: Record<string, number> = {};
    const agesByField: Record<string, number> = {};

    for (const field of dateFields) {
      if (!(field in (data[0] ?? {}))) continue;

      let futureDates = 0;
      const validAgesMs: number[] = [];

      for (const row of data) {
        const raw = row[field];
        if (raw === null || raw === undefined || raw === "") continue;
        const d = new Date(String(raw));
        if (isNaN(d.getTime())) continue;
        if (d > nowDate) {
          futureDates++;
        } else {
          validAgesMs.push(now - d.getTime());
        }
      }

      futureByField[field] = futureDates;
      totalFutureDates += futureDates;

      if (futureDates > 0) {
        issues.push(
          `Column '${field}': ${futureDates} future dates (data anomaly)`
        );
        recommendations.push(
          `Verify '${field}' – future dates indicate data entry errors`
        );
      }

      if (validAgesMs.length > 0) {
        const avgAgeDays =
          validAgesMs.reduce((a, b) => a + b, 0) /
          validAgesMs.length /
          (1000 * 60 * 60 * 24);
        agesByField[field] = Math.round(avgAgeDays);
        if (avgAgeDays > 365 * 5) {
          issues.push(
            `Column '${field}': mean data age is ${Math.round(avgAgeDays)} days (>5 years)`
          );
          recommendations.push(
            `Review '${field}' for stale data – mean age exceeds 5 years`
          );
        }
      }
    }

    const futurePenalty =
      data.length > 0 ? totalFutureDates / data.length : 0;
    const score = Math.max(0, 1 - futurePenalty);

    metrics["future_dates_by_field"] = futureByField;
    metrics["mean_age_days_by_field"] = agesByField;
    metrics["total_future_dates"] = totalFutureDates;

    return {
      dimension: "timeliness",
      score,
      level: scoreToDimensionLevel(score),
      issues,
      recommendations,
      metrics,
    };
  }

  // -------------------------------------------------------------------------
  // Statistical tests
  // -------------------------------------------------------------------------

  /**
   * Compute per-column descriptive statistics and a simplified normality proxy
   * (|skewness| < 2 and |kurtosis - 3| < 7) using `simple-statistics`.
   *
   * Returns a plain object keyed by column name; each value carries:
   * `mean`, `median`, `std`, `skewness`, `kurtosis`, `normalityPassed`.
   */
  _runStatisticalTests(
    data: Record<string, unknown>[]
  ): Record<string, Record<string, unknown>> {
    const result: Record<string, Record<string, unknown>> = {};

    if (data.length < 4) return result;

    const numericCols = getNumericColumns(data);

    for (const field of numericCols) {
      const values = data
        .map((row) => row[field])
        .filter(isNumeric) as number[];

      if (values.length < 4) continue;

      try {
        const mean = ss.mean(values);
        const median = ss.median(values);
        const std = ss.standardDeviation(values);
        const skewness = values.length >= 3 ? ss.sampleSkewness(values) : 0;
        const kurtosis = values.length >= 4 ? ss.sampleKurtosis(values) : 3;
        // Simplified normality proxy: Bliss-style skewness/kurtosis thresholds
        const normalityPassed =
          Math.abs(skewness) < 2 && Math.abs(kurtosis - 3) < 7;

        result[field] = {
          mean,
          median,
          std,
          skewness,
          kurtosis,
          normalityPassed,
          n: values.length,
        };
      } catch {
        // Skip column if computation fails (e.g., constant column with zero std)
        result[field] = { error: "computation_failed", n: values.length };
      }
    }

    return result;
  }

  // -------------------------------------------------------------------------
  // Private: convert numeric score → DimensionScore label
  // -------------------------------------------------------------------------

  /**
   * Map a numeric `score` (0–1) to its qualitative {@link DimensionScore}.
   *
   * Delegates to the shared {@link scoreToDimensionLevel} helper to keep
   * thresholds consistent with the schema module.
   */
  _scoreToLevel(score: number) {
    return scoreToDimensionLevel(score);
  }
}

// Re-export helper used in tests
export { isNumeric, countMissing, getNumericColumns, getObjectColumns };
