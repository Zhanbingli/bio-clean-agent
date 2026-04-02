/**
 * @file repl/tools.ts
 * @description Vercel AI SDK tool definitions for the interactive REPL.
 */

import { tool } from "ai";
import { z } from "zod";
import {
  EnhancedClinicalTrialHandler,
  DataQualityAssessor,
} from "@bio-clean/core";

// ---------------------------------------------------------------------------
// Session state shared across tool executions
// ---------------------------------------------------------------------------

export interface ReplSession {
  handler: EnhancedClinicalTrialHandler | null;
  data: Record<string, unknown>[];
  filePath: string | null;
}

export function createSession(): ReplSession {
  return { handler: null, data: [], filePath: null };
}

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------

/* eslint-disable @typescript-eslint/no-explicit-any */
export function createTools(session: ReplSession): Record<string, any> {
  return {
    load_data: tool({
      description: "Load a CSV data file for analysis and cleaning",
      parameters: z.object({
        filePath: z.string().describe("Path to the CSV file"),
      }),
      execute: async ({ filePath }) => {
        try {
          session.handler = new EnhancedClinicalTrialHandler(filePath, "repl");
          session.data = session.handler.loadData();
          session.filePath = filePath;
          const cols = session.data.length > 0 ? Object.keys(session.data[0]) : [];
          return {
            success: true,
            rows: session.data.length,
            columns: cols.length,
            column_names: cols,
          };
        } catch (e) {
          return { success: false, error: String(e) };
        }
      },
    }),

    inspect_data: tool({
      description: "Inspect loaded data: show first rows, column types, and basic statistics",
      parameters: z.object({
        rows: z.number().optional().describe("Number of rows to preview (default 5)"),
      }),
      execute: async ({ rows = 5 }) => {
        if (!session.handler || session.data.length === 0) {
          return { error: "No data loaded. Use load_data first." };
        }
        const profile = session.handler.profileData();
        const sample = session.data.slice(0, rows);
        return { profile, sample };
      },
    }),

    assess_quality: tool({
      description: "Run a comprehensive ISO 8000 quality assessment on the loaded data",
      parameters: z.object({}),
      execute: async () => {
        if (!session.handler) {
          return { error: "No data loaded. Use load_data first." };
        }
        const report = session.handler.assessDataQuality();
        return report;
      },
    }),

    detect_issues: tool({
      description: "Detect data quality issues with evidence-based analysis",
      parameters: z.object({}),
      execute: async () => {
        if (!session.handler) {
          return { error: "No data loaded. Use load_data first." };
        }
        const issues = session.handler.detectIssuesWithEvidence();
        return {
          issue_count: issues.length,
          issues: issues.slice(0, 20).map((i) => ({
            severity: i.severity,
            category: i.category,
            field: i.field,
            message: i.message,
            recommendation: i.recommendation,
          })),
        };
      },
    }),

    clean_duplicates: tool({
      description: "Remove duplicate records from the loaded data",
      parameters: z.object({
        keep: z.enum(["first", "last"]).optional().describe("Which duplicate to keep"),
      }),
      execute: async ({ keep = "first" }) => {
        if (!session.handler) {
          return { error: "No data loaded. Use load_data first." };
        }
        const removed = session.handler.cleanDuplicatesWithLineage(keep);
        return { removed_count: removed, remaining_rows: session.data.length - removed };
      },
    }),

    handle_missing: tool({
      description: "Handle missing values in a specific column using evidence-based methods",
      parameters: z.object({
        column: z.string().describe("Column name to handle missing values for"),
      }),
      execute: async ({ column }) => {
        if (!session.handler) {
          return { error: "No data loaded. Use load_data first." };
        }
        try {
          const [affected, method, reason] =
            session.handler.handleMissingValuesEvidenceBased(column, true);
          return { affected, method, reason };
        } catch (e) {
          return { error: String(e) };
        }
      },
    }),

    export_data: tool({
      description: "Export the cleaned data to a CSV file",
      parameters: z.object({
        outputPath: z.string().describe("Output file path"),
      }),
      execute: async ({ outputPath }) => {
        if (!session.handler) {
          return { error: "No data loaded. Use load_data first." };
        }
        try {
          session.handler.saveCleanedData(outputPath);
          return { success: true, path: outputPath };
        } catch (e) {
          return { error: String(e) };
        }
      },
    }),
  };
}
