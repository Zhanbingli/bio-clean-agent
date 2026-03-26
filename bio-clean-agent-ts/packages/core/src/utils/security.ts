/**
 * @file security.ts
 * @description Security utilities for the Bio Clean Agent, ported from Python
 * bio_clean_agent/utils/security.py. Uses the Node.js built-in `crypto` module.
 */

import { createHash, randomUUID } from "node:crypto";
import { basename, extname } from "node:path";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Set of permitted file extensions for uploads. */
export const ALLOWED_EXTENSIONS: ReadonlySet<string> = new Set([
  ".csv",
  ".txt",
  ".xlsx",
  ".xls",
  ".tsv",
  ".json",
]);

/** Maximum permitted upload size: 100 MB. */
export const MAX_FILE_SIZE: number = 100 * 1024 * 1024;

/** Maximum permitted filename length in characters. */
export const MAX_FILENAME_LENGTH: number = 255;

// ---------------------------------------------------------------------------
// SecurityError
// ---------------------------------------------------------------------------

/** Thrown when a security validation fails. */
export class SecurityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SecurityError";
  }
}

// ---------------------------------------------------------------------------
// validateFileUpload
// ---------------------------------------------------------------------------

/**
 * Validates a file upload against extension allow-list and size limit.
 *
 * @param filename - Name of the uploaded file.
 * @param size - Size of the file in bytes.
 * @param allowedExtensions - Override the default extension allow-list.
 * @param maxSize - Override the default maximum size in bytes.
 * @throws {@link SecurityError} when validation fails.
 */
export function validateFileUpload(
  filename: string,
  size: number,
  allowedExtensions: ReadonlySet<string> = ALLOWED_EXTENSIONS,
  maxSize: number = MAX_FILE_SIZE
): void {
  if (!filename) {
    throw new SecurityError("Filename cannot be empty");
  }

  if (filename.length > MAX_FILENAME_LENGTH) {
    throw new SecurityError(
      `Filename too long (max ${MAX_FILENAME_LENGTH} characters)`
    );
  }

  const safe = sanitizeFilename(filename);
  if (safe !== filename) {
    throw new SecurityError(
      "Filename contains invalid characters. Use only alphanumeric, dash, underscore, and dot."
    );
  }

  const ext = extname(filename).toLowerCase();
  if (!allowedExtensions.has(ext)) {
    const sorted = [...allowedExtensions].sort().join(", ");
    throw new SecurityError(`File type not allowed. Allowed types: ${sorted}`);
  }

  if (size > maxSize) {
    const mb = (maxSize / (1024 * 1024)).toFixed(1);
    throw new SecurityError(`File too large. Maximum size: ${mb}MB`);
  }
}

// ---------------------------------------------------------------------------
// sanitizeFilename
// ---------------------------------------------------------------------------

/**
 * Sanitizes a filename to prevent directory traversal and injection attacks.
 *
 * - Strips path components (keeps only the basename).
 * - Removes null bytes.
 * - Replaces any character that is not alphanumeric, `.`, `_`, or `-` with `_`.
 * - Prevents hidden files by replacing a leading `.` with `_`.
 * - Falls back to `"unnamed_file"` when the result would be empty.
 *
 * @param filename - Original filename.
 * @returns A filesystem-safe filename string.
 */
export function sanitizeFilename(filename: string): string {
  // Keep only the final path component.
  let name = basename(filename);

  // Strip null bytes.
  name = name.replace(/\0/g, "");

  // Allow only safe characters.
  name = name.replace(/[^a-zA-Z0-9._-]/g, "_");

  // Prevent hidden files.
  if (name.startsWith(".")) {
    name = "_" + name.slice(1);
  }

  // Prevent empty result.
  if (!name || name === ".") {
    name = "unnamed_file";
  }

  return name;
}

// ---------------------------------------------------------------------------
// generateSecureId
// ---------------------------------------------------------------------------

/**
 * Generates a cryptographically secure UUID-based identifier.
 *
 * @returns A UUID v4 string (e.g. `"3b7f…"`).
 */
export function generateSecureId(): string {
  return randomUUID();
}

// ---------------------------------------------------------------------------
// validateApiKeyFormat
// ---------------------------------------------------------------------------

/** Patterns that indicate a placeholder rather than a real API key. */
const INVALID_KEY_PATTERNS: readonly string[] = [
  "test",
  "demo",
  "placeholder",
  "example",
  "your_key_here",
  "xxx",
  "000",
];

/**
 * Validates that an API key has a plausible format.
 *
 * Checks minimum length and rejects common placeholder values.
 *
 * @param apiKey - The API key to validate.
 * @returns `true` when the key passes basic format checks.
 */
export function validateApiKeyFormat(apiKey: string): boolean {
  if (!apiKey || apiKey.length < 20) {
    return false;
  }

  const lower = apiKey.toLowerCase();
  return !INVALID_KEY_PATTERNS.some((pattern) => lower.includes(pattern));
}

// ---------------------------------------------------------------------------
// hashPhiValue
// ---------------------------------------------------------------------------

/**
 * Creates a deterministic SHA-256 hash for a PHI (Protected Health Information) value.
 *
 * @param value - PHI string to hash.
 * @param salt - Optional salt prepended to the value before hashing.
 * @returns Hex-encoded SHA-256 digest.
 */
export function hashPhiValue(value: string, salt?: string): string {
  const input = salt != null ? salt + value : value;
  return createHash("sha256").update(input, "utf8").digest("hex");
}

// ---------------------------------------------------------------------------
// maskSensitiveValue
// ---------------------------------------------------------------------------

/**
 * Masks a sensitive string for safe logging, showing only the last few characters.
 *
 * @param value - Sensitive value to mask (e.g. an API key).
 * @param showChars - Number of trailing characters to reveal (default `4`).
 * @returns A string of the form `"********abc1"`.
 */
export function maskSensitiveValue(value: string, showChars = 4): string {
  if (!value || value.length <= showChars) {
    return "********";
  }
  return "********" + value.slice(-showChars);
}

// ---------------------------------------------------------------------------
// AuditLogEntry / createAuditLogEntry
// ---------------------------------------------------------------------------

/** Shape of a structured audit log entry. */
export interface AuditLogEntry {
  timestamp: string;
  operation: string;
  details: Record<string, unknown>;
}

/**
 * Creates a structured audit log entry for sensitive or auditable operations.
 *
 * @param operation - Human-readable name of the operation (e.g. `"PHI_ACCESS"`).
 * @param details - Arbitrary key/value metadata to attach to the entry.
 * @returns A plain {@link AuditLogEntry} object ready for logging or persistence.
 */
export function createAuditLogEntry(
  operation: string,
  details: Record<string, unknown>
): AuditLogEntry {
  return {
    timestamp: new Date().toISOString(),
    operation,
    details,
  };
}
