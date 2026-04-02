/**
 * @file app.module.ts
 * @description Root NestJS module.  Imports and wires together all feature
 * modules that constitute the Bio Clean Agent REST + WebSocket API.
 */

import { Module } from '@nestjs/common';
import { JobsModule } from './jobs/jobs.module.js';
import { UploadModule } from './upload/upload.module.js';
import { AnalysisModule } from './analysis/analysis.module.js';
import { KnowledgeModule } from './knowledge/knowledge.module.js';
import { LlmModule } from './llm/llm.module.js';
import { HealthController } from './health.controller.js';

/**
 * Root application module.
 *
 * Feature modules are registered here; each module encapsulates its own
 * controllers, services, and (where applicable) gateways.
 */
@Module({
  imports: [
    JobsModule,
    UploadModule,
    AnalysisModule,
    KnowledgeModule,
    LlmModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}
