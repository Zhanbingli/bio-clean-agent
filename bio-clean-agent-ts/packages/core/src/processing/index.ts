/**
 * @file processing/index.ts
 * @description Public API barrel for the processing sub-module.
 *
 * Re-exports all types, interfaces, and classes from the pipeline module
 * so consumers can import from a single path:
 *
 * @example
 * ```ts
 * import {
 *   Pipeline,
 *   PipelineStep,
 *   PipelineReport,
 * } from "@bio-clean/core/processing";
 * import type { StepResult, StepAction } from "@bio-clean/core/processing";
 * ```
 */

export type { StepResult, StepAction } from "./pipeline.js";

export { PipelineReport, PipelineStep, Pipeline } from "./pipeline.js";
