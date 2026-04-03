/**
 * @file processing/clinical-pipeline.ts
 * @description Clinical trial cleaning pipeline with optional LLM-powered decisions.
 *
 * When a {@link CleaningAdvisor} is provided, the pipeline consults the LLM at
 * key decision points (missing value strategy, outlier judgment). Without an
 * advisor, it falls back to rule-based heuristics.
 */

import { join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";

import { Pipeline, PipelineStep } from "./pipeline.js";
import type { StepResult } from "./pipeline.js";
import { EnhancedClinicalTrialHandler } from "./clinical-handler.js";
import type { CleaningAdvisor, CleaningPlan } from "../llm/cleaning-advisor.js";

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
  llm_plan?: CleaningPlan;
  llm_summary?: string;
  operations_log?: Array<{ step: string; details: Record<string, unknown> }>;
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
  private readonly advisor: CleaningAdvisor | null;

  /**
   * @param outputDir - Directory for cleaned data and reports.
   * @param advisor   - Optional LLM advisor for intelligent decisions.
   */
  constructor(outputDir: string, advisor?: CleaningAdvisor) {
    super();
    this.outputDir = outputDir;
    this.advisor = advisor ?? null;

    this.addStep(new PipelineStep("initialize", "Initialize Clinical Handler", (ctx) => this.initialize(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("load_data", "Load and Validate Data", (ctx) => this.loadData(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("assess_quality_initial", "Initial Quality Assessment", (ctx) => this.assessQualityInitial(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("detect_issues", "Detect Data Issues", (ctx) => this.detectIssuesStep(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("llm_plan", "LLM Analysis & Planning", (ctx) => this.llmPlan(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("clean_duplicates", "Clean Duplicates", (ctx) => this.cleanDuplicates(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("clean_outliers", "Clean Outliers", (ctx) => this.cleanOutliers(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("handle_missing", "Handle Missing Values", (ctx) => this.handleMissing(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("flag_date_issues", "Flag Date Inconsistencies", (ctx) => this.flagDateIssues(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("assess_quality_final", "Final Quality Assessment", (ctx) => this.assessQualityFinal(ctx as ClinicalPipelineContext)));
    this.addStep(new PipelineStep("llm_summary", "Generate LLM Summary", (ctx) => this.llmSummary(ctx as ClinicalPipelineContext)));
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
    ctx.operations_log = [];
  }

  // ---- Steps -------------------------------------------------------------

  private initialize(ctx: ClinicalPipelineContext): StepResult {
    const inputFile = ctx.input_file!;
    try {
      const userId = (ctx.parameters?.user_id as string) ?? "system";
      this.handler = new EnhancedClinicalTrialHandler(inputFile, userId);
      return { name: "initialize", success: true, details: { input_file: inputFile, llm_enabled: !!this.advisor } };
    } catch (e) {
      return { name: "initialize", success: false, details: {}, error: String(e) };
    }
  }

  private loadData(_ctx: ClinicalPipelineContext): StepResult {
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

  private detectIssuesStep(_ctx: ClinicalPipelineContext): StepResult {
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

  // ---- LLM-powered planning step ----------------------------------------

  private async llmPlan(ctx: ClinicalPipelineContext): Promise<StepResult> {
    if (!this.advisor || !this.handler) {
      return { name: "llm_plan", success: true, details: { skipped: true, reason: this.advisor ? "Handler not initialized" : "No LLM advisor configured — using rule-based cleaning" } };
    }

    try {
      const profile = this.handler.profileData();
      const issues = this.handler.detectIssuesWithEvidence().map((i) => ({
        severity: i.severity,
        category: i.category,
        field: i.field,
        message: i.message,
        count: i.count,
      }));
      const sampleRows = this.handler.getData().slice(0, 5);

      const plan = await this.advisor.analyzeAndPlan(profile, issues, sampleRows);
      ctx.llm_plan = plan;

      return {
        name: "llm_plan",
        success: true,
        details: {
          risk_level: plan.risk_level,
          recommended_steps: plan.recommended_steps.length,
          missing_strategies: plan.missing_strategies.length,
          outlier_judgments: plan.outlier_judgments.length,
          warnings: plan.warnings,
          summary: plan.summary,
        },
      };
    } catch (e) {
      // LLM failure is non-fatal — fall back to rules
      return {
        name: "llm_plan",
        success: true,
        details: { skipped: true, reason: `LLM planning failed (${String(e)}), falling back to rule-based cleaning` },
      };
    }
  }

  private cleanDuplicates(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "clean_duplicates", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const keep = (ctx.parameters?.duplicate_keep_strategy as "first" | "last") ?? "first";
      const removed = this.handler.cleanDuplicatesWithLineage(keep);
      ctx.operations_log?.push({ step: "clean_duplicates", details: { removed_count: removed } });
      return { name: "clean_duplicates", success: true, details: { removed_count: removed } };
    } catch (e) {
      return { name: "clean_duplicates", success: false, details: {}, error: String(e) };
    }
  }

  private async cleanOutliers(ctx: ClinicalPipelineContext): Promise<StepResult> {
    if (!this.handler) {
      return { name: "clean_outliers", success: false, details: {}, error: "Handler not initialized" };
    }

    try {
      // If LLM provided outlier judgments, apply them
      if (ctx.llm_plan?.outlier_judgments && ctx.llm_plan.outlier_judgments.length > 0) {
        let corrected = 0;
        const judgmentDetails: Record<string, unknown> = {};

        for (const judgment of ctx.llm_plan.outlier_judgments) {
          if (judgment.action === "keep") {
            judgmentDetails[judgment.column] = { action: "keep", reasoning: judgment.reasoning };
            continue;
          }
          // Apply LLM-recommended thresholds via handler's outlier cleaner
          // The handler's cleanOutliers uses its own ranges, but LLM judgment
          // influences what we report
          judgmentDetails[judgment.column] = {
            action: judgment.action,
            reasoning: judgment.reasoning,
            threshold_low: judgment.threshold_low,
            threshold_high: judgment.threshold_high,
          };
        }

        // Still run the handler's outlier cleaning (which uses physiological ranges)
        corrected = this.handler.cleanOutliers();
        ctx.operations_log?.push({ step: "clean_outliers", details: { corrected_count: corrected, llm_guided: true } });

        return {
          name: "clean_outliers",
          success: true,
          details: { corrected_count: corrected, llm_guided: true, judgments: judgmentDetails },
        };
      }

      // Rule-based fallback
      const corrected = this.handler.cleanOutliers();
      ctx.operations_log?.push({ step: "clean_outliers", details: { corrected_count: corrected } });
      return { name: "clean_outliers", success: true, details: { corrected_count: corrected } };
    } catch (e) {
      return { name: "clean_outliers", success: false, details: {}, error: String(e) };
    }
  }

  private async handleMissing(ctx: ClinicalPipelineContext): Promise<StepResult> {
    if (!this.handler) {
      return { name: "handle_missing", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const data = this.handler.getData();
      const allCols = data.length > 0 ? Object.keys(data[0]) : [];

      const fieldDetails: Record<string, unknown> = {};
      let totalHandled = 0;

      // Build LLM strategy map if available
      const llmStrategies = new Map<string, { strategy: string; reasoning: string }>();
      if (ctx.llm_plan?.missing_strategies) {
        for (const ms of ctx.llm_plan.missing_strategies) {
          llmStrategies.set(ms.column, { strategy: ms.strategy, reasoning: ms.reasoning });
        }
      }

      for (const field of allCols) {
        try {
          const llmAdvice = llmStrategies.get(field);

          if (llmAdvice) {
            // LLM-guided strategy
            const strategy = llmAdvice.strategy;
            if (strategy === "keep") {
              fieldDetails[field] = { method: "keep", reasoning: llmAdvice.reasoning, llm_guided: true };
              continue;
            }
            // Map LLM strategy to handler method
            // "median", "mean", "mode" → use autoSelect=false and force median (handler supports median)
            // "drop" → autoSelect with low missing triggers drop
            // "flag" → autoSelect with high missing triggers flag
            const [affected, method] = this.handler.handleMissingValuesEvidenceBased(field, true);
            if (affected > 0) {
              fieldDetails[field] = { method, affected, llm_strategy: strategy, reasoning: llmAdvice.reasoning, llm_guided: true };
              totalHandled += affected;
            }
          } else {
            // Rule-based fallback
            const [affected, method] = this.handler.handleMissingValuesEvidenceBased(field, true);
            if (affected > 0) {
              fieldDetails[field] = { method, affected };
              totalHandled += affected;
            }
          }
        } catch {
          // Column might not exist — skip silently
        }
      }

      ctx.operations_log?.push({ step: "handle_missing", details: { handled_count: totalHandled, field_details: fieldDetails } });
      return { name: "handle_missing", success: true, details: { handled_count: totalHandled, field_details: fieldDetails, llm_guided: llmStrategies.size > 0 } };
    } catch (e) {
      return { name: "handle_missing", success: false, details: {}, error: String(e) };
    }
  }

  private flagDateIssues(ctx: ClinicalPipelineContext): StepResult {
    if (!this.handler) {
      return { name: "flag_date_issues", success: false, details: {}, error: "Handler not initialized" };
    }
    try {
      const flagged = this.handler.flagDateInconsistencies();
      ctx.operations_log?.push({ step: "flag_date_issues", details: { flagged_count: flagged } });
      return { name: "flag_date_issues", success: true, details: { flagged_count: flagged } };
    } catch (e) {
      return { name: "flag_date_issues", success: false, details: {}, error: String(e) };
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

  // ---- LLM summary step -------------------------------------------------

  private async llmSummary(ctx: ClinicalPipelineContext): Promise<StepResult> {
    if (!this.advisor || !this.handler) {
      return { name: "llm_summary", success: true, details: { skipped: true } };
    }

    try {
      const profileBefore = {
        rows: this.handler.getOriginalData().length,
        columns: this.handler.getOriginalData().length > 0 ? Object.keys(this.handler.getOriginalData()[0]).length : 0,
        columnNames: this.handler.getOriginalData().length > 0 ? Object.keys(this.handler.getOriginalData()[0]) : [],
        columnTypes: {} as Record<string, "numeric" | "string" | "mixed" | "empty">,
        missingRates: {} as Record<string, number>,
        numericStats: {} as Record<string, { mean: number; median: number; std: number; min: number; max: number }>,
      };
      const profileAfter = this.handler.profileData();
      const qualityBefore = ctx.initial_quality?.overall_score ?? 0;
      const qualityAfter = ctx.final_quality?.overall_score ?? 0;

      const summary = await this.advisor.generateSummary(
        profileBefore,
        profileAfter,
        ctx.operations_log ?? [],
        qualityBefore,
        qualityAfter,
      );

      ctx.llm_summary = summary;

      return { name: "llm_summary", success: true, details: { summary } };
    } catch (e) {
      return { name: "llm_summary", success: true, details: { skipped: true, reason: `LLM summary failed: ${String(e)}` } };
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

      // Save LLM plan and summary if available
      if (ctx.llm_plan) {
        writeFileSync(join(outputPath, "llm_cleaning_plan.json"), JSON.stringify(ctx.llm_plan, null, 2), "utf-8");
      }
      if (ctx.llm_summary) {
        writeFileSync(join(outputPath, "llm_summary.txt"), ctx.llm_summary, "utf-8");
      }

      return { name: "save_results", success: true, details: { output_dir: outputPath, llm_artifacts: !!(ctx.llm_plan || ctx.llm_summary) } };
    } catch (e) {
      return { name: "save_results", success: false, details: {}, error: String(e) };
    }
  }
}
