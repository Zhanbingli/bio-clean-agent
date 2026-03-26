/**
 * Quality module public API.
 *
 * Re-exports the {@link DataQualityAssessor} and supporting types from the
 * quality sub-modules so consumers can import from a single path:
 *
 * @example
 * ```ts
 * import { DataQualityAssessor, ReferenceRange } from "@bio-clean/core/quality";
 * ```
 */

export {
  DataQualityAssessor,
  ReferenceRange,
  isNumeric,
  countMissing,
  getNumericColumns,
  getObjectColumns,
} from "./assessor.js";
