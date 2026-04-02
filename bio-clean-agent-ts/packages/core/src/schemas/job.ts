/**
 * @file job.ts
 * @description Zod schemas for job lifecycle management: requests, progress tracking,
 * and human-in-the-loop decision points.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

/** Lifecycle states a job can occupy. */
export const JobStatusSchema = z.enum([
  "submitted",
  "planning",
  "awaiting_decision",
  "running",
  "completed",
  "failed",
  "cancelled",
]);
export type JobStatus = z.infer<typeof JobStatusSchema>;

/** Scheduling priority for a job. */
export const JobPrioritySchema = z
  .enum(["low", "normal", "high", "urgent"])
  .describe("Scheduling priority for the job");
export type JobPriority = z.infer<typeof JobPrioritySchema>;

/**
 * Domain-specific data type processed by the job.
 */
export const DataTypeSchema = z
  .enum([
    "clinical_trial",
    "ehr",
    "general",
  ])
  .describe("Biomedical domain type of the input data");
export type DataType = z.infer<typeof DataTypeSchema>;

// ---------------------------------------------------------------------------
// JobRequest
// ---------------------------------------------------------------------------

/**
 * Schema for submitting a new cleaning/processing job.
 *
 * @example
 * ```ts
 * const req = JobRequestSchema.parse({
 *   data_type: "clinical_trial",
 *   input_paths: ["/data/trial.csv"],
 *   output_dir: "/results/job-001",
 * });
 * ```
 */
export const JobRequestSchema = z
  .object({
    /** Unique job identifier – auto-generated via `crypto.randomUUID()` when omitted. */
    job_id: z
      .string()
      .uuid()
      .default(() => crypto.randomUUID())
      .describe("Unique job identifier (UUID v4)"),

    /** Domain type of the input data. */
    data_type: DataTypeSchema,

    /** One or more absolute or relative paths to input data files or directories. */
    input_paths: z
      .array(z.string().min(1))
      .min(1)
      .describe("Input file or directory paths"),

    /** Directory where job outputs will be written. */
    output_dir: z.string().min(1).describe("Output directory path"),

    /** High-level objectives that guide the cleaning plan. */
    objectives: z
      .array(z.string())
      .default([])
      .describe("List of high-level objectives for the cleaning job"),

    /**
     * Arbitrary key-value parameters forwarded to the processing pipeline.
     * Values may be any JSON-serialisable type.
     */
    parameters: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Pipeline-specific parameters"),

    /** Job scheduling priority. */
    priority: JobPrioritySchema.default("normal"),

    /**
     * When `true`, decision points are automatically resolved using default options
     * without requiring human confirmation.
     */
    auto_approve: z
      .boolean()
      .default(false)
      .describe("Automatically approve all decision points without human review"),

    /** Emit a notification when a decision is required. */
    notify_on_decision: z
      .boolean()
      .default(true)
      .describe("Send a notification when the job requires a human decision"),

    /** Emit a notification when the job reaches a terminal state. */
    notify_on_completion: z
      .boolean()
      .default(true)
      .describe("Send a notification on job completion or failure"),
  })
  .describe("Job submission request payload");

export type JobRequest = z.infer<typeof JobRequestSchema>;

// ---------------------------------------------------------------------------
// DecisionPoint
// ---------------------------------------------------------------------------

/**
 * Represents a moment in the pipeline where human input is required before
 * execution can continue.
 */
export const DecisionPointSchema = z
  .object({
    /** Unique identifier for this decision point. */
    decision_id: z
      .string()
      .uuid()
      .default(() => crypto.randomUUID())
      .describe("Unique decision-point identifier (UUID v4)"),

    /** The question posed to the human reviewer. */
    question: z.string().min(1).describe("Question posed to the human reviewer"),

    /**
     * Additional context (data profiles, statistics, sample rows, etc.)
     * that helps the reviewer make an informed choice.
     */
    context: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Contextual information to aid the reviewer"),

    /**
     * Enumerated options the reviewer may choose from.
     * Each option is an arbitrary key-value map (e.g. `{ id, label, description }`).
     */
    options: z
      .array(z.record(z.string(), z.unknown()))
      .default([])
      .describe("Available choices for the reviewer"),

    /** Key of the option that will be selected when `auto_approve` is true. */
    default_option: z
      .string()
      .nullable()
      .optional()
      .describe("Default option selected during auto-approval"),

    /** ISO 8601 timestamp when this decision point was created. */
    timestamp: z
      .string()
      .datetime()
      .default(() => new Date().toISOString())
      .describe("Creation timestamp (ISO 8601)"),
  })
  .describe("A human-in-the-loop decision checkpoint");

export type DecisionPoint = z.infer<typeof DecisionPointSchema>;

// ---------------------------------------------------------------------------
// StepProgress
// ---------------------------------------------------------------------------

/** Step execution status literals. */
export const StepStatusSchema = z
  .enum(["pending", "running", "completed", "failed"])
  .describe("Current execution status of a pipeline step");
export type StepStatus = z.infer<typeof StepStatusSchema>;

/**
 * Tracks real-time progress of a single pipeline step.
 */
export const StepProgressSchema = z
  .object({
    /** Human-readable name of the pipeline step. */
    step_name: z.string().min(1).describe("Name of the pipeline step"),

    /** Current execution status. */
    status: StepStatusSchema,

    /** Completion percentage in the range [0, 100]. */
    progress_percent: z
      .number()
      .min(0)
      .max(100)
      .default(0)
      .describe("Completion percentage (0–100)"),

    /** Optional progress or status message. */
    message: z.string().default("").describe("Human-readable progress message"),

    /** ISO 8601 timestamp when the step began executing. */
    started_at: z
      .string()
      .datetime()
      .nullable()
      .optional()
      .describe("Step start timestamp (ISO 8601)"),

    /** ISO 8601 timestamp when the step finished. */
    completed_at: z
      .string()
      .datetime()
      .nullable()
      .optional()
      .describe("Step completion timestamp (ISO 8601)"),

    /** Error message if the step failed. */
    error: z
      .string()
      .nullable()
      .optional()
      .describe("Error message when the step fails"),
  })
  .describe("Real-time progress snapshot for a single pipeline step");

export type StepProgress = z.infer<typeof StepProgressSchema>;
