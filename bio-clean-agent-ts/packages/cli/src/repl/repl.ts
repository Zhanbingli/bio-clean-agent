/**
 * @file repl/repl.ts
 * @description LLM-powered interactive REPL for Bio Clean Agent.
 *
 * Uses Vercel AI SDK `generateText` with tool calling and `maxSteps`
 * to power a conversational data cleaning assistant.
 */

import * as readline from "node:readline";
import chalk from "chalk";
import ora from "ora";
import { generateText } from "ai";
import { createOpenAI } from "@ai-sdk/openai";
import { createSession, createTools } from "./tools.js";
import { printHeader } from "../ui/dashboard.js";

// ---------------------------------------------------------------------------
// REPL options
// ---------------------------------------------------------------------------

export interface ReplOptions {
  provider: string;
  model?: string;
}

// ---------------------------------------------------------------------------
// System prompt
// ---------------------------------------------------------------------------

const SYSTEM_PROMPT = `You are Bio Clean Agent, an expert AI assistant for cleaning and processing biological and medical data.

You have access to tools for loading, inspecting, assessing, cleaning, and exporting data files.

When a user asks you to work with data:
1. Use load_data to load the file
2. Use inspect_data or assess_quality to understand the data
3. Use detect_issues to find problems
4. Use clean_duplicates or handle_missing to fix issues
5. Use export_data to save results

Always explain what you're doing and why. Reference medical standards when relevant.
Be concise but informative. This is a task-oriented interface, not a chatbot.`;

// ---------------------------------------------------------------------------
// Provider setup
// ---------------------------------------------------------------------------

function createProvider(options: ReplOptions) {
  const providerName = options.provider.toLowerCase();

  if (providerName === "deepseek") {
    const apiKey = process.env["DEEPSEEK_API_KEY"];
    if (!apiKey) {
      throw new Error("DEEPSEEK_API_KEY environment variable is required for DeepSeek provider");
    }
    return createOpenAI({
      apiKey,
      baseURL: "https://api.deepseek.com/v1",
    });
  }

  // Default: OpenAI
  const apiKey = process.env["OPENAI_API_KEY"];
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY environment variable is required for OpenAI provider");
  }
  return createOpenAI({ apiKey });
}

function getModelId(options: ReplOptions): string {
  if (options.model) return options.model;
  if (options.provider.toLowerCase() === "deepseek") return "deepseek-chat";
  return "gpt-4o-mini";
}

// ---------------------------------------------------------------------------
// REPL loop
// ---------------------------------------------------------------------------

export async function startRepl(options: ReplOptions): Promise<void> {
  printHeader("Bio Clean Agent — Interactive Mode");

  let provider;
  try {
    provider = createProvider(options);
  } catch (e) {
    console.error(chalk.red(String(e)));
    console.log(chalk.dim("Run `bio-clean wizard` to configure your API keys."));
    return;
  }

  const modelId = getModelId(options);
  const model = provider(modelId);
  const session = createSession();
  const tools = createTools(session);

  console.log(chalk.dim(`Provider: ${options.provider} | Model: ${modelId}`));
  console.log(chalk.dim("Type /help for commands, /quit to exit.\n"));

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const messages: Array<{ role: "user" | "assistant"; content: string }> = [];

  const prompt = (): void => {
    rl.question(chalk.cyan("you> "), async (input) => {
      const trimmed = input.trim();
      if (!trimmed) {
        prompt();
        return;
      }

      // Handle special commands
      if (trimmed === "/quit" || trimmed === "/exit") {
        console.log(chalk.dim("Goodbye!"));
        rl.close();
        return;
      }

      if (trimmed === "/help") {
        console.log("");
        console.log(chalk.bold("Commands:"));
        console.log("  /help     Show this help");
        console.log("  /quit     Exit the REPL");
        console.log("  /status   Show loaded data status");
        console.log("");
        console.log(chalk.bold("Examples:"));
        console.log('  Load and analyze data/sample.csv');
        console.log('  What issues are in the data?');
        console.log('  Clean duplicates and handle missing values');
        console.log('  Export the cleaned data to output/clean.csv');
        console.log("");
        prompt();
        return;
      }

      if (trimmed === "/status") {
        if (session.filePath) {
          console.log(chalk.dim(`File: ${session.filePath}`));
          console.log(chalk.dim(`Rows: ${session.data.length}`));
          const cols = session.data.length > 0 ? Object.keys(session.data[0]).length : 0;
          console.log(chalk.dim(`Columns: ${cols}`));
        } else {
          console.log(chalk.dim("No data loaded."));
        }
        console.log("");
        prompt();
        return;
      }

      // Send to LLM
      messages.push({ role: "user", content: trimmed });

      const spinner = ora({ text: "Thinking...", color: "cyan" }).start();

      try {
        const result = await generateText({
          model,
          system: SYSTEM_PROMPT,
          messages,
          tools,
          maxSteps: 5,
        });

        spinner.stop();

        // Show tool calls
        for (const step of result.steps) {
          for (const tc of step.toolCalls) {
            console.log(chalk.dim(`  [tool] ${tc.toolName}(${JSON.stringify(tc.args)})`));
          }
          for (const tr of step.toolResults) {
            const preview = JSON.stringify((tr as Record<string, unknown>).result, null, 2);
            const lines = preview.split("\n");
            const truncated = lines.length > 10
              ? lines.slice(0, 10).join("\n") + "\n  ..."
              : preview;
            console.log(chalk.dim(`  [result] ${truncated}`));
          }
        }

        // Show assistant response
        if (result.text) {
          console.log("");
          console.log(chalk.white(result.text));
          console.log("");
          messages.push({ role: "assistant", content: result.text });
        }
      } catch (e) {
        spinner.stop();
        console.error(chalk.red(`Error: ${e}`));
        console.log("");
      }

      prompt();
    });
  };

  prompt();
}
