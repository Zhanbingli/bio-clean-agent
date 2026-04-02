/**
 * @file commands/interactive.ts
 * @description `bio-clean interactive` — start an LLM-powered interactive REPL.
 */

import { startRepl } from "../repl/repl.js";

/** Options for the interactive command. */
export interface InteractiveOptions {
  /** LLM provider: "openai" | "deepseek" */
  provider: string;
  /** Optional model name override. */
  model?: string;
}

/**
 * Start the interactive REPL.
 *
 * @param options - Provider and model configuration.
 */
export async function interactiveCommand(
  options: InteractiveOptions
): Promise<void> {
  await startRepl({ provider: options.provider, model: options.model });
}
