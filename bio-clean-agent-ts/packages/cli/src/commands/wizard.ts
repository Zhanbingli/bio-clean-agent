/**
 * @file commands/wizard.ts
 * @description `bio-clean wizard` — interactive setup wizard using
 * \@inquirer/prompts. Writes configuration to a `.env` file.
 */

import path from "node:path";
import fs from "node:fs";
import { select, input, password } from "@inquirer/prompts";
import chalk from "chalk";

/**
 * Run the interactive setup wizard.
 *
 * Prompts the user for LLM provider, API key, and default output directory,
 * then writes the values to `.env` in the current working directory.
 */
export async function wizardCommand(): Promise<void> {
  console.log();
  console.log(chalk.bold.cyan("Bio Clean Agent") + chalk.gray(" — Setup Wizard"));
  console.log(chalk.gray("─".repeat(50)));
  console.log(
    chalk.gray("This wizard will configure your Bio Clean Agent environment.")
  );
  console.log();

  // -------------------------------------------------------------------------
  // Step 1: LLM provider
  // -------------------------------------------------------------------------
  const provider = await select({
    message: "Which LLM provider would you like to use?",
    choices: [
      { name: "OpenAI (gpt-4o, gpt-4o-mini, …)", value: "openai" },
      { name: "DeepSeek (deepseek-chat, …)", value: "deepseek" },
      { name: "None (disable LLM features)", value: "none" },
    ],
  });

  // -------------------------------------------------------------------------
  // Step 2: API key
  // -------------------------------------------------------------------------
  let apiKey = "";
  if (provider !== "none") {
    const keyName =
      provider === "openai" ? "OPENAI_API_KEY" : "DEEPSEEK_API_KEY";
    const existingKey = process.env[keyName];

    if (existingKey) {
      console.log(
        chalk.green(`  ${keyName} is already set in the environment.`)
      );
      const useExisting = await select({
        message: `Use the existing ${keyName}?`,
        choices: [
          { name: "Yes, keep it", value: "yes" },
          { name: "No, enter a new key", value: "no" },
        ],
      });
      if (useExisting === "no") {
        apiKey = await password({ message: `Enter your ${keyName}:` });
      } else {
        apiKey = existingKey;
      }
    } else {
      apiKey = await password({ message: `Enter your ${provider === "openai" ? "OPENAI" : "DEEPSEEK"} API key:` });
    }
  }

  // -------------------------------------------------------------------------
  // Step 3: Default output directory
  // -------------------------------------------------------------------------
  const outputDir = await input({
    message: "Default output directory for cleaned datasets:",
    default: "./output",
  });

  // -------------------------------------------------------------------------
  // Step 4: Write .env file
  // -------------------------------------------------------------------------
  const envPath = path.join(process.cwd(), ".env");
  const lines: string[] = ["# Bio Clean Agent configuration", ""];

  if (provider !== "none" && apiKey) {
    const keyName =
      provider === "openai" ? "OPENAI_API_KEY" : "DEEPSEEK_API_KEY";
    lines.push(`${keyName}="${apiKey}"`);
  }

  lines.push(`BIO_CLEAN_PROVIDER="${provider}"`);
  lines.push(`BIO_CLEAN_OUTPUT_DIR="${outputDir}"`);
  lines.push("");

  try {
    // Merge with existing .env if it exists, preserving unrelated entries
    let existingContent = "";
    if (fs.existsSync(envPath)) {
      existingContent = fs.readFileSync(envPath, "utf-8");
    }

    const existingLines = existingContent
      .split("\n")
      .filter((line) => {
        // Remove lines we're about to overwrite
        const key = line.split("=")[0]?.trim() ?? "";
        const managedKeys = [
          "OPENAI_API_KEY",
          "DEEPSEEK_API_KEY",
          "BIO_CLEAN_PROVIDER",
          "BIO_CLEAN_OUTPUT_DIR",
          "# Bio Clean Agent configuration",
        ];
        return (
          key !== "" &&
          !key.startsWith("#") &&
          !managedKeys.includes(key)
        );
      });

    const merged = [...existingLines, ...lines].join("\n");
    fs.writeFileSync(envPath, merged, "utf-8");

    console.log();
    console.log(chalk.bold.green("Setup complete!"));
    console.log(chalk.gray("─".repeat(50)));
    console.log(chalk.white("  Configuration saved to:"), chalk.cyan(envPath));
    console.log(
      chalk.white("  LLM Provider  :"),
      chalk.cyan(provider)
    );
    console.log(
      chalk.white("  Output Dir    :"),
      chalk.cyan(outputDir)
    );
    console.log();
    console.log(
      chalk.gray(
        "  Run `bio-clean --help` to explore available commands."
      )
    );
    console.log();
  } catch (err) {
    console.error(
      chalk.red("Failed to write .env file:"),
      (err as Error).message
    );
    process.exitCode = 1;
  }
}
