/**
 * @file knowledge/knowledge.module.ts
 * @description NestJS feature module for the knowledge-base API.
 */

import { Module } from '@nestjs/common';
import { KnowledgeController } from './knowledge.controller.js';

/**
 * Exposes medical standards and evidence entries at `/knowledge/*`.
 *
 * No additional providers are needed because the knowledge-base classes
 * (`MedicalStandards`, `EvidenceBase`) are instantiated directly inside
 * the controller — they carry no external dependencies.
 */
@Module({
  controllers: [KnowledgeController],
})
export class KnowledgeModule {}
