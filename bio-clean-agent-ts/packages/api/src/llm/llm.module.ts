/**
 * @file llm/llm.module.ts
 * @description NestJS feature module for LLM integration.
 *
 * Exports {@link LlmService} so any module that needs LLM capabilities
 * (e.g. a future AI-assisted planning endpoint) can import this module
 * and inject the service.
 */

import { Module } from '@nestjs/common';
import { LlmService } from './llm.service.js';

/**
 * Provides LLM capabilities (plan generation and chat) through the
 * {@link LlmService}.
 */
@Module({
  providers: [LlmService],
  exports: [LlmService],
})
export class LlmModule {}
