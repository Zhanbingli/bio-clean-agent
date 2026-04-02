/**
 * @file event-stream.ts
 * @description EventStream class for real-time job monitoring. Uses Node.js EventEmitter as the
 * underlying dispatch mechanism.
 */

import { EventEmitter } from "node:events";
import type { Event, EventListener, EventType } from "../schemas/events.js";

// ---------------------------------------------------------------------------
// Internal constants
// ---------------------------------------------------------------------------

/** Internal EventEmitter channel used for all emitted events. */
const EMIT_CHANNEL = "event";

/** Maximum number of events retained in the in-memory history ring. */
const MAX_HISTORY_SIZE = 1000;

// ---------------------------------------------------------------------------
// EventStream
// ---------------------------------------------------------------------------

/**
 * Manages event emission and subscription for job execution monitoring.
 *
 * - Job-specific listeners receive only events for the subscribed `jobId`.
 * - Global listeners receive every event regardless of `jobId`.
 * - Up to {@link MAX_HISTORY_SIZE} events are retained for replay via
 *   {@link getHistory}.
 *
 * @example
 * ```ts
 * const stream = new EventStream();
 *
 * const unsub = stream.subscribe((ev) => console.log(ev), "job-1");
 *
 * stream.emit({ eventType: "job.started", jobId: "job-1", ... });
 * unsub(); // stop listening
 * ```
 */
export class EventStream {
  /** Per-job listener lists, keyed by jobId. */
  private readonly _listeners = new Map<string, EventListener[]>();
  /** Listeners that receive every event, regardless of jobId. */
  private _globalListeners: EventListener[] = [];
  /** Chronological event ring buffer. */
  private _eventHistory: Event[] = [];

  /** Underlying Node.js emitter used for fan-out dispatch. */
  private readonly _emitter: EventEmitter;

  constructor() {
    this._emitter = new EventEmitter();
    // Prevent the default Node.js warning for many listeners on a single channel.
    this._emitter.setMaxListeners(0);

    // Central dispatch: forward to job-specific and global listeners.
    this._emitter.on(EMIT_CHANNEL, (event: Event) => {
      // Job-specific listeners.
      const jobListeners = this._listeners.get(event.job_id);
      if (jobListeners !== undefined) {
        for (const listener of jobListeners) {
          try {
            listener(event);
          } catch (err) {
            console.error("Error in event listener:", err);
          }
        }
      }

      // Global listeners.
      for (const listener of this._globalListeners) {
        try {
          listener(event);
        } catch (err) {
          console.error("Error in global event listener:", err);
        }
      }
    });
  }

  // -------------------------------------------------------------------------
  // emit
  // -------------------------------------------------------------------------

  /**
   * Emits an event to all matching subscribers and appends it to history.
   *
   * @param event - The event to broadcast.
   */
  emit(event: Event): void {
    // Append to history, trimming to the ring size.
    this._eventHistory.push(event);
    if (this._eventHistory.length > MAX_HISTORY_SIZE) {
      this._eventHistory = this._eventHistory.slice(-MAX_HISTORY_SIZE);
    }

    this._emitter.emit(EMIT_CHANNEL, event);
  }

  // -------------------------------------------------------------------------
  // subscribe
  // -------------------------------------------------------------------------

  /**
   * Subscribes a listener to events.
   *
   * @param listener - Callback invoked for each matching event.
   * @param jobId - When provided, the listener only receives events for this
   *                job. Omit (or pass `undefined`) to receive all events.
   * @returns A zero-argument function that removes the subscription.
   */
  subscribe(listener: EventListener, jobId?: string): () => void {
    if (jobId !== undefined) {
      const existing = this._listeners.get(jobId);
      if (existing !== undefined) {
        existing.push(listener);
      } else {
        this._listeners.set(jobId, [listener]);
      }

      return () => {
        const list = this._listeners.get(jobId);
        if (list !== undefined) {
          const idx = list.indexOf(listener);
          if (idx !== -1) list.splice(idx, 1);
        }
      };
    }

    this._globalListeners.push(listener);
    return () => {
      const idx = this._globalListeners.indexOf(listener);
      if (idx !== -1) this._globalListeners.splice(idx, 1);
    };
  }

  // -------------------------------------------------------------------------
  // getHistory
  // -------------------------------------------------------------------------

  /**
   * Returns a filtered slice of the event history.
   *
   * @param jobId - When provided, only events for this job are returned.
   * @param eventTypes - When provided, only events whose `eventType` is in
   *                     this list are returned.
   * @param limit - Maximum number of events to return, taken from the end of
   *                the (filtered) history (default `100`).
   * @returns A new array of matching events in chronological order.
   */
  getHistory(
    jobId?: string,
    eventTypes?: readonly EventType[],
    limit = 100
  ): Event[] {
    let events = this._eventHistory;

    if (jobId !== undefined) {
      events = events.filter((e) => e.job_id === jobId);
    }

    if (eventTypes !== undefined && eventTypes.length > 0) {
      const typeSet = new Set<EventType>(eventTypes);
      events = events.filter((e) => typeSet.has(e.event_type));
    }

    return events.slice(-limit);
  }

  // -------------------------------------------------------------------------
  // clearHistory
  // -------------------------------------------------------------------------

  /**
   * Clears the event history.
   *
   * @param jobId - When provided, only events for this job are removed.
   *                Omit to clear all history.
   */
  clearHistory(jobId?: string): void {
    if (jobId !== undefined) {
      this._eventHistory = this._eventHistory.filter(
        (e) => e.job_id !== jobId
      );
    } else {
      this._eventHistory = [];
    }
  }
}
