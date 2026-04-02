/**
 * @file api-key.guard.ts
 * @description Optional API-key guard.
 *
 * When the `WEB_API_KEY` environment variable is set, every incoming request
 * must carry a matching value in the `X-API-Key` header.  When the variable
 * is absent the guard becomes a no-op, which is convenient for local
 * development without any key management overhead.
 */

import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import type { Request } from 'express';

/**
 * Guard that enforces a shared API key supplied via the `X-API-Key` request
 * header.  Validation is skipped entirely when `WEB_API_KEY` is not defined
 * in the process environment.
 *
 * @example
 * Apply to a single controller:
 * ```ts
 * \@UseGuards(ApiKeyGuard)
 * \@Controller('admin')
 * export class AdminController { ... }
 * ```
 *
 * Apply globally from `main.ts`:
 * ```ts
 * app.useGlobalGuards(new ApiKeyGuard());
 * ```
 */
@Injectable()
export class ApiKeyGuard implements CanActivate {
  /**
   * Evaluates the guard for the current execution context.
   *
   * @param context - NestJS execution context providing access to the raw
   *   HTTP request.
   * @returns `true` when the request is allowed to proceed.
   * @throws {UnauthorizedException} When `WEB_API_KEY` is configured and the
   *   header value does not match.
   */
  canActivate(context: ExecutionContext): boolean {
    const expectedKey = process.env.WEB_API_KEY;

    // Guard is disabled when no key is configured.
    if (!expectedKey) {
      return true;
    }

    const request = context.switchToHttp().getRequest<Request>();
    const providedKey =
      (request.headers['x-api-key'] as string | undefined) ?? '';

    if (providedKey !== expectedKey) {
      throw new UnauthorizedException(
        'Invalid or missing API key. Supply a valid key in the X-API-Key header.',
      );
    }

    return true;
  }
}
