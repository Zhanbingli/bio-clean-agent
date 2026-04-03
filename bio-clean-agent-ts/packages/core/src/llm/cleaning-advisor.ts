/**
 * @file llm/cleaning-advisor.ts
 * @description LLM-powered advisor that makes intelligent cleaning decisions.
 *
 * Uses Vercel AI SDK `generateObject` for structured decisions and
 * `generateText` for natural language summaries. Falls back gracefully
 * when LLM is unavailable.
 */

import { generateObject, generateText } from "ai";
import { createOpenAI } from "@ai-sdk/openai";
import { z } from "zod";
import type { DataProfile } from "../processing/clinical-handler.js";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

export interface LLMAdvisorConfig {
  /** API key for the LLM provider. */
  apiKey: string;
  /** Base URL override (e.g. DeepSeek, Ollama). */
  baseURL?: string;
  /** Model identifier (default: "gpt-4o-mini"). */
  model?: string;
}

// ---------------------------------------------------------------------------
// Zod schemas for structured LLM output
// ---------------------------------------------------------------------------

const MissingStrategyDecisionSchema = z.object({
  column: z.string().describe("Column name"),
  strategy: z.enum(["median", "mean", "mode", "drop", "flag", "keep"]).describe("Chosen imputation strategy"),
  reasoning: z.string().describe("Why this strategy was chosen for this specific column"),
  confidence: z.number().min(0).max(1).describe("Confidence in the decision (0-1)"),
});

const OutlierJudgmentSchema = z.object({
  column: z.string().describe("Column name"),
  action: z.enum(["nullify", "cap", "keep", "flag"]).describe("What to do with outliers"),
  reasoning: z.string().describe("Clinical reasoning for this decision"),
  threshold_low: z.number().optional().describe("Lower bound for valid values"),
  threshold_high: z.number().optional().describe("Upper bound for valid values"),
});

const CleaningPlanSchema = z.object({
  summary: z.string().describe("Brief natural language summary of the data quality situation"),
  risk_level: z.enum(["low", "medium", "high", "critical"]).describe("Overall data quality risk"),
  recommended_steps: z.array(z.object({
    step: z.string().describe("Cleaning step name"),
    priority: z.enum(["must", "should", "could"]).describe("Priority level"),
    reasoning: z.string().describe("Why this step is needed"),
  })).describe("Ordered list of recommended cleaning actions"),
  missing_strategies: z.array(MissingStrategyDecisionSchema).describe("Per-column missing value strategies"),
  outlier_judgments: z.array(OutlierJudgmentSchema).describe("Per-column outlier handling decisions"),
  warnings: z.array(z.string()).describe("Important warnings or caveats"),
});

export type CleaningPlan = z.infer<typeof CleaningPlanSchema>;
export type MissingStrategyDecision = z.infer<typeof MissingStrategyDecisionSchema>;
export type OutlierJudgment = z.infer<typeof OutlierJudgmentSchema>;

// ---------------------------------------------------------------------------
// CleaningAdvisor
// ---------------------------------------------------------------------------

/**
 * LLM-powered cleaning advisor.
 *
 * Analyzes data profiles and issues to produce intelligent, context-aware
 * cleaning decisions with full reasoning chains.
 */
export class CleaningAdvisor {
  private readonly model;

  constructor(config: LLMAdvisorConfig) {
    const provider = createOpenAI({
      apiKey: config.apiKey,
      baseURL: config.baseURL,
    });
    this.model = provider(config.model ?? "gpt-4o-mini");
  }

  // -----------------------------------------------------------------------
  // Main: analyze data and produce a full cleaning plan
  // -----------------------------------------------------------------------

  /**
   * Analyze data profile and detected issues, then produce a comprehensive
   * cleaning plan with per-column strategies.
   */
  async analyzeAndPlan(
    profile: DataProfile,
    issues: Array<{ severity: string; category: string; field: string; message: string; count: number }>,
    sampleRows: Record<string, unknown>[],
  ): Promise<CleaningPlan> {
    const prompt = this._buildAnalysisPrompt(profile, issues, sampleRows);

    const result = await generateObject({
      model: this.model,
      schema: CleaningPlanSchema,
      prompt,
      temperature: 0.1,
    });

    return result.object;
  }

  // -----------------------------------------------------------------------
  // Focused: missing value strategy for a single column
  // -----------------------------------------------------------------------

  /**
   * Decide the best missing value strategy for a specific column.
   */
  async decideMissingStrategy(
    column: string,
    profile: DataProfile,
    missingCount: number,
    totalCount: number,
    sampleValues: unknown[],
  ): Promise<MissingStrategyDecision> {
    const colType = profile.columnTypes[column] ?? "unknown";
    const stats = profile.numericStats[column];
    const missingRate = ((missingCount / totalCount) * 100).toFixed(1);

    const prompt = `You are a clinical data quality expert.

Decide the best strategy for handling missing values in the column "${column}".

Column info:
- Type: ${colType}
- Missing: ${missingCount}/${totalCount} (${missingRate}%)
- Sample non-null values: ${JSON.stringify(sampleValues.slice(0, 10))}
${stats ? `- Stats: mean=${stats.mean.toFixed(2)}, median=${stats.median.toFixed(2)}, std=${stats.std.toFixed(2)}, min=${stats.min}, max=${stats.max}` : ""}

Clinical context:
- This is clinical trial data where data integrity is critical for regulatory compliance
- Patient safety data must not be fabricated
- Statistical analyses downstream depend on correct imputation choices

Choose the most appropriate strategy and explain your clinical reasoning.`;

    const result = await generateObject({
      model: this.model,
      schema: MissingStrategyDecisionSchema,
      prompt,
      temperature: 0.1,
    });

    return result.object;
  }

  // -----------------------------------------------------------------------
  // Focused: outlier judgment for a column
  // -----------------------------------------------------------------------

  /**
   * Judge whether outlier values in a column are real clinical data or errors.
   */
  async judgeOutliers(
    column: string,
    outlierValues: number[],
    normalRange: { min: number; max: number; mean: number; median: number },
    totalCount: number,
  ): Promise<OutlierJudgment> {
    const prompt = `You are a clinical data quality expert.

Evaluate outlier values in the column "${column}" from a clinical trial dataset.

Normal distribution:
- Range: [${normalRange.min}, ${normalRange.max}]
- Mean: ${normalRange.mean.toFixed(2)}, Median: ${normalRange.median.toFixed(2)}
- Total records: ${totalCount}

Outlier values found: ${JSON.stringify(outlierValues)}

Clinical context:
- In clinical trials, extreme values can be real (e.g., severe hypertension BP=180) or data entry errors (e.g., age=-5, BP=9999)
- Real clinical abnormalities should be KEPT as they are scientifically important
- Only clearly impossible values (physiologically impossible) should be nullified
- When uncertain, prefer flagging over removing

Decide what to do with these outlier values and explain your clinical reasoning.`;

    const result = await generateObject({
      model: this.model,
      schema: OutlierJudgmentSchema,
      prompt,
      temperature: 0.1,
    });

    return result.object;
  }

  // -----------------------------------------------------------------------
  // Summary: natural language quality report
  // -----------------------------------------------------------------------

  /**
   * Generate a human-readable summary of cleaning results.
   */
  async generateSummary(
    profileBefore: DataProfile,
    profileAfter: DataProfile,
    operationsPerformed: Array<{ step: string; details: Record<string, unknown> }>,
    qualityBefore: number,
    qualityAfter: number,
  ): Promise<string> {
    const prompt = `You are a clinical data quality expert writing a brief cleaning report.

Dataset: ${profileBefore.rows} records, ${profileBefore.columns} columns

Quality score: ${(qualityBefore * 100).toFixed(1)}% → ${(qualityAfter * 100).toFixed(1)}% (${qualityAfter > qualityBefore ? "+" : ""}${((qualityAfter - qualityBefore) * 100).toFixed(1)}%)

Operations performed:
${operationsPerformed.map((op) => `- ${op.step}: ${JSON.stringify(op.details)}`).join("\n")}

Records: ${profileBefore.rows} → ${profileAfter.rows}

Write a concise (3-5 sentence) clinical data quality summary. Mention key improvements, remaining concerns, and whether the data is ready for analysis. Use professional but accessible language.`;

    const result = await generateText({
      model: this.model,
      prompt,
      temperature: 0.3,
      maxTokens: 300,
    });

    return result.text;
  }

  // -----------------------------------------------------------------------
  // Private: prompt construction
  // -----------------------------------------------------------------------

  private _buildAnalysisPrompt(
    profile: DataProfile,
    issues: Array<{ severity: string; category: string; field: string; message: string; count: number }>,
    sampleRows: Record<string, unknown>[],
  ): string {
    const issuesSummary = issues
      .map((i) => `  [${i.severity.toUpperCase()}] ${i.field}: ${i.message} (${i.count} records)`)
      .join("\n");

    const columnInfo = profile.columnNames
      .map((col) => {
        const type = profile.columnTypes[col];
        const missing = profile.missingRates[col];
        const stats = profile.numericStats[col];
        let info = `  ${col}: type=${type}, missing=${(missing * 100).toFixed(1)}%`;
        if (stats) {
          info += `, range=[${stats.min}, ${stats.max}], mean=${stats.mean.toFixed(2)}, std=${stats.std.toFixed(2)}`;
        }
        return info;
      })
      .join("\n");

    return `You are a senior clinical data quality expert. Analyze this clinical trial dataset and produce a comprehensive cleaning plan.

DATASET OVERVIEW:
- Records: ${profile.rows}
- Columns: ${profile.columns}

COLUMN DETAILS:
${columnInfo}

DETECTED ISSUES:
${issuesSummary || "  No issues detected"}

SAMPLE DATA (first 3 rows):
${JSON.stringify(sampleRows.slice(0, 3), null, 2)}

REQUIREMENTS:
1. Clinical trial data must comply with FDA 21 CFR Part 11
2. Patient safety data (vital signs, adverse events) must not be fabricated
3. Real clinical abnormalities (e.g., hypertension, fever) must be preserved
4. Only physiologically impossible values should be corrected
5. All decisions must be traceable and justified

Produce a cleaning plan with:
- Overall risk assessment
- Prioritized cleaning steps
- Per-column missing value strategies (considering clinical semantics)
- Per-column outlier judgments (distinguishing real abnormalities from errors)
- Warnings about data quality concerns`;
  }
}
