/**
 * @file ui/dashboard.ts
 * @description Terminal progress display utilities using chalk and ora.
 */

import chalk from "chalk";
import ora, { type Ora } from "ora";

// ---------------------------------------------------------------------------
// Step status display
// ---------------------------------------------------------------------------

type StepStatus = "pending" | "running" | "completed" | "failed";

interface StepInfo {
  name: string;
  status: StepStatus;
  message?: string;
}

const STATUS_ICONS: Record<StepStatus, string> = {
  pending: chalk.gray("○"),
  running: chalk.cyan("◉"),
  completed: chalk.green("✓"),
  failed: chalk.red("✗"),
};

const STATUS_COLORS: Record<StepStatus, (s: string) => string> = {
  pending: chalk.gray,
  running: chalk.cyan,
  completed: chalk.green,
  failed: chalk.red,
};

/**
 * Display a list of pipeline steps with their statuses.
 */
export function showStepList(steps: StepInfo[]): void {
  console.log("");
  console.log(chalk.bold("Pipeline Steps:"));
  console.log("");
  for (const step of steps) {
    const icon = STATUS_ICONS[step.status];
    const color = STATUS_COLORS[step.status];
    const msg = step.message ? chalk.dim(` — ${step.message}`) : "";
    console.log(`  ${icon} ${color(step.name)}${msg}`);
  }
  console.log("");
}

// ---------------------------------------------------------------------------
// Spinner helpers
// ---------------------------------------------------------------------------

let activeSpinner: Ora | null = null;

/**
 * Start or update a progress spinner for a given step.
 */
export function showProgress(stepName: string, status: StepStatus): void {
  if (status === "running") {
    if (activeSpinner) {
      activeSpinner.text = stepName;
    } else {
      activeSpinner = ora({ text: stepName, color: "cyan" }).start();
    }
  } else if (status === "completed") {
    if (activeSpinner) {
      activeSpinner.succeed(stepName);
      activeSpinner = null;
    } else {
      console.log(`  ${chalk.green("✓")} ${stepName}`);
    }
  } else if (status === "failed") {
    if (activeSpinner) {
      activeSpinner.fail(stepName);
      activeSpinner = null;
    } else {
      console.log(`  ${chalk.red("✗")} ${stepName}`);
    }
  }
}

/**
 * Stop any active spinner.
 */
export function stopProgress(): void {
  if (activeSpinner) {
    activeSpinner.stop();
    activeSpinner = null;
  }
}

// ---------------------------------------------------------------------------
// Quality summary display
// ---------------------------------------------------------------------------

interface QualitySummary {
  overall_score: number;
  overall_level: string;
  dimensions?: Record<string, { score: number; level: string }>;
}

/**
 * Print a formatted quality assessment summary.
 */
export function showQualitySummary(report: QualitySummary): void {
  console.log("");
  console.log(chalk.bold("Quality Assessment:"));
  console.log("");

  const scoreColor =
    report.overall_score >= 0.95
      ? chalk.green
      : report.overall_score >= 0.8
        ? chalk.yellow
        : chalk.red;

  console.log(
    `  Overall: ${scoreColor(`${(report.overall_score * 100).toFixed(1)}%`)} (${report.overall_level})`
  );

  if (report.dimensions) {
    console.log("");
    for (const [dim, info] of Object.entries(report.dimensions)) {
      const dc =
        info.score >= 0.95
          ? chalk.green
          : info.score >= 0.8
            ? chalk.yellow
            : chalk.red;
      const bar = renderBar(info.score, 20);
      console.log(`  ${dim.padEnd(15)} ${bar} ${dc(`${(info.score * 100).toFixed(1)}%`)}`);
    }
  }
  console.log("");
}

function renderBar(ratio: number, width: number): string {
  const filled = Math.round(ratio * width);
  const empty = width - filled;
  return chalk.green("█".repeat(filled)) + chalk.gray("░".repeat(empty));
}

// ---------------------------------------------------------------------------
// General output helpers
// ---------------------------------------------------------------------------

export function printHeader(title: string): void {
  console.log("");
  console.log(chalk.bold.hex("#667eea")(`  ${title}`));
  console.log(chalk.dim("  " + "─".repeat(title.length + 2)));
  console.log("");
}

export function printError(message: string): void {
  console.error(chalk.red(`Error: ${message}`));
}

export function printSuccess(message: string): void {
  console.log(chalk.green(`✓ ${message}`));
}
