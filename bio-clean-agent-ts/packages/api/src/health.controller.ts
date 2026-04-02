/**
 * @file health.controller.ts
 * @description Lightweight health-check endpoint consumed by load balancers,
 * container orchestrators (Kubernetes readiness/liveness probes), and
 * monitoring dashboards.
 */

import { Controller, Get } from '@nestjs/common';

/** Shape of the health-check response body. */
export interface HealthResponse {
  status: 'ok';
  service: string;
  version: string;
  timestamp: string;
}

/**
 * Exposes a single `GET /health` endpoint that returns the current service
 * status as a structured JSON payload.
 */
@Controller('health')
export class HealthController {
  /**
   * Returns a 200 OK response when the API process is alive and accepting
   * requests.  Can be extended to probe downstream dependencies (DB, message
   * broker, etc.) when needed.
   *
   * @returns A {@link HealthResponse} payload.
   */
  @Get()
  check(): HealthResponse {
    return {
      status: 'ok',
      service: 'bio-clean-agent-api',
      version: process.env.npm_package_version ?? '0.1.0',
      timestamp: new Date().toISOString(),
    };
  }
}
