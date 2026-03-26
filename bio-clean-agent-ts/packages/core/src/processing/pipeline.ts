/**
 * @file processing/pipeline.ts
 * @description Pipeline base classes for the Bio Clean processing framework.
 *
 * Provides the building blocks for composable, step-based data processing:
 * - {@link StepResult}   – outcome of a single pipeline step execution
 * - {@link PipelineReport} – aggregated report for a completed pipeline run
 * - {@link PipelineStep}   – named, callable unit of work within a pipeline
 * - {@link Pipeline}       – ordered, context-driven step orchestrator
 *
 * Ported from the Python dataclass / class hierarchy in `processing/pipeline.py`.
 */

// ---------------------------------------------------------------------------
// StepResult
// ---------------------------------------------------------------------------

/**
 * The result produced by a single {@link PipelineStep} execution.
 *
 * @example
 * ```ts
 * const result: StepResult = {
 *   name: "validate_schema",
 *   success: true,
 *   details: { rows_checked: 1000 },
 * };
 * ```
 */
export interface StepResult {
  /** Human-readable name matching {@link PipelineStep.name}. */
  name: string;
  /** Whether the step completed without error. */
  success: boolean;
  /** Arbitrary step-specific output details. */
  details: Record<string, unknown>;
  /** Error message when {@link success} is `false`. `undefined` on success. */
  error?: string;
}

// ---------------------------------------------------------------------------
// PipelineReport
// ---------------------------------------------------------------------------

/**
 * Aggregated report produced after a full {@link Pipeline} run.
 *
 * The report is structurally immutable — create a new instance for each run.
 *
 * @example
 * ```ts
 * const report = new PipelineReport("clinical", "ds-001", results);
 * console.log(report.success); // true if every step succeeded
 * const json = report.summary();
 * ```
 */
export class PipelineReport {
  /** Name of the pipeline that produced this report. */
  readonly pipelineName: string;
  /** Identifier of the dataset that was processed. */
  readonly datasetId: string;
  /** Ordered list of individual step results. */
  readonly results: readonly StepResult[];

  constructor(
    pipelineName: string,
    datasetId: string,
    results: StepResult[]
  ) {
    this.pipelineName = pipelineName;
    this.datasetId = datasetId;
    this.results = Object.freeze([...results]);
  }

  /**
   * `true` when every step in {@link results} succeeded.
   * An empty results list is considered successful (vacuously true).
   */
  get success(): boolean {
    return this.results.every((step) => step.success);
  }

  /**
   * Returns a plain-object summary suitable for JSON serialisation or logging.
   */
  summary(): Record<string, unknown> {
    return {
      pipeline: this.pipelineName,
      dataset_id: this.datasetId,
      success: this.success,
      steps: this.results.map((s) => ({
        name: s.name,
        success: s.success,
        details: s.details,
        ...(s.error !== undefined ? { error: s.error } : {}),
      })),
    };
  }
}

// ---------------------------------------------------------------------------
// PipelineStep
// ---------------------------------------------------------------------------

/**
 * Callback signature for a pipeline step action.
 *
 * The action receives the shared mutable context and must return a
 * {@link StepResult}.  Throwing an exception from the action is safe —
 * {@link Pipeline.run} will catch it and produce a failure result.
 */
export type StepAction = (context: Record<string, unknown>) => StepResult;

/**
 * A named, executable unit of work within a {@link Pipeline}.
 *
 * Steps are registered on the pipeline via {@link Pipeline.addStep} and
 * executed in registration order by {@link Pipeline.run}.
 *
 * @example
 * ```ts
 * const step = new PipelineStep(
 *   "validate_schema",
 *   "Ensure required columns are present",
 *   (ctx) => {
 *     const dataset = ctx["dataset"] as Record<string, unknown>;
 *     // ... validation logic ...
 *     return { name: "validate_schema", success: true, details: {} };
 *   }
 * );
 * ```
 */
export class PipelineStep {
  /** Human-readable step name. Must be unique within a pipeline. */
  readonly name: string;
  /** Full description of what this step does. */
  readonly description: string;
  private readonly _action: StepAction;

  constructor(name: string, description: string, action: StepAction) {
    this.name = name;
    this.description = description;
    this._action = action;
  }

  /**
   * Execute the step's action with the provided context.
   *
   * @param context - Shared mutable context object passed across all steps.
   * @returns The {@link StepResult} produced by the action.
   */
  run(context: Record<string, unknown>): StepResult {
    return this._action(context);
  }
}

// ---------------------------------------------------------------------------
// Pipeline
// ---------------------------------------------------------------------------

/**
 * Abstract base for ordered, context-driven step pipelines.
 *
 * Subclasses customise behaviour by:
 * - Overriding {@link name} and {@link datasetType} static properties.
 * - Calling {@link addStep} in the constructor (or lazily in
 *   {@link buildSteps}) to register processing steps.
 * - Optionally overriding {@link validateContext} to reject invalid input
 *   before any step executes.
 * - Optionally overriding {@link buildSteps} to generate steps dynamically
 *   from the context (e.g. data-profile-driven step selection).
 *
 * @example
 * ```ts
 * class ClinicalPipeline extends Pipeline {
 *   override name = "clinical";
 *   override datasetType = "clinical";
 *
 *   constructor() {
 *     super();
 *     this.addStep(new PipelineStep("load", "Load records", loadAction));
 *     this.addStep(new PipelineStep("dedupe", "Remove duplicates", dedupeAction));
 *   }
 * }
 *
 * const report = await new ClinicalPipeline().run({ dataset: myData });
 * ```
 */
export abstract class Pipeline {
  /** Logical name used to identify this pipeline in reports and logs. */
  name: string = "pipeline";

  /** Domain type of datasets this pipeline handles (e.g. `"clinical"`). */
  datasetType: string = "generic";

  private _steps: PipelineStep[] = [];

  // ------------------------------------------------------------------
  // Step registration
  // ------------------------------------------------------------------

  /**
   * Append a step to the pipeline's ordered step list.
   *
   * @param step - The {@link PipelineStep} to register.
   */
  addStep(step: PipelineStep): void {
    this._steps.push(step);
  }

  // ------------------------------------------------------------------
  // Hooks for subclasses
  // ------------------------------------------------------------------

  /**
   * Validate the execution context before any step runs.
   *
   * Override this method to enforce required context keys or value types.
   * Throw an `Error` to abort the pipeline before it starts.
   *
   * The default implementation accepts any context without modification.
   *
   * @param _context - The context passed to {@link run}.
   * @throws {Error} When the context is invalid.
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  validateContext(_context: Record<string, unknown>): void {
    // No-op by default. Subclasses override to enforce constraints.
  }

  /**
   * Produce the ordered set of steps to execute for this particular run.
   *
   * Override to generate steps dynamically from the context (e.g. based on
   * a data profile stored in `context["profile"]`).  The default
   * implementation returns the steps registered via {@link addStep}.
   *
   * @param _context - The execution context.
   * @returns An iterable of {@link PipelineStep} objects in execution order.
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  buildSteps(_context: Record<string, unknown>): Iterable<PipelineStep> {
    return this._steps;
  }

  // ------------------------------------------------------------------
  // Execution
  // ------------------------------------------------------------------

  /**
   * Execute the pipeline against the provided context.
   *
   * Execution flow:
   * 1. {@link validateContext} is called; any thrown error produces an
   *    immediate single-step failure report.
   * 2. {@link buildSteps} is called to retrieve the ordered step list.
   * 3. Steps are executed in order.  Each step result is stored under
   *    `context["results"][step.name]` for downstream steps to inspect.
   * 4. If a step returns a failure result, execution stops immediately
   *    and the accumulated results are returned.
   * 5. Uncaught exceptions from a step action are caught and converted into
   *    a failure result; the pipeline then stops.
   *
   * @param context - Shared mutable execution context.  The key `"results"`
   *   is reserved and will be written by the pipeline.
   * @returns A {@link PipelineReport} with the outcome of every step that ran.
   */
  run(context: Record<string, unknown>): PipelineReport {
    const results: StepResult[] = [];

    // Initialise the results map in the context so steps can inspect it.
    if (!("results" in context) || typeof context["results"] !== "object") {
      context["results"] = {} as Record<string, StepResult>;
    }
    const contextResults = context["results"] as Record<string, StepResult>;

    // Validate context before executing any steps.
    try {
      this.validateContext(context);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : String(err);
      const validationFailure: StepResult = {
        name: "validate_context",
        success: false,
        details: {},
        error: `Context validation failed: ${message}`,
      };
      results.push(validationFailure);
      contextResults["validate_context"] = validationFailure;
      return new PipelineReport(this.name, String(context["dataset_id"] ?? ""), results);
    }

    const steps = this.buildSteps(context);

    for (const step of steps) {
      let result: StepResult;

      try {
        result = step.run(context);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : String(err);
        result = {
          name: step.name,
          success: false,
          details: {},
          error: `Unhandled exception: ${message}`,
        };
      }

      results.push(result);
      contextResults[step.name] = result;

      // Stop execution on the first failure.
      if (!result.success) {
        break;
      }
    }

    const datasetId = String(context["dataset_id"] ?? "");
    return new PipelineReport(this.name, datasetId, results);
  }
}
