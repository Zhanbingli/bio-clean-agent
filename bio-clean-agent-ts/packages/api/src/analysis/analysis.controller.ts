/**
 * @file analysis/analysis.controller.ts
 * @description REST controller for the `/analyze` endpoint.
 *
 * Accepts `POST /analyze?file_id=<id>` and returns a full analysis of the
 * previously uploaded dataset including a data profile, detected issues, an
 * execution plan, and evidence-based recommendations.
 */

import {
  Controller,
  Post,
  Query,
  BadRequestException,
} from '@nestjs/common';
import { AnalysisService, type AnalysisResult } from './analysis.service.js';

/**
 * Exposes the data-analysis capabilities over HTTP.
 */
@Controller('analyze')
export class AnalysisController {
  constructor(private readonly analysisService: AnalysisService) {}

  /**
   * Analyse an uploaded dataset.
   *
   * ### Request
   * ```
   * POST /analyze?file_id=<uuid>
   * ```
   *
   * ### Response `201`
   * ```json
   * {
   *   "file_id": "<uuid>",
   *   "profile": { "rows": 500, "columns": 12, ... },
   *   "issues": [...],
   *   "plan": { "steps": [...], "warnings": [...] },
   *   "recommendations": [...]
   * }
   * ```
   *
   * @param fileId - `file_id` returned by `POST /upload`.
   * @returns A fully populated {@link AnalysisResult}.
   * @throws {BadRequestException} When `file_id` is missing from the query.
   */
  @Post()
  async analyze(@Query('file_id') fileId: string): Promise<AnalysisResult> {
    if (!fileId || fileId.trim().length === 0) {
      throw new BadRequestException(
        'Query parameter "file_id" is required. ' +
          'Example: POST /analyze?file_id=<uuid>',
      );
    }

    return this.analysisService.analyze(fileId.trim());
  }
}
