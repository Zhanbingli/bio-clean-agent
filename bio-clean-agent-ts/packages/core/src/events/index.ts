/**
 * @file index.ts
 * @description Public barrel for the @bio-clean/core events module.
 * Re-exports {@link EventStream} and the {@link getEventStream} singleton getter.
 */

export { EventStream } from "./event-stream.js";

import { EventStream } from "./event-stream.js";

// ---------------------------------------------------------------------------
// Module-level singleton
// ---------------------------------------------------------------------------

let _instance: EventStream | undefined;

/**
 * Returns the process-wide {@link EventStream} singleton, creating it on the
 * first call (lazy initialisation).
 *
 * @returns The shared {@link EventStream} instance.
 *
 * @example
 * ```ts
 * import { getEventStream } from "@bio-clean/core/events";
 *
 * const stream = getEventStream();
 * stream.subscribe((ev) => console.log(ev.eventType));
 * ```
 */
export function getEventStream(): EventStream {
  if (_instance === undefined) {
    _instance = new EventStream();
  }
  return _instance;
}
