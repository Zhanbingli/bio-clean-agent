/**
 * @file decisions/index.ts
 * @description Public API barrel for the decisions sub-module.
 *
 * Re-exports all types, interfaces, and classes from manager and strategies
 * so consumers can import from a single path:
 *
 * @example
 * ```ts
 * import {
 *   DecisionManager,
 *   AutoApproveStrategy,
 *   NotifyAndWaitStrategy,
 *   LLMAssistedStrategy,
 *   MedicalDataDecisions,
 * } from "@bio-clean/core/decisions";
 * ```
 */

export type {
  DecisionOption,
  DecisionContext,
  DecisionStrategy,
} from "./manager.js";

export {
  DecisionManager,
  MedicalDataDecisions,
} from "./manager.js";

export type {
  PendingDecision,
  PlannerFunction,
} from "./strategies.js";

export {
  AutoApproveStrategy,
  NotifyAndWaitStrategy,
  LLMAssistedStrategy,
} from "./strategies.js";
