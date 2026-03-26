/**
 * @file planning/index.ts
 * @description Public API barrel for the planning sub-module.
 *
 * Re-exports all types, interfaces, and classes from the smart-planner
 * so consumers can import from a single path:
 *
 * @example
 * ```ts
 * import { SmartPlanner } from "@bio-clean/core/planning";
 * import type { DataProfile, ColumnProfile } from "@bio-clean/core/planning";
 * ```
 */

export type { DataProfile, ColumnProfile } from "./smart-planner.js";

export { SmartPlanner } from "./smart-planner.js";
