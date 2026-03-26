/**
 * @file logging.ts
 * @description Lightweight logger factory, ported from Python
 * bio_clean_agent/utils/logging.py. Uses console output only — no external
 * dependencies — to keep the package footprint minimal.
 */

// ---------------------------------------------------------------------------
// Logger interface
// ---------------------------------------------------------------------------

/** Log severity levels. */
export type LogLevel = "debug" | "info" | "warn" | "error";

/** A named logger instance. */
export interface Logger {
  /** Log a debug-level message (only shown when DEBUG is enabled). */
  debug(message: string, ...args: unknown[]): void;
  /** Log an informational message. */
  info(message: string, ...args: unknown[]): void;
  /** Log a warning. */
  warn(message: string, ...args: unknown[]): void;
  /** Log an error. */
  error(message: string, ...args: unknown[]): void;
}

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

/**
 * Formats a single log line.
 *
 * @example
 * `2026-03-26T12:00:00.000Z [INFO] [my-logger] Starting job`
 */
function formatLine(level: string, name: string, message: string): string {
  const ts = new Date().toISOString();
  return `${ts} [${level.toUpperCase()}] [${name}] ${message}`;
}

class ConsoleLogger implements Logger {
  constructor(private readonly name: string) {}

  debug(message: string, ...args: unknown[]): void {
    // Honour the DEBUG environment variable; omit debug lines in production.
    if (process.env["DEBUG"]) {
      console.debug(formatLine("debug", this.name, message), ...args);
    }
  }

  info(message: string, ...args: unknown[]): void {
    console.info(formatLine("info", this.name, message), ...args);
  }

  warn(message: string, ...args: unknown[]): void {
    console.warn(formatLine("warn", this.name, message), ...args);
  }

  error(message: string, ...args: unknown[]): void {
    console.error(formatLine("error", this.name, message), ...args);
  }
}

// ---------------------------------------------------------------------------
// Logger registry (one instance per name, like Python's logging.getLogger)
// ---------------------------------------------------------------------------

const _registry = new Map<string, Logger>();

/**
 * Returns a named {@link Logger}, creating one on first call for that name.
 *
 * Subsequent calls with the same `name` return the cached instance, matching
 * the behaviour of Python's `logging.getLogger`.
 *
 * @param name - Logger name, typically the module or component name.
 * @returns A {@link Logger} that writes to the console with timestamps.
 *
 * @example
 * ```ts
 * const log = getLogger("bio-clean-agent");
 * log.info("Starting job", { jobId: "abc" });
 * ```
 */
export function getLogger(name = "bio-clean-agent"): Logger {
  const existing = _registry.get(name);
  if (existing !== undefined) {
    return existing;
  }
  const logger = new ConsoleLogger(name);
  _registry.set(name, logger);
  return logger;
}
