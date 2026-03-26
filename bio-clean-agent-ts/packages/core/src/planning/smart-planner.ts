/**
 * @file planning/smart-planner.ts
 * @description Evidence-based execution plan generator for Bio Clean jobs.
 *
 * {@link SmartPlanner} uses the knowledge base trio
 * ({@link MedicalStandards}, {@link EvidenceBase}, {@link ValidationRules})
 * to assemble a domain-aware {@link ExecutionPlan} from high-level objectives
 * and an optional data profile.
 *
 * Ported from Python `planning/smart_planner.py`.
 */

import {
  MedicalStandards,
  EvidenceBase,
  ValidationRules,
} from "../knowledge/index.js";
import type {
  PlanStep,
  ExecutionPlan,
  TaskPriority,
} from "../schemas/planning.js";

// ---------------------------------------------------------------------------
// Internal helper types
// ---------------------------------------------------------------------------

/**
 * Mutable draft of an {@link ExecutionPlan} used during plan construction.
 * Fields marked optional are populated progressively by the builder methods.
 */
interface PlanDraft {
  jobId: string;
  dataType: string;
  objectives: string[];
  steps: PlanStep[];
  detectedIssues: string[];
  recommendations: string[];
  warnings: string[];
  estimatedQualityImprovement?: number | null;
  estimatedDataLoss?: number | null;
}

/**
 * Optional data profile passed to {@link SmartPlanner.createPlan}.
 *
 * Keys correspond to column names; values are per-column statistics.
 */
export interface DataProfile {
  /** Total number of rows in the dataset. */
  row_count?: number;
  /** Total number of columns in the dataset. */
  column_count?: number;
  /** Per-column statistics map. */
  columns?: Record<string, ColumnProfile>;
  /** Any extra profile fields forwarded from the profiler. */
  [key: string]: unknown;
}

/**
 * Per-column statistics collected during data profiling.
 */
export interface ColumnProfile {
  /** Data type string (e.g. `"numeric"`, `"categorical"`, `"datetime"`). */
  dtype?: string;
  /** Fraction of rows with a missing value in this column [0, 1]. */
  missing_rate?: number;
  /** Number of rows with a missing value. */
  missing_count?: number;
  /** Number of detected outlier values. */
  outlier_count?: number;
  /** Sample outlier values for context. */
  outlier_values?: unknown[];
  /** Number of duplicate records when this column is used as a key. */
  duplicate_count?: number;
  /** `true` when the column appears to be a potential join / key column. */
  is_key_column?: boolean;
  /** Any extra per-column statistics. */
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// SmartPlanner
// ---------------------------------------------------------------------------

/**
 * Generates evidence-based {@link ExecutionPlan} objects for Bio Clean jobs.
 *
 * The planner follows a deterministic six-phase pipeline:
 * 1. Add profiling steps (always).
 * 2. Analyse the data profile (when a profile is supplied).
 * 3. Create cleaning steps from the objectives.
 * 4. Add verification steps.
 * 5. Optimise step order.
 * 6. Estimate outcomes (quality improvement, data loss).
 *
 * @example
 * ```ts
 * const planner = new SmartPlanner();
 * const plan = planner.createPlan(
 *   "job-uuid",
 *   "clinical_trial",
 *   ["Remove duplicates", "Handle missing values"],
 *   { row_count: 5000, columns: { age: { missing_rate: 0.08 } } }
 * );
 * ```
 */
export class SmartPlanner {
  private readonly _medicalStandards: MedicalStandards;
  private readonly _evidenceBase: EvidenceBase;
  private readonly _validationRules: ValidationRules;

  constructor() {
    this._medicalStandards = new MedicalStandards();
    this._evidenceBase = new EvidenceBase();
    this._validationRules = new ValidationRules();
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  /**
   * Generate a complete execution plan for a cleaning job.
   *
   * @param jobId       - UUID of the job this plan is generated for.
   * @param dataType    - Domain type of the dataset (e.g. `"clinical_trial"`).
   * @param objectives  - High-level cleaning objectives provided by the user.
   * @param dataProfile - Optional profiling statistics; used to add targeted steps.
   * @returns A fully populated {@link ExecutionPlan}.
   */
  createPlan(
    jobId: string,
    dataType: string,
    objectives: string[],
    dataProfile?: DataProfile
  ): ExecutionPlan {
    const draft: PlanDraft = {
      jobId,
      dataType,
      objectives: [...objectives],
      steps: [],
      detectedIssues: [],
      recommendations: [],
      warnings: [],
      estimatedQualityImprovement: null,
      estimatedDataLoss: null,
    };

    this._addProfilingSteps(draft);

    if (dataProfile !== undefined) {
      this._analyzeDataProfile(draft, dataProfile);
    }

    this._createCleaningSteps(draft, objectives);
    this._addVerificationSteps(draft);
    this._optimizePlanOrder(draft);
    this._estimateOutcomes(draft);

    return this._buildExecutionPlan(draft);
  }

  // ------------------------------------------------------------------
  // Phase 1: Profiling steps
  // ------------------------------------------------------------------

  /**
   * Add mandatory data-profiling steps to the plan draft.
   *
   * These steps always run first so that downstream steps can rely on
   * up-to-date statistics being present in the execution context.
   *
   * @param draft - Mutable plan draft being built.
   */
  private _addProfilingSteps(draft: PlanDraft): void {
    const steps: PlanStep[] = [
      {
        id: "step-001",
        name: "Initial data profiling",
        description:
          "Compute basic statistics (row/column counts, missing rates, " +
          "type inference, cardinalities) for all columns in the dataset.",
        step_type: "validation",
        priority: "critical" as TaskPriority,
        rationale:
          "Profiling is required to inform evidence-based cleaning decisions. " +
          "Without baseline statistics, downstream steps cannot be optimised.",
        evidence_based: true,
        evidence_summary:
          "Baseline profiling is a universally accepted prerequisite for " +
          "data cleaning in biomedical informatics.",
        depends_on: [],
        required: true,
        estimated_duration: 30,
        parameters: {},
        risk_level: "low",
        reversible: true,
      },
      {
        id: "step-002",
        name: "Schema and type validation",
        description:
          "Verify that column names, data types, and structural constraints " +
          "match the expected schema for this dataset type.",
        step_type: "validation",
        priority: "critical" as TaskPriority,
        rationale:
          "Type and schema mismatches can cause silent failures in downstream " +
          "processing steps.",
        evidence_based: true,
        evidence_summary:
          "Schema validation is a mandatory pre-condition per FDA data " +
          "integrity guidance (2018).",
        depends_on: ["step-001"],
        required: true,
        estimated_duration: 15,
        parameters: {},
        risk_level: "low",
        reversible: true,
      },
    ];

    draft.steps.push(...steps);
  }

  // ------------------------------------------------------------------
  // Phase 2: Profile analysis
  // ------------------------------------------------------------------

  /**
   * Analyse the data profile and add issue-specific cleaning steps.
   *
   * Issues detected here are appended to {@link PlanDraft.detectedIssues}
   * and targeted steps are inserted before the final verification phase.
   *
   * @param draft   - Mutable plan draft being built.
   * @param profile - Data profiling statistics for this dataset.
   */
  private _analyzeDataProfile(draft: PlanDraft, profile: DataProfile): void {
    const columns = profile.columns ?? {};
    let stepIndex = draft.steps.length + 1;

    const highMissingColumns: string[] = [];
    const outlierColumns: string[] = [];
    let hasDuplicates = false;
    let totalDuplicates = 0;

    for (const [colName, colProfile] of Object.entries(columns)) {
      const missingRate = colProfile.missing_rate ?? 0;

      // -- Missing values --
      if (missingRate > 0) {
        const issue =
          `Column "${colName}" has ${(missingRate * 100).toFixed(1)}% ` +
          `missing values (${colProfile.missing_count ?? "unknown"} records).`;
        draft.detectedIssues.push(issue);

        if (missingRate > 0.2) {
          highMissingColumns.push(colName);
          draft.warnings.push(
            `Column "${colName}" has >20% missing data. ` +
              "Evaluate carefully before imputation."
          );
        }

        const recommendation = this._evidenceBase.getCleaningRecommendation(
          "missing_data",
          { missing_rate: missingRate }
        );
        if (recommendation !== undefined) {
          const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
          draft.steps.push({
            id: stepId,
            name: `Handle missing values: ${colName}`,
            description:
              `Apply evidence-based imputation strategy to column "${colName}". ` +
              recommendation.statement,
            step_type: "cleaning",
            priority: missingRate > 0.1 ? "high" : ("medium" as TaskPriority),
            rationale: recommendation.rationale,
            evidence_based: true,
            evidence_summary: recommendation.statement,
            depends_on: ["step-001", "step-002"],
            required: false,
            estimated_duration: 10,
            parameters: { column: colName, missing_rate: missingRate },
            risk_level: missingRate > 0.2 ? "medium" : "low",
            reversible: true,
          });
          stepIndex++;
        }
      }

      // -- Outliers --
      const outlierCount = colProfile.outlier_count ?? 0;
      if (outlierCount > 0) {
        outlierColumns.push(colName);
        draft.detectedIssues.push(
          `Column "${colName}" has ${outlierCount} potential outliers.`
        );

        const recommendation = this._evidenceBase.getCleaningRecommendation(
          "outliers",
          {}
        );
        if (recommendation !== undefined) {
          const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
          draft.steps.push({
            id: stepId,
            name: `Handle outliers: ${colName}`,
            description:
              `Detect and treat outliers in column "${colName}". ` +
              recommendation.statement,
            step_type: "cleaning",
            priority: "medium" as TaskPriority,
            rationale: recommendation.rationale,
            evidence_based: true,
            evidence_summary: recommendation.statement,
            depends_on: ["step-001", "step-002"],
            required: false,
            estimated_duration: 15,
            parameters: {
              column: colName,
              outlier_count: outlierCount,
              sample_values: colProfile.outlier_values ?? [],
            },
            risk_level: "medium",
            reversible: true,
          });
          stepIndex++;
        }
      }

      // -- Duplicates --
      const dupCount = colProfile.duplicate_count ?? 0;
      if (dupCount > 0 && (colProfile.is_key_column === true)) {
        hasDuplicates = true;
        totalDuplicates = Math.max(totalDuplicates, dupCount);
      }
    }

    // Add a single consolidated duplicate-handling step when needed.
    if (hasDuplicates) {
      const rowCount = profile.row_count ?? 0;
      draft.detectedIssues.push(
        `Found approximately ${totalDuplicates} duplicate records in the dataset.`
      );

      const recommendation = this._evidenceBase.getCleaningRecommendation(
        "duplicates",
        {}
      );

      const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
      draft.steps.push({
        id: stepId,
        name: "Remove duplicate records",
        description:
          (recommendation?.statement ??
            "Identify and remove duplicate records.") +
          ` Detected ~${totalDuplicates} duplicates in ${rowCount} rows.`,
        step_type: "cleaning",
        priority: "high" as TaskPriority,
        rationale:
          recommendation?.rationale ??
          "Duplicate records bias analyses and inflate sample sizes.",
        evidence_based: recommendation !== undefined,
        evidence_summary: recommendation?.statement ?? null,
        depends_on: ["step-001", "step-002"],
        required: true,
        estimated_duration: 20,
        parameters: { estimated_duplicate_count: totalDuplicates },
        risk_level: "medium",
        reversible: true,
      });
      stepIndex++;
    }

    // Global recommendations from the knowledge base.
    if (highMissingColumns.length > 0) {
      draft.recommendations.push(
        `Consider collecting complete data for: ${highMissingColumns.join(", ")}. ` +
          "High missingness reduces statistical power."
      );
    }

    if (outlierColumns.length > 2) {
      draft.recommendations.push(
        "Multiple columns contain outliers. Consider running a sensitivity " +
          "analysis with and without outliers to assess their impact."
      );
    }
  }

  // ------------------------------------------------------------------
  // Phase 3: Objective-driven cleaning steps
  // ------------------------------------------------------------------

  /**
   * Map high-level user objectives to concrete cleaning steps.
   *
   * @param draft      - Mutable plan draft being built.
   * @param objectives - User-supplied high-level objectives.
   */
  private _createCleaningSteps(
    draft: PlanDraft,
    objectives: string[]
  ): void {
    // Use the current step count to assign sequential IDs.
    let stepIndex = draft.steps.length + 1;

    const objectiveLower = objectives.map((o) => o.toLowerCase());

    // Normalisation
    if (
      objectiveLower.some(
        (o) => o.includes("normaliz") || o.includes("standardiz") || o.includes("transform")
      )
    ) {
      const recommendation = this._evidenceBase.getCleaningRecommendation(
        "transformation",
        {}
      );
      const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
      draft.steps.push({
        id: stepId,
        name: "Normalise and standardise columns",
        description:
          "Apply appropriate normalisation or standardisation transformations " +
          "(z-score, log, min-max) based on column distribution properties.",
        step_type: "transformation",
        priority: "medium" as TaskPriority,
        rationale:
          recommendation?.rationale ??
          "Standardisation enables fair comparison across variables with different units.",
        evidence_based: recommendation !== undefined,
        evidence_summary: recommendation?.statement ?? null,
        depends_on: ["step-001"],
        required: false,
        estimated_duration: 20,
        parameters: { strategy: "auto" },
        risk_level: "low",
        reversible: true,
      });
      stepIndex++;
    }

    // Value range validation
    if (
      objectiveLower.some(
        (o) =>
          o.includes("valid") ||
          o.includes("range") ||
          o.includes("plausib")
      )
    ) {
      const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
      draft.steps.push({
        id: stepId,
        name: "Validate clinical value ranges",
        description:
          "Check all clinical variables against evidence-based reference " +
          "ranges (vital signs, lab values, anthropometrics) from medical standards.",
        step_type: "validation",
        priority: "high" as TaskPriority,
        rationale:
          "Clinically implausible values indicate data-entry errors or " +
          "instrument malfunction and must be flagged before analysis.",
        evidence_based: true,
        evidence_summary:
          "Biological plausibility checks are recommended before statistical " +
          "outlier methods (van der Loo & de Jonge, 2018).",
        depends_on: ["step-001", "step-002"],
        required: false,
        estimated_duration: 25,
        parameters: { data_type: draft.dataType },
        risk_level: "low",
        reversible: true,
      });
      stepIndex++;
    }

    // Deduplication (if not already added from profile analysis)
    if (
      objectiveLower.some(
        (o) =>
          o.includes("dedup") ||
          o.includes("duplicate") ||
          o.includes("unique")
      )
    ) {
      const alreadyHasDedupe = draft.steps.some(
        (s) => s.name.toLowerCase().includes("duplicate")
      );

      if (!alreadyHasDedupe) {
        const recommendation = this._evidenceBase.getCleaningRecommendation(
          "duplicates",
          {}
        );
        const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
        draft.steps.push({
          id: stepId,
          name: "Remove duplicate records",
          description:
            recommendation?.statement ??
            "Identify and remove exact and partial duplicate records from the dataset.",
          step_type: "cleaning",
          priority: "high" as TaskPriority,
          rationale:
            recommendation?.rationale ??
            "Duplicate records bias downstream statistical analyses.",
          evidence_based: recommendation !== undefined,
          evidence_summary: recommendation?.statement ?? null,
          depends_on: ["step-001", "step-002"],
          required: true,
          estimated_duration: 20,
          parameters: {},
          risk_level: "medium",
          reversible: true,
        });
        stepIndex++;
      }
    }

    // Generic missing-value handling (if not already added from profile)
    if (
      objectiveLower.some(
        (o) =>
          o.includes("missing") ||
          o.includes("impute") ||
          o.includes("null") ||
          o.includes("na ")
      )
    ) {
      const alreadyHasMissing = draft.steps.some(
        (s) =>
          s.name.toLowerCase().includes("missing") ||
          s.name.toLowerCase().includes("impute")
      );

      if (!alreadyHasMissing) {
        const recommendation = this._evidenceBase.getCleaningRecommendation(
          "missing_data",
          {}
        );
        const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
        draft.steps.push({
          id: stepId,
          name: "Handle missing values",
          description:
            "Apply evidence-based imputation strategy to columns with missing data. " +
            (recommendation?.statement ?? ""),
          step_type: "cleaning",
          priority: "high" as TaskPriority,
          rationale:
            recommendation?.rationale ??
            "Missing data reduces statistical power and may introduce bias.",
          evidence_based: recommendation !== undefined,
          evidence_summary: recommendation?.statement ?? null,
          depends_on: ["step-001", "step-002"],
          required: false,
          estimated_duration: 30,
          parameters: {},
          risk_level: "low",
          reversible: true,
        });
        stepIndex++;
      }
    }

    // Data type coercion / format standardisation
    if (
      objectiveLower.some(
        (o) =>
          o.includes("format") ||
          o.includes("type") ||
          o.includes("coerce") ||
          o.includes("parse")
      )
    ) {
      const stepId = `step-${String(stepIndex).padStart(3, "0")}`;
      draft.steps.push({
        id: stepId,
        name: "Standardise data formats",
        description:
          "Coerce columns to canonical formats: ISO 8601 dates, standardised " +
          "categorical codes, and consistent numeric representations.",
        step_type: "transformation",
        priority: "medium" as TaskPriority,
        rationale:
          "Inconsistent formats cause parse failures and join mismatches " +
          "in downstream pipelines.",
        evidence_based: false,
        evidence_summary: null,
        depends_on: ["step-001", "step-002"],
        required: false,
        estimated_duration: 15,
        parameters: {},
        risk_level: "low",
        reversible: true,
      });
      stepIndex++;
    }
  }

  // ------------------------------------------------------------------
  // Phase 4: Verification steps
  // ------------------------------------------------------------------

  /**
   * Append post-cleaning verification steps to the plan draft.
   *
   * @param draft - Mutable plan draft being built.
   */
  private _addVerificationSteps(draft: PlanDraft): void {
    // Determine the last step ID to use as a dependency.
    const lastStepId =
      draft.steps.length > 0
        ? draft.steps[draft.steps.length - 1]!.id
        : "step-002";

    // Assign the next available step IDs.
    const verifyStepIndex = draft.steps.length + 1;
    const finalStepIndex = verifyStepIndex + 1;

    draft.steps.push({
      id: `step-${String(verifyStepIndex).padStart(3, "0")}`,
      name: "Post-cleaning quality assessment",
      description:
        "Re-run data quality metrics after cleaning to quantify improvement " +
        "and confirm that issues detected during profiling have been resolved.",
      step_type: "verification",
      priority: "high" as TaskPriority,
      rationale:
        "Post-cleaning assessment provides objective evidence that the " +
        "pipeline achieved its quality objectives.",
      evidence_based: true,
      evidence_summary:
        "Verification is a mandatory step in FDA data integrity workflows.",
      depends_on: [lastStepId],
      required: true,
      estimated_duration: 20,
      parameters: {},
      risk_level: "low",
      reversible: true,
    });

    draft.steps.push({
      id: `step-${String(finalStepIndex).padStart(3, "0")}`,
      name: "Generate cleaning report",
      description:
        "Produce a structured report summarising all cleaning operations, " +
        "records modified, values imputed, and quality metrics before and after.",
      step_type: "verification",
      priority: "medium" as TaskPriority,
      rationale:
        "A cleaning report is required for regulatory submissions and " +
        "provides an audit trail for reproducibility.",
      evidence_based: true,
      evidence_summary: "Audit trails are mandated by FDA 21 CFR Part 11.",
      depends_on: [`step-${String(verifyStepIndex).padStart(3, "0")}`],
      required: true,
      estimated_duration: 10,
      parameters: {},
      risk_level: "low",
      reversible: true,
    });
  }

  // ------------------------------------------------------------------
  // Phase 5: Step order optimisation
  // ------------------------------------------------------------------

  /**
   * Reorder steps so that critical and high-priority steps run earlier.
   *
   * The sort is stable (preserving original insertion order among equal-
   * priority steps) and respects the type ordering:
   * `validation` < `cleaning` < `transformation` < `verification`.
   *
   * @param draft - Mutable plan draft to sort in-place.
   */
  private _optimizePlanOrder(draft: PlanDraft): void {
    const priorityOrder: Record<TaskPriority, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
    };

    const typeOrder: Record<string, number> = {
      validation: 0,
      cleaning: 1,
      transformation: 2,
      verification: 3,
    };

    draft.steps.sort((a, b) => {
      // Primary: step type
      const typeA = typeOrder[a.step_type] ?? 99;
      const typeB = typeOrder[b.step_type] ?? 99;
      if (typeA !== typeB) return typeA - typeB;

      // Secondary: priority
      const priA = priorityOrder[a.priority] ?? 99;
      const priB = priorityOrder[b.priority] ?? 99;
      return priA - priB;
    });

    // Re-assign sequential IDs after reordering.
    draft.steps.forEach((step, idx) => {
      step.id = `step-${String(idx + 1).padStart(3, "0")}`;
    });

    // Rebuild dependency references to use new IDs.
    // After re-ordering, all validation steps should precede cleaning steps.
    // Rebuild depends_on for cleaning/transformation/verification steps
    // to depend on all validation steps (simplistic but safe).
    const validationIds = draft.steps
      .filter((s) => s.step_type === "validation")
      .map((s) => s.id);

    for (const step of draft.steps) {
      if (step.step_type !== "validation") {
        // Repoint to all completed validation steps if the original deps were
        // the old step-001 / step-002 placeholders.
        if (
          step.depends_on.some(
            (dep) => dep === "step-001" || dep === "step-002"
          )
        ) {
          step.depends_on = [...validationIds];
        }
      }
    }
  }

  // ------------------------------------------------------------------
  // Phase 6: Outcome estimation
  // ------------------------------------------------------------------

  /**
   * Estimate overall quality improvement and data loss fraction.
   *
   * Uses simple heuristics based on the number and types of steps in the plan.
   *
   * @param draft - Mutable plan draft to annotate with estimates.
   */
  private _estimateOutcomes(draft: PlanDraft): void {
    const cleaningSteps = draft.steps.filter(
      (s) => s.step_type === "cleaning"
    ).length;

    const totalSteps = draft.steps.length;

    if (totalSteps === 0) {
      draft.estimatedQualityImprovement = null;
      draft.estimatedDataLoss = null;
      return;
    }

    // Quality improvement: each cleaning step contributes ~5-8 pp.
    const baseImprovement = Math.min(0.05 + cleaningSteps * 0.07, 0.5);
    draft.estimatedQualityImprovement = parseFloat(baseImprovement.toFixed(2));

    // Data loss: only steps with risk_level !== "low" contribute.
    const riskySteps = draft.steps.filter(
      (s) => s.risk_level !== "low"
    ).length;
    const estimatedLoss = Math.min(riskySteps * 0.02, 0.15);
    draft.estimatedDataLoss = parseFloat(estimatedLoss.toFixed(3));

    // Add a warning when data loss is non-trivial.
    if (estimatedLoss > 0.05) {
      draft.warnings.push(
        `Estimated data loss is ~${(estimatedLoss * 100).toFixed(1)}%. ` +
          "Review cleaning steps for high-risk operations."
      );
    }
  }

  // ------------------------------------------------------------------
  // Build the final ExecutionPlan
  // ------------------------------------------------------------------

  /**
   * Convert the mutable {@link PlanDraft} into an immutable {@link ExecutionPlan}.
   *
   * @param draft - Completed plan draft.
   * @returns A validated {@link ExecutionPlan}.
   */
  private _buildExecutionPlan(draft: PlanDraft): ExecutionPlan {
    return {
      job_id: draft.jobId,
      data_type: draft.dataType,
      objectives: draft.objectives,
      steps: draft.steps,
      detected_issues: draft.detectedIssues,
      recommendations: draft.recommendations,
      warnings: draft.warnings,
      estimated_quality_improvement: draft.estimatedQualityImprovement,
      estimated_data_loss: draft.estimatedDataLoss,
    };
  }
}
