/**
 * Knowledge module public API.
 *
 * Re-exports all types, enums, interfaces, helpers, and classes from the
 * four knowledge sub-modules so consumers can import from a single path:
 *
 * @example
 * ```ts
 * import {
 *   EvidenceLevel,
 *   ConfidenceLevel,
 *   MedicalStandards,
 *   EvidenceBase,
 *   ValidationRules,
 * } from "@bio-clean/core/knowledge";
 * ```
 */

// Base types, enums, interfaces, helpers, and abstract class
export {
  // Enums
  EvidenceLevel,
  ConfidenceLevel,
  // Interfaces
  Citation,
  KnowledgeEntry,
  KnowledgeEntryDict,
  RecommendationContext,
  ValidationResult as KnowledgeValidationResult,
  SearchOptions,
  // Constants
  CONFIDENCE_ORDER,
  EVIDENCE_ORDER,
  // Factory helpers
  createEntry,
  entryToDict,
  // Abstract class
  KnowledgeBase,
} from "./base.js";

// Medical standards
export {
  MedicalStandards,
  ReferenceRange,
} from "./medical-standards.js";

// Evidence base
export {
  EvidenceBase,
  CleaningContext,
} from "./evidence-base.js";

// Validation rules engine
export {
  ValidationRules,
  ValidationResult,
  ValidationResultDict,
  VitalSignField,
  LabTestName,
  VitalSignContext,
  LabValueContext,
} from "./validation-rules.js";
