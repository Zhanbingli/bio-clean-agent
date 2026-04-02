/**
 * @file processing/clinical-pipeline.ts
 * @description Clinical trial cleaning pipeline — an 8-step orchestration
 * that leverages {@link EnhancedClinicalTrialHandler} for the heavy lifting.
 *
 */

import { join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";

import { Pipeline, PipelineStep } from "./pipeline.js";
import type { StepResult } from "./pipeline.js";
import { EnhancedClinicalTrialHandler } from "./clinical-handler.js";

// ---------------------------------------------------------------------------
// Pipeline context shape
// ---------------------------------------------------------------------------

interface ClinicalPipelineContext {
  dataset: { raw_paths: string[]; dataset_id?: string };
  dataset_id?: string;
  workdir?: string;
  parameters?: Record<string, unknown>;
  input_file?: string;
  initial_quality?: ReturnType<EnhancedClinicalTrialHandler["assessDataQuality"]>;
  final_quality?: ReturnType<EnhancedClinicalTrialHandler["assessDataQuality"]>;
  results?: Record<string, StepResult>;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// ClinicalTrialCleaningPipeline
// ---------------------------------------------------------------------------

export class ClinicalTrialCleaningPipeline extends Pipeline {
  override name = "clinical_trial_cleaning";
  override datasetType = "clinical";

  private handler: EnhancedClinicalTrialHandler | null = null;
  private readonly outputDir: string;

  constructor(outputDir: string) {
    super();
    this.outputDir = outputDir;

    this.addStep(new PipelineStep("initialize", "Initialize Clinical Handler", (ctx) => this.initialize(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("load_data", "Load and Validate Data", (ctx) => this.loadData(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("assess_quality_initial", "Initial Quality Assessment", (ctx) => this.assessQualityInitial(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("detect_issues", "Detect Data Issues", (ctx) => this.detectIssuesStep(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("clean_duplicates", "Clean Duplicates", (ctx) => this.cleanDuplicates(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("handle_missing", "Handle Missing Values", (ctx) => this.handleMissing(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("assess_quality_final", "Final Quality Assessment", (ctx) => this.assessQualityFinal(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("save_results", "Save Results and Reports", (ctx) => this.saveResults(ctx as ClinicalPipelineContext)));
  }

  // ---- Context validation ------------------------------------------------

  override validateContext(context: Record<string, unknown>): void {
    const ctx = context as ClinicalPipelineContext;
    if (!ctx.dataset) {
      throw new Error("Clinical pipeline requires 'dataset' in context");
    }
    const dataset = ctx.dataset;
    if (!dataset.raw_paths || dataset.raw_paths.length === 0) {
      throw new Error("Clinical dataset must contain at least one raw path (the data file)");
    }
    const inputFile = dataset.raw_paths[0];
    ctx.workdir ??= this.outputDir;
    mkdirSync(ctx.workdir, { recursive: true });
    ctx.input_file = inputFile;
  }

  // ---- Steps -------------------------------------------------------------

  private initialize(ctx: ClinicalPipelineContext): StepResult {
    const inputFile = ctx.input_file!;
    try {
      const userId = (ctx.parameters?.user_id as string) ?? "system";
      this.handler = new EnhancedClinicalTrialHandler(inputFile, userId);
      return { name: "initialize", success: true, details: { input_file: inputFile } };
    } catch (e) {
      return { name: "initialize", success: false, details: {}, error: String(e) };
    }
  }

  private loadData(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "load_data", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const rows = this.handler.loadData();
      const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
      return { name: "load_data", success: true, details: { rows: rows.length, columns } };
    } catch (e) {
      return { name: "load_data", success: false, details: {}, error: String(e) };
    }
  }

  private assessQualityInitial(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "assess_quality_initial", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const metrics = this.handler.assessDataQuality();
      ctx.initial_quality = metrics;
      return { name: "assess_quality_initial", success: true, details: { overall_score: metrics.overall_score, overall_level: metrics.overall_level } };
    } catch (e) {
      return { name: "assess_quality_initial", success: false, details: {}, error: String(e) };
    }
  }

  private detectIssuesStep(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "detect_issues", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const issues = this.handler.detectIssuesWithEvidence();
      const summary: Record<string, number> = {};
      for (const issue of issues) {
        summary[issue.severity] = (summary[issue.severity] ?? 0) + 1;
      }
      return { name: "detect_issues", success: true, details: { issue_count: issues.length, issues_summary: summary } };
    } catch (e) {
      return { name: "detect_issues", success: false, details: {}, error: String(e) };
    }
  }

  private cleanDuplicates(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "clean_duplicates", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const keep = (ctx.parameters?.duplicate_keep_strategy as "first" | "last") ?? "first";
      const removed = this.handler.cleanDuplicatesWithLineage(keep);
      return { name: "clean_duplicates", success: true, details: { removed_count: removed } };
    } catch (e) {
      return { name: "clean_duplicates", success: false, details: {}, error: String(e) };
    }
  }

  private handleMissing(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "handle_missing", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const defaultFields = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "weight"];
      const userFields = ctx.parameters?.missing_value_fields as string[] | undefined;
      const keyFields = userFields ?? defaultFields;

      const fieldDetails: Record<string, unknown> = {};
      let totalHandled = 0;

      for (const field of keyFields) {
        try {
          const [affected, method] = this.handler.handleMissingValuesEvidenceBased(field, true);
          if (affected > 0) {
            fieldDetails[field] = { method, affected };
            totalHandled += affected;
          }
        } catch {
          // Column might not exist — skip silently
        }
      }

      return { name: "handle_missing", success: true, details: { handled_count: totalHandled, field_details: fieldDetails } };
    } catch (e) {
      return { name: "handle_missing", success: false, details: {}, error: String(e) };
    }
  }

  private assessQualityFinal(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "assess_quality_final", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const metrics = this.handler.assessDataQuality();
      ctx.final_quality = metrics;

      let improvement = 0;
      if (ctx.initial_quality) {
        improvement = metrics.overall_score - ctx.initial_quality.overall_score;
      }

      return {
        name: "assess_quality_final",
        success: true,
        details: { overall_score: metrics.overall_score, overall_level: metrics.overall_level, improvement_score: improvement },
      };
    } catch (e) {
      return { name: "assess_quality_final", success: false, details: {}, error: String(e) };
    }
  }

  private saveResults(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "save_results", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const outputPath = ctx.workdir ?? this.outputDir;
      mkdirSync(outputPath, { recursive: true });

      // Save cleaned data
      this.handler.saveCleanedData(join(outputPath, "cleaned_data.csv"));

      // Save audit artifacts
      this.handler.exportAuditTrail(join(outputPath, "audit_trail.json"));
      this.handler.exportLineage(join(outputPath, "data_lineage.json"));

      // Save quality report
      const report = this.handler.generateQualityReport();
      writeFileSync(join(outputPath, "quality_report.json"), JSON.stringify(report, null, 2), "utf-8");

      return { name: "save_results", success: true, details: { output_dir: outputPath } };
    } catch (e) {
      return { name: "save_results", success: false, details: {}, error: String(e) };
    }
  }
}
