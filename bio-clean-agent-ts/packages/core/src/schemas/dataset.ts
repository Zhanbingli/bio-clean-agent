/**
 * @file dataset.ts
 * @description Zod schemas for clinical dataset types.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** All valid dataset type literals. */
export const DATASET_TYPES = ["clinical"] as const;

/** Tuple type for all dataset type strings. */
export type DatasetTypeValue = (typeof DATASET_TYPES)[number];

// ---------------------------------------------------------------------------
// Base schema (shared fields)
// ---------------------------------------------------------------------------

export const DatasetBaseSchema = z.object({
  /** Unique identifier for the dataset. */
  dataset_id: z.string().min(1).describe("Unique identifier for the dataset"),

  /** Optional path to accompanying metadata file. */
  metadata_path: z
    .string()
    .nullable()
    .optional()
    .describe("Optional path to a metadata file associated with this dataset"),
});

// ---------------------------------------------------------------------------
// Clinical dataset
// ---------------------------------------------------------------------------

export const ClinicalDatasetSchema = DatasetBaseSchema.extend({
  dataset_type: z.literal("clinical").default("clinical"),

  /** One or more paths to clinical data files. */
  raw_paths: z
    .array(z.string().min(1))
    .min(1)
    .describe("Paths to clinical data files"),

  /** Clinical study or trial identifier. */
  study_id: z
    .string()
    .nullable()
    .optional()
    .describe("Clinical study or trial identifier"),

  /** Free-text description of the clinical dataset. */
  description: z
    .string()
    .nullable()
    .optional()
    .describe("Human-readable description of the clinical dataset"),
});

export type ClinicalDataset = z.infer<typeof ClinicalDatasetSchema>;

// ---------------------------------------------------------------------------
// Primary dataset schema (clinical only)
// ---------------------------------------------------------------------------

/**
 * The primary dataset schema for parsing clinical dataset payloads.
 *
 * @example
 * ```ts
 * const ds = DatasetSchema.parse(rawInput);
 * if (ds.dataset_type === "clinical") { ... }
 * ```
 */
export const DatasetSchema = ClinicalDatasetSchema;

export type Dataset = z.infer<typeof DatasetSchema>;

// ---------------------------------------------------------------------------
// Dataset loader
// ---------------------------------------------------------------------------

/**
 * Parses and validates `data` against the clinical dataset Zod schema.
 * Throws a {@link z.ZodError} when validation fails or an {@link Error}
 * when `modelType` is not `"clinical"` or `"ehr"` (ehr maps to clinical).
 *
 * @param modelType - Must be `"clinical"` or `"ehr"`.
 * @param data      - Raw (unknown) payload to validate.
 * @returns         The validated, typed clinical dataset object.
 *
 * @example
 * ```ts
 * const ds = loadDataset("clinical", {
 *   dataset_id: "ds-001",
 *   raw_paths: ["trial.csv"],
 * });
 * ```
 */
export function loadDataset(modelType: string, data: unknown): Dataset {
  const normalisedType = modelType === "ehr" ? "clinical" : modelType;

  if (!DATASET_TYPES.includes(normalisedType as DatasetTypeValue)) {
    throw new Error(
      `Unknown dataset type "${modelType}". ` +
        `Expected one of: ${DATASET_TYPES.join(", ")}.`
    );
  }

  return ClinicalDatasetSchema.parse(data);
}
