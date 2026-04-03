/**
 * @file agent.ts
 * @description Bio Clean Agent — the top-level orchestrator for dataset cleaning jobs.
 *
 * The {@link BioCleaningAgent} coordinates dataset loading, pipeline selection,
 * smart planning, and execution into a single cohesive workflow.
 *
 * Key types:
 * - {@link AgentRequest}         – input descriptor for a cleaning run
 * - {@link AgentPlan}            – derived execution blueprint produced by {@link BioCleaningAgent.plan}
 * - {@link AgentExecutionResult} – final outcome returned by {@link BioCleaningAgent.planAndExecute}
 *
 * @example
 * ```ts
 * const agent = new BioCleaningAgent();
 *
 * // Register a pipeline factory for clinical datasets.
 * agent.registerPipeline("clinical", () => new ClinicalPipeline());
 *
 * // One-shot plan + execute.
 * const result = await agent.planAndExecute({
 *   dataset: { dataset_type: "clinical", dataset_id: "ds-001", raw_paths: ["data.csv"] },
 *   output_dir: "./outputs/ds-001",
 * });
 * ```
 */

import path from "node:path";

import { loadDataset } from "./schemas/dataset.js";
import type { Dataset } from "./schemas/dataset.js";
import type { ExecutionPlan, PlanStep } from "./schemas/planning.js";
import type { PlannerOutput } from "./schemas/llm.js";
import { Pipeline, PipelineReport } from "./processing/pipeline.js";
import { SmartPlanner } from "./planning/smart-planner.js";
import type { DataProfile } from "./planning/smart-planner.js";

// ---------------------------------------------------------------------------
// AgentRequest
// ---------------------------------------------------------------------------

/**
 * Input descriptor supplied to the agent for a single cleaning request.
 *
 * The `dataset` field accepts an arbitrary plain-object record so that
 * callers are not required to pre-parse the dataset before handing it to
 * the agent.  The agent validates and narrows the type internally via
 * {@link loadDataset}.
 */
export interface AgentRequest {
  /**
   * Raw dataset descriptor.  Must include at minimum a `dataset_type` field
   * matching one of the registered dataset types (`"clinical"`, `"ehr"`).
   */
  dataset: Record<string, unknown>;

  /**
   * Directory where pipeline outputs will be written.
   * When omitted the agent derives a path from the default output root and
   * the `dataset_id`.
   */
  output_dir?: string;

  /**
   * Arbitrary key-value parameters forwarded to the selected pipeline.
   * Values may be any JSON-serialisable type.
   */
  parameters?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// AgentPlan
// ---------------------------------------------------------------------------

/**
 * Derived execution blueprint produced by {@link BioCleaningAgent.plan}.
 *
 * Consumers can inspect the plan before committing to execution, allowing
 * for human review, cost estimation, or conditional step skipping.
 */
export interface AgentPlan {
  /** Identifier of the dataset to be processed. */
  datasetId: string;

  /** Detected dataset type (e.g. `"clinical"`, `"ehr"`). */
  datasetType: string;

  /** Name of the pipeline that will be used to process the dataset. */
  pipeline: string;

  /** Absolute path to the output directory for this run. */
  workdir: string;

  /** Ordered list of plan steps to execute. */
  steps: PlanStep[];

  /**
   * Pipeline-specific parameters merged from the request and any smart-planner
   * recommendations.
   */
  parameters: Record<string, unknown>;

  /**
   * Non-critical warnings produced during plan generation
   * (e.g. high missingness, low sample size).
   */
  warnings: string[];
}

// ---------------------------------------------------------------------------
// AgentExecutionResult
// ---------------------------------------------------------------------------

/**
 * Final outcome returned by {@link BioCleaningAgent.planAndExecute}.
 */
export interface AgentExecutionResult {
  /** The plan that was executed. */
  plan: AgentPlan;

  /** The pipeline execution report. */
  report: PipelineReport;

  /**
   * Raw output from the smart planner, if one was used.
   * `undefined` when planning was skipped or used a pre-supplied plan.
   */
  plannerOutput?: PlannerOutput;
}

// ---------------------------------------------------------------------------
// Pipeline factory type
// ---------------------------------------------------------------------------

/**
 * Factory function that creates a fresh {@link Pipeline} instance for a given
 * dataset type.  Registered via {@link BioCleaningAgent.registerPipeline}.
 */
export type PipelineFactory = () => Pipeline;

// ---------------------------------------------------------------------------
// BioCleaningAgent
// ---------------------------------------------------------------------------

/**
 * Top-level orchestrator that coordinates dataset loading, pipeline selection,
 * smart planning, and execution.
 *
 * The agent maintains a registry of {@link PipelineFactory} functions keyed by
 * dataset type.  Callers register pipelines with {@link registerPipeline} before
 * invoking {@link run} or {@link planAndExecute}.
 *
 * @example
 * ```ts
 * const agent = new BioCleaningAgent("./output");
 *
 * agent.registerPipeline("clinical", () => new MyClinicalPipeline());
 *
 * const result = await agent.planAndExecute({
 *   dataset: {
 *     dataset_type: "clinical",
 *     dataset_id:   "trial-007",
 *     raw_paths:    ["./data/trial.csv"],
 *   },
 * });
 * ```
 */
export class BioCleaningAgent {
  /** Root directory where per-dataset output subdirectories are created. */
  readonly defaultOutputRoot: string;

  /** Optional default executor pipeline (unused unless explicitly set). */
  private _defaultExecutor: Pipeline | null;

  /** Registry mapping dataset type strings to pipeline factory functions. */
  private readonly _pipelineRegistry: Map<string, PipelineFactory> = new Map();

  constructor(
    defaultOutputRoot: string = "outputs",
    executor: Pipeline | null = null
  ) {
    this.defaultOutputRoot = defaultOutputRoot;
    this._defaultExecutor = executor;
  }

  // ------------------------------------------------------------------
  // Pipeline registry
  // ------------------------------------------------------------------

  /**
   * Register a pipeline factory for a given dataset type.
   *
   * The factory is called each time a pipeline instance is needed for that
   * type, so a fresh object is created per run (preventing state leakage).
   *
   * @param datasetType - Dataset type string (e.g. `"clinical"`).
   * @param factory     - Zero-argument function returning a new {@link Pipeline}.
   */
  registerPipeline(datasetType: string, factory: PipelineFactory): void {
    this._pipelineRegistry.set(datasetType, factory);
  }

  // ------------------------------------------------------------------
  // Plan
  // ------------------------------------------------------------------

  /**
   * Derive an {@link AgentPlan} from a dataset descriptor without executing.
   *
   * @param dataset    - Raw dataset descriptor (must contain `dataset_type`).
   * @param outputDir  - Optional explicit output directory.
   * @param parameters - Optional execution parameters.
   * @returns A fully populated {@link AgentPlan}.
   * @throws {Error} When the dataset type cannot be determined or is invalid.
   */
  plan(
    dataset: Record<string, unknown>,
    outputDir?: string,
    parameters?: Record<string, unknown>
  ): AgentPlan {
    // Resolve the dataset type string first so we can use it for path derivation
    // before full schema validation.
    const rawType = dataset["dataset_type"];
    if (typeof rawType !== "string" || rawType.length === 0) {
      throw new Error(
        'Dataset must include a non-empty string "dataset_type" field.'
      );
    }

    // Validate and parse the dataset via the schema registry.
    const validatedDataset: Dataset = loadDataset(rawType, dataset);

    const datasetId = validatedDataset.dataset_id;
    const datasetType = validatedDataset.dataset_type;

    // Determine the output directory.
    const workdir =
      outputDir ??
      path.join(this.defaultOutputRoot, datasetId);

    // Resolve the pipeline name.
    const factory = this._pipelineRegistry.get(datasetType);
    const pipelineName = factory
      ? factory().name
      : `${datasetType}_pipeline`;

    // Build a simple plan from the dataset type and any supplied parameters.
    const mergedParams: Record<string, unknown> = {
      dataset_type: datasetType,
      dataset_id: datasetId,
      workdir,
      ...parameters,
    };

    return {
      datasetId,
      datasetType,
      pipeline: pipelineName,
      workdir,
      steps: [],
      parameters: mergedParams,
      warnings: [],
    };
  }

  // ------------------------------------------------------------------
  // Run
  // ------------------------------------------------------------------

  /**
   * Execute a pipeline for the given request, optionally using a pre-built plan.
   *
   * The method:
   * 1. Validates the dataset descriptor.
   * 2. Looks up (or creates) a pipeline from the registry.
   * 3. Builds an execution context from the request and plan.
   * 4. Runs the pipeline and returns the {@link PipelineReport}.
   *
   * @param request - The cleaning request.
   * @param plan    - Optional pre-built plan; if omitted {@link plan} is called.
   * @returns A {@link PipelineReport} for the completed run.
   * @throws {Error} When no pipeline is registered for the dataset type.
   */
  async run(request: AgentRequest, plan?: AgentPlan): Promise<PipelineReport> {
    const agentPlan = plan ?? this.plan(request.dataset, request.output_dir, request.parameters);

    // Validate and load the dataset.
    const validatedDataset = loadDataset(
      agentPlan.datasetType,
      request.dataset
    );

    // Resolve the pipeline.
    const factory = this._pipelineRegistry.get(agentPlan.datasetType);
    let pipeline: Pipeline;

    if (factory !== undefined) {
      pipeline = factory();
    } else if (this._defaultExecutor !== null) {
      pipeline = this._defaultExecutor;
    } else {
      throw new Error(
        `No pipeline registered for dataset type "${agentPlan.datasetType}". ` +
          "Call agent.registerPipeline() before running."
      );
    }

    // Build the execution context.
    const context: Record<string, unknown> = {
      dataset: validatedDataset,
      dataset_id: validatedDataset.dataset_id,
      dataset_type: agentPlan.datasetType,
      workdir: agentPlan.workdir,
      parameters: agentPlan.parameters,
      plan: agentPlan,
      results: {},
    };

    return await pipeline.run(context);
  }

  // ------------------------------------------------------------------
  // Plan and execute
  // ------------------------------------------------------------------

  /**
   * Generate a smart plan and execute it in a single call.
   *
   * This is the primary entry point for automated pipelines.  It:
   * 1. Parses the dataset descriptor.
   * 2. Optionally runs the {@link SmartPlanner} to generate a cleaning plan.
   * 3. Builds an {@link AgentPlan} enriched with the smart-planner output.
   * 4. Runs the pipeline and returns an {@link AgentExecutionResult}.
   *
   * @param request      - The cleaning request.
   * @param userGoal     - Optional free-text goal forwarded to the smart planner.
   * @param planner      - Optional {@link SmartPlanner} instance; a default one
   *   is created when omitted.
   * @param confirmStep  - Optional async callback called with the generated plan
   *   before execution.  Return `false` to abort.  When omitted the plan is
   *   executed unconditionally.
   * @returns An {@link AgentExecutionResult} containing the plan, report, and
   *   optional planner output.
   * @throws {Error} When `confirmStep` returns `false` (execution cancelled).
   */
  async planAndExecute(
    request: AgentRequest,
    userGoal?: string,
    planner?: SmartPlanner,
    confirmStep?: (plan: AgentPlan) => Promise<boolean> | boolean
  ): Promise<AgentExecutionResult> {
    // Resolve the dataset type for planning.
    const rawType = request.dataset["dataset_type"];
    if (typeof rawType !== "string" || rawType.length === 0) {
      throw new Error(
        'Dataset must include a non-empty string "dataset_type" field.'
      );
    }

    const validatedDataset = loadDataset(rawType, request.dataset);

    const outputDir =
      request.output_dir ??
      path.join(this.defaultOutputRoot, validatedDataset.dataset_id);

    // Build objectives list from parameters and userGoal.
    const objectives: string[] = [];
    if (userGoal !== undefined && userGoal.trim().length > 0) {
      objectives.push(userGoal.trim());
    }
    const paramObjectives = request.parameters?.["objectives"];
    if (Array.isArray(paramObjectives)) {
      objectives.push(
        ...paramObjectives.filter((o): o is string => typeof o === "string")
      );
    }

    // Run the smart planner.
    const activePlanner = planner ?? new SmartPlanner();
    const dataProfile =
      request.parameters?.["data_profile"] as DataProfile | undefined;

    const executionPlan: ExecutionPlan = activePlanner.createPlan(
      validatedDataset.dataset_id,
      validatedDataset.dataset_type,
      objectives,
      dataProfile
    );

    // Convert the ExecutionPlan steps into an AgentPlan.
    const agentPlan: AgentPlan = {
      datasetId: validatedDataset.dataset_id,
      datasetType: validatedDataset.dataset_type,
      pipeline:
        this._pipelineRegistry.get(validatedDataset.dataset_type)?.()?.name ??
        `${validatedDataset.dataset_type}_pipeline`,
      workdir: outputDir,
      steps: executionPlan.steps,
      parameters: {
        dataset_type: validatedDataset.dataset_type,
        dataset_id: validatedDataset.dataset_id,
        workdir: outputDir,
        objectives,
        ...request.parameters,
      },
      warnings: executionPlan.warnings,
    };

    // Optionally confirm the plan before executing.
    if (confirmStep !== undefined) {
      const confirmed = await Promise.resolve(confirmStep(agentPlan));
      if (!confirmed) {
        throw new Error(
          `Execution cancelled by confirmStep callback for dataset "${validatedDataset.dataset_id}".`
        );
      }
    }

    // Execute the pipeline.
    const report = await this.run(request, agentPlan);

    return {
      plan: agentPlan,
      report,
      plannerOutput: undefined,
    };
  }
}
