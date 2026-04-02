#!/usr/bin/env node
/**
 * @file index.ts
 * @description Bio Clean Agent CLI — main entry point.
 *
 * Registers all top-level sub-commands and delegates to their
 * respective handler modules.
 */

import { Command } from "commander";
import { runCommand } from "./commands/run.js";
import { analyzeCommand } from "./commands/analyze.js";
import { interactiveCommand } from "./commands/interactive.js";
import { wizardCommand } from "./commands/wizard.js";
import { serveCommand } from "./commands/serve.js";

const program = new Command();

program
  .name("bio-clean")
  .description("Bio Clean Agent CLI")
  .version("0.1.0");

// ---------------------------------------------------------------------------
// bio-clean run <file>
// ---------------------------------------------------------------------------
program
  .command("run <file>")
  .description("Run the cleaning pipeline on a data file")
  .option(
    "--type <type>",
    "Dataset type (clinical|ehr)",
    "clinical"
  )
  .option("--output <dir>", "Output directory", "./output")
  .option("--auto-approve", "Skip confirmation prompts and auto-approve plan")
  .action(
    async (
      file: string,
      options: { type: string; output: string; autoApprove?: boolean }
    ) => {
      await runCommand(file, options);
    }
  );

// ---------------------------------------------------------------------------
// bio-clean analyze <file>
// ---------------------------------------------------------------------------
program
  .command("analyze <file>")
  .description("Analyze a data file and report quality issues")
  .option("--type <type>", "Dataset type (clinical)", "clinical")
  .action(
    async (file: string, options: { type: string }) => {
      await analyzeCommand(file, options);
    }
  );

// ---------------------------------------------------------------------------
// bio-clean interactive
// ---------------------------------------------------------------------------
program
  .command("interactive")
  .description("Start an LLM-powered interactive REPL")
  .option(
    "--provider <provider>",
    "LLM provider (openai|deepseek)",
    "openai"
  )
  .option("--model <model>", "Model name override")
  .action(
    async (options: { provider: string; model?: string }) => {
      await interactiveCommand(options);
    }
  );

// ---------------------------------------------------------------------------
// bio-clean wizard
// ---------------------------------------------------------------------------
program
  .command("wizard")
  .description("Interactive setup wizard — configure providers and defaults")
  .action(async () => {
    await wizardCommand();
  });

// ---------------------------------------------------------------------------
// bio-clean serve
// ---------------------------------------------------------------------------
program
  .command("serve")
  .description("Start the Bio Clean API server")
  .option("--port <number>", "Port number", "3000")
  .action(async (options: { port: string }) => {
    await serveCommand({ port: parseInt(options.port, 10) });
  });

program.parse(process.argv);
