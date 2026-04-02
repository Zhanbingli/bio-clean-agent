/**
 * @file planning.ts
 * @description Zod schemas for LLM-generated cleaning execution plans.
 * Models a structured plan composed of ordered, dependency-aware steps
 * with priority and risk metadata.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

/**
 * Priority level assigned to an individual plan step.
 * `critical` steps must succeed for the job to be considered valid.
 */
export const TaskPrioritySchema = z
  .enum(["critical", "high", "medium", "low"])
  .describe("Execution priority of a plan step");

export type TaskPriority = z.infer<typeof TaskPrioritySchema>;

/**
 * Functional category of a plan step, determining which
 * pipeline module handles its execution.
 */
export const StepTypeSchema = z
  .enum(["validation", "cleaning", "transformation", "verification"])
  .describe("Functional category of a plan step");

export type StepType = z.infer<typeof StepTypeSchema>;

// ---------------------------------------------------------------------------
// PlanStep
// ---------------------------------------------------------------------------

/**
 * A single, executable unit within a cleaning execution plan.
 *
 * Steps are ordered by the planner but execution respects the
 * `depends_on` graph to allow safe parallelism.
 */
export const PlanStepSchema = z
  .object({
    /** Unique identifier for this step within the plan (e.g. "step-001"). */
    id: z
      .string()
      .min(1)
      .describe("Unique step identifier within the execution plan"),

    /** Short, human-readable name (e.g. "Remove duplicate records"). */
    name: z.string().min(1).describe("Short human-readable step name"),

    /** Detailed description of what this step does and why. */
    description: z
      .string()
      .min(1)
      .describe("Full description of the step's purpose and methodology"),

    /** Functional category that determines the handling pipeline module. */
    step_type: StepTypeSchema,

    /** Scheduling priority of this step. */
    priority: TaskPrioritySchema,

    /**
     * Planner's reasoning for including this step
     * (e.g. "Column 'dob' contains 8 % out-of-range dates per profile").
     */
    rationale: z
      .string()
      .min(1)
      .describe("Planner reasoning for including this step"),

    /**
     * `true` when the rationale is grounded in profiling statistics or
     * domain-knowledge rules rather than heuristic reasoning.
     */
    evidence_based: z
      .boolean()
      .default(false)
      .describe("Whether the rationale is grounded in empirical evidence"),

    /**
     * Summary of the supporting evidence (profile stats, referenced papers, etc.).
     * Present only when `evidence_based` is `true`.
     */
    evidence_summary: z
      .string()
      .nullable()
      .optional()
      .describe("Summary of the empirical evidence supporting this step"),

    /**
     * IDs of steps that must complete successfully before this step can start.
     * An empty array means no dependencies (may run immediately).
     */
    depends_on: z
      .array(z.string())
      .default([])
      .describe("IDs of prerequisite steps"),

    /**
     * When `true`, the job will fail if this step fails.
     * Optional (non-critical) steps are skipped on failure with a warning.
     */
    required: z
      .boolean()
      .default(true)
      .describe("Whether step failure causes the whole job to fail"),

    /**
     * Estimated wall-clock duration in seconds.
     * `null` when the planner cannot estimate duration.
     */
    estimated_duration: z
      .number()
      .positive()
      .nullable()
      .optional()
      .describe("Estimated execution duration in seconds"),

    /**
     * Step-specific parameters forwarded to the execution handler
     * (e.g. `{ threshold: 0.05, strategy: "median" }`).
     */
    parameters: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Step-specific execution parameters"),

    /**
     * Risk level associated with the operation:
     * - `low`    – read-only or fully reversible
     * - `medium` – modifies data but changes are logged
     * - `high`   – potentially destructive; requires extra confirmation
     */
    risk_level: z
      .enum(["low", "medium", "high"])
      .default("low")
      .describe("Risk level: low | medium | high"),

    /**
     * `true` when the step's changes can be undone using the audit trail
     * (e.g. value imputations logged per-record in `DataLineage`).
     */
    reversible: z
      .boolean()
      .default(true)
      .describe("Whether the step's changes can be reversed via the audit trail"),
  })
  .describe("A single executable unit within a cleaning execution plan");

export type PlanStep = z.infer<typeof PlanStepSchema>;

// ---------------------------------------------------------------------------
// ExecutionPlan
// ---------------------------------------------------------------------------

/**
 * Complete, LLM-generated execution plan for a cleaning job.
 * Produced by the Planner agent and consumed by the Executor.
 */
export const ExecutionPlanSchema = z
  .object({
    /** The job this plan belongs to. */
    job_id: z
      .string()
      .uuid()
      .describe("Identifier of the job this plan was generated for"),

    /**
     * Data domain type, used to select domain-specific cleaning strategies.
     * Mirrors {@link DataType} in job.ts.
     */
    data_type: z
      .string()
      .min(1)
      .describe("Domain type of the data being processed"),

    /** High-level objectives that guided plan generation. */
    objectives: z
      .array(z.string())
      .default([])
      .describe("High-level objectives provided in the job request"),

    /**
     * Ordered list of plan steps.  The executor may parallelise steps
     * whose `depends_on` graphs allow it.
     */
    steps: z
      .array(PlanStepSchema)
      .min(1)
      .describe("Ordered list of cleaning steps"),

    /**
     * Data quality or structural issues detected during profiling
     * that motivated the plan (e.g. "12 % missing values in column 'age'").
     */
    detected_issues: z
      .array(z.string())
      .default([])
      .describe("Issues detected during data profiling"),

    /**
     * Broader recommendations that are not captured by individual steps
     * (e.g. "Consider collecting date-of-birth at intake rather than imputing").
     */
    recommendations: z
      .array(z.string())
      .default([])
      .describe("High-level recommendations beyond the immediate plan"),

    /**
     * Non-critical cautions surfaced during planning
     * (e.g. "Sample size drops below 500 after deduplication").
     */
    warnings: z
      .array(z.string())
      .default([])
      .describe("Non-critical warnings from the planner"),

    /**
     * Estimated improvement in the overall quality score [0, 1] after plan execution.
     * `null` when the planner cannot estimate the improvement.
     */
    estimated_quality_improvement: z
      .number()
      .min(0)
      .max(1)
      .nullable()
      .optional()
      .describe(
        "Estimated overall quality score improvement after plan execution (0–1)"
      ),

    /**
     * Estimated fraction of records that will be removed or heavily modified.
     * Value in [0, 1]; `null` when unknown.
     */
    estimated_data_loss: z
      .number()
      .min(0)
      .max(1)
      .nullable()
      .optional()
      .describe("Estimated fraction of records affected by data loss (0–1)"),
  })
  .describe("LLM-generated execution plan for a cleaning job");

export type ExecutionPlan = z.infer<typeof ExecutionPlanSchema>;
