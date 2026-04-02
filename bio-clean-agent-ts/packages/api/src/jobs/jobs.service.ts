/**
 * @file jobs/jobs.service.ts
 * @description In-memory job store and lifecycle manager for Bio Clean jobs.
 *
 * Maintains a `Map<string, JobRecord>` that tracks every submitted job through
 * its full lifecycle:  submitted → planning → awaiting_decision → running →
 * completed | failed | cancelled.
 *
 * Real-time events are broadcast to connected WebSocket clients via the
 * lazily-injected {@link JobsGateway}.
 */

import {
  Injectable,
  NotFoundException,
  BadRequestException,
  InternalServerErrorException,
  Logger,
} from '@nestjs/common';
import {
  JobStatusSchema,
  type JobStatus,
  type JobRequest,
  type DecisionPoint,
  type StepProgress,
  type Event,
} from '@bio-clean/core';
import { generateSecureId } from '@bio-clean/core';
import { UploadService } from '../upload/upload.service.js';

// ---------------------------------------------------------------------------
// Domain types for the in-memory store
// ---------------------------------------------------------------------------

/**
 * Full job record held in memory.  A superset of the `JobRequest` schema
 * enriched with runtime tracking fields.
 */
export interface JobRecord {
  /** Unique job identifier (UUID v4). */
  job_id: string;
  /** Current lifecycle status. */
  status: JobStatus;
  /** Original submission payload. */
  request: JobRequest;
  /** ISO 8601 creation timestamp. */
  created_at: string;
  /** ISO 8601 timestamp of the last status change. */
  updated_at: string;
  /** Decision points that require human input. */
  pending_decisions: DecisionPoint[];
  /** Resolved decision records. */
  resolved_decisions: ResolvedDecision[];
  /** Per-step progress snapshots. */
  steps: StepProgress[];
  /** All events emitted so far (for audit / replay). */
  events: Event[];
  /** Terminal error message when status is `"failed"`. */
  error?: string;
  /** Summary produced on successful completion. */
  result_summary?: Record<string, unknown>;
}

/** A resolved decision point with the chosen option stored. */
export interface ResolvedDecision {
  decision_id: string;
  chosen_option: string;
  resolved_at: string;
  resolved_by: string;
}

/** Slim DTO returned in list responses to reduce payload size. */
export interface JobListItem {
  job_id: string;
  status: JobStatus;
  data_type: string;
  created_at: string;
  updated_at: string;
  step_count: number;
  pending_decision_count: number;
}

/** Body shape for the `PUT /jobs/:id/decisions/:decisionId` endpoint. */
export interface ResolveDecisionDto {
  chosen_option: string;
  resolved_by?: string;
}

/**
 * Manages job lifecycle in memory and publishes events to the WebSocket
 * gateway.
 */
@Injectable()
export class JobsService {
  private readonly logger = new Logger(JobsService.name);

  /** Central in-memory store keyed by `job_id`. */
  private readonly jobs = new Map<string, JobRecord>();

  /**
   * Lazily set by {@link JobsGateway} to avoid a circular-dependency issue
   * between the service and the gateway.  Use the setter rather than
   * constructor injection.
   */
  private gateway: { emitJobEvent: (jobId: string, event: Event) => void } | null =
    null;

  constructor(private readonly uploadService: UploadService) {}

  // ---------------------------------------------------------------------------
  // Gateway injection (lazy / setter to break circular dep)
  // ---------------------------------------------------------------------------

  /**
   * Called by {@link JobsGateway} during its `onModuleInit` lifecycle hook.
   *
   * @param gw - Gateway instance that can broadcast events to subscribers.
   */
  setGateway(
    gw: { emitJobEvent: (jobId: string, event: Event) => void },
  ): void {
    this.gateway = gw;
  }

  // ---------------------------------------------------------------------------
  // CRUD
  // ---------------------------------------------------------------------------

  /**
   * Submit a new cleaning job.
   *
   * Validates that the referenced `file_id` exists, persists the job record
   * with status `submitted`, and begins an asynchronous simulated lifecycle.
   *
   * @param fileId - `file_id` returned by `POST /upload`.
   * @param body - Optional additional job configuration (partial `JobRequest`).
   * @returns The newly created {@link JobRecord}.
   * @throws {BadRequestException} When `file_id` is missing or does not resolve.
   */
  submit(fileId: string, body: Partial<JobRequest> = {}): JobRecord {
    if (!fileId || fileId.trim().length === 0) {
      throw new BadRequestException(
        'Query parameter "file_id" is required.',
      );
    }

    const filePath = this.uploadService.resolveFilePath(fileId.trim());
    if (!filePath) {
      throw new BadRequestException(
        `No uploaded file found for file_id "${fileId}". ` +
          'Upload a file first via POST /upload.',
      );
    }

    const jobId = generateSecureId();
    const now = new Date().toISOString();

    const request: JobRequest = {
      job_id: jobId,
      data_type: (body.data_type as JobRequest['data_type']) ?? 'clinical_trial',
      input_paths: [filePath],
      output_dir: `./outputs/${jobId}`,
      objectives: body.objectives ?? [],
      parameters: { ...(body.parameters ?? {}), file_id: fileId },
      priority: body.priority ?? 'normal',
      auto_approve: body.auto_approve ?? false,
      notify_on_decision: body.notify_on_decision ?? true,
      notify_on_completion: body.notify_on_completion ?? true,
    };

    const record: JobRecord = {
      job_id: jobId,
      status: 'submitted',
      request,
      created_at: now,
      updated_at: now,
      pending_decisions: [],
      resolved_decisions: [],
      steps: [],
      events: [],
    };

    this.jobs.set(jobId, record);
    this.emitEvent(jobId, 'job.submitted', { job_request: request }, 'Job submitted');

    // Kick off simulated async lifecycle (no await – fire and forget).
    void this.runJobLifecycle(jobId);

    this.logger.log(`Job ${jobId} submitted for file_id=${fileId}`);
    return record;
  }

  /**
   * Returns a slim summary list of all stored jobs.
   *
   * @returns Array of {@link JobListItem} sorted by `created_at` descending.
   */
  listAll(): JobListItem[] {
    return [...this.jobs.values()]
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      .map(this.toListItem);
  }

  /**
   * Returns the full {@link JobRecord} for the given job ID.
   *
   * @param jobId - UUID of the job.
   * @throws {NotFoundException} When no job with that ID exists.
   */
  findById(jobId: string): JobRecord {
    const record = this.jobs.get(jobId);
    if (!record) {
      throw new NotFoundException(`Job "${jobId}" not found.`);
    }
    return record;
  }

  /**
   * Resolve a pending decision point.
   *
   * Moves the decision from `pending_decisions` to `resolved_decisions` and,
   * when no other pending decisions remain, transitions the job back to
   * `running`.
   *
   * @param jobId - UUID of the job.
   * @param decisionId - UUID of the decision point.
   * @param dto - Resolution payload containing the chosen option.
   * @returns The updated {@link JobRecord}.
   * @throws {NotFoundException} When the job or decision point is not found.
   * @throws {BadRequestException} When the job is not in `awaiting_decision`.
   */
  resolveDecision(
    jobId: string,
    decisionId: string,
    dto: ResolveDecisionDto,
  ): JobRecord {
    const record = this.findById(jobId);

    if (record.status !== 'awaiting_decision') {
      throw new BadRequestException(
        `Job "${jobId}" is not awaiting a decision (current status: ${record.status}).`,
      );
    }

    const decisionIndex = record.pending_decisions.findIndex(
      (d) => d.decision_id === decisionId,
    );
    if (decisionIndex === -1) {
      throw new NotFoundException(
        `Decision "${decisionId}" not found in job "${jobId}".`,
      );
    }

    const [decision] = record.pending_decisions.splice(decisionIndex, 1);
    const resolved: ResolvedDecision = {
      decision_id: decisionId,
      chosen_option: dto.chosen_option,
      resolved_at: new Date().toISOString(),
      resolved_by: dto.resolved_by ?? 'api-user',
    };
    record.resolved_decisions.push(resolved);

    this.emitEvent(
      jobId,
      'decision.resolved',
      { decision_id: decisionId, chosen_option: dto.chosen_option },
      `Decision resolved: ${dto.chosen_option}`,
    );

    // Resume execution when all decisions are handled.
    if (record.pending_decisions.length === 0) {
      this.transitionStatus(record, 'running');
    }

    record.updated_at = new Date().toISOString();
    return record;
  }

  /**
   * Cancel a job that has not yet reached a terminal state.
   *
   * @param jobId - UUID of the job.
   * @throws {NotFoundException} When the job does not exist.
   * @throws {BadRequestException} When the job is already in a terminal state.
   */
  cancel(jobId: string): void {
    const record = this.findById(jobId);

    const terminalStates: JobStatus[] = ['completed', 'failed', 'cancelled'];
    if (terminalStates.includes(record.status)) {
      throw new BadRequestException(
        `Job "${jobId}" is already in a terminal state: ${record.status}.`,
      );
    }

    this.transitionStatus(record, 'cancelled');
    this.emitEvent(jobId, 'job.cancelled', {}, 'Job cancelled by user');
    this.logger.log(`Job ${jobId} cancelled`);
  }

  // ---------------------------------------------------------------------------
  // Simulated job lifecycle
  // ---------------------------------------------------------------------------

  /**
   * Simulates a complete job lifecycle for demonstration / integration-test
   * purposes.  In a production system this would be replaced by actual
   * pipeline execution.
   *
   * Flow:
   * 1. `submitted` → `planning` (immediate)
   * 2. `planning`  → `awaiting_decision` after 1 s (if not auto_approve)
   * 3. `awaiting_decision` → waits for human input or auto-resolves
   * 4. `running`   → `completed` after 2 s
   *
   * @param jobId - UUID of the job to process.
   */
  private async runJobLifecycle(jobId: string): Promise<void> {
    const delay = (ms: number): Promise<void> =>
      new Promise((resolve) => setTimeout(resolve, ms));

    try {
      const record = this.jobs.get(jobId);
      if (!record) return;

      // 1. submitted → planning
      await delay(200);
      if (!this.isActive(jobId)) return;
      this.transitionStatus(record, 'planning');
      this.emitEvent(jobId, 'job.started', {}, 'Planning started');

      await delay(800);
      if (!this.isActive(jobId)) return;

      // 2. Optionally pause for a decision.
      if (!record.request.auto_approve) {
        const decisionId = generateSecureId();
        const decision: DecisionPoint = {
          decision_id: decisionId,
          question:
            'The dataset contains missing values in one or more columns. ' +
            'How should these be handled?',
          context: {
            file_id: record.request.parameters['file_id'],
            missing_value_columns: [],
          },
          options: [
            { id: 'median_impute', label: 'Median imputation', description: 'Replace with column median' },
            { id: 'drop_rows', label: 'Drop rows', description: 'Remove rows with missing values (<5%)' },
            { id: 'flag_only', label: 'Flag only', description: 'Add a missingness indicator column' },
          ],
          default_option: 'median_impute',
          timestamp: new Date().toISOString(),
        };

        record.pending_decisions.push(decision);
        this.transitionStatus(record, 'awaiting_decision');
        this.emitEvent(
          jobId,
          'decision.required',
          { decision_point: decision },
          'Human decision required before execution',
        );

        // Wait up to 30 s for a human decision; then auto-approve.
        const maxWait = 30_000;
        const pollInterval = 500;
        let waited = 0;
        while (record.status === 'awaiting_decision' && waited < maxWait) {
          await delay(pollInterval);
          waited += pollInterval;
        }

        // Auto-approve if still waiting.
        if (record.status === 'awaiting_decision') {
          record.pending_decisions = [];
          record.resolved_decisions.push({
            decision_id: decisionId,
            chosen_option: decision.default_option ?? 'median_impute',
            resolved_at: new Date().toISOString(),
            resolved_by: 'auto-approve',
          });
          this.emitEvent(jobId, 'decision.resolved', { decision_id: decisionId, auto: true }, 'Auto-approved');
          this.transitionStatus(record, 'running');
        }
      } else {
        this.transitionStatus(record, 'running');
      }

      if (!this.isActive(jobId)) return;

      // 3. Running – simulate step progress.
      const stepNames = [
        'load_data',
        'validate_schema',
        'handle_missing_values',
        'remove_duplicates',
        'validate_ranges',
        'export_results',
      ];

      for (let i = 0; i < stepNames.length; i++) {
        if (!this.isActive(jobId)) return;

        const stepName = stepNames[i]!;
        const stepProgress: StepProgress = {
          step_name: stepName,
          status: 'running',
          progress_percent: 0,
          message: `Starting ${stepName}`,
          started_at: new Date().toISOString(),
        };

        // Upsert step.
        const existingIdx = record.steps.findIndex((s) => s.step_name === stepName);
        if (existingIdx >= 0) {
          record.steps[existingIdx] = stepProgress;
        } else {
          record.steps.push(stepProgress);
        }

        this.emitEvent(jobId, 'step.started', { step_name: stepName }, `Step started: ${stepName}`);

        await delay(300);
        if (!this.isActive(jobId)) return;

        // Mark step complete.
        const completedStep: StepProgress = {
          ...stepProgress,
          status: 'completed',
          progress_percent: 100,
          message: `${stepName} completed`,
          completed_at: new Date().toISOString(),
        };
        const idx = record.steps.findIndex((s) => s.step_name === stepName);
        if (idx >= 0) record.steps[idx] = completedStep;

        this.emitEvent(
          jobId,
          'step.completed',
          { step_name: stepName, progress_percent: 100 },
          `Step completed: ${stepName}`,
        );
      }

      // 4. Complete the job.
      if (!this.isActive(jobId)) return;
      record.result_summary = {
        steps_executed: stepNames.length,
        completed_at: new Date().toISOString(),
      };
      this.transitionStatus(record, 'completed');
      this.emitEvent(
        jobId,
        'job.completed',
        { result_summary: record.result_summary },
        'Job completed successfully',
      );
      this.logger.log(`Job ${jobId} completed`);
    } catch (err) {
      const record = this.jobs.get(jobId);
      if (record && !['completed', 'failed', 'cancelled'].includes(record.status)) {
        record.error = (err as Error).message;
        this.transitionStatus(record, 'failed');
        this.emitEvent(jobId, 'job.failed', { error: record.error }, `Job failed: ${record.error}`);
        this.logger.error(`Job ${jobId} failed`, (err as Error).stack);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private isActive(jobId: string): boolean {
    const record = this.jobs.get(jobId);
    if (!record) return false;
    return !['completed', 'failed', 'cancelled'].includes(record.status);
  }

  private transitionStatus(record: JobRecord, next: JobStatus): void {
    const valid = JobStatusSchema.safeParse(next);
    if (!valid.success) {
      throw new InternalServerErrorException(`Invalid job status: ${next}`);
    }
    record.status = next;
    record.updated_at = new Date().toISOString();
  }

  private emitEvent(
    jobId: string,
    eventType: Event['event_type'],
    data: Record<string, unknown>,
    message: string,
  ): void {
    const event: Event = {
      event_type: eventType,
      job_id: jobId,
      timestamp: new Date().toISOString(),
      data,
      message,
    };

    const record = this.jobs.get(jobId);
    if (record) {
      record.events.push(event);
    }

    this.gateway?.emitJobEvent(jobId, event);
  }

  private readonly toListItem = (r: JobRecord): JobListItem => ({
    job_id: r.job_id,
    status: r.status,
    data_type: r.request.data_type,
    created_at: r.created_at,
    updated_at: r.updated_at,
    step_count: r.steps.length,
    pending_decision_count: r.pending_decisions.length,
  });
}
