/**
 * @file upload/upload.controller.ts
 * @description REST controller for the `/upload` endpoint.
 *
 * Accepts `multipart/form-data` POST requests with a single `file` field,
 * delegates validation and persistence to {@link UploadService}, and returns
 * structured upload metadata with an optional CSV preview.
 */

import {
  Controller,
  Post,
  UseInterceptors,
  UploadedFile,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { UploadService, type UploadResult } from './upload.service.js';

/**
 * Handles file uploads at `POST /upload`.
 *
 * Files are held in memory by Multer (no temp-file I/O on the worker) and
 * then written to the `uploads/` directory by {@link UploadService}.
 */
@Controller('upload')
export class UploadController {
  constructor(private readonly uploadService: UploadService) {}

  /**
   * Upload a single data file for subsequent analysis or cleaning.
   *
   * ### Request
   * - Content-Type: `multipart/form-data`
   * - Field name: `file`
   * - Permitted extensions: `.csv`, `.txt`, `.xlsx`, `.xls`, `.tsv`, `.json`
   * - Maximum size: 100 MB
   *
   * ### Response `201`
   * ```json
   * {
   *   "file_id": "<uuid>",
   *   "filename": "trial_data.csv",
   *   "size": 204800,
   *   "path": "/app/uploads/<uuid>.csv",
   *   "preview": {
   *     "headers": ["patient_id", "age", "systolic_bp"],
   *     "rows": [["P001", "42", "120"], ...],
   *     "total_rows_sampled": 5
   *   }
   * }
   * ```
   *
   * @param file - Multer file populated by the `FileInterceptor`.
   * @returns The {@link UploadResult} for the stored file.
   */
  @Post()
  @HttpCode(HttpStatus.CREATED)
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(),
      limits: {
        // 100 MB – mirrors MAX_FILE_SIZE from @bio-clean/core.
        fileSize: 100 * 1024 * 1024,
      },
    }),
  )
  upload(@UploadedFile() file: Express.Multer.File): UploadResult {
    return this.uploadService.processUpload(file);
  }
}
