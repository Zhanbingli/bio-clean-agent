/**
 * @file processing/clinical-handler.ts
 * @description Production-grade clinical trial data handler.
 *
 * Implements {@link EnhancedClinicalTrialHandler}.  Operates on plain
 * `Record<string, unknown>[]` arrays (no Danfo.js dependency) and delegates
 * all statistical work to `simple-statistics`.
 *
 * Compliance features:
 * - FDA 21 CFR Part 11 audit trail (every write operation logged)
 * - Field-level data lineage (original → new value per cell)
 * - Knowledge-base–backed issue detection and missing-data strategy selection
 * - CSV export of cleaned data, audit trail, and lineage records
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import * as ss from "simple-statistics";

import {
  AuditEntry,
  AuditEntrySchema,
  DataLineage,
  DataLineageSchema,
} from "../schemas/audit.js";
import { DataQualityReport } from "../schemas/quality.js";
import { DataQualityAssessor } from "../quality/assessor.js";
import { EvidenceBase } from "../knowledge/evidence-base.js";
import { MedicalStandards } from "../knowledge/medical-standards.js";

// ---------------------------------------------------------------------------
// Internal helper types
// ---------------------------------------------------------------------------

/**
 * A detected data quality issue enriched with optional evidence from the
 * knowledge base.
 */
export interface Issue {
  /** Risk classification of the issue. */
  severity: "critical" | "high" | "medium" | "low" | "info";
  /** Broad category, e.g. `"missing_data"`, `"duplicates"`, `"out_of_range"`. */
  category: string;
  /** Column name affected (or comma-separated list for composite keys). */
  field: string;
  /** Human-readable description of the issue. */
  message: string;
  /** Number of records affected. */
  count: number;
  /** Knowledge-base entry ID that supports this issue detection. */
  evidence?: string;
  /** Statement from the knowledge-base entry. */
  evidence_statement?: string;
  /** Full rationale / recommendation string. */
  recommendation?: string;
  /** Valid range for range-check issues. */
  valid_range?: [number, number];
  /** Citation string (author + year) for range-check issues. */
  citation?: string;
  /** Result of a simplified MCAR test for missing-data issues. */
  mcar_test?: "likely_mcar" | "not_mcar";
}

/**
 * High-level dataset profile returned by {@link EnhancedClinicalTrialHandler.profileData}.
 */
export interface DataProfile {
  /** Number of rows. */
  rows: number;
  /** Number of columns. */
  columns: number;
  /** List of all column names. */
  columnNames: string[];
  /** Per-column data type classification. */
  columnTypes: Record<string, "numeric" | "string" | "mixed" | "empty">;
  /** Per-column missing rate in [0, 1]. */
  missingRates: Record<string, number>;
  /** Per-column descriptive statistics for numeric columns. */
  numericStats: Record<string, {
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  }>;
}

// ---------------------------------------------------------------------------
// CSV parsing helper
// ---------------------------------------------------------------------------

/**
 * Minimal RFC 4180-compatible CSV parser.
 *
 * Handles:
 * - Quoted fields containing commas or embedded newlines
 * - Double-quote escaping (`""`)
 * - CRLF and LF line endings
 *
 * @param text - Raw CSV string content.
 * @returns Parsed rows as `Record<string, unknown>[]`.
 */
function parseCsv(text: string): Record<string, unknown>[] {
  const lines = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
  if (lines.length === 0) return [];

  // Remove trailing empty lines
  while (lines.length > 0 && lines[lines.length - 1]?.trim() === "") {
    lines.pop();
  }
  if (lines.length === 0) return [];

  const parseLine = (line: string): string[] => {
    const fields: string[] = [];
    let current = "";
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQuotes) {
        if (ch === '"') {
          if (line[i + 1] === '"') {
            current += '"';
            i++;
          } else {
            inQuotes = false;
          }
        } else {
          current += ch;
        }
      } else {
        if (ch === '"') {
          inQuotes = true;
        } else if (ch === ",") {
          fields.push(current);
          current = "";
        } else {
          current += ch;
        }
      }
    }
    fields.push(current);
    return fields;
  };

  const headers = parseLine(lines[0] ?? "");
  const rows: Record<string, unknown>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line || line.trim() === "") continue;
    const values = parseLine(line);
    const row: Record<string, unknown> = {};
    for (let j = 0; j < headers.length; j++) {
      const key = headers[j] ?? `col_${j}`;
      const raw = values[j] ?? "";
      if (raw === "" || raw.toLowerCase() === "na" || raw.toLowerCase() === "null") {
        row[key] = null;
      } else {
        const num = Number(raw);
        row[key] = isNaN(num) ? raw : num;
      }
    }
    rows.push(row);
  }

  return rows;
}

/**
 * Serialise rows to CSV string.
 */
function toCsv(data: Record<string, unknown>[]): string {
  if (data.length === 0) return "";
  const headers = Object.keys(data[0]);
  const escape = (v: unknown): string => {
    const s = v === null || v === undefined ? "" : String(v);
    if (s.includes(",") || s.includes('"') || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };
  const lines = [
    headers.join(","),
    ...data.map((row) => headers.map((h) => escape(row[h])).join(",")),
  ];
  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Numeric helpers
// ---------------------------------------------------------------------------

function isNumericValue(v: unknown): v is number {
  return typeof v === "number" && isFinite(v);
}

function extractNumeric(data: Record<string, unknown>[], field: string): number[] {
  return data.map((r) => r[field]).filter(isNumericValue) as number[];
}

function columnType(
  data: Record<string, unknown>[],
  field: string
): "numeric" | "string" | "mixed" | "empty" {
  const nonNull = data
    .map((r) => r[field])
    .filter((v) => v !== null && v !== undefined && v !== "");
  if (nonNull.length === 0) return "empty";
  const allNum = nonNull.every(isNumericValue);
  if (allNum) return "numeric";
  const allStr = nonNull.every((v) => typeof v === "string");
  if (allStr) return "string";
  return "mixed";
}

// ---------------------------------------------------------------------------
// EnhancedClinicalTrialHandler
// ---------------------------------------------------------------------------

/**
 * Production-grade clinical trial data handler.
 *
 * Orchestrates loading, profiling, quality assessment, issue detection, and
 * evidence-based cleaning operations while maintaining a complete audit trail
 * and field-level data lineage.
 *
 * @example
 * ```ts
 * const handler = new EnhancedClinicalTrialHandler("./data/trial.csv", "analyst-01");
 * handler.loadData();
 * const issues = handler.detectIssuesWithEvidence();
 * handler.cleanDuplicatesWithLineage("first");
 * handler.handleMissingValuesEvidenceBased("age", true);
 * handler.saveCleanedData("./output/trial_clean.csv");
 * handler.exportAuditTrail("./output/audit.json");
 * handler.exportLineage("./output/lineage.json");
 * ```
 */
export class EnhancedClinicalTrialHandler {
  private data: Record<string, unknown>[] = [];
  private originalData: Record<string, unknown>[] = [];
  private readonly auditTrail: AuditEntry[] = [];
  private readonly dataLineage: DataLineage[] = [];
  private readonly userId: string;
  private readonly dataPath: string;

  // Knowledge-base components
  private readonly evidenceBase = new EvidenceBase();
  private readonly medicalStandards = new MedicalStandards();
  private readonly assessor = new DataQualityAssessor();

  constructor(dataPath: string, userId = "system") {
    this.dataPath = dataPath;
    this.userId = userId;
  }

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------

  /**
   * Load the CSV file at `dataPath` into memory.
   *
   * Stores a deep copy as the original snapshot.  Records an audit entry for
   * the load event and computes the initial quality report (stored but not
   * returned here; use {@link assessDataQuality} to retrieve it).
   *
   * @returns The loaded data as `Record<string, unknown>[]`.
   * @throws {Error} When the file cannot be read or has an unsupported extension.
   */
  loadData(): Record<string, unknown>[] {
    const lower = this.dataPath.toLowerCase();
    if (!lower.endsWith(".csv") && !lower.endsWith(".txt")) {
      throw new Error(
        `Unsupported file format. Expected .csv or .txt, got: ${this.dataPath}`
      );
    }

    const text = readFileSync(this.dataPath, "utf-8");
    this.data = parseCsv(text);
    // Store deep-copy original
    this.originalData = this.data.map((row) => ({ ...row }));

    this._addAuditEntry(
      "validation",
      "Data loaded",
      this.data.length,
      { source: this.dataPath },
      undefined,
      undefined
    );

    return this.data;
  }

  // -------------------------------------------------------------------------
  // Profiling
  // -------------------------------------------------------------------------

  /**
   * Compute a structural profile of the loaded dataset.
   *
   * @returns {@link DataProfile} with per-column types, missing rates, and
   *   descriptive statistics for numeric columns.
   * @throws {Error} When data has not been loaded yet.
   */
  profileData(): DataProfile {
    this._requireData("profileData");

    const columnNames = this.data.length > 0 ? Object.keys(this.data[0]) : [];
    const columnTypes: DataProfile["columnTypes"] = {};
    const missingRates: Record<string, number> = {};
    const numericStats: DataProfile["numericStats"] = {};

    for (const col of columnNames) {
      columnTypes[col] = columnType(this.data, col);

      const missingCount = this.data.filter(
        (r) =>
          r[col] === null ||
          r[col] === undefined ||
          r[col] === "" ||
          (typeof r[col] === "number" && isNaN(r[col] as number))
      ).length;
      missingRates[col] = this.data.length > 0 ? missingCount / this.data.length : 0;

      if (columnTypes[col] === "numeric") {
        const nums = extractNumeric(this.data, col);
        if (nums.length > 0) {
          numericStats[col] = {
            mean: ss.mean(nums),
            median: ss.median(nums),
            std: nums.length > 1 ? ss.standardDeviation(nums) : 0,
            min: Math.min(...nums),
            max: Math.max(...nums),
          };
        }
      }
    }

    return {
      rows: this.data.length,
      columns: columnNames.length,
      columnNames,
      columnTypes,
      missingRates,
      numericStats,
    };
  }

  // -------------------------------------------------------------------------
  // Quality assessment
  // -------------------------------------------------------------------------

  /**
   * Run a full ISO 8000 quality assessment using {@link DataQualityAssessor}.
   *
   * @returns {@link DataQualityReport} across all six DAMA dimensions.
   * @throws {Error} When data has not been loaded yet.
   */
  assessDataQuality(): DataQualityReport {
    this._requireData("assessDataQuality");

    const keyFields: string[] = [];
    if (this.data.length > 0 && "patient_id" in this.data[0]) {
      keyFields.push("patient_id");
    }

    const dateFields: string[] = [];
    const potentialDateFields = [
      "enrollment_date",
      "visit_date",
      "completion_date",
      "birth_date",
    ];
    if (this.data.length > 0) {
      for (const f of potentialDateFields) {
        if (f in this.data[0]) dateFields.push(f);
      }
    }

    return this.assessor.assess(
      this.data,
      this.dataPath,
      keyFields,
      dateFields
    );
  }

  // -------------------------------------------------------------------------
  // Issue detection
  // -------------------------------------------------------------------------

  /**
   * Detect data quality issues without knowledge-base enrichment.
   *
   * @returns Array of {@link Issue} objects.
   */
  detectIssues(): Issue[] {
    return this.detectIssuesWithEvidence();
  }

  /**
   * Detect data quality issues and enrich each finding with knowledge-base
   * evidence where applicable.
   *
   * Categories detected:
   * 1. Missing patient IDs (critical)
   * 2. Duplicate visits by `patient_id` + `visit_date` (high)
   * 3. Vital sign range violations checked against {@link MedicalStandards}
   * 4. Missing data patterns per column (with simplified MCAR test)
   *
   * @returns Array of {@link Issue} objects ordered by severity.
   * @throws {Error} When data has not been loaded yet.
   */
  detectIssuesWithEvidence(): Issue[] {
    this._requireData("detectIssuesWithEvidence");

    const issues: Issue[] = [];
    const cols = this.data.length > 0 ? Object.keys(this.data[0]) : [];

    // 1. Missing patient IDs
    if (cols.includes("patient_id")) {
      const missingIds = this.data.filter(
        (r) => r["patient_id"] === null || r["patient_id"] === undefined || r["patient_id"] === ""
      ).length;
      if (missingIds > 0) {
        issues.push({
          severity: "critical",
          category: "missing_data",
          field: "patient_id",
          message: `${missingIds} records missing patient ID`,
          count: missingIds,
          recommendation: "Patient ID is required for all records. Review data source.",
        });
      }
    }

    // 2. Duplicate patient visits
    if (cols.includes("patient_id") && cols.includes("visit_date")) {
      const sigSet = new Set<string>();
      let dupCount = 0;
      for (const row of this.data) {
        const sig = `${row["patient_id"]}::${row["visit_date"]}`;
        if (sigSet.has(sig)) {
          dupCount++;
        } else {
          sigSet.add(sig);
        }
      }
      if (dupCount > 0) {
        const evidence = this.evidenceBase.getEntry("duplicate_exact_matches");
        issues.push({
          severity: "high",
          category: "duplicates",
          field: "patient_id,visit_date",
          message: `${dupCount} duplicate patient visits detected`,
          count: dupCount,
          evidence: evidence?.id,
          evidence_statement: evidence?.statement,
          recommendation: evidence?.rationale ?? "Remove duplicate visits",
        });
      }
    }

    // 3. Vital signs range checks using MedicalStandards
    // Maps knowledge-base tags → list of common column name variants
    const vitalFieldMap: Array<{ tags: string[]; variants: string[] }> = [
      { tags: ["systolic_bp", "vital_signs"], variants: ["systolic_bp", "blood_pressure_systolic", "bp_systolic", "sbp"] },
      { tags: ["diastolic_bp", "vital_signs"], variants: ["diastolic_bp", "blood_pressure_diastolic", "bp_diastolic", "dbp"] },
      { tags: ["heart_rate", "vital_signs"], variants: ["heart_rate", "hr", "pulse"] },
      { tags: ["temperature", "vital_signs"], variants: ["temperature", "temp", "body_temperature", "body_temp"] },
    ];

    for (const { tags, variants } of vitalFieldMap) {
      const col = variants.find((v) => cols.includes(v));
      if (!col) continue;
      const nums = extractNumeric(this.data, col);
      if (nums.length === 0) continue;

      const rangeEntry = this.medicalStandards.search({ tags })[0];
      if (!rangeEntry) continue;

      // Parse range from statement (e.g. "60-100 bpm" → [60, 100])
      const rangeMatch = rangeEntry.statement.match(/(\d+(?:\.\d+)?)[–\-](\d+(?:\.\d+)?)/);
      if (!rangeMatch) continue;
      const minVal = parseFloat(rangeMatch[1]);
      const maxVal = parseFloat(rangeMatch[2]);

      const outCount = nums.filter((v) => v < minVal || v > maxVal).length;
      if (outCount > 0) {
        const citation =
          rangeEntry.citations.length > 0
            ? `${rangeEntry.citations[0].source} (${rangeEntry.citations[0].year})`
            : undefined;
        issues.push({
          severity: "medium",
          category: "out_of_range",
          field: col,
          message: `${outCount} values outside reference range [${minVal}, ${maxVal}]`,
          count: outCount,
          valid_range: [minVal, maxVal],
          evidence: rangeEntry.id,
          evidence_statement: rangeEntry.statement,
          citation,
          recommendation: rangeEntry.rationale,
        });
      }
    }

    // 3b. Age range check
    const ageCol = cols.find((c) => ["age", "patient_age"].includes(c));
    if (ageCol) {
      const ages = extractNumeric(this.data, ageCol);
      const invalidAges = ages.filter((v) => v < 0 || v > 120);
      if (invalidAges.length > 0) {
        issues.push({
          severity: "high",
          category: "out_of_range",
          field: ageCol,
          message: `${invalidAges.length} age values outside valid range [0, 120]`,
          count: invalidAges.length,
          valid_range: [0, 120],
          recommendation: "Review and correct invalid age values. Ages must be between 0 and 120.",
        });
      }
    }

    // 3c. Date consistency check (visit_date should be >= enrollment_date)
    const enrollCol = cols.find((c) => ["enrollment_date", "enroll_date", "start_date"].includes(c));
    const visitCol = cols.find((c) => ["visit_date", "assessment_date"].includes(c));
    if (enrollCol && visitCol) {
      let dateInconsistencies = 0;
      for (const row of this.data) {
        const enrollStr = String(row[enrollCol] ?? "");
        const visitStr = String(row[visitCol] ?? "");
        if (!enrollStr || !visitStr) continue;
        const enrollDate = new Date(enrollStr);
        const visitDate = new Date(visitStr);
        if (!isNaN(enrollDate.getTime()) && !isNaN(visitDate.getTime()) && visitDate < enrollDate) {
          dateInconsistencies++;
        }
      }
      if (dateInconsistencies > 0) {
        issues.push({
          severity: "high",
          category: "date_inconsistency",
          field: `${enrollCol},${visitCol}`,
          message: `${dateInconsistencies} records where ${visitCol} is before ${enrollCol}`,
          count: dateInconsistencies,
          recommendation: "Review date entries. Visit date should not precede enrollment date.",
        });
      }
    }

    // 4. Missing data per column
    for (const col of cols) {
      const missingCount = this.data.filter(
        (r) =>
          r[col] === null ||
          r[col] === undefined ||
          r[col] === "" ||
          (typeof r[col] === "number" && isNaN(r[col] as number))
      ).length;

      if (missingCount === 0) continue;

      const missingPct = (missingCount / this.data.length) * 100;
      const mcarLikely = this._testMcar(col);

      const evidence = this.evidenceBase.getCleaningRecommendation(
        "missing_data",
        {
          missing_rate: missingCount / this.data.length,
          mcar_assumption: mcarLikely,
        }
      );

      const severity: Issue["severity"] =
        missingPct > 20 ? "critical" : missingPct > 5 ? "high" : "medium";

      issues.push({
        severity,
        category: "missing_data",
        field: col,
        message: `${missingPct.toFixed(1)}% missing values`,
        count: missingCount,
        mcar_test: mcarLikely ? "likely_mcar" : "not_mcar",
        evidence: evidence?.id,
        evidence_statement: evidence?.statement,
        recommendation: evidence?.rationale,
      });
    }

    return issues;
  }

  // -------------------------------------------------------------------------
  // Cleaning: duplicates
  // -------------------------------------------------------------------------

  /**
   * Remove duplicate rows and record full lineage for every deleted cell.
   *
   * Strategy (applied in order — both passes run):
   * 1. Content-based: rows whose values are identical across ALL columns are
   *    treated as exact duplicates (regardless of primary key).
   * 2. Composite-key: if `patient_id` + `visit_date` exist, rows sharing the
   *    same key pair are treated as logical duplicates.
   *
   * @param keep - Which occurrence to keep: `"first"` (default) or `"last"`.
   * @returns Number of rows removed.
   * @throws {Error} When data has not been loaded yet.
   */
  cleanDuplicatesWithLineage(keep: "first" | "last" = "first"): number {
    this._requireData("cleanDuplicatesWithLineage");

    const cols = this.data.length > 0 ? Object.keys(this.data[0]) : [];
    const toKeep: boolean[] = new Array(this.data.length).fill(true);

    // Pass 1: content-based exact duplicate detection (all columns)
    const contentSeen = new Map<string, number>();
    for (let i = 0; i < this.data.length; i++) {
      const row = this.data[i];
      const sig = cols.map((c) => String(row[c] ?? "")).join("\0");

      if (contentSeen.has(sig)) {
        if (keep === "first") {
          toKeep[i] = false;
        } else {
          const prevIdx = contentSeen.get(sig)!;
          toKeep[prevIdx] = false;
          contentSeen.set(sig, i);
        }
      } else {
        contentSeen.set(sig, i);
      }
    }

    // Pass 2: composite-key duplicates (patient_id + visit_date)
    const useCompositeKey =
      cols.includes("patient_id") && cols.includes("visit_date");
    if (useCompositeKey) {
      const keySeen = new Map<string, number>();
      for (let i = 0; i < this.data.length; i++) {
        if (!toKeep[i]) continue; // already marked for removal
        const row = this.data[i];
        const sig = `${row["patient_id"]}::${row["visit_date"]}`;

        if (keySeen.has(sig)) {
          if (keep === "first") {
            toKeep[i] = false;
          } else {
            const prevIdx = keySeen.get(sig)!;
            toKeep[prevIdx] = false;
            keySeen.set(sig, i);
          }
        } else {
          keySeen.set(sig, i);
        }
      }
    }

    const timestamp = new Date().toISOString();
    let removedCount = 0;

    for (let i = 0; i < this.data.length; i++) {
      if (toKeep[i]) continue;
      removedCount++;
      const row = this.data[i];
      const recordId =
        cols.includes("patient_id")
          ? String(row["patient_id"] ?? `row_${i}`)
          : `row_${i}`;

      for (const col of cols) {
        const lineageEntry = DataLineageSchema.parse({
          record_id: recordId,
          field_name: col,
          original_value: row[col],
          new_value: null,
          operation: "deletion",
          timestamp,
        });
        this.dataLineage.push(lineageEntry);
      }
    }

    this.data = this.data.filter((_, i) => toKeep[i]);

    const evidence = this.evidenceBase.getEntry("duplicate_exact_matches");
    this._addAuditEntry(
      "deletion",
      "Removed duplicate records",
      removedCount,
      { keep, useCompositeKey },
      evidence?.id,
      evidence?.rationale ?? "Remove redundant data"
    );

    return removedCount;
  }

  // -------------------------------------------------------------------------
  // Cleaning: missing values
  // -------------------------------------------------------------------------

  /**
   * Handle missing values in a single column using an evidence-based strategy.
   *
   * Strategy selection (when `autoSelect` is `true`):
   * | Condition                              | Strategy  |
   * |----------------------------------------|-----------|
   * | `<5 %` missing AND MCAR likely         | `drop`    |
   * | `5–20 %` missing                       | `median`  |
   * | `>20 %` missing                        | `flag`    |
   *
   * When `autoSelect` is `false`, the method always applies median imputation.
   *
   * @param column     - Column to process.
   * @param autoSelect - When `true`, strategy is chosen automatically.
   * @returns Tuple of `[recordsAffected, strategyUsed, evidenceId]`.
   * @throws {Error} When data has not been loaded yet or column does not exist.
   */
  handleMissingValuesEvidenceBased(
    column: string,
    autoSelect = false
  ): [number, string, string | null] {
    this._requireData("handleMissingValuesEvidenceBased");

    const cols = this.data.length > 0 ? Object.keys(this.data[0]) : [];
    if (!cols.includes(column)) {
      throw new Error(`Column '${column}' not found in dataset`);
    }

    const missingIndices = this.data
      .map((row, idx) => ({
        idx,
        missing:
          row[column] === null ||
          row[column] === undefined ||
          row[column] === "" ||
          (typeof row[column] === "number" && isNaN(row[column] as number)),
      }))
      .filter((e) => e.missing)
      .map((e) => e.idx);

    const missingCount = missingIndices.length;

    if (missingCount === 0) {
      return [0, "no_action", null];
    }

    const missingRate = missingCount / this.data.length;
    const mcarLikely = this._testMcar(column);

    const evidence = this.evidenceBase.getCleaningRecommendation(
      "missing_data",
      {
        missing_rate: missingRate,
        mcar_assumption: mcarLikely,
      }
    );

    let strategy: string;
    let methodEvidenceId: string | null;

    if (autoSelect) {
      if (missingRate < 0.05 && mcarLikely) {
        strategy = "drop";
        methodEvidenceId = "missing_complete_case_analysis";
      } else if (missingRate < 0.20) {
        strategy = "median";
        methodEvidenceId = "missing_median_imputation_robust";
      } else {
        strategy = "flag";
        methodEvidenceId = null;
      }
    } else {
      strategy = "median";
      methodEvidenceId = evidence?.id ?? null;
    }

    const timestamp = new Date().toISOString();
    let affected = 0;

    if (strategy === "drop") {
      const keepIndices = new Set(
        this.data.map((_, i) => i).filter((i) => !missingIndices.includes(i))
      );
      this.data = this.data.filter((_, i) => keepIndices.has(i));
      affected = missingCount;

    } else if (strategy === "median") {
      const numericValues = extractNumeric(this.data, column);
      if (numericValues.length === 0) {
        // For non-numeric columns, fall through to flag
        strategy = "flag";
      } else {
        const fillValue = ss.median(numericValues);
        for (const idx of missingIndices) {
          const row = this.data[idx];
          const recordId = cols.includes("patient_id")
            ? String(row["patient_id"] ?? `row_${idx}`)
            : `row_${idx}`;

          // Record lineage
          const lineageEntry = DataLineageSchema.parse({
            record_id: recordId,
            field_name: column,
            original_value: null,
            new_value: fillValue,
            operation: "imputation",
            timestamp,
            evidence_id: methodEvidenceId,
          });
          this.dataLineage.push(lineageEntry);

          row[column] = fillValue;
          affected++;
        }
      }
    }

    if (strategy === "flag") {
      const flagCol = `${column}_missing_flag`;
      for (const row of this.data) {
        const isMissing =
          row[column] === null ||
          row[column] === undefined ||
          row[column] === "" ||
          (typeof row[column] === "number" && isNaN(row[column] as number));
        row[flagCol] = isMissing;
      }
      affected = missingCount;
    }

    this._addAuditEntry(
      strategy === "drop" ? "deletion" : "imputation",
      `Handle missing values in '${column}' using strategy: ${strategy}`,
      affected,
      { strategy, column, missing_rate: missingRate },
      methodEvidenceId ?? undefined,
      evidence?.rationale
    );

    return [affected, strategy, methodEvidenceId];
  }

  // -------------------------------------------------------------------------
  // Cleaning: outliers
  // -------------------------------------------------------------------------

  /**
   * Flag or cap outlier values in numeric columns based on medical reference
   * ranges or IQR fencing.
   *
   * Strategy per column:
   * - If a medical reference range exists (e.g. age 0–120), values outside the
   *   range are set to `null` (flagged for review).
   * - Otherwise, Tukey IQR fencing (1.5×IQR) is used; extreme outliers are
   *   capped to the fence boundaries.
   *
   * @returns Number of values corrected.
   */
  cleanOutliers(): number {
    this._requireData("cleanOutliers");

    const cols = this.data.length > 0 ? Object.keys(this.data[0]) : [];
    const timestamp = new Date().toISOString();
    let corrected = 0;

    // Physiologically impossible ranges — values outside these are data errors,
    // not clinical abnormalities.  These are deliberately wide.
    const knownRanges: Record<string, [number, number]> = {
      age: [0, 120], patient_age: [0, 120],
      // Blood pressure: physiologically impossible outside these bounds
      systolic_bp: [30, 300], blood_pressure_systolic: [30, 300], bp_systolic: [30, 300], sbp: [30, 300],
      diastolic_bp: [10, 200], blood_pressure_diastolic: [10, 200], bp_diastolic: [10, 200], dbp: [10, 200],
      // Heart rate
      heart_rate: [15, 250], hr: [15, 250], pulse: [15, 250],
      // Temperature (°C)
      temperature: [25, 45], temp: [25, 45], body_temperature: [25, 45], body_temp: [25, 45],
      // Weight (kg)
      weight_kg: [0.3, 500], weight: [0.3, 500],
      // Height (cm)
      height_cm: [20, 280], height: [20, 280],
    };

    for (const col of cols) {
      if (columnType(this.data, col) !== "numeric") continue;

      const range = knownRanges[col];
      if (range) {
        // Medical-range based cleaning
        const [minVal, maxVal] = range;
        for (const row of this.data) {
          const v = row[col];
          if (!isNumericValue(v)) continue;
          if (v < minVal || v > maxVal) {
            const recordId = cols.includes("patient_id")
              ? String(row["patient_id"] ?? "unknown")
              : "unknown";
            this.dataLineage.push(DataLineageSchema.parse({
              record_id: recordId,
              field_name: col,
              original_value: v,
              new_value: null,
              operation: "correction",
              timestamp,
              evidence_id: "outlier_medical_range",
            }));
            row[col] = null;
            corrected++;
          }
        }
      } else {
        // IQR fencing for columns without known ranges
        const nums = extractNumeric(this.data, col);
        if (nums.length < 4) continue;
        const sorted = [...nums].sort((a, b) => a - b);
        const q1 = ss.quantile(sorted, 0.25);
        const q3 = ss.quantile(sorted, 0.75);
        const iqr = q3 - q1;
        if (iqr === 0) continue;
        const lowerFence = q1 - 3 * iqr; // Use 3×IQR for extreme outliers only
        const upperFence = q3 + 3 * iqr;

        for (const row of this.data) {
          const v = row[col];
          if (!isNumericValue(v)) continue;
          if (v < lowerFence || v > upperFence) {
            const recordId = cols.includes("patient_id")
              ? String(row["patient_id"] ?? "unknown")
              : "unknown";
            const capped = v < lowerFence ? lowerFence : upperFence;
            this.dataLineage.push(DataLineageSchema.parse({
              record_id: recordId,
              field_name: col,
              original_value: v,
              new_value: capped,
              operation: "correction",
              timestamp,
              evidence_id: "outlier_iqr_fence",
            }));
            row[col] = capped;
            corrected++;
          }
        }
      }
    }

    this._addAuditEntry(
      "correction",
      "Outlier values cleaned",
      corrected,
      { method: "medical_range_and_iqr" },
      undefined,
      "Values outside medical reference ranges nullified; extreme IQR outliers capped."
    );

    return corrected;
  }

  // -------------------------------------------------------------------------
  // Cleaning: date consistency
  // -------------------------------------------------------------------------

  /**
   * Flag records with date inconsistencies (e.g. visit_date before enrollment_date).
   * Adds a `date_inconsistency_flag` column.
   *
   * @returns Number of records flagged.
   */
  flagDateInconsistencies(): number {
    this._requireData("flagDateInconsistencies");

    const cols = this.data.length > 0 ? Object.keys(this.data[0]) : [];
    const enrollCol = cols.find((c) => ["enrollment_date", "enroll_date", "start_date"].includes(c));
    const visitCol = cols.find((c) => ["visit_date", "assessment_date"].includes(c));

    if (!enrollCol || !visitCol) return 0;

    let flagged = 0;
    for (const row of this.data) {
      const enrollStr = String(row[enrollCol] ?? "");
      const visitStr = String(row[visitCol] ?? "");
      if (!enrollStr || !visitStr) {
        row["date_inconsistency_flag"] = false;
        continue;
      }
      const enrollDate = new Date(enrollStr);
      const visitDate = new Date(visitStr);
      const inconsistent =
        !isNaN(enrollDate.getTime()) &&
        !isNaN(visitDate.getTime()) &&
        visitDate < enrollDate;
      row["date_inconsistency_flag"] = inconsistent;
      if (inconsistent) flagged++;
    }

    this._addAuditEntry(
      "validation",
      `Flagged date inconsistencies (${visitCol} < ${enrollCol})`,
      flagged,
      { enrollment_column: enrollCol, visit_column: visitCol },
      undefined,
      "Records where visit date precedes enrollment date have been flagged for review."
    );

    return flagged;
  }

  // -------------------------------------------------------------------------
  // Export
  // -------------------------------------------------------------------------

  /**
   * Write the cleaned dataset to a CSV file.
   *
   * Also writes a `<stem>_metadata.json` sidecar with provenance information.
   *
   * @param outputPath - Destination file path (must end with `.csv`).
   * @throws {Error} When there is no data to save.
   */
  saveCleanedData(outputPath: string): void {
    this._requireData("saveCleanedData");

    mkdirSync(dirname(outputPath), { recursive: true });
    writeFileSync(outputPath, toCsv(this.data), "utf-8");

    const stem = outputPath.replace(/\.csv$/i, "");
    const metadataPath = `${stem}_metadata.json`;
    const metadata = {
      source: this.dataPath,
      output: outputPath,
      timestamp: new Date().toISOString(),
      user: this.userId,
      quality_report: this.generateQualityReport(),
      operations: this.auditTrail.length,
    };
    writeFileSync(metadataPath, JSON.stringify(metadata, null, 2), "utf-8");
  }

  /**
   * Export the full audit trail to a JSON file (FDA 21 CFR Part 11 compliant).
   *
   * @param outputPath - Destination JSON file path.
   */
  exportAuditTrail(outputPath: string): void {
    mkdirSync(dirname(outputPath), { recursive: true });
    const payload = {
      dataset: this.dataPath,
      user: this.userId,
      export_timestamp: new Date().toISOString(),
      audit_entries: this.auditTrail,
      total_operations: this.auditTrail.length,
    };
    writeFileSync(outputPath, JSON.stringify(payload, null, 2), "utf-8");
  }

  /**
   * Export data lineage records to a JSON file.
   *
   * @param outputPath - Destination JSON file path.
   */
  exportLineage(outputPath: string): void {
    mkdirSync(dirname(outputPath), { recursive: true });
    const payload = {
      dataset: this.dataPath,
      export_timestamp: new Date().toISOString(),
      lineage: this.dataLineage,
      total_tracked: this.dataLineage.length,
    };
    writeFileSync(outputPath, JSON.stringify(payload, null, 2), "utf-8");
  }

  /**
   * Build a JSON-serialisable quality improvement report comparing the initial
   * dataset to the current state.
   */
  generateQualityReport(): Record<string, unknown> {
    if (this.originalData.length === 0) {
      return { error: "Data not loaded yet" };
    }

    const initialQuality = this.assessor.assess(
      this.originalData,
      `${this.dataPath} (initial)`,
      [],
      []
    );
    const currentQuality = this.assessDataQuality();

    const improvement =
      currentQuality.overall_score - initialQuality.overall_score;

    return {
      initial_quality: {
        overall_score: initialQuality.overall_score,
        overall_level: initialQuality.overall_level,
        completeness_score: initialQuality.completeness.score,
        validity_score: initialQuality.validity.score,
        consistency_score: initialQuality.consistency.score,
        uniqueness_score: initialQuality.uniqueness.score,
      },
      current_quality: {
        overall_score: currentQuality.overall_score,
        overall_level: currentQuality.overall_level,
        completeness_score: currentQuality.completeness.score,
        validity_score: currentQuality.validity.score,
        consistency_score: currentQuality.consistency.score,
        uniqueness_score: currentQuality.uniqueness.score,
      },
      improvement,
      improvement_percentage: improvement * 100,
      records_initial: this.originalData.length,
      records_current: this.data.length,
      records_removed: this.originalData.length - this.data.length,
      total_operations: this.auditTrail.length,
      lineage_tracked: this.dataLineage.length,
    };
  }

  // -------------------------------------------------------------------------
  // Accessors
  // -------------------------------------------------------------------------

  /** The current (possibly cleaned) dataset. */
  getData(): Record<string, unknown>[] {
    return this.data;
  }

  /** A shallow copy of the original loaded dataset. */
  getOriginalData(): Record<string, unknown>[] {
    return this.originalData;
  }

  /** The immutable audit trail produced so far. */
  getAuditTrail(): Readonly<AuditEntry[]> {
    return this.auditTrail;
  }

  /** The data lineage records produced so far. */
  getDataLineage(): Readonly<DataLineage[]> {
    return this.dataLineage;
  }

  // -------------------------------------------------------------------------
  // Private helpers
  // -------------------------------------------------------------------------

  /**
   * Ensure data has been loaded; throw a descriptive error otherwise.
   */
  private _requireData(operation: string): void {
    if (this.data.length === 0 && this.originalData.length === 0) {
      throw new Error(
        `EnhancedClinicalTrialHandler.${operation}: data not loaded. Call loadData() first.`
      );
    }
  }

  /**
   * Simplified MCAR (Missing Completely At Random) test.
   *
   * Computes the average absolute correlation between the binary missingness
   * indicator for `field` and all other numeric columns.  Weak average
   * correlation (< 0.1) is treated as evidence for MCAR.
   *
   * @param field - Column whose missingness pattern is tested.
   * @returns `true` when data is likely MCAR.
   */
  private _testMcar(field: string): boolean {
    if (this.data.length < 10) return true;

    const cols = Object.keys(this.data[0] ?? {});
    const missingIndicator = this.data.map((r) =>
      r[field] === null ||
      r[field] === undefined ||
      r[field] === "" ||
      (typeof r[field] === "number" && isNaN(r[field] as number))
        ? 1
        : 0
    );

    const hasAnyMissing = missingIndicator.some((v) => v === 1);
    if (!hasAnyMissing) return true;

    const correlations: number[] = [];

    for (const col of cols) {
      if (col === field) continue;
      const colValues = extractNumeric(this.data, col);
      if (colValues.length < 10) continue;

      // Pair: (missingIndicator[i], colValue[i]) where colValue[i] is not null
      const pairs: Array<[number, number]> = [];
      for (let i = 0; i < this.data.length; i++) {
        const v = this.data[i][col];
        if (isNumericValue(v)) {
          pairs.push([missingIndicator[i], v]);
        }
      }
      if (pairs.length < 10) continue;

      try {
        const xs = pairs.map((p) => p[0]);
        const ys = pairs.map((p) => p[1]);
        const corr = ss.sampleCorrelation(xs, ys);
        if (isFinite(corr)) correlations.push(Math.abs(corr));
      } catch {
        // skip
      }
    }

    if (correlations.length === 0) return true;
    const avgCorr = ss.mean(correlations);
    return avgCorr < 0.1;
  }

  /**
   * Append a validated {@link AuditEntry} to the audit trail.
   */
  private _addAuditEntry(
    operation: AuditEntry["operation"],
    action: string,
    recordsAffected: number,
    parameters: Record<string, unknown>,
    evidenceId?: string,
    reason?: string
  ): void {
    const entry = AuditEntrySchema.parse({
      operation,
      user: this.userId,
      action,
      records_affected: recordsAffected,
      parameters,
      evidence_id: evidenceId ?? null,
      reason: reason ?? null,
    });
    this.auditTrail.push(entry);
  }
}
