/**
 * @file dataset.ts
 * @description Zod schemas for bioinformatics dataset types, ported from Python Pydantic models.
 * Supports sequencing, transcriptomics, metabolomics, and clinical dataset variants
 * via a discriminated union on `dataset_type`.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** All valid dataset type literals. */
export const DATASET_TYPES = [
  "sequencing",
  "transcriptomics",
  "metabolomics",
  "clinical",
] as const;

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
// Sequencing dataset
// ---------------------------------------------------------------------------

/** Accepted file extensions for raw sequencing reads. */
const SEQUENCING_EXTENSIONS = /\.(fastq|fq)(\.gz)?$/i;

export const SequencingDatasetSchema = DatasetBaseSchema.extend({
  dataset_type: z.literal("sequencing").default("sequencing"),

  /**
   * One or more paths to raw read files.
   * Each path must end with .fastq, .fq, .fastq.gz, or .fq.gz.
   */
  raw_paths: z
    .array(
      z
        .string()
        .min(1)
        .regex(
          SEQUENCING_EXTENSIONS,
          "Each raw path must end with .fastq, .fq, .fastq.gz, or .fq.gz"
        )
    )
    .min(1)
    .describe("Paths to raw sequencing read files"),

  /** Whether reads are single-end or paired-end. */
  read_type: z
    .enum(["single", "paired"])
    .describe("Sequencing read type: single-end or paired-end"),

  /** Sequencing platform, e.g. Illumina, PacBio. */
  platform: z
    .string()
    .nullable()
    .optional()
    .describe("Sequencing platform (e.g. Illumina NovaSeq, PacBio Sequel)"),
});

export type SequencingDataset = z.infer<typeof SequencingDatasetSchema>;

// ---------------------------------------------------------------------------
// Transcriptomics dataset
// ---------------------------------------------------------------------------

export const TranscriptomicsDatasetSchema = DatasetBaseSchema.extend({
  dataset_type: z.literal("transcriptomics").default("transcriptomics"),

  /** One or more paths to expression matrix files. */
  raw_paths: z
    .array(z.string().min(1))
    .min(1)
    .describe("Paths to expression matrix files"),

  /** Quantification unit used in the expression matrix. */
  matrix_format: z
    .enum(["counts", "tpm", "fpkm"])
    .describe("Expression quantification format: counts, TPM, or FPKM"),

  /** Path or identifier for the gene annotation reference. */
  gene_annotation: z
    .string()
    .nullable()
    .optional()
    .describe("Gene annotation reference (GTF/GFF path or Ensembl release ID)"),
});

export type TranscriptomicsDataset = z.infer<typeof TranscriptomicsDatasetSchema>;

// ---------------------------------------------------------------------------
// Metabolomics dataset
// ---------------------------------------------------------------------------

export const MetabolomicsDatasetSchema = DatasetBaseSchema.extend({
  dataset_type: z.literal("metabolomics").default("metabolomics"),

  /** One or more paths to raw metabolomics data files. */
  raw_paths: z
    .array(z.string().min(1))
    .min(1)
    .describe("Paths to raw metabolomics data files"),

  /** Analytical instrument or platform used for data acquisition. */
  analytical_platform: z
    .string()
    .nullable()
    .optional()
    .describe("Analytical platform (e.g. LC-MS, GC-MS, NMR)"),

  /** ESI ionisation mode used during data acquisition. */
  ion_mode: z
    .enum(["positive", "negative"])
    .nullable()
    .optional()
    .describe("Electrospray ionisation mode"),
});

export type MetabolomicsDataset = z.infer<typeof MetabolomicsDatasetSchema>;

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
// Discriminated union
// ---------------------------------------------------------------------------

/**
 * Discriminated union of all dataset variants, keyed on `dataset_type`.
 * Use this as the primary schema when parsing unknown dataset payloads.
 *
 * @example
 * ```ts
 * const ds = DatasetSchema.parse(rawInput);
 * if (ds.dataset_type === "sequencing") { ... }
 * ```
 */
export const DatasetSchema = z.discriminatedUnion("dataset_type", [
  SequencingDatasetSchema,
  TranscriptomicsDatasetSchema,
  MetabolomicsDatasetSchema,
  ClinicalDatasetSchema,
]);

export type Dataset = z.infer<typeof DatasetSchema>;

// ---------------------------------------------------------------------------
// Schema registry for dynamic dispatch
// ---------------------------------------------------------------------------

const DATASET_SCHEMA_MAP = {
  sequencing: SequencingDatasetSchema,
  transcriptomics: TranscriptomicsDatasetSchema,
  metabolomics: MetabolomicsDatasetSchema,
  clinical: ClinicalDatasetSchema,
} satisfies Record<DatasetTypeValue, z.ZodTypeAny>;

/**
 * Parses and validates `data` against the Zod schema that corresponds to the
 * given `modelType` string.  Throws a {@link z.ZodError} when validation fails
 * or an {@link Error} when `modelType` is not a recognised dataset type.
 *
 * @param modelType - One of the strings in {@link DATASET_TYPES}.
 * @param data      - Raw (unknown) payload to validate.
 * @returns         The validated, typed dataset object.
 *
 * @example
 * ```ts
 * const ds = loadDataset("sequencing", {
 *   dataset_id: "ds-001",
 *   raw_paths: ["sample.fastq.gz"],
 *   read_type: "paired",
 * });
 * ```
 */
export function loadDataset(modelType: string, data: unknown): Dataset {
  if (!DATASET_TYPES.includes(modelType as DatasetTypeValue)) {
    throw new Error(
      `Unknown dataset type "${modelType}". ` +
        `Expected one of: ${DATASET_TYPES.join(", ")}.`
    );
  }

  const schema = DATASET_SCHEMA_MAP[modelType as DatasetTypeValue];
  return schema.parse(data) as Dataset;
}
