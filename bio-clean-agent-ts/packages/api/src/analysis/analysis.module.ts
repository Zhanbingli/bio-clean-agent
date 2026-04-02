/**
 * @file analysis/analysis.module.ts
 * @description NestJS feature module for data analysis functionality.
 */

import { Module } from '@nestjs/common';
import { AnalysisController } from './analysis.controller.js';
import { AnalysisService } from './analysis.service.js';
import { UploadModule } from '../upload/upload.module.js';

/**
 * Encapsulates all analysis-related controllers and services.
 *
 * Imports {@link UploadModule} to access {@link UploadService} for resolving
 * uploaded file paths by `file_id`.
 */
@Module({
  imports: [UploadModule],
  controllers: [AnalysisController],
  providers: [AnalysisService],
  exports: [AnalysisService],
})
export class AnalysisModule {}
