/**
 * @file storage.ts
 * @description Storage utilities for the Bio Clean Agent, porting helpers from
 * Python bio_clean_agent/utils/storage.py and adding Node.js file-I/O helpers
 * required by the TypeScript agent.
 */

import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { join } from "node:path";

// ---------------------------------------------------------------------------
// estimateDatasetSize
// ---------------------------------------------------------------------------

/**
 * Sums the on-disk sizes of the given file paths, silently skipping any path
 * that does not exist (mirrors Python's `estimate_dataset_size`).
 *
 * @param paths - Iterable of filesystem paths.
 * @returns Total size in bytes.
 */
export async function estimateDatasetSize(
  paths: Iterable<string>
): Promise<number> {
  let total = 0;
  for (const p of paths) {
    try {
      const info = await stat(p);
      total += info.size;
    } catch {
      // File not found — skip, matching Python behaviour.
    }
  }
  return total;
}

// ---------------------------------------------------------------------------
// formatBytes
// ---------------------------------------------------------------------------

/**
 * Formats a byte count as a human-readable string (e.g. `"1.23 MB"`).
 *
 * @param numBytes - Non-negative integer byte count.
 * @returns Formatted string, e.g. `"0 B"`, `"512.00 KB"`, `"1.50 GB"`.
 */
export function formatBytes(numBytes: number): string {
  if (numBytes <= 0) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB", "TB", "PB"] as const;
  let idx = 0;
  let value = numBytes;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx++;
  }
  return `${value.toFixed(2)} ${units[idx]}`;
}

// ---------------------------------------------------------------------------
// ensureDir
// ---------------------------------------------------------------------------

/**
 * Creates `dirPath` (and any missing ancestors) if it does not already exist.
 * Equivalent to Python's `Path(path).mkdir(parents=True, exist_ok=True)`.
 *
 * @param dirPath - Directory path to create.
 */
export async function ensureDir(dirPath: string): Promise<void> {
  await mkdir(dirPath, { recursive: true });
}

// ---------------------------------------------------------------------------
// saveJson
// ---------------------------------------------------------------------------

/**
 * Serialises `data` to pretty-printed JSON and writes it to `filePath`.
 * The parent directory must already exist (or call {@link ensureDir} first).
 *
 * @param filePath - Destination file path.
 * @param data - Value to serialise. Must be JSON-serialisable.
 */
export async function saveJson(filePath: string, data: unknown): Promise<void> {
  const json = JSON.stringify(data, null, 2);
  await writeFile(filePath, json, "utf8");
}

// ---------------------------------------------------------------------------
// loadJson
// ---------------------------------------------------------------------------

/**
 * Reads and parses a JSON file.
 *
 * @param filePath - Path to the JSON file.
 * @returns The parsed value. Type is `unknown`; callers should validate with
 *          a schema (e.g. Zod) before use.
 * @throws If the file is missing or contains invalid JSON.
 */
export async function loadJson(filePath: string): Promise<unknown> {
  const raw = await readFile(filePath, "utf8");
  return JSON.parse(raw) as unknown;
}

// ---------------------------------------------------------------------------
// saveResults
// ---------------------------------------------------------------------------

/**
 * Saves processing results to a JSON file inside `outputDir`.
 *
 * Creates `outputDir` if it does not exist, then writes `data` as JSON to
 * `<outputDir>/<filename>`. If `filename` is omitted it defaults to
 * `"results.json"`.
 *
 * @param outputDir - Directory in which to save the file.
 * @param data - Serialisable result data.
 * @param filename - Output filename (default `"results.json"`).
 * @returns The absolute path to the written file.
 */
export async function saveResults(
  outputDir: string,
  data: unknown,
  filename = "results.json"
): Promise<string> {
  await ensureDir(outputDir);
  const filePath = join(outputDir, filename);
  await saveJson(filePath, data);
  return filePath;
}
