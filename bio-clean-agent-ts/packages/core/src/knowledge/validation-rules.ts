/**
 * Scientific validation rules engine.
 *
 * Validates data against medical knowledge and best practices.
 * All validation decisions are backed by entries in {@link MedicalStandards}.
 */

import { KnowledgeEntry } from "./base.js";
import { MedicalStandards } from "./medical-standards.js";

// ============================================================
// TYPES
// ============================================================

/**
 * Serializable plain-object form of a {@link ValidationResult}.
 */
export interface ValidationResultDict {
  valid: boolean;
  errors: string[];
  warnings: string[];
  recommendations: string[];
  /** Number of supporting knowledge entries found */
  evidenceCount: number;
}

/**
 * Known vital-sign field names accepted by {@link ValidationRules.validateVitalSign}.
 */
export type VitalSignField =
  | "systolic_bp"
  | "diastolic_bp"
  | "heart_rate"
  | "temperature"
  | "respiratory_rate"
  | "oxygen_saturation";

/**
 * Known laboratory test names accepted by {@link ValidationRules.validateLabValue}.
 */
export type LabTestName = "glucose" | "hba1c" | "hemoglobin" | "creatinine";

/**
 * Internal tuple describing a numeric range and its unit string.
 * [min, max, unit]
 */
type RangeTuple = [number, number, string];

/**
 * Patient context forwarded to vital-sign validation.
 */
export interface VitalSignContext {
  /** Patient age in years */
  age?: number;
  /** `true` when the patient is a trained athlete */
  athlete?: boolean;
  [key: string]: unknown;
}

/**
 * Context forwarded to lab-value validation.
 */
export interface LabValueContext {
  /** `true` when patient has been fasting for at least 8 hours */
  fasting?: boolean;
  /** Patient biological sex: "male" | "female" */
  sex?: "male" | "female";
  [key: string]: unknown;
}

// ============================================================
// VALIDATION RESULT CLASS
// ============================================================

/**
 * Accumulates errors, warnings, recommendations, and supporting evidence
 * produced during a single validation run.
 *
 * A result starts as `valid = true`; the first call to {@link addError}
 * flips it to `false`.
 */
export class ValidationResult {
  /** Whether the validated value passes all rules */
  valid = true;
  /** Non-recoverable rule violations */
  readonly warnings: string[] = [];
  /** Non-fatal advisory messages */
  readonly errors: string[] = [];
  /** Suggested corrective actions */
  readonly recommendations: string[] = [];
  /** Knowledge entries consulted during validation */
  readonly evidence: KnowledgeEntry[] = [];

  /**
   * Record a non-recoverable error and mark the result invalid.
   *
   * @param message  Human-readable error description.
   * @param evidence Optional supporting knowledge entry.
   */
  addError(message: string, evidence?: KnowledgeEntry): void {
    this.valid = false;
    this.errors.push(message);
    if (evidence !== undefined) {
      this.evidence.push(evidence);
    }
  }

  /**
   * Record an advisory warning (does not affect `valid`).
   *
   * @param message  Human-readable warning description.
   * @param evidence Optional supporting knowledge entry.
   */
  addWarning(message: string, evidence?: KnowledgeEntry): void {
    this.warnings.push(message);
    if (evidence !== undefined) {
      this.evidence.push(evidence);
    }
  }

  /**
   * Record a suggested corrective action.
   *
   * @param message Human-readable recommendation.
   */
  addRecommendation(message: string): void {
    this.recommendations.push(message);
  }

  /**
   * Serialize to a plain JSON-compatible object.
   */
  toDict(): ValidationResultDict {
    return {
      valid: this.valid,
      errors: [...this.errors],
      warnings: [...this.warnings],
      recommendations: [...this.recommendations],
      evidenceCount: this.evidence.length,
    };
  }
}

// ============================================================
// REFERENCE RANGE MAPS
// ============================================================

/**
 * Acceptable (plausible) ranges for vital signs used as hard limits during
 * validation.  Values inside the range are not necessarily "normal" — they
 * are simply not physiologically impossible for a living human.
 *
 * Key: {@link VitalSignField}
 * Value: [min, max, unit]
 */
const VITAL_SIGN_RANGES: Record<VitalSignField, RangeTuple> = {
  systolic_bp: [70, 200, "mmHg"],
  diastolic_bp: [40, 130, "mmHg"],
  heart_rate: [40, 150, "bpm"],
  temperature: [35.0, 42.0, "\u00b0C"],
  respiratory_rate: [8, 30, "breaths/min"],
  oxygen_saturation: [70, 100, "%"],
};

/**
 * Normal reference ranges for common laboratory tests.
 * The inner map key is a sub-context (e.g. "fasting", "male", "female").
 *
 * Key: {@link LabTestName}
 * Inner key: sub-context
 * Value: [min, max, unit]
 */
const LAB_VALUE_RANGES: Record<LabTestName, Record<string, RangeTuple>> = {
  glucose: {
    fasting: [70, 100, "mg/dL"],
    random: [70, 200, "mg/dL"],
  },
  hba1c: {
    normal: [4.0, 5.6, "%"],
  },
  hemoglobin: {
    male: [13.5, 17.5, "g/dL"],
    female: [12.0, 15.5, "g/dL"],
  },
  creatinine: {
    male: [0.7, 1.3, "mg/dL"],
    female: [0.6, 1.1, "mg/dL"],
  },
};

// ============================================================
// VALIDATION RULES ENGINE
// ============================================================

/**
 * Scientific validation rules engine.
 *
 * Validates individual data points against medical knowledge and best
 * practices.  Each public method returns a {@link ValidationResult}
 * populated with errors, warnings, recommendations, and supporting
 * {@link KnowledgeEntry} evidence.
 */
export class ValidationRules {
  /** Backing knowledge base used for evidence look-ups */
  private readonly medicalStandards: MedicalStandards;

  constructor() {
    this.medicalStandards = new MedicalStandards();
  }

  // ----------------------------------------------------------
  // Vital Signs
  // ----------------------------------------------------------

  /**
   * Validate a vital sign value against physiologically plausible ranges
   * and produce clinically contextualised warnings.
   *
   * @param field   Vital sign identifier (must be a {@link VitalSignField}).
   * @param value   Measured numeric value.
   * @param context Optional patient context (e.g. `{ age: 30, athlete: true }`).
   */
  validateVitalSign(
    field: string,
    value: number,
    context: VitalSignContext = {}
  ): ValidationResult {
    const result = new ValidationResult();

    if (!Object.prototype.hasOwnProperty.call(VITAL_SIGN_RANGES, field)) {
      result.addWarning(`Unknown vital sign: ${field}`);
      return result;
    }

    const [minVal, maxVal, unit] = VITAL_SIGN_RANGES[field as VitalSignField];
    const evidence = this.medicalStandards.getReferenceRange(field, context);

    if (value < minVal || value > maxVal) {
      result.addError(
        `${field} value ${value}${unit} is outside acceptable range (${minVal}-${maxVal}${unit})`,
        evidence?.source
      );

      // Field-specific recommendations for out-of-range values
      if (field === "systolic_bp") {
        if (value > maxVal) {
          result.addRecommendation(
            "High blood pressure detected. Verify measurement technique. " +
              "Consider data entry error or true hypertensive crisis."
          );
        } else {
          result.addRecommendation(
            "Low blood pressure detected. May indicate hypotension or measurement error."
          );
        }
      } else if (field === "temperature") {
        if (value > 38.0) {
          result.addRecommendation(
            `Fever detected (${value}\u00b0C). Document as clinically significant finding.`
          );
        } else if (value < 35.0) {
          result.addRecommendation(
            `Hypothermia detected (${value}\u00b0C). Verify measurement.`
          );
        }
      }
    } else if (field === "heart_rate") {
      // In-range but clinically noteworthy sub-conditions
      if (value < 50 && !context.athlete) {
        result.addWarning(
          `Bradycardia (${value} bpm). May be normal for athletes or indicate pathology.`
        );
      } else if (value > 100) {
        result.addWarning(
          `Tachycardia (${value} bpm). May be due to stress, exercise, or pathology.`
        );
      }
    }

    return result;
  }

  // ----------------------------------------------------------
  // Age
  // ----------------------------------------------------------

  /**
   * Validate a patient age value.
   *
   * @param age Age in years (may be fractional for infants).
   */
  validateAge(age: number): ValidationResult {
    const result = new ValidationResult();

    if (age < 0 || age > 120) {
      result.addError(
        `Age ${age} is outside valid range (0-120 years). Likely data entry error.`
      );
    } else if (age > 110) {
      result.addWarning(`Age ${age} is extremely high. Verify this is correct.`);
    }

    return result;
  }

  // ----------------------------------------------------------
  // Date Consistency
  // ----------------------------------------------------------

  /**
   * Validate that a visit date occurs on or after the enrollment date.
   *
   * Both strings must be ISO-8601 date/datetime values parseable by `Date`.
   *
   * @param enrollmentDate ISO-8601 enrollment date string.
   * @param visitDate      ISO-8601 visit date string.
   */
  validateDateConsistency(
    enrollmentDate: string,
    visitDate: string
  ): ValidationResult {
    const result = new ValidationResult();

    const enroll = new Date(enrollmentDate);
    const visit = new Date(visitDate);

    if (isNaN(enroll.getTime())) {
      result.addError(`Invalid enrollment date format: "${enrollmentDate}"`);
      return result;
    }
    if (isNaN(visit.getTime())) {
      result.addError(`Invalid visit date format: "${visitDate}"`);
      return result;
    }

    if (visit < enroll) {
      result.addError(
        `Visit date (${visitDate}) is before enrollment date (${enrollmentDate}). ` +
          "This is logically impossible."
      );
      result.addRecommendation(
        "Review source documents to correct date error."
      );
    }

    return result;
  }

  // ----------------------------------------------------------
  // BMI
  // ----------------------------------------------------------

  /**
   * Validate a BMI derived from weight and height, and produce a WHO-based
   * clinical interpretation.
   *
   * @param weightKg  Patient weight in kilograms.
   * @param heightCm  Patient height in centimetres.
   */
  validateBmi(weightKg: number, heightCm: number): ValidationResult {
    const result = new ValidationResult();

    if (weightKg <= 0 || weightKg > 300) {
      result.addError(`Invalid weight: ${weightKg} kg`);
    }
    if (heightCm <= 0 || heightCm > 250) {
      result.addError(`Invalid height: ${heightCm} cm`);
    }

    if (!result.valid) {
      return result;
    }

    const heightM = heightCm / 100;
    const bmi = weightKg / (heightM * heightM);
    const bmiEntry = this.medicalStandards.getEntry("anthro_bmi_categories");

    if (bmi < 16) {
      result.addError(
        `BMI ${bmi.toFixed(1)} indicates severe underweight. Verify measurements.`
      );
    } else if (bmi < 18.5) {
      result.addWarning(
        `BMI ${bmi.toFixed(1)} indicates underweight (WHO classification).`
      );
      if (bmiEntry !== undefined) {
        result.evidence.push(bmiEntry);
      }
    } else if (bmi < 25) {
      // 18.5 <= bmi < 25: normal range — no message
    } else if (bmi < 30) {
      result.addWarning(
        `BMI ${bmi.toFixed(1)} indicates overweight (WHO classification).`
      );
      if (bmiEntry !== undefined) {
        result.evidence.push(bmiEntry);
      }
    } else if (bmi < 40) {
      result.addWarning(
        `BMI ${bmi.toFixed(1)} indicates obesity (WHO classification).`
      );
      if (bmiEntry !== undefined) {
        result.evidence.push(bmiEntry);
      }
    } else {
      result.addError(
        `BMI ${bmi.toFixed(1)} indicates severe obesity or measurement error. Verify data.`
      );
    }

    return result;
  }

  // ----------------------------------------------------------
  // Laboratory Values
  // ----------------------------------------------------------

  /**
   * Validate a laboratory test result against established reference ranges.
   *
   * @param test    Laboratory test name (must be a {@link LabTestName}).
   * @param value   Numeric test result.
   * @param unit    Unit string reported with the result.
   * @param context Optional patient context (e.g. `{ fasting: true, sex: "male" }`).
   */
  validateLabValue(
    test: string,
    value: number,
    unit: string,
    context: LabValueContext = {}
  ): ValidationResult {
    const result = new ValidationResult();

    if (!Object.prototype.hasOwnProperty.call(LAB_VALUE_RANGES, test)) {
      result.addWarning(`Unknown lab test: ${test}`);
      return result;
    }

    const testRanges = LAB_VALUE_RANGES[test as LabTestName];
    const keys = Object.keys(testRanges);

    // Select the most applicable sub-range based on context
    let rangeKey: string;
    if (keys.length === 1) {
      rangeKey = keys[0];
    } else if (context.fasting && test === "glucose" && "fasting" in testRanges) {
      rangeKey = "fasting";
    } else if (context.sex === "male" && "male" in testRanges) {
      rangeKey = "male";
    } else if (context.sex === "female" && "female" in testRanges) {
      rangeKey = "female";
    } else {
      rangeKey = keys[0];
    }

    if (!(rangeKey in testRanges)) {
      rangeKey = keys[0];
    }

    const [minVal, maxVal, refUnit] = testRanges[rangeKey];

    // Warn on unit mismatch
    if (unit !== refUnit) {
      result.addWarning(
        `Unit mismatch: provided ${unit}, expected ${refUnit}. ` +
          "Value may need unit conversion."
      );
    }

    if (value < minVal || value > maxVal) {
      result.addError(
        `${test} value ${value}${unit} is outside normal range (${minVal}-${maxVal}${refUnit})`
      );

      // Clinical interpretation for known tests
      if (test === "glucose" && value > maxVal) {
        if (value >= 126) {
          result.addWarning("Glucose \u2265126 mg/dL indicates diabetes (ADA criteria)");
        } else if (value >= 100) {
          result.addWarning("Glucose 100-125 mg/dL indicates prediabetes");
        }
      } else if (test === "hba1c" && value > maxVal) {
        if (value >= 6.5) {
          result.addWarning("HbA1c \u22656.5% indicates diabetes (ADA criteria)");
        } else if (value >= 5.7) {
          result.addWarning("HbA1c 5.7-6.4% indicates prediabetes");
        }
      }
    }

    return result;
  }

  // ----------------------------------------------------------
  // ICD-10 Code Format
  // ----------------------------------------------------------

  /**
   * Validate that a string conforms to the ICD-10 code format.
   *
   * Valid patterns: `A00`, `A00.0`, `A00.00`.
   *
   * @param code ICD-10 code string to validate.
   */
  validateIcd10Format(code: string): ValidationResult {
    const result = new ValidationResult();

    // ICD-10 format: Letter + 2 digits + optional decimal + 1-2 digits
    const pattern = /^[A-Z][0-9]{2}(\.[0-9]{1,2})?$/;

    if (!pattern.test(code)) {
      result.addError(
        `Invalid ICD-10 code format: '${code}'. ` +
          "Expected format: A00 or A00.0 or A00.00"
      );
      result.addRecommendation(
        "ICD-10 codes must start with a letter followed by 2 digits, " +
          "optionally with a decimal point and 1-2 more digits."
      );
    }

    return result;
  }

  // ----------------------------------------------------------
  // Data Completeness
  // ----------------------------------------------------------

  /**
   * Validate that all required fields are present and non-empty in a data record.
   *
   * A field is considered missing when:
   * - it is absent from the `data` object, OR
   * - its value is `null`, `undefined`, or an empty string `""`.
   *
   * @param requiredFields List of field names that must be present and non-empty.
   * @param data           Data record to inspect.
   */
  validateDataCompleteness(
    requiredFields: string[],
    data: Record<string, unknown>
  ): ValidationResult {
    const result = new ValidationResult();

    for (const field of requiredFields) {
      const value = data[field];
      if (value === undefined || value === null || value === "") {
        result.addError(`Required field '${field}' is missing or empty`);
      }
    }

    if (result.errors.length > 0) {
      result.addRecommendation(
        `Complete all required fields: ${requiredFields.join(", ")}`
      );
    }

    return result;
  }
}
