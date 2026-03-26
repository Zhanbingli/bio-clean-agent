/**
 * @file events.ts
 * @description Zod schemas for the internal event bus used to stream
 * real-time job progress, decisions, and log messages.
 * Ported from Python Pydantic models and the original TypeScript interface stubs.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// EventType enumeration
// ---------------------------------------------------------------------------

/** All valid event type string literals, mirroring Python's EventType enum. */
export const EVENT_TYPES = [
  "job.submitted",
  "job.started",
  "job.completed",
  "job.failed",
  "job.cancelled",
  "step.started",
  "step.progress",
  "step.completed",
  "step.failed",
  "decision.required",
  "decision.resolved",
  "data.profiled",
  "issue.detected",
  "issue.resolved",
  "log.info",
  "log.warning",
  "log.error",
] as const;

/**
 * All event type strings emitted by the Bio Clean pipeline.
 *
 * Grouped by domain:
 * - `job.*`      – job lifecycle transitions
 * - `step.*`     – individual pipeline step progress
 * - `decision.*` – human-in-the-loop checkpoints
 * - `data.*`     – data profiling and issue tracking
 * - `log.*`      – structured log messages
 */
export const EventTypeSchema = z
  .enum([
    // Job lifecycle
    "job.submitted",
    "job.started",
    "job.completed",
    "job.failed",
    "job.cancelled",

    // Step progress
    "step.started",
    "step.progress",
    "step.completed",
    "step.failed",

    // Human-in-the-loop decisions
    "decision.required",
    "decision.resolved",

    // Data profiling and issue management
    "data.profiled",
    "issue.detected",
    "issue.resolved",

    // Structured log messages
    "log.info",
    "log.warning",
    "log.error",
  ])
  .describe("Event type emitted by the Bio Clean pipeline");

/** Union type of all event type strings. */
export type EventType = z.infer<typeof EventTypeSchema>;

// ---------------------------------------------------------------------------
// Event
// ---------------------------------------------------------------------------

/**
 * A single event emitted by the pipeline and consumed by subscribers
 * (UI, audit logger, notification service, etc.).
 *
 * The `data` field carries event-specific payload.  Consumers should
 * narrow on `event_type` before accessing `data` to get a typed payload.
 *
 * @example
 * ```ts
 * const event = EventSchema.parse(raw);
 * if (event.event_type === "step.progress") {
 *   const pct = (event.data as { progress_percent: number }).progress_percent;
 * }
 * ```
 */
export const EventSchema = z
  .object({
    /** Discriminant that identifies the kind of event. */
    event_type: EventTypeSchema,

    /**
     * Identifier of the job this event belongs to.
     * Every event is scoped to exactly one job.
     */
    job_id: z
      .string()
      .min(1)
      .describe("Identifier of the job this event is associated with"),

    /**
     * ISO 8601 timestamp when the event was emitted.
     * Defaults to the current moment.
     */
    timestamp: z
      .string()
      .datetime()
      .default(() => new Date().toISOString())
      .describe("Event emission timestamp (ISO 8601)"),

    /**
     * Arbitrary, event-type-specific payload.
     * Consumers narrow on `event_type` to interpret this field correctly.
     *
     * Common shapes:
     * - `job.submitted`      → `{ job_request: JobRequest }`
     * - `step.progress`      → `{ step_name: string; progress_percent: number }`
     * - `decision.required`  → `{ decision_point: DecisionPoint }`
     * - `issue.detected`     → `{ issue: string; column?: string; count?: number }`
     * - `log.*`              → `{ level: string; logger?: string }`
     */
    data: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Event-type-specific payload"),

    /**
     * Short human-readable summary of the event, suitable for display in
     * a notification or log stream.
     */
    message: z
      .string()
      .nullable()
      .optional()
      .describe("Short human-readable description of the event"),
  })
  .describe("A single pipeline event emitted to the internal event bus");

export type Event = z.infer<typeof EventSchema>;

// ---------------------------------------------------------------------------
// Legacy interface aliases (backwards-compatible with original stubs)
// ---------------------------------------------------------------------------

/** Serialised (plain-object) representation of an {@link Event}. */
export type EventDict = Event;

/** Callback signature for event listeners. */
export type EventListener = (event: Event) => void;
