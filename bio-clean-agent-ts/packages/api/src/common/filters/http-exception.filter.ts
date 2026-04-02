/**
 * @file http-exception.filter.ts
 * @description Global exception filter that catches all unhandled exceptions
 * and returns a consistent, structured JSON error response.
 *
 * Registered globally in `main.ts` via `app.useGlobalFilters()`.
 */

import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import type { Request, Response } from 'express';

/** Shape of every error response returned by this API. */
export interface ErrorResponse {
  statusCode: number;
  error: string;
  message: string | string[];
  path: string;
  timestamp: string;
}

/**
 * Catches all exceptions thrown within the NestJS request lifecycle and
 * serialises them as a uniform `ErrorResponse` JSON body.
 *
 * - {@link HttpException} instances are forwarded as-is (status code and
 *   message are taken directly from the exception).
 * - Any other `Error` is treated as an internal server error (HTTP 500).
 * - Non-`Error` throws are also handled gracefully.
 */
@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  /**
   * Intercepts the exception and writes a structured JSON error response.
   *
   * @param exception - The thrown value (may be any type).
   * @param host - NestJS arguments host used to obtain the HTTP context.
   */
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let statusCode: number;
    let message: string | string[];
    let error: string;

    if (exception instanceof HttpException) {
      statusCode = exception.getStatus();
      const exceptionResponse = exception.getResponse();

      if (typeof exceptionResponse === 'string') {
        message = exceptionResponse;
        error = exception.name;
      } else if (typeof exceptionResponse === 'object' && exceptionResponse !== null) {
        const resp = exceptionResponse as Record<string, unknown>;
        message = (resp['message'] as string | string[]) ?? exception.message;
        error = (resp['error'] as string) ?? exception.name;
      } else {
        message = exception.message;
        error = exception.name;
      }
    } else if (exception instanceof Error) {
      statusCode = HttpStatus.INTERNAL_SERVER_ERROR;
      message = exception.message;
      error = 'Internal Server Error';
      // Log the full stack trace for unexpected errors.
      this.logger.error(
        `Unhandled exception on ${request.method} ${request.url}`,
        exception.stack,
      );
    } else {
      statusCode = HttpStatus.INTERNAL_SERVER_ERROR;
      message = 'An unexpected error occurred';
      error = 'Internal Server Error';
      this.logger.error(
        `Unknown throw on ${request.method} ${request.url}`,
        String(exception),
      );
    }

    const body: ErrorResponse = {
      statusCode,
      error,
      message,
      path: request.url,
      timestamp: new Date().toISOString(),
    };

    response.status(statusCode).json(body);
  }
}
