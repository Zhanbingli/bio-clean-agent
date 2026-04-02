/**
 * @file main.ts
 * @description NestJS application bootstrap for the Bio Clean Agent API.
 *
 * Configures CORS, global pipes, and exception filters before binding
 * the HTTP server to the configured port.
 */

import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module.js';
import { HttpExceptionFilter } from './common/filters/http-exception.filter.js';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);

  // CORS – allow comma-separated origins from the environment or fall back to
  // the local frontend dev server.
  app.enableCors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') ?? ['http://localhost:3001'],
    credentials: true,
  });

  // Validate and transform incoming request payloads globally.
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: false,
      transform: true,
    }),
  );

  // Ensure all errors are returned as structured JSON.
  app.useGlobalFilters(new HttpExceptionFilter());

  const port = process.env.API_PORT ?? 3000;
  await app.listen(port);
  console.log(`Bio Clean Agent API running on http://localhost:${port}`);
}

bootstrap();
