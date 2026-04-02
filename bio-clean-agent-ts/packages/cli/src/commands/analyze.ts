/**
 * @file commands/analyze.ts
 * @description `bio-clean analyze <file>` — profile a dataset, detect quality
 * issues with evidence, generate a smart plan, and print a formatted report.
 */

import path from "node:path";
import chalk from "chalk";
import ora from "ora";
import {
  EnhancedClinicalTrialHandler,
  SmartPlanner,
} from "@bio-clean/core";
import type { Issue } from "@bio-clean/core";

/** Options accepted by the `analyze` command. */
export interface AnalyzeOptions {
  /** Dataset type (currently only "clinical" is handled). */
  type: string;
}

/**
 * Analyze a data file and print a quality report.
 *
 * @param filePath - Absolute or relative path to the CSV data file.
 * @param options  - Command options.
 */
export async function analyzeCommand(
  filePath: string,
  options: AnalyzeOptions
): Promise<void> {
  const resolvedFile = path.resolve(filePath);

  console.log();
  console.log(chalk.bold.cyan("Bio Clean Agent") + chalk.gray(" — Analyze"));
  console.log(chalk.gray("─".repeat(50)));
  console.log(chalk.white("  File :"), chalk.yellow(resolvedFile));
  console.log(chalk.white("  Type :"), chalk.yellow(options.type));
  console.log();

  const spinner = ora({
    text: chalk.cyan("Loading data…"),
    spinner: "dots",
  }).start();

  try {
    // -------------------------------------------------------------------------
    // Load and profile
    // -------------------------------------------------------------------------
    const handler = new EnhancedClinicalTrialHandler(resolvedFile, "cli-user");

    handler.loadData();
    spinner.text = chalk.cyan("Profiling dataset…");

    const profile = handler.profileData();

    spinner.text = chalk.cyan("Detecting issues…");
    const issues = handler.detectIssuesWithEvidence();

    // -------------------------------------------------------------------------
    // Smart plan
    // -------------------------------------------------------------------------
    spinner.text = chalk.cyan("Generating smart plan…");
    const planner = new SmartPlanner();
    const datasetId = path.basename(resolvedFile, path.extname(resolvedFile));

    const dataProfile = {
      row_count: profile.rows,
      column_count: profile.columns,
      columns: Object.fromEntries(
        profile.columnNames.map((col) => [
          col,
          {
            dtype: profile.columnTypes[col],
            missing_rate: profile.missingRates[col] ?? 0,
          },
        ])
      ),
    };

    const executionPlan = planner.createPlan(
      datasetId,
      "clinical",
      ["improve_data_quality"],
      dataProfile
    );

    spinner.succeed(chalk.green("Analysis complete."));

    // -------------------------------------------------------------------------
    // Print report
    // -------------------------------------------------------------------------
    printDataProfile(profile);
    printIssues(issues);
    printPlanSummary(executionPlan, issues);
  } catch (err) {
    spinner.fail(chalk.red("Analysis failed."));
    console.error(chalk.red((err as Error).message));
    process.exitCode = 1;
  }
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

interface ProfileData {
  rows: number;
  columns: number;
  columnNames: string[];
  columnTypes: Record<string, string>;
  missingRates: Record<string, number>;
}

interface PlanData {
  steps: Array<{ name: string; priority?: string }>;
  recommendations?: string[];
  warnings?: string[];
}

/**
 * Print the data profile section.
 */
function printDataProfile(profile: ProfileData): void {
  console.log();
  console.log(chalk.bold.white("Data Profile"));
  console.log(chalk.gray("─".repeat(50)));
  console.log(
    chalk.white("  Records :"),
    chalk.cyan(profile.rows.toLocaleString())
  );
  console.log(
    chalk.white("  Columns :"),
    chalk.cyan(profile.columns.toLocaleString())
  );

  if (profile.columnNames.length > 0) {
    console.log();
    console.log(chalk.bold("  Column breakdown:"));

    const maxNameLen = Math.max(
      ...profile.columnNames.map((n) => n.length),
      6
    );

    for (const col of profile.columnNames) {
      const type = profile.columnTypes[col] ?? "unknown";
      const missingRate = profile.missingRates[col] ?? 0;
      const missingPct = (missingRate * 100).toFixed(1);
      const missingLabel =
        missingRate > 0.2
          ? chalk.red(`${missingPct}% missing`)
          : missingRate > 0.05
          ? chalk.yellow(`${missingPct}% missing`)
          : missingRate > 0
          ? chalk.gray(`${missingPct}% missing`)
          : chalk.green("complete");

      const paddedName = col.padEnd(maxNameLen);
      const paddedType = type.padEnd(8);
      console.log(
        `    ${chalk.white(paddedName)}  ${chalk.gray(paddedType)}  ${missingLabel}`
      );
    }
  }
}

/**
 * Print the issues section with severity-based colouring.
 */
function printIssues(issues: Issue[]): void {
  console.log();
  console.log(chalk.bold.white("Quality Issues"));
  console.log(chalk.gray("─".repeat(50)));

  if (issues.length === 0) {
    console.log(chalk.green("  No issues detected."));
    return;
  }

  // Sort by severity weight
  const severityOrder: Record<Issue["severity"], number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
    info: 4,
  };

  const sorted = [...issues].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  for (const issue of sorted) {
    const badge = severityBadge(issue.severity);
    console.log(
      `  ${badge} ${chalk.white(issue.field)} — ${chalk.gray(issue.message)}`
    );
    if (issue.recommendation) {
      console.log(
        chalk.gray(`       Recommendation: ${issue.recommendation}`)
      );
    }
    if (issue.evidence_statement) {
      console.log(
        chalk.gray(`       Evidence: ${issue.evidence_statement}`)
      );
    }
  }

  // Tally
  const counts = issues.reduce<Record<string, number>>((acc, i) => {
    acc[i.severity] = (acc[i.severity] ?? 0) + 1;
    return acc;
  }, {});

  console.log();
  console.log(chalk.bold("  Summary:"));
  if (counts["critical"]) {
    console.log(chalk.red(`    ${counts["critical"]} critical`));
  }
  if (counts["high"]) {
    console.log(chalk.red(`    ${counts["high"]} high`));
  }
  if (counts["medium"]) {
    console.log(chalk.yellow(`    ${counts["medium"]} medium`));
  }
  if (counts["low"]) {
    console.log(chalk.blue(`    ${counts["low"]} low`));
  }
  if (counts["info"]) {
    console.log(chalk.gray(`    ${counts["info"]} info`));
  }
}

/**
 * Print the plan summary and top recommendations.
 */
function printPlanSummary(plan: PlanData, issues: Issue[]): void {
  console.log();
  console.log(chalk.bold.white("Execution Plan Summary"));
  console.log(chalk.gray("─".repeat(50)));
  console.log(
    chalk.white("  Steps planned :"),
    chalk.cyan(String(plan.steps.length))
  );

  if (plan.steps.length > 0) {
    console.log();
    for (const step of plan.steps) {
      const priority =
        (step as { priority?: string }).priority ?? "normal";
      const priorityColour =
        priority === "high"
          ? chalk.red
          : priority === "medium"
          ? chalk.yellow
          : chalk.gray;
      console.log(
        `  ${chalk.gray("•")} ${chalk.white(step.name)} ${priorityColour(`[${priority}]`)}`
      );
    }
  }

  // Top recommendations derived from issues
  const topRecs = issues
    .filter((i) => i.recommendation)
    .slice(0, 5)
    .map((i) => i.recommendation as string);

  if (topRecs.length > 0) {
    console.log();
    console.log(chalk.bold("  Top Recommendations:"));
    for (const rec of topRecs) {
      console.log(`  ${chalk.green("→")} ${chalk.white(rec)}`);
    }
  }

  if (plan.warnings && plan.warnings.length > 0) {
    console.log();
    console.log(chalk.yellow("  Warnings:"));
    for (const w of plan.warnings) {
      console.log(chalk.yellow(`  • ${w}`));
    }
  }

  console.log();
}

/**
 * Return a chalk-coloured severity badge string.
 */
function severityBadge(severity: Issue["severity"]): string {
  switch (severity) {
    case "critical":
      return chalk.bgRed.white(" CRITICAL ");
    case "high":
      return chalk.red("  [HIGH]  ");
    case "medium":
      return chalk.yellow(" [MEDIUM] ");
    case "low":
      return chalk.blue("  [LOW]   ");
    case "info":
      return chalk.gray("  [INFO]  ");
  }
}
