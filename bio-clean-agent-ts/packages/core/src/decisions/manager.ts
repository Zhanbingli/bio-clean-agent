/**
 * @file decisions/manager.ts
 * @description Decision management for human-in-the-loop pipeline checkpoints.
 *
 * Provides:
 * - {@link DecisionContext}     – structured description of a single decision point
 * - {@link DecisionStrategy}    – abstract strategy interface
 * - {@link DecisionManager}     – orchestrates decision resolution via a strategy
 * - {@link MedicalDataDecisions} – factory for common biomedical decision contexts
 *
 * Ported from Python `decisions/manager.py`.
 */

// ---------------------------------------------------------------------------
// DecisionContext
// ---------------------------------------------------------------------------

/**
 * A single named option presented to a decision-maker.
 *
 * The `id` field must be unique within its parent {@link DecisionContext.options}
 * array and must match the value used in {@link DecisionContext.defaultOption}.
 */
export interface DecisionOption {
  /** Machine-readable identifier for this option. */
  id: string;
  /** Human-readable label displayed in UI / notifications. */
  label: string;
  /** Optional extended description shown as help text. */
  description?: string;
  /** Additional option-specific key-value metadata. */
  [key: string]: unknown;
}

/**
 * All the information a {@link DecisionStrategy} needs to resolve a decision.
 *
 * Instances are produced by factory methods on {@link MedicalDataDecisions}
 * and by callers of {@link DecisionManager.requestDecision}.
 *
 * @example
 * ```ts
 * const ctx = MedicalDataDecisions.missingValueStrategy(
 *   "systolic_bp", 120, 1000, "numeric"
 * );
 * const choice = await manager.requestDecision(
 *   ctx.jobId, ctx.stepName, ctx.question, ctx.options
 * );
 * ```
 */
export interface DecisionContext {
  /** Identifier of the job that raised this decision. */
  jobId: string;
  /** Name of the pipeline step that raised this decision. */
  stepName: string;
  /** Plain-language question posed to the decision-maker. */
  question: string;
  /** Ordered list of choices available to the decision-maker. */
  options: DecisionOption[];
  /**
   * Contextual data that helps the decision-maker choose
   * (e.g. data profiles, sample values, statistics).
   */
  metadata: Record<string, unknown>;
  /**
   * `id` of the option to select when no explicit choice is provided
   * (used by {@link AutoApproveStrategy} and as fallback).
   */
  defaultOption?: string;
}

// ---------------------------------------------------------------------------
// DecisionStrategy (abstract)
// ---------------------------------------------------------------------------

/**
 * Strategy interface for resolving a {@link DecisionContext}.
 *
 * Implement this interface to provide different resolution behaviours:
 * automatic approval, human interaction, LLM assistance, etc.
 *
 * @example
 * ```ts
 * class AlwaysFirstStrategy implements DecisionStrategy {
 *   decide(context: DecisionContext): DecisionOption {
 *     return context.options[0]!;
 *   }
 * }
 * ```
 */
export interface DecisionStrategy {
  /**
   * Resolve a decision and return the chosen option.
   *
   * @param context - The full decision context to resolve.
   * @returns The chosen {@link DecisionOption}.
   */
  decide(context: DecisionContext): DecisionOption;
}

// ---------------------------------------------------------------------------
// DecisionManager
// ---------------------------------------------------------------------------

/**
 * Orchestrates decision resolution for a running pipeline.
 *
 * The manager delegates to a pluggable {@link DecisionStrategy}, making it
 * easy to swap between auto-approve, LLM-assisted, and notification-based
 * behaviours without changing the pipeline code.
 *
 * @example
 * ```ts
 * const manager = new DecisionManager(new AutoApproveStrategy());
 * const choice = manager.requestDecision(
 *   "job-123",
 *   "handle_missing_values",
 *   "How should missing values in 'age' be handled?",
 *   [
 *     { id: "median", label: "Impute with median" },
 *     { id: "drop",   label: "Drop rows" },
 *   ],
 *   { missing_count: 42, total_count: 1000 },
 *   "median"
 * );
 * ```
 */
export class DecisionManager {
  private _strategy: DecisionStrategy;

  constructor(strategy: DecisionStrategy) {
    this._strategy = strategy;
  }

  /**
   * Replace the active decision strategy at runtime.
   *
   * @param strategy - The new strategy to use for subsequent decisions.
   */
  setStrategy(strategy: DecisionStrategy): void {
    this._strategy = strategy;
  }

  /**
   * Raise a decision checkpoint and return the chosen option.
   *
   * Constructs a {@link DecisionContext} and delegates resolution to the
   * configured {@link DecisionStrategy}.
   *
   * @param jobId         - Identifier of the owning job.
   * @param stepName      - Name of the pipeline step raising this decision.
   * @param question      - Plain-language question for the decision-maker.
   * @param options       - Available choices (at least one required).
   * @param metadata      - Optional context data forwarded to the strategy.
   * @param defaultOption - Optional `id` of the default choice.
   * @returns The {@link DecisionOption} selected by the strategy.
   */
  requestDecision(
    jobId: string,
    stepName: string,
    question: string,
    options: DecisionOption[],
    metadata: Record<string, unknown> = {},
    defaultOption?: string
  ): DecisionOption {
    const context: DecisionContext = {
      jobId,
      stepName,
      question,
      options,
      metadata,
      defaultOption,
    };

    return this._strategy.decide(context);
  }
}

// ---------------------------------------------------------------------------
// MedicalDataDecisions
// ---------------------------------------------------------------------------

/**
 * Static factory producing {@link DecisionContext} objects for the most
 * common biomedical data-quality decision points.
 *
 * Each method returns a fully populated context ready to be passed to
 * {@link DecisionManager.requestDecision} (or consumed directly by a strategy).
 */
export class MedicalDataDecisions {
  /**
   * Build a decision context for handling missing values in a column.
   *
   * @param columnName   - Name of the column with missing values.
   * @param missingCount - Number of records with a missing value.
   * @param totalCount   - Total number of records in the dataset.
   * @param columnType   - Data type of the column (e.g. `"numeric"`, `"categorical"`).
   * @returns A {@link DecisionContext} with standard imputation options.
   */
  static missingValueStrategy(
    columnName: string,
    missingCount: number,
    totalCount: number,
    columnType: string
  ): DecisionContext {
    const missingRate =
      totalCount > 0
        ? ((missingCount / totalCount) * 100).toFixed(1)
        : "0.0";

    const options: DecisionOption[] = [
      {
        id: "median_impute",
        label: "Impute with median",
        description:
          "Replace missing values with the column median (robust for skewed data)",
      },
      {
        id: "mean_impute",
        label: "Impute with mean",
        description:
          "Replace missing values with the column mean (suitable for symmetric distributions)",
      },
      {
        id: "mode_impute",
        label: "Impute with mode",
        description:
          "Replace missing values with the most frequent value (suitable for categorical columns)",
      },
      {
        id: "drop_rows",
        label: "Drop rows with missing values",
        description:
          "Remove all records that have a missing value in this column",
      },
      {
        id: "keep_missing",
        label: "Keep missing values",
        description: "Leave missing values as-is and flag them for review",
      },
    ];

    return {
      jobId: "",
      stepName: "handle_missing_values",
      question:
        `Column "${columnName}" has ${missingCount} missing values ` +
        `(${missingRate}% of ${totalCount} records, type: ${columnType}). ` +
        `How should missing values be handled?`,
      options,
      metadata: {
        column_name: columnName,
        missing_count: missingCount,
        total_count: totalCount,
        missing_rate: missingCount / Math.max(totalCount, 1),
        column_type: columnType,
      },
      defaultOption: columnType === "categorical" ? "mode_impute" : "median_impute",
    };
  }

  /**
   * Build a decision context for resolving detected outliers in a column.
   *
   * @param columnName    - Name of the column containing outliers.
   * @param outlierCount  - Number of outlier records detected.
   * @param outlierValues - Sample outlier values for context.
   * @returns A {@link DecisionContext} with standard outlier-handling options.
   */
  static outlierDetection(
    columnName: string,
    outlierCount: number,
    outlierValues: unknown[]
  ): DecisionContext {
    const sampleValues = outlierValues.slice(0, 5);

    const options: DecisionOption[] = [
      {
        id: "winsorize",
        label: "Winsorize (cap at percentile boundaries)",
        description:
          "Replace outlier values with the nearest boundary value (1st / 99th percentile)",
      },
      {
        id: "remove_outliers",
        label: "Remove outlier records",
        description: "Delete rows containing outlier values",
      },
      {
        id: "flag_only",
        label: "Flag outliers for review",
        description:
          "Mark outlier rows with a flag column without modifying the values",
      },
      {
        id: "keep_outliers",
        label: "Keep outliers unchanged",
        description: "Treat outlier values as valid and continue without modification",
      },
    ];

    return {
      jobId: "",
      stepName: "handle_outliers",
      question:
        `Column "${columnName}" has ${outlierCount} potential outliers. ` +
        `Sample values: [${sampleValues.join(", ")}]. ` +
        `How should these outliers be handled?`,
      options,
      metadata: {
        column_name: columnName,
        outlier_count: outlierCount,
        sample_outlier_values: sampleValues,
      },
      defaultOption: "flag_only",
    };
  }

  /**
   * Build a decision context for resolving duplicate records.
   *
   * @param duplicateCount - Number of duplicate records detected.
   * @param totalCount     - Total number of records in the dataset.
   * @param keyColumns     - Columns used to identify duplicates.
   * @returns A {@link DecisionContext} with standard deduplication options.
   */
  static duplicateRecords(
    duplicateCount: number,
    totalCount: number,
    keyColumns: string[]
  ): DecisionContext {
    const dupRate =
      totalCount > 0
        ? ((duplicateCount / totalCount) * 100).toFixed(1)
        : "0.0";

    const options: DecisionOption[] = [
      {
        id: "keep_first",
        label: "Keep first occurrence",
        description: "Retain the first record from each duplicate group and remove the rest",
      },
      {
        id: "keep_last",
        label: "Keep last occurrence",
        description: "Retain the most recent record from each duplicate group and remove the rest",
      },
      {
        id: "keep_most_complete",
        label: "Keep most complete record",
        description:
          "Retain the record with the fewest missing values from each duplicate group",
      },
      {
        id: "flag_review",
        label: "Flag for manual review",
        description: "Mark duplicate records for human review without automatic removal",
      },
      {
        id: "remove_all_duplicates",
        label: "Remove all duplicate records",
        description:
          "Delete all records that have a duplicate, keeping none from each group",
      },
    ];

    return {
      jobId: "",
      stepName: "handle_duplicates",
      question:
        `Found ${duplicateCount} duplicate records (${dupRate}% of ${totalCount}) ` +
        `based on key columns: [${keyColumns.join(", ")}]. ` +
        `How should duplicate records be resolved?`,
      options,
      metadata: {
        duplicate_count: duplicateCount,
        total_count: totalCount,
        duplicate_rate: duplicateCount / Math.max(totalCount, 1),
        key_columns: keyColumns,
      },
      defaultOption: "keep_first",
    };
  }
}
