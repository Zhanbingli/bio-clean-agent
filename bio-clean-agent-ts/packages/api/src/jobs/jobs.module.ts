/**
 * @file jobs/jobs.module.ts
 * @description NestJS feature module for job management.
 *
 * Registers the REST controller, the in-memory service, and the Socket.IO
 * WebSocket gateway that streams real-time events to subscribed clients.
 */

import { Module } from '@nestjs/common';
import { JobsController } from './jobs.controller.js';
import { JobsService } from './jobs.service.js';
import { JobsGateway } from './jobs.gateway.js';
import { UploadModule } from '../upload/upload.module.js';

/**
 * Encapsulates job lifecycle management:
 * - REST CRUD via {@link JobsController}
 * - In-memory state via {@link JobsService}
 * - WebSocket streaming via {@link JobsGateway}
 *
 * Imports {@link UploadModule} to resolve file paths by `file_id`.
 */
@Module({
  imports: [UploadModule],
  controllers: [JobsController],
  providers: [JobsService, JobsGateway],
  exports: [JobsService],
})
export class JobsModule {}
