/**
 * @file commands/serve.ts
 * @description `bio-clean serve` — start the Bio Clean API server.
 */

export interface ServeOptions {
  port: number;
}

export async function serveCommand(options: ServeOptions): Promise<void> {
  console.log(`Starting Bio Clean Agent API server on port ${options.port}...`);
  console.log("Tip: Make sure @bio-clean/api is built first.");
  console.log("");

  try {
    // Dynamic import to avoid hard dependency on NestJS in CLI package
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const nestCore = await (Function('return import("@nestjs/core")')() as Promise<{ NestFactory: { create: (m: unknown) => Promise<{ enableCors: (o: unknown) => void; listen: (p: number) => Promise<void> }> } }>);
    const appMod = await (Function('return import("@bio-clean/api/dist/app.module.js")')() as Promise<{ AppModule: unknown }>);

    const app = await nestCore.NestFactory.create(appMod.AppModule);
    app.enableCors({
      origin: process.env["ALLOWED_ORIGINS"]?.split(",") ?? ["http://localhost:3001"],
      credentials: true,
    });
    await app.listen(options.port);
    console.log(`Bio Clean Agent API running on http://localhost:${options.port}`);
  } catch {
    console.error(
      "Failed to start API server. Run from the api package instead:\n" +
      "  cd packages/api && pnpm dev"
    );
    process.exit(1);
  }
}
