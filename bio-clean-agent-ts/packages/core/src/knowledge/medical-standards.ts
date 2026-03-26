/**
 * Medical standards and reference ranges based on clinical guidelines.
 *
 * Sources:
 * - WHO guidelines
 * - American Heart Association (AHA)
 * - Clinical Laboratory Standards Institute (CLSI)
 * - FDA guidance documents
 * - American Diabetes Association
 * - American Academy of Pediatrics
 * - American Geriatrics Society
 * - British Thoracic Society
 * - American Thoracic Society
 */

import {
  Citation,
  ConfidenceLevel,
  CONFIDENCE_ORDER,
  EvidenceLevel,
  KnowledgeBase,
  KnowledgeEntry,
  createEntry,
} from "./base.js";

// ============================================================
// RETURN TYPES
// ============================================================

/**
 * Structured reference range for a clinical field.
 * Returned by {@link MedicalStandards.getReferenceRange}.
 */
export interface ReferenceRange {
  /** The knowledge entry that provides the authoritative reference */
  source: KnowledgeEntry;
  /** Confidence level string value of the source entry */
  confidence: string;
  /** Evidence level string value of the source entry */
  evidenceLevel: string;
}

// ============================================================
// CLASS
// ============================================================

/**
 * Evidence-based medical standards for data validation.
 *
 * Covers vital signs, anthropometry, laboratory values, age-specific
 * considerations, and statistical/data-quality standards — each entry
 * backed by authoritative citations.
 */
export class MedicalStandards extends KnowledgeBase {
  /**
   * Populate the knowledge base with all medical standards entries.
   * Organised into the following sections:
   * 1. Vital Signs (adult reference ranges)
   * 2. Anthropometric Measurements
   * 3. Laboratory Values
   * 4. Age-Specific Considerations
   * 5. Data Quality / Statistical Considerations
   */
  protected buildKnowledgeBase(): void {
    this.buildVitalSigns();
    this.buildAnthropometry();
    this.buildLabValues();
    this.buildAgeSpecific();
    this.buildStatisticalStandards();
  }

  // ----------------------------------------------------------
  // Section 1: Vital Signs — Adult Reference Ranges
  // ----------------------------------------------------------

  private buildVitalSigns(): void {
    const ahaBloodPressureCitation: Citation = {
      source: "American Heart Association",
      title: "2017 ACC/AHA Guideline for High Blood Pressure in Adults",
      year: 2017,
      url: "https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065",
    };

    this.addEntry(
      createEntry({
        id: "vs_blood_pressure_normal",
        category: "vital_signs",
        topic: "blood_pressure_normal_range",
        statement:
          "Normal adult systolic blood pressure: 90-120 mmHg, diastolic: 60-80 mmHg",
        rationale:
          "Based on AHA/ACC guidelines. Values outside this range may indicate hypertension, " +
          "hypotension, or measurement error.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [ahaBloodPressureCitation],
        conditions: ["age >= 18", "at_rest"],
        tags: ["blood_pressure", "systolic_bp", "diastolic_bp", "vital_signs"],
      })
    );

    this.addEntry(
      createEntry({
        id: "vs_heart_rate_normal",
        category: "vital_signs",
        topic: "heart_rate_normal_range",
        statement: "Normal adult resting heart rate: 60-100 bpm",
        rationale:
          "Standard clinical reference range. Athletes may have lower rates (40-60 bpm). " +
          "Values >100 indicate tachycardia, <60 bradycardia.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "American Heart Association",
            title: "Target Heart Rates Chart",
            year: 2021,
            url: "https://www.heart.org/en/healthy-living/fitness/fitness-basics/target-heart-rates",
          },
        ],
        conditions: ["age >= 18", "at_rest"],
        tags: ["heart_rate", "pulse", "vital_signs"],
      })
    );

    this.addEntry(
      createEntry({
        id: "vs_temperature_normal",
        category: "vital_signs",
        topic: "body_temperature_normal",
        statement:
          "Normal adult body temperature: 36.1-37.2\u00b0C (97.0-99.0\u00b0F)",
        rationale:
          "Core body temperature reference range. Varies by measurement site (oral, rectal, axillary). " +
          "Fever defined as >38.0\u00b0C (100.4\u00b0F).",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "WHO",
            title: "Temperature Measurement in Clinical Practice",
            year: 2018,
          },
        ],
        tags: ["temperature", "fever", "vital_signs"],
      })
    );

    this.addEntry(
      createEntry({
        id: "vs_respiratory_rate_normal",
        category: "vital_signs",
        topic: "respiratory_rate_normal",
        statement: "Normal adult respiratory rate: 12-20 breaths/minute",
        rationale:
          "Standard clinical reference. <12 indicates bradypnea, >20 tachypnea.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "American Thoracic Society",
            title: "Guidelines for Respiratory Rate Assessment",
            year: 2019,
          },
        ],
        conditions: ["age >= 18", "at_rest"],
        tags: ["respiratory_rate", "breathing", "vital_signs"],
      })
    );

    this.addEntry(
      createEntry({
        id: "vs_oxygen_saturation_normal",
        category: "vital_signs",
        topic: "oxygen_saturation_normal",
        statement: "Normal oxygen saturation (SpO2): 95-100%",
        rationale:
          "Pulse oximetry reference range. Values <95% may indicate hypoxemia. " +
          "<90% requires clinical intervention.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "British Thoracic Society",
            title: "Emergency Oxygen Guideline",
            year: 2017,
          },
        ],
        tags: ["oxygen_saturation", "spo2", "vital_signs"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 2: Anthropometric Measurements
  // ----------------------------------------------------------

  private buildAnthropometry(): void {
    this.addEntry(
      createEntry({
        id: "anthro_weight_adult",
        category: "anthropometry",
        topic: "adult_weight_range",
        statement: "Typical adult weight: 40-200 kg (88-440 lbs)",
        rationale:
          "Practical range for data validation. Extreme values likely indicate " +
          "measurement or data entry errors.",
        evidenceLevel: EvidenceLevel.EXPERT_OPINION,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "CDC",
            title: "Anthropometric Reference Data",
            year: 2020,
          },
        ],
        conditions: ["age >= 18"],
        tags: ["weight", "anthropometry"],
      })
    );

    this.addEntry(
      createEntry({
        id: "anthro_height_adult",
        category: "anthropometry",
        topic: "adult_height_range",
        statement: "Typical adult height: 140-210 cm (4'7\"-6'11\")",
        rationale:
          "Covers 99.9% of global adult population. Extreme outliers suggest data errors.",
        evidenceLevel: EvidenceLevel.EXPERT_OPINION,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "WHO",
            title: "Global Height Distribution Data",
            year: 2019,
          },
        ],
        conditions: ["age >= 18"],
        tags: ["height", "anthropometry"],
      })
    );

    this.addEntry(
      createEntry({
        id: "anthro_bmi_categories",
        category: "anthropometry",
        topic: "bmi_classification",
        statement:
          "BMI categories: Underweight <18.5, Normal 18.5-24.9, Overweight 25-29.9, Obese \u226530",
        rationale:
          "WHO international classification for adults. Used for health risk assessment.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "WHO",
            title: "BMI Classification",
            year: 2000,
            url: "https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight",
          },
        ],
        conditions: ["age >= 18"],
        contraindications: ["pregnancy", "athlete", "bodybuilder"],
        tags: ["bmi", "obesity", "anthropometry"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 3: Laboratory Values — Common Tests
  // ----------------------------------------------------------

  private buildLabValues(): void {
    this.addEntry(
      createEntry({
        id: "lab_glucose_fasting",
        category: "laboratory",
        topic: "fasting_glucose_normal",
        statement:
          "Normal fasting glucose: 70-100 mg/dL (3.9-5.6 mmol/L)",
        rationale:
          "American Diabetes Association criteria. 100-125 mg/dL indicates prediabetes, " +
          "\u2265126 mg/dL diabetes.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "American Diabetes Association",
            title: "Standards of Medical Care in Diabetes",
            year: 2023,
            doi: "10.2337/dc23-S002",
          },
        ],
        conditions: ["fasting >= 8_hours"],
        tags: ["glucose", "diabetes", "laboratory"],
      })
    );

    this.addEntry(
      createEntry({
        id: "lab_hba1c_normal",
        category: "laboratory",
        topic: "hba1c_normal_range",
        statement: "Normal HbA1c: <5.7%",
        rationale:
          "Reflects average blood glucose over 2-3 months. 5.7-6.4% indicates prediabetes, " +
          "\u22656.5% diabetes.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "American Diabetes Association",
            title: "Classification and Diagnosis of Diabetes",
            year: 2023,
          },
        ],
        tags: ["hba1c", "diabetes", "laboratory"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 4: Age-Specific Considerations
  // ----------------------------------------------------------

  private buildAgeSpecific(): void {
    this.addEntry(
      createEntry({
        id: "age_pediatric_ranges",
        category: "age_specific",
        topic: "pediatric_vital_signs",
        statement:
          "Pediatric vital signs differ significantly from adults and vary by age",
        rationale:
          "Children have higher heart rates, respiratory rates, and different BP ranges. " +
          "Age-specific references must be used.",
        evidenceLevel: EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "American Academy of Pediatrics",
            title: "Pediatric Vital Sign Normal Ranges",
            year: 2020,
          },
        ],
        conditions: ["age < 18"],
        tags: ["pediatric", "age_specific", "vital_signs"],
      })
    );

    this.addEntry(
      createEntry({
        id: "age_geriatric_considerations",
        category: "age_specific",
        topic: "geriatric_considerations",
        statement:
          "Geriatric patients (\u226565 years) may have different normal ranges and higher measurement variability",
        rationale:
          "Physiological changes with aging affect vital signs and lab values. " +
          "More lenient BP targets for elderly.",
        evidenceLevel: EvidenceLevel.COHORT_STUDY,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "American Geriatrics Society",
            title: "Clinical Guidelines for Older Adults",
            year: 2021,
          },
        ],
        conditions: ["age >= 65"],
        tags: ["geriatric", "elderly", "age_specific"],
      })
    );
  }

  // ----------------------------------------------------------
  // Section 5: Data Quality — Statistical Considerations
  // ----------------------------------------------------------

  private buildStatisticalStandards(): void {
    this.addEntry(
      createEntry({
        id: "stat_outlier_detection_iqr",
        category: "statistics",
        topic: "outlier_detection_iqr_method",
        statement:
          "IQR method: Outliers defined as values < Q1-1.5*IQR or > Q3+1.5*IQR",
        rationale:
          "Robust non-parametric method for outlier detection. Less sensitive to extreme values than z-score.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.HIGH,
        citations: [
          {
            source: "Tukey, J.W.",
            title: "Exploratory Data Analysis",
            year: 1977,
          },
        ],
        tags: ["outliers", "statistics", "data_quality"],
      })
    );

    this.addEntry(
      createEntry({
        id: "stat_missing_data_threshold",
        category: "statistics",
        topic: "missing_data_deletion_threshold",
        statement:
          "Variables with >20% missing data should be carefully evaluated before deletion",
        rationale:
          "High missingness may indicate systematic issues. Multiple imputation preferred over " +
          "deletion when possible.",
        evidenceLevel: EvidenceLevel.EXPERT_OPINION,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "Little & Rubin",
            title: "Statistical Analysis with Missing Data",
            year: 2019,
          },
        ],
        tags: ["missing_data", "statistics", "data_quality"],
      })
    );

    this.addEntry(
      createEntry({
        id: "clean_duplicate_resolution",
        category: "data_cleaning",
        topic: "duplicate_record_handling",
        statement:
          "For duplicate records, keep the most complete record or the one with most recent timestamp",
        rationale:
          "Preserves maximum information while removing redundancy. Timestamp priority assumes newer data is more accurate.",
        evidenceLevel: EvidenceLevel.BEST_PRACTICE,
        confidence: ConfidenceLevel.MEDIUM,
        citations: [
          {
            source: "FDA",
            title: "Data Integrity and Compliance Guidance",
            year: 2018,
          },
        ],
        tags: ["duplicates", "data_cleaning"],
      })
    );
  }

  // ----------------------------------------------------------
  // Domain-Specific Method
  // ----------------------------------------------------------

  /**
   * Get the reference range entry for a clinical field.
   *
   * Searches entries tagged with `field`, optionally filters by patient age
   * context, then returns the highest-confidence entry together with its
   * confidence and evidence-level string values.
   *
   * @param field   Clinical parameter name, e.g. `"systolic_bp"`, `"heart_rate"`.
   * @param context Optional patient context.  Recognised keys: `age` (number).
   * @returns A {@link ReferenceRange} object, or `undefined` if no match found.
   */
  getReferenceRange(
    field: string,
    context?: Record<string, unknown>
  ): ReferenceRange | undefined {
    let candidates = this.search({ tags: [field] });

    if (candidates.length === 0) {
      return undefined;
    }

    // Apply age-based filtering when context provides an age
    if (context) {
      const age = context["age"];
      if (typeof age === "number") {
        if (age < 18) {
          // For paediatric patients, prefer entries that do NOT require age >= 18
          const paediatricCandidates = candidates.filter(
            (e) =>
              e.tags.includes("pediatric") ||
              e.conditions.every((c) => !c.includes("age >= 18"))
          );
          if (paediatricCandidates.length > 0) {
            candidates = paediatricCandidates;
          }
        } else if (age >= 65) {
          // For geriatric patients, prefer geriatric-specific entries when available
          const geriatricCandidates = candidates.filter((e) =>
            e.tags.includes("geriatric")
          );
          if (geriatricCandidates.length > 0) {
            candidates = geriatricCandidates;
          }
        }
      }
    }

    if (candidates.length === 0) {
      return undefined;
    }

    // Return the entry with the highest confidence
    const best = candidates.slice().sort(
      (a, b) =>
        CONFIDENCE_ORDER.indexOf(a.confidence) -
        CONFIDENCE_ORDER.indexOf(b.confidence)
    )[0];

    return {
      source: best,
      confidence: best.confidence,
      evidenceLevel: best.evidenceLevel,
    };
  }
}
