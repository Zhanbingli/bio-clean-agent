/**
 * @file llm.ts
 * @description Zod schemas for LLM model descriptors, configuration, and
 * generation parameters. Supports multi-provider setups (OpenAI, Anthropic,
 * local Ollama, HuggingFace, etc.).
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// ModelDescriptor
// ---------------------------------------------------------------------------

/**
 * Static descriptor for a single LLM model entry in the model registry.
 * Used to populate UI model-picker dropdowns and to resolve the runtime
 * model configuration from a human-readable `key`.
 *
 * @example
 * ```ts
 * const descriptor = ModelDescriptorSchema.parse({
 *   key: "gpt-4o",
 *   provider: "openai",
 *   name: "GPT-4o",
 *   description: "OpenAI's most capable multimodal model.",
 *   tags: ["reasoning", "multimodal"],
 *   recommended: true,
 * });
 * ```
 */
export const ModelDescriptorSchema = z
  .object({
    /**
     * Short, URL-safe identifier used to reference this model throughout
     * the pipeline (e.g. `"gpt-4o"`, `"claude-3-5-sonnet"`, `"llama3-70b"`).
     */
    key: z.string().min(1).describe("Short identifier used to reference the model"),

    /**
     * LLM provider name (e.g. `"openai"`, `"anthropic"`, `"ollama"`,
     * `"huggingface"`, `"local"`).
     */
    provider: z
      .string()
      .min(1)
      .describe("LLM provider (e.g. openai, anthropic, ollama)"),

    /** Human-readable model name (e.g. `"GPT-4o"`, `"Claude 3.5 Sonnet"`). */
    name: z.string().min(1).describe("Human-readable model name"),

    /** Brief description of the model's strengths and best use cases. */
    description: z
      .string()
      .default("")
      .describe("Brief description of the model's capabilities"),

    /**
     * Capability tags used for filtering in the model registry
     * (e.g. `["reasoning", "long-context", "code"]`).
     */
    tags: z
      .array(z.string())
      .default([])
      .describe("Capability tags for filtering in the model registry"),

    /**
     * Provider-specific default options forwarded to the inference API
     * (e.g. `{ response_format: { type: "json_object" } }`).
     */
    default_options: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Provider-specific default inference options"),

    /**
     * `true` when this is the recommended model for production use.
     * At most one model per provider should be marked recommended.
     */
    recommended: z
      .boolean()
      .default(false)
      .describe("Whether this is the recommended model for this provider"),
  })
  .describe("Static descriptor for an LLM model entry in the model registry");

export type ModelDescriptor = z.infer<typeof ModelDescriptorSchema>;

// ---------------------------------------------------------------------------
// ModelConfig
// ---------------------------------------------------------------------------

/**
 * Runtime model configuration resolved from user settings or job parameters.
 * Pairs a selected model key with optional overrides and an API key.
 *
 * @example
 * ```ts
 * const config = ModelConfigSchema.parse({
 *   choice: "claude-3-5-sonnet",
 *   options: { max_retries: 3 },
 * });
 * ```
 */
export const ModelConfigSchema = z
  .object({
    /**
     * Key of the selected model, matching a {@link ModelDescriptor.key} in the
     * registry.  When omitted the pipeline uses its built-in default.
     */
    choice: z
      .string()
      .nullable()
      .optional()
      .describe("Registry key of the selected model (null = pipeline default)"),

    /**
     * Runtime override options merged on top of the model's `default_options`.
     * Useful for per-job tuning without touching the global registry.
     */
    options: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Runtime option overrides for the selected model"),

    /**
     * API key for the model provider.
     * When absent the pipeline falls back to the relevant environment variable
     * (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
     *
     * @remarks Never log or persist this value in plain text.
     */
    api_key: z
      .string()
      .nullable()
      .optional()
      .describe("Provider API key (falls back to environment variable when omitted)"),
  })
  .describe("Runtime LLM model configuration for a job or pipeline component");

export type ModelConfig = z.infer<typeof ModelConfigSchema>;

// ---------------------------------------------------------------------------
// GenerationConfig
// ---------------------------------------------------------------------------

/**
 * Text-generation hyperparameters forwarded to the inference API.
 * Defaults are tuned for deterministic, structured output suitable for
 * planning and data-cleaning tasks.
 *
 * @example
 * ```ts
 * const gen = GenerationConfigSchema.parse({
 *   temperature: 0.0,
 *   max_new_tokens: 2048,
 * });
 * ```
 */
export const GenerationConfigSchema = z
  .object({
    /**
     * Sampling temperature controlling output randomness.
     * `0` = greedy (deterministic); higher values increase diversity.
     * Default: `0.1` (nearly deterministic for structured output).
     */
    temperature: z
      .number()
      .min(0)
      .max(2)
      .default(0.1)
      .describe("Sampling temperature (0 = deterministic, 2 = maximum randomness)"),

    /**
     * Nucleus sampling probability mass.
     * Only the tokens comprising the top-`top_p` probability mass are sampled.
     * Default: `0.9`.
     */
    top_p: z
      .number()
      .min(0)
      .max(1)
      .default(0.9)
      .describe("Nucleus sampling probability (top-p)"),

    /**
     * Maximum number of new tokens the model may generate per call.
     * Default: `768`.  Increase for plans with many steps.
     */
    max_new_tokens: z
      .number()
      .int()
      .positive()
      .default(768)
      .describe("Maximum number of tokens to generate"),

    /**
     * Additional provider- or model-specific generation options not covered
     * by the standard fields above
     * (e.g. `{ stop: ["\n\n"], seed: 42, logit_bias: {} }`).
     */
    extra_options: z
      .record(z.string(), z.unknown())
      .default({})
      .describe("Extra provider-specific generation options"),
  })
  .describe("Text-generation hyperparameters forwarded to the inference API");

export type GenerationConfig = z.infer<typeof GenerationConfigSchema>;

// ---------------------------------------------------------------------------
// PlannerOutput
// ---------------------------------------------------------------------------

/**
 * Structured output produced by the Planner LLM call.
 *
 * The planner returns this JSON object which is then validated and
 * converted into a full {@link ExecutionPlan} by the orchestrator.
 *
 * @example
 * ```ts
 * const output = PlannerOutputSchema.parse(llmResponse);
 * if (output.confidence_score < 0.6) {
 *   // Escalate to human review before executing
 * }
 * ```
 */
export const PlannerOutputSchema = z
  .object({
    /**
     * Raw plan step descriptors as generated by the LLM.
     * Each element is an unvalidated record; the orchestrator validates
     * them against {@link PlanStepSchema} before building the execution plan.
     */
    plan_steps: z
      .array(z.record(z.string(), z.unknown()))
      .min(1)
      .describe("Raw plan step objects produced by the LLM"),

    /**
     * Natural-language summary of the generated plan, intended for
     * display in the UI or inclusion in a notification.
     */
    summary: z
      .string()
      .min(1)
      .describe("Human-readable summary of the generated execution plan"),

    /**
     * Self-assessed confidence score in the range [0, 1].
     * Values below 0.6 should trigger a human review before execution.
     */
    confidence_score: z
      .number()
      .min(0)
      .max(1)
      .describe("Self-assessed LLM confidence score for the generated plan (0–1)"),
  })
  .describe("Structured JSON output from the Planner LLM call");

export type PlannerOutput = z.infer<typeof PlannerOutputSchema>;
