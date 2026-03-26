/**
 * @file index.ts
 * @description Barrel re-export for all Zod schemas and inferred types in the
 * `@bio-clean/core` schemas module. Import from this entry point rather than
 * from individual schema files to keep consumer imports stable as the schema
 * set grows.
 *
 * @example
 * ```ts
 * import {
 *   DatasetSchema,
 *   JobRequestSchema,
 *   DataQualityReportSchema,
 *   EventSchema,
 * } from "@bio-clean/core/schemas";
 * ```
 */

// ---------------------------------------------------------------------------
// Dataset schemas
// ---------------------------------------------------------------------------
export {
  DATASET_TYPES,
  DatasetBaseSchema,
  SequencingDatasetSchema,
  TranscriptomicsDatasetSchema,
  MetabolomicsDatasetSchema,
  ClinicalDatasetSchema,
  DatasetSchema,
  loadDataset,
} from "./dataset.js";

export type {
  DatasetTypeValue,
  SequencingDataset,
  TranscriptomicsDataset,
  MetabolomicsDataset,
  ClinicalDataset,
  Dataset,
} from "./dataset.js";

// ---------------------------------------------------------------------------
// Job schemas
// ---------------------------------------------------------------------------
export {
  JobStatusSchema,
  JobPrioritySchema,
  DataTypeSchema,
  JobRequestSchema,
  DecisionPointSchema,
  StepStatusSchema,
  StepProgressSchema,
} from "./job.js";

export type {
  JobStatus,
  JobPriority,
  DataType,
  JobRequest,
  DecisionPoint,
  StepStatus,
  StepProgress,
} from "./job.js";

// ---------------------------------------------------------------------------
// Quality schemas
// ---------------------------------------------------------------------------
export {
  QualityDimensionSchema,
  DimensionScoreSchema,
  DimensionAssessmentSchema,
  DataQualityReportSchema,
  scoreToDimensionLevel,
} from "./quality.js";

export type {
  QualityDimension,
  DimensionScore,
  DimensionAssessment,
  DataQualityReport,
} from "./quality.js";

// ---------------------------------------------------------------------------
// Planning schemas
// ---------------------------------------------------------------------------
export {
  TaskPrioritySchema,
  StepTypeSchema,
  PlanStepSchema,
  ExecutionPlanSchema,
} from "./planning.js";

export type {
  TaskPriority,
  StepType,
  PlanStep,
  ExecutionPlan,
} from "./planning.js";

// ---------------------------------------------------------------------------
// Event schemas
// ---------------------------------------------------------------------------
export {
  EVENT_TYPES,
  EventTypeSchema,
  EventSchema,
} from "./events.js";

export type {
  EventType,
  Event,
  EventDict,
  EventListener,
} from "./events.js";

// ---------------------------------------------------------------------------
// Audit schemas
// ---------------------------------------------------------------------------
export {
  OperationTypeSchema,
  SeverityLevelSchema,
  AuditEntrySchema,
  DataLineageSchema,
} from "./audit.js";

export type {
  OperationType,
  SeverityLevel,
  AuditEntry,
  DataLineage,
} from "./audit.js";

// ---------------------------------------------------------------------------
// LLM schemas
// ---------------------------------------------------------------------------
export {
  ModelDescriptorSchema,
  ModelConfigSchema,
  GenerationConfigSchema,
  PlannerOutputSchema,
} from "./llm.js";

export type {
  ModelDescriptor,
  ModelConfig,
  GenerationConfig,
  PlannerOutput,
} from "./llm.js";
