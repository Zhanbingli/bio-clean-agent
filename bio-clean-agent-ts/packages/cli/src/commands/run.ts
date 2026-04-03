/**
 * @file commands/run.ts
 * @description `bio-clean run <file>` — execute the full cleaning pipeline on
 * a dataset file, with spinner-based progress feedback.
 *
 * When an LLM API key is available (OPENAI_API_KEY or DEEPSEEK_API_KEY),
 * the pipeline uses an LLM advisor for intelligent cleaning decisions.
 */

import path from "node:path";
import chalk from "chalk";
import ora from "ora";
import {
  BioCleaningAgent,
  ClinicalTrialCleaningPipeline,
  CleaningAdvisor,
} from "@bio-clean/core";
import type { AgentExecutionResult, LLMAdvisorConfig } from "@bio-clean/core";

/** Options accepted by the `run` command. */
export interface RunOptions {
  /** Dataset type: clinical | ehr */
  type: string;
  /** Output directory path. */
  output: string;
  /** Skip confirmation and auto-approve the plan. */
  autoApprove?: boolean;
  /** Disable LLM even when API key is available. */
  noLlm?: boolean;
}

/**
 * Detect available LLM provider from environment variables.
 */
function detectLLMConfig(): LLMAdvisorConfig | null {
  const deepseekKey = process.env["DEEPSEEK_API_KEY"];
  if (deepseekKey) {
    return {
      apiKey: deepseekKey,
      baseURL: "https://api.deepseek.com/v1",
      model: "deepseek-chat",
    };
  }

  const openaiKey = process.env["OPENAI_API_KEY"];
  if (openaiKey) {
    return {
      apiKey: openaiKey,
      model: "gpt-4o-mini",
    };
  }

  return null;
}

/**
 * Execute the cleaning pipeline on the given file.
 *
 * @param filePath - Absolute or relative path to the CSV data file.
 * @param options  - Command options.
 */
export async function runCommand(
  filePath: string,
  options: RunOptions
): Promise<void> {
  const resolvedFile = path.resolve(filePath);
  const resolvedOutput = path.resolve(options.output);

  // Detect LLM availability
  const llmConfig = options.noLlm ? null : detectLLMConfig();
  const advisor = llmConfig ? new CleaningAdvisor(llmConfig) : null;

  console.log();
  console.log(chalk.bold.cyan("Bio Clean Agent") + chalk.gray(" — Run Pipeline"));
  console.log(chalk.gray("─".repeat(50)));
  console.log(chalk.white("  File   :"), chalk.yellow(resolvedFile));
  console.log(chalk.white("  Type   :"), chalk.yellow(options.type));
  console.log(chalk.white("  Output :"), chalk.yellow(resolvedOutput));
  if (advisor) {
    console.log(chalk.white("  LLM    :"), chalk.green(`${llmConfig!.model} (${llmConfig!.baseURL ? "DeepSeek" : "OpenAI"})`));
  } else {
    console.log(chalk.white("  LLM    :"), chalk.dim("disabled (no API key or --no-llm)"));
  }
  console.log();

  // ---------------------------------------------------------------------------
  // Setup agent
  // ---------------------------------------------------------------------------
  const spinner = ora({
    text: chalk.cyan("Initialising agent…"),
    spinner: "dots",
  }).start();

  let result: AgentExecutionResult;

  try {
    const agent = new BioCleaningAgent(resolvedOutput);

    // Register pipelines — pass advisor when available
    agent.registerPipeline("clinical", () => new ClinicalTrialCleaningPipeline(resolvedOutput, advisor ?? undefined));

    spinner.text = chalk.cyan("Loading dataset…");

    const datasetType = normaliseType(options.type);

    const dataset: Record<string, unknown> = {
      dataset_type: datasetType,
      dataset_id: path.basename(resolvedFile, path.extname(resolvedFile)),
      raw_paths: [resolvedFile],
    };

    spinner.text = chalk.cyan("Planning execution…");

    // Confirmation callback (skip when --auto-approve)
    const confirmStep = options.autoApprove
      ? undefined
      : async (plan: Parameters<typeof agent.planAndExecute>[2] extends undefined ? never : unknown) => {
          spinner.stop();
          const { confirm } = await import("@inquirer/prompts");
          console.log();
          console.log(chalk.bold("Execution Plan:"));
          const agentPlan = plan as {
            pipeline: string;
            datasetId: string;
            datasetType: string;
            warnings: string[];
          };
          console.log(
            chalk.gray("  Pipeline :"),
            chalk.white(agentPlan.pipeline)
          );
          console.log(
            chalk.gray("  Dataset  :"),
            chalk.white(agentPlan.datasetId)
          );
          console.log(
            chalk.gray("  Type     :"),
            chalk.white(agentPlan.datasetType)
          );
          if (agentPlan.warnings.length > 0) {
            console.log(chalk.yellow("  Warnings :"));
            for (const w of agentPlan.warnings) {
              console.log(chalk.yellow(`    • ${w}`));
            }
          }
          console.log();
          const ok = await confirm({ message: "Proceed with this plan?" });
          spinner.start();
          return ok;
        };

    spinner.text = advisor
      ? chalk.cyan("Running pipeline with LLM advisor…")
      : chalk.cyan("Running pipeline…");

    result = await agent.planAndExecute(
      { dataset, output_dir: resolvedOutput },
      undefined,
      undefined,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      confirmStep as any
    );

    spinner.succeed(chalk.green("Pipeline completed successfully."));
  } catch (err) {
    spinner.fail(chalk.red("Pipeline failed."));
    console.error(chalk.red((err as Error).message));
    process.exitCode = 1;
    return;
  }

  // ---------------------------------------------------------------------------
  // Print results summary
  // ---------------------------------------------------------------------------
  printResultsSummary(result);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Normalise user-supplied type string to a recognised dataset type key.
 */
function normaliseType(raw: string): string {
  const map: Record<string, string> = {
    clinical: "clinical",
    ehr: "clinical",
  };
  return map[raw.toLowerCase()] ?? raw.toLowerCase();
}

/**
 * Print a coloured summary of the execution result.
 */
function printResultsSummary(result: AgentExecutionResult): void {
  const { plan, report } = result;

  console.log();
  console.log(chalk.bold.green("Results Summary"));
  console.log(chalk.gray("─".repeat(50)));
  console.log(chalk.white("  Dataset  :"), chalk.cyan(plan.datasetId));
  console.log(chalk.white("  Pipeline :"), chalk.cyan(plan.pipeline));
  console.log(chalk.white("  Workdir  :"), chalk.cyan(plan.workdir));
  console.log();

  // Report steps
  if (report.results.length > 0) {
    console.log(chalk.bold("Steps:"));
    for (const step of report.results) {
      const icon = step.success
        ? chalk.green("✓")
        : chalk.red("✗");
      const errMsg = step.error ? chalk.red(` — ${step.error}`) : "";

      // Show LLM-specific details
      const details = step.details;
      let extra = "";
      if (step.name === "llm_plan" && !details.skipped) {
        extra = chalk.dim(` [${details.risk_level} risk, ${details.recommended_steps} steps]`);
      } else if (step.name === "llm_plan" && details.skipped) {
        extra = chalk.dim(` [${details.reason}]`);
      } else if (step.name === "llm_summary" && details.skipped) {
        extra = chalk.dim(" [skipped]");
      } else if (details.llm_guided) {
        extra = chalk.magenta(" [LLM-guided]");
      }

      console.log(`  ${icon} ${chalk.white(step.name)}${extra}${errMsg}`);
    }
    console.log();
  }

  // Show LLM summary if available
  const summaryStep = report.results.find((s) => s.name === "llm_summary");
  if (summaryStep?.details.summary) {
    console.log(chalk.bold.magenta("LLM Analysis:"));
    console.log(chalk.white(`  ${summaryStep.details.summary}`));
    console.log();
  }

  // Overall status
  const statusColour = report.success
    ? chalk.bold.green
    : chalk.bold.red;

  console.log(
    chalk.white("  Status   :"),
    statusColour(report.success ? "COMPLETED" : "FAILED")
  );

  if (plan.warnings.length > 0) {
    console.log();
    console.log(chalk.yellow("Warnings:"));
    for (const w of plan.warnings) {
      console.log(chalk.yellow(`  • ${w}`));
    }
  }

  console.log();
}
