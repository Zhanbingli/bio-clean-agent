/**
 * @file analysis/analysis.service.ts
 * @description Service that orchestrates data profiling, smart planning, and
 * evidence-based recommendations for a previously uploaded file.
 *
 * Delegates heavy lifting to:
 * - {@link EnhancedClinicalTrialHandler} – loads the CSV and profiles columns
 * - {@link SmartPlanner} – constructs an evidence-aware execution plan
 * - {@link EvidenceBase} – surfaces knowledge-base recommendations
 */

import {
  Injectable,
  NotFoundException,
  BadRequestException,
  InternalServerErrorException,
} from '@nestjs/common';
import {
  EnhancedClinicalTrialHandler,
  SmartPlanner,
  EvidenceBase,
  type ExecutionPlan,
} from '@bio-clean/core';
import type { Issue } from '@bio-clean/core';
import { UploadService } from '../upload/upload.service.js';

/** Complete response returned by the analysis endpoint. */
export interface AnalysisResult {
  file_id: string;
  profile: DataProfileSummary;
  issues: Issue[];
  plan: ExecutionPlan;
  recommendations: RecommendationSummary[];
}

/** Condensed view of the data profile for API consumers. */
export interface DataProfileSummary {
  rows: number;
  columns: number;
  column_names: string[];
  column_types: Record<string, string>;
  missing_rates: Record<string, number>;
  numeric_stats: Record<string, {
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  }>;
}

/** A single knowledge-base recommendation surfaced for the dataset. */
export interface RecommendationSummary {
  id: string;
  category: string;
  statement: string;
  rationale: string;
  confidence: string;
}

/**
 * Runs the full analysis pipeline on an uploaded file identified by its
 * `file_id`.
 */
@Injectable()
export class AnalysisService {
  private readonly evidenceBase = new EvidenceBase();

  constructor(private readonly uploadService: UploadService) {}

  /**
   * Profiles the dataset, detects issues, and generates a smart cleaning plan.
   *
   * @param fileId - The `file_id` returned by the upload endpoint.
   * @returns An {@link AnalysisResult} containing profile, issues, plan, and
   *   recommendations.
   * @throws {NotFoundException} When no file is found for the given `file_id`.
   * @throws {BadRequestException} When the file cannot be loaded by the handler.
   * @throws {InternalServerErrorException} For unexpected processing errors.
   */
  async analyze(fileId: string): Promise<AnalysisResult> {
    const filePath = this.uploadService.resolveFilePath(fileId);
    if (!filePath) {
      throw new NotFoundException(
        `No uploaded file found for file_id "${fileId}". ` +
          'Please upload the file first via POST /upload.',
      );
    }

    let handler: EnhancedClinicalTrialHandler;
    try {
      handler = new EnhancedClinicalTrialHandler(filePath, 'api-analysis');
      handler.loadData();
    } catch (err) {
      throw new BadRequestException(
        `Failed to load dataset: ${(err as Error).message}`,
      );
    }

    // -- Profile --
    let rawProfile: ReturnType<EnhancedClinicalTrialHandler['profileData']>;
    try {
      rawProfile = handler.profileData();
    } catch (err) {
      throw new InternalServerErrorException(
        `Profiling failed: ${(err as Error).message}`,
      );
    }

    const profile: DataProfileSummary = {
      rows: rawProfile.rows,
      columns: rawProfile.columns,
      column_names: rawProfile.columnNames,
      column_types: rawProfile.columnTypes,
      missing_rates: rawProfile.missingRates,
      numeric_stats: rawProfile.numericStats,
    };

    // -- Issues --
    let issues: Issue[];
    try {
      issues = handler.detectIssuesWithEvidence();
    } catch (err) {
      throw new InternalServerErrorException(
        `Issue detection failed: ${(err as Error).message}`,
      );
    }

    // -- Plan via SmartPlanner --
    const planner = new SmartPlanner();

    // Build a DataProfile compatible with SmartPlanner.createPlan
    const plannerProfile: Record<string, unknown> = {
      row_count: rawProfile.rows,
      column_count: rawProfile.columns,
      columns: Object.fromEntries(
        rawProfile.columnNames.map((col) => [
          col,
          {
            dtype: rawProfile.columnTypes[col],
            missing_rate: rawProfile.missingRates[col] ?? 0,
            missing_count: Math.round(
              (rawProfile.missingRates[col] ?? 0) * rawProfile.rows,
            ),
          },
        ]),
      ),
    };

    const objectives = issues
      .filter((i) => i.severity === 'critical' || i.severity === 'high')
      .map((i) => `Address ${i.category} in column ${i.field}`);

    let plan: ExecutionPlan;
    try {
      plan = planner.createPlan(
        fileId,
        'clinical_trial',
        objectives,
        plannerProfile as Parameters<SmartPlanner['createPlan']>[3],
      );
    } catch (err) {
      throw new InternalServerErrorException(
        `Planning failed: ${(err as Error).message}`,
      );
    }

    // -- Recommendations --
    const categories = [...new Set(issues.map((i) => i.category))];
    const recommendations: RecommendationSummary[] = [];

    for (const category of categories) {
      const issueForCategory = issues.find((i) => i.category === category);
      const entry = this.evidenceBase.getCleaningRecommendation(
        category,
        {
          missing_rate: issueForCategory
            ? (rawProfile.missingRates[issueForCategory.field] ?? 0)
            : 0,
        },
      );
      if (entry) {
        recommendations.push({
          id: entry.id,
          category: entry.category,
          statement: entry.statement,
          rationale: entry.rationale,
          confidence: entry.confidence,
        });
      }
    }

    return {
      file_id: fileId,
      profile,
      issues,
      plan,
      recommendations,
    };
  }
}
