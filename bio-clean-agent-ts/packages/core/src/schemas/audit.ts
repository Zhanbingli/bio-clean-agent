/**
 * @file audit.ts
 * @description Zod schemas for FDA 21 CFR Part 11-compliant audit trail records.
 * Every destructive or modifying data operation must produce an {@link AuditEntry}
 * and, for field-level changes, a {@link DataLineage} record.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

/**
 * Category of data operation performed.
 *
 * | Value            | Description                                           |
 * |------------------|-------------------------------------------------------|
 * | `validation`     | Read-only check; no data is modified                  |
 * | `deletion`       | One or more records or fields are removed             |
 * | `imputation`     | Missing or invalid values are filled algorithmically  |
 * | `transformation` | Values are transformed (normalisation, encoding, etc.)|
 * | `flagging`       | Records are annotated but not modified                |
 */
export const OperationTypeSchema = z
  .enum(["validation", "deletion", "imputation", "transformation", "flagging"])
  .describe("Category of data operation captured in the audit trail");

export type OperationType = z.infer<typeof OperationTypeSchema>;

/**
 * Severity level of an audit event, used for risk classification and alerting.
 *
 * | Value      | Description                                          |
 * |------------|------------------------------------------------------|
 * | `critical` | Potentially regulatory-non-compliant operation       |
 * | `high`     | Significant data modification requiring review       |
 * | `medium`   | Moderate modification; normal cleaning activity      |
 * | `low`      | Minor or reversible change                           |
 * | `info`     | Informational; no data modification                  |
 */
export const SeverityLevelSchema = z
  .enum(["critical", "high", "medium", "low", "info"])
  .describe("Severity classification of the audit event");

export type SeverityLevel = z.infer<typeof SeverityLevelSchema>;

// ---------------------------------------------------------------------------
// AuditEntry
// ---------------------------------------------------------------------------

/**
 * Immutable record of a single data operation, written to the audit log.
 *
 * Designed to satisfy FDA 21 CFR Part 11 requirements:
 * - Who performed the action (`user`)
 * - What was done (`action`, `operation`)
 * - When it happened (`timestamp`)
 * - How many records were affected (`records_affected`)
 * - Why it was done (`reason`, `evidence_id`)
 *
 * @example
 * ```ts
 * const entry = AuditEntrySchema.parse({
 *   operation: "imputation",
 *   user: "pipeline:planner-agent",
 *   action: "Imputed missing 'age' values with column median",
 *   records_affected: 42,
 *   parameters: { strategy: "median", column: "age" },
 *   reason: "12 % missing rate detected in profiling",
 * });
 * ```
 */
export const AuditEntrySchema = z
  .object({
    /**
     * ISO 8601 timestamp when the operation was executed.
     * Defaults to the current moment.
     */
    timestamp: z
      .string()
      .datetime()
      .default(() => new Date().toISOString())
      .describe("Operation execution timestamp (ISO 8601)"),

    /** Category of the data operation. */
    operation: OperationTypeSchema,

    /**
     * Identity of the actor that performed the operation.
     * May be a human user ID, a service account, or an agent identifier
     * (e.g. `"pipeline:cleaner-agent"`).
     */
    user: z
      .string()
      .min(1)
      .describe("Actor identity – human user ID or agent identifier"),

    /** Human-readable description of the specific action taken. */
    action: z
      .string()
      .min(1)
      .describe("Human-readable description of the action performed"),

    /** Number of data records affected by the operation. */
    records_affected: z
      .number()
      .int()
      .nonnegative()
      .describe("Count of records affected by the operation"),

    /**
     * Parameters used to execute the operation
     * (e.g. `{ strategy: "median", column: "age", threshold: 3.0 }`).
     */
    parameters: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Execution parameters for the operation"),

    /**
     * Reference to an external evidence document (e.g. a literature DOI,
     * a knowledge-base rule ID, or a profiling report artifact ID).
     */
    evidence_id: z
      .string()
      .nullable()
      .optional()
      .describe("External evidence document identifier"),

    /**
     * Justification for performing the operation.
     * Required for `deletion` and `critical`-severity operations.
     */
    reason: z
      .string()
      .nullable()
      .optional()
      .describe("Justification for the operation"),
  })
  .describe("Immutable FDA-compliant audit record for a single data operation");

export type AuditEntry = z.infer<typeof AuditEntrySchema>;

// ---------------------------------------------------------------------------
// DataLineage
// ---------------------------------------------------------------------------

/**
 * Field-level provenance record capturing the before/after state of a
 * single cell value change.
 *
 * One {@link AuditEntry} may produce many `DataLineage` records (one per
 * modified cell).  Together they form a complete data lineage graph that
 * supports full reproducibility and rollback.
 *
 * @example
 * ```ts
 * const lineage = DataLineageSchema.parse({
 *   record_id: "patient-00142",
 *   field_name: "age",
 *   original_value: null,
 *   new_value: 54,
 *   operation: "imputation",
 * });
 * ```
 */
export const DataLineageSchema = z
  .object({
    /** Unique identifier of the data record (row) that was modified. */
    record_id: z
      .string()
      .min(1)
      .describe("Identifier of the modified data record"),

    /** Name of the field (column) that was changed. */
    field_name: z
      .string()
      .min(1)
      .describe("Name of the field whose value changed"),

    /**
     * The field's value before the operation.
     * `null` represents a missing (NULL/NaN) value.
     */
    original_value: z
      .unknown()
      .describe("Original field value before the operation (null = missing)"),

    /**
     * The field's value after the operation.
     * `null` represents an explicitly nullified value (e.g. after redaction).
     */
    new_value: z
      .unknown()
      .describe("New field value after the operation (null = explicitly nullified)"),

    /** The category of operation that caused this change. */
    operation: OperationTypeSchema,

    /**
     * ISO 8601 timestamp when the change was applied.
     * Defaults to the current moment.
     */
    timestamp: z
      .string()
      .datetime()
      .default(() => new Date().toISOString())
      .describe("Change application timestamp (ISO 8601)"),

    /**
     * Reference to the external evidence that justified this specific change.
     * Links back to the corresponding {@link AuditEntry.evidence_id}.
     */
    evidence_id: z
      .string()
      .nullable()
      .optional()
      .describe("Evidence document identifier that justified this change"),
  })
  .describe(
    "Field-level data lineage record capturing the before/after state of a single cell change"
  );

export type DataLineage = z.infer<typeof DataLineageSchema>;
