/**
 * @file jobs/jobs.controller.ts
 * @description REST controller exposing the job management API.
 *
 * Endpoints:
 * - POST   /jobs?file_id=xxx       – submit a new cleaning job
 * - GET    /jobs                   – list all jobs (slim DTO)
 * - GET    /jobs/:id               – full job record
 * - PUT    /jobs/:id/decisions/:decisionId – resolve a human-in-the-loop decision
 * - DELETE /jobs/:id               – cancel a running job
 */

import {
  Controller,
  Post,
  Get,
  Put,
  Delete,
  Param,
  Query,
  Body,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import {
  JobsService,
  type JobRecord,
  type JobListItem,
  type ResolveDecisionDto,
} from './jobs.service.js';
import type { JobRequest } from '@bio-clean/core';

/**
 * Manages job resources at the `/jobs` path prefix.
 */
@Controller('jobs')
export class JobsController {
  constructor(private readonly jobsService: JobsService) {}

  /**
   * Submit a new data-cleaning job.
   *
   * ### Request
   * ```
   * POST /jobs?file_id=<uuid>
   * Content-Type: application/json  (optional body with JobRequest overrides)
   * ```
   *
   * @param fileId - `file_id` returned by `POST /upload`.
   * @param body - Optional partial `JobRequest` configuration.
   * @returns The newly created {@link JobRecord}.
   */
  @Post()
  @HttpCode(HttpStatus.CREATED)
  submit(
    @Query('file_id') fileId: string,
    @Body() body: Partial<JobRequest> = {},
  ): JobRecord {
    return this.jobsService.submit(fileId, body);
  }

  /**
   * List all jobs in reverse chronological order (newest first).
   *
   * @returns An array of slim {@link JobListItem} DTOs.
   */
  @Get()
  listAll(): JobListItem[] {
    return this.jobsService.listAll();
  }

  /**
   * Retrieve the full record for a single job.
   *
   * @param id - UUID of the job.
   * @returns The complete {@link JobRecord}.
   */
  @Get(':id')
  findOne(@Param('id') id: string): JobRecord {
    return this.jobsService.findById(id);
  }

  /**
   * Resolve a pending human-in-the-loop decision.
   *
   * ### Request body
   * ```json
   * { "chosen_option": "median_impute", "resolved_by": "dr-smith" }
   * ```
   *
   * @param id - UUID of the job.
   * @param decisionId - UUID of the decision point.
   * @param dto - Resolution payload.
   * @returns The updated {@link JobRecord}.
   */
  @Put(':id/decisions/:decisionId')
  resolveDecision(
    @Param('id') id: string,
    @Param('decisionId') decisionId: string,
    @Body() dto: ResolveDecisionDto,
  ): JobRecord {
    return this.jobsService.resolveDecision(id, decisionId, dto);
  }

  /**
   * Cancel a non-terminal job.
   *
   * @param id - UUID of the job to cancel.
   * @returns HTTP 204 No Content on success.
   */
  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  cancel(@Param('id') id: string): void {
    this.jobsService.cancel(id);
  }
}
