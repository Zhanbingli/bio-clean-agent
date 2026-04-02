/**
 * @file llm/llm.service.ts
 * @description LLM integration service using the Vercel AI SDK.
 *
 * Wraps `generateObject` (structured plan generation) and `generateText`
 * (free-form chat with optional tool use) behind a clean injectable interface.
 *
 * ## Provider configuration
 *
 * The service uses `createOpenAI` from `@ai-sdk/openai` which is compatible
 * with any OpenAI-compatible API, including:
 * - **DeepSeek** – set `LLM_BASE_URL=https://api.deepseek.com/v1` and
 *   `LLM_API_KEY=<your-key>`.
 * - **OpenAI** – set `OPENAI_API_KEY`; optionally set `LLM_MODEL` to override
 *   the default model.
 * - **Local Ollama** – set `LLM_BASE_URL=http://localhost:11434/v1` and
 *   `LLM_API_KEY=ollama` (any non-empty string is accepted).
 *
 * ## Environment variables
 *
 * | Variable         | Default                              | Description                   |
 * |------------------|--------------------------------------|-------------------------------|
 * | `LLM_BASE_URL`   | `https://api.openai.com/v1`          | Provider base URL             |
 * | `LLM_API_KEY`    | `process.env.OPENAI_API_KEY`         | Provider API key              |
 * | `LLM_MODEL`      | `deepseek-chat`                      | Model name / identifier       |
 * | `LLM_MAX_TOKENS` | `1024`                               | Max tokens per generation     |
 * | `LLM_TEMPERATURE`| `0.1`                                | Sampling temperature          |
 */

import { Injectable, Logger, InternalServerErrorException } from '@nestjs/common';
import { generateObject, generateText } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';
import type { PlannerOutput } from '@bio-clean/core';

// ---------------------------------------------------------------------------
// Zod schema mirroring PlannerOutputSchema from @bio-clean/core
// (re-declared here to keep the Vercel AI SDK call self-contained)
// ---------------------------------------------------------------------------

const PlanStepSchema = z.object({
  id: z.string().describe('Unique step identifier'),
  name: z.string().describe('Human-readable step name'),
  step_type: z
    .enum(['validation', 'cleaning', 'transformation', 'verification'])
    .describe('Functional category'),
  description: z.string().describe('What this step does'),
  priority: z
    .enum(['critical', 'high', 'medium', 'low'])
    .default('medium')
    .describe('Execution priority'),
  depends_on: z.array(z.string()).default([]).describe('Step IDs this step depends on'),
  estimated_duration_seconds: z
    .number()
    .positive()
    .optional()
    .describe('Estimated wall-clock time'),
  risk_level: z.string().optional().describe('Risk classification'),
  parameters: z.record(z.string(), z.unknown()).default({}).describe('Step parameters'),
});

const LlmPlannerOutputSchema = z.object({
  plan_steps: z.array(PlanStepSchema).min(1).describe('Ordered cleaning steps'),
  summary: z.string().min(1).describe('Human-readable plan summary'),
  confidence_score: z
    .number()
    .min(0)
    .max(1)
    .describe('Self-assessed confidence in the generated plan'),
});

// ---------------------------------------------------------------------------
// Chat message type
// ---------------------------------------------------------------------------

/** A single message in a multi-turn conversation. */
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

/** A tool definition compatible with the Vercel AI SDK. */
export interface AiTool {
  description: string;
  parameters: z.ZodTypeAny;
  execute?: (args: Record<string, unknown>) => Promise<unknown>;
}

/** Result returned by the {@link LlmService.chat} method. */
export interface ChatResult {
  text: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason: string;
}

/**
 * Provides structured plan generation and free-form chat via the Vercel AI
 * SDK, configured for OpenAI-compatible providers (including DeepSeek).
 */
@Injectable()
export class LlmService {
  private readonly logger = new Logger(LlmService.name);

  /** Vercel AI provider instance (OpenAI-compatible). */
  private readonly provider: ReturnType<typeof createOpenAI>;

  /** Default model identifier. */
  private readonly modelId: string;

  /** Max tokens per generation call. */
  private readonly maxTokens: number;

  /** Sampling temperature. */
  private readonly temperature: number;

  constructor() {
    const baseURL =
      process.env.LLM_BASE_URL ?? 'https://api.openai.com/v1';

    const apiKey =
      process.env.LLM_API_KEY ??
      process.env.OPENAI_API_KEY ??
      'placeholder-key';

    this.modelId = process.env.LLM_MODEL ?? 'deepseek-chat';
    this.maxTokens = parseInt(process.env.LLM_MAX_TOKENS ?? '1024', 10);
    this.temperature = parseFloat(process.env.LLM_TEMPERATURE ?? '0.1');

    this.provider = createOpenAI({
      baseURL,
      apiKey,
    });

    this.logger.log(
      `LLM service initialised – provider: ${baseURL}, model: ${this.modelId}`,
    );
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /**
   * Generate a structured cleaning plan using `generateObject`.
   *
   * The prompt is expected to describe the dataset and cleaning objectives.
   * The returned object is validated against {@link LlmPlannerOutputSchema}
   * and returned as a {@link PlannerOutput}.
   *
   * @param prompt - Free-text description of the dataset and goals.
   * @returns A validated {@link PlannerOutput} containing steps, summary, and
   *   confidence score.
   * @throws {InternalServerErrorException} When the LLM call or schema
   *   validation fails.
   */
  async generatePlan(prompt: string): Promise<PlannerOutput> {
    this.logger.debug(`generatePlan – prompt length: ${prompt.length}`);

    try {
      const { object } = await generateObject({
        model: this.provider(this.modelId),
        schema: LlmPlannerOutputSchema,
        prompt,
        maxTokens: this.maxTokens,
        temperature: this.temperature,
      });

      return object as PlannerOutput;
    } catch (err) {
      const message = (err as Error).message;
      this.logger.error(`generatePlan failed: ${message}`);
      throw new InternalServerErrorException(
        `LLM plan generation failed: ${message}`,
      );
    }
  }

  /**
   * Send a multi-turn conversation to the LLM using `generateText`.
   *
   * Supports optional tool definitions which the model may invoke over
   * multiple steps (controlled by `maxSteps`).
   *
   * @param messages - Ordered list of conversation messages.
   * @param tools - Optional map of tool name → {@link AiTool} definitions.
   * @param maxSteps - Maximum number of agentic reasoning steps (default `5`).
   * @returns A {@link ChatResult} with the final assistant text and token usage.
   * @throws {InternalServerErrorException} When the underlying API call fails.
   */
  async chat(
    messages: ChatMessage[],
    tools: Record<string, AiTool> = {},
    maxSteps = 5,
  ): Promise<ChatResult> {
    this.logger.debug(`chat – ${messages.length} messages, ${Object.keys(tools).length} tools`);

    // Convert tools to the Vercel AI SDK format.
    const sdkTools = Object.keys(tools).length > 0
      ? Object.fromEntries(
          Object.entries(tools).map(([name, tool]) => [
            name,
            {
              description: tool.description,
              parameters: tool.parameters,
              execute: tool.execute,
            },
          ]),
        )
      : undefined;

    try {
      const result = await generateText({
        model: this.provider(this.modelId),
        messages: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        ...(sdkTools ? { tools: sdkTools } : {}),
        maxSteps,
        maxTokens: this.maxTokens,
        temperature: this.temperature,
      });

      return {
        text: result.text,
        usage: result.usage
          ? {
              promptTokens: result.usage.promptTokens,
              completionTokens: result.usage.completionTokens,
              totalTokens: result.usage.totalTokens,
            }
          : undefined,
        finishReason: result.finishReason,
      };
    } catch (err) {
      const message = (err as Error).message;
      this.logger.error(`chat failed: ${message}`);
      throw new InternalServerErrorException(
        `LLM chat failed: ${message}`,
      );
    }
  }
}
