/**
 * @file upload/upload.module.ts
 * @description NestJS feature module for file upload functionality.
 */

import { Module } from '@nestjs/common';
import { UploadController } from './upload.controller.js';
import { UploadService } from './upload.service.js';

/**
 * Encapsulates all upload-related controllers, services, and configuration.
 *
 * Exports {@link UploadService} so sibling modules (e.g. `AnalysisModule`,
 * `JobsModule`) can resolve uploaded file paths by `file_id`.
 */
@Module({
  controllers: [UploadController],
  providers: [UploadService],
  exports: [UploadService],
})
export class UploadModule {}
