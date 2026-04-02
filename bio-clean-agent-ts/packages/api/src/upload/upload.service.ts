/**
 * @file upload/upload.service.ts
 * @description Service responsible for persisting uploaded files, validating
 * them against the @bio-clean/core security rules, and producing a CSV
 * preview for the caller.
 */

import { Injectable, BadRequestException, InternalServerErrorException } from '@nestjs/common';
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import { join, extname } from 'node:path';
import {
  validateFileUpload,
  sanitizeFilename,
  generateSecureId,
  SecurityError,
} from '@bio-clean/core';

/** Metadata and preview returned after a successful upload. */
export interface UploadResult {
  /** Opaque identifier used to reference this file in later API calls. */
  file_id: string;
  /** Sanitised filename as stored on disk. */
  filename: string;
  /** File size in bytes. */
  size: number;
  /** Absolute path to the stored file. */
  path: string;
  /** Up to 5 data rows parsed from a CSV file; `null` for non-CSV uploads. */
  preview: CsvPreview | null;
}

/** Parsed CSV header and first 5 data rows. */
export interface CsvPreview {
  headers: string[];
  rows: string[][];
  total_rows_sampled: number;
}

/**
 * Handles all file-upload concerns: security validation, secure storage,
 * and lightweight CSV preview generation.
 */
@Injectable()
export class UploadService {
  /** Directory where uploaded files are persisted. */
  private readonly uploadsDir: string;

  constructor() {
    this.uploadsDir = join(process.cwd(), 'uploads');
    mkdirSync(this.uploadsDir, { recursive: true });
  }

  /**
   * Validates, stores, and previews an uploaded file.
   *
   * @param file - Multer file object provided by the `FileInterceptor`.
   * @returns An {@link UploadResult} containing the file_id, metadata, and
   *   optional CSV preview.
   * @throws {BadRequestException} when the file fails security validation.
   * @throws {InternalServerErrorException} when the file cannot be written.
   */
  processUpload(file: Express.Multer.File): UploadResult {
    if (!file) {
      throw new BadRequestException('No file was attached to the request.');
    }

    // Run security checks from @bio-clean/core.
    try {
      validateFileUpload(file.originalname, file.size);
    } catch (err) {
      if (err instanceof SecurityError) {
        throw new BadRequestException(err.message);
      }
      throw err;
    }

    const fileId = generateSecureId();
    const safeOriginal = sanitizeFilename(file.originalname);
    const ext = extname(safeOriginal);
    // Prefix the stored filename with the file_id to prevent collisions.
    const storedFilename = `${fileId}${ext}`;
    const storagePath = join(this.uploadsDir, storedFilename);

    try {
      writeFileSync(storagePath, file.buffer);
    } catch (err) {
      throw new InternalServerErrorException(
        `Failed to write uploaded file: ${(err as Error).message}`,
      );
    }

    const preview =
      ext.toLowerCase() === '.csv' || ext.toLowerCase() === '.tsv'
        ? this.parseCsvPreview(file.buffer, ext.toLowerCase() === '.tsv' ? '\t' : ',')
        : null;

    return {
      file_id: fileId,
      filename: safeOriginal,
      size: file.size,
      path: storagePath,
      preview,
    };
  }

  /**
   * Resolves the on-disk path for a given `file_id`.
   *
   * Searches the uploads directory for a file whose name starts with the
   * supplied `file_id`.
   *
   * @param fileId - The opaque file identifier returned by {@link processUpload}.
   * @returns The absolute path when found, or `null` otherwise.
   */
  resolveFilePath(fileId: string): string | null {
    const allowed = ['.csv', '.txt', '.xlsx', '.xls', '.tsv', '.json'];
    for (const ext of allowed) {
      const candidate = join(this.uploadsDir, `${fileId}${ext}`);
      if (existsSync(candidate)) {
        return candidate;
      }
    }
    return null;
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  /**
   * Parses the first 5 data rows of a CSV/TSV buffer for preview purposes.
   *
   * Uses a simple split-based approach; not RFC 4180 compliant for embedded
   * newlines inside quoted fields, but sufficient for quick previews.
   *
   * @param buffer - Raw file content.
   * @param delimiter - Column separator character (`','` or `'\t'`).
   * @returns A {@link CsvPreview} object.
   */
  private parseCsvPreview(buffer: Buffer, delimiter: string): CsvPreview {
    const text = buffer.toString('utf-8');
    const lines = text
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .split('\n')
      .filter((l) => l.trim().length > 0);

    if (lines.length === 0) {
      return { headers: [], rows: [], total_rows_sampled: 0 };
    }

    const splitLine = (line: string): string[] =>
      line.split(delimiter).map((cell) => cell.replace(/^"|"$/g, '').trim());

    const headers = splitLine(lines[0] ?? '');
    const dataLines = lines.slice(1, 6); // up to first 5 data rows
    const rows = dataLines.map(splitLine);

    return {
      headers,
      rows,
      total_rows_sampled: dataLines.length,
    };
  }
}
