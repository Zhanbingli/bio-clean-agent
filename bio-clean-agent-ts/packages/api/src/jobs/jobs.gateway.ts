/**
 * @file jobs/jobs.gateway.ts
 * @description Socket.IO WebSocket gateway for real-time job event streaming.
 *
 * Clients connect to the `/ws` namespace and subscribe to individual jobs
 * using the `subscribe_job` message.  All subsequent events for that job are
 * pushed to the subscribing socket.
 *
 * ## Protocol
 *
 * ### Client → Server
 * | Message            | Payload                      | Description                  |
 * |--------------------|------------------------------|------------------------------|
 * | `subscribe_job`    | `{ job_id: string }`         | Begin receiving job events   |
 * | `unsubscribe_job`  | `{ job_id: string }`         | Stop receiving job events    |
 * | `ping`             | _(none)_                     | Keepalive heartbeat          |
 *
 * ### Server → Client
 * | Message            | Payload                      | Description                  |
 * |--------------------|------------------------------|------------------------------|
 * | `job_event`        | `Event`                      | Streamed job event           |
 * | `subscribed`       | `{ job_id: string }`         | Subscription confirmed       |
 * | `pong`             | `{ ts: string }`             | Heartbeat reply              |
 * | `error`            | `{ message: string }`        | Protocol or auth error       |
 */

import {
  OnGatewayConnection,
  OnGatewayDisconnect,
  OnGatewayInit,
  SubscribeMessage,
  WebSocketGateway,
  WebSocketServer,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Logger, OnModuleInit } from '@nestjs/common';
import { Server, Socket } from 'socket.io';
import type { Event } from '@bio-clean/core';
import { JobsService } from './jobs.service.js';

/** Inbound message body for job subscription operations. */
interface SubscribeJobPayload {
  job_id: string;
}

/**
 * WebSocket gateway mounted on the `/ws` Socket.IO namespace.
 *
 * Each socket maintains a `Set<string>` of subscribed job IDs stored in
 * `socket.data.subscriptions`.  Events are delivered only to sockets that
 * have explicitly subscribed to the emitting job.
 */
@WebSocketGateway({ cors: true, namespace: '/ws' })
export class JobsGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect, OnModuleInit
{
  @WebSocketServer()
  private readonly server!: Server;

  private readonly logger = new Logger(JobsGateway.name);

  constructor(private readonly jobsService: JobsService) {}

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------

  /** Register this gateway instance with {@link JobsService} on startup. */
  onModuleInit(): void {
    this.jobsService.setGateway(this);
  }

  /** Invoked after the Socket.IO server is bound. */
  afterInit(_server: Server): void {
    this.logger.log('WebSocket gateway initialised on namespace /ws');
  }

  /** Invoked when a new client connects. */
  handleConnection(socket: Socket): void {
    socket.data['subscriptions'] = new Set<string>();
    this.logger.debug(`Client connected: ${socket.id}`);
  }

  /** Invoked when a client disconnects (graceful or dropped). */
  handleDisconnect(socket: Socket): void {
    this.logger.debug(`Client disconnected: ${socket.id}`);
  }

  // ---------------------------------------------------------------------------
  // Message handlers
  // ---------------------------------------------------------------------------

  /**
   * Subscribe the requesting socket to events for a specific job.
   *
   * @param socket - The originating Socket.IO socket.
   * @param payload - Object containing the `job_id` to subscribe to.
   */
  @SubscribeMessage('subscribe_job')
  handleSubscribeJob(
    @ConnectedSocket() socket: Socket,
    @MessageBody() payload: SubscribeJobPayload,
  ): void {
    const { job_id } = payload ?? {};

    if (!job_id || typeof job_id !== 'string') {
      socket.emit('error', { message: 'subscribe_job requires a "job_id" string field.' });
      return;
    }

    (socket.data['subscriptions'] as Set<string>).add(job_id);

    // Immediately replay stored events so the client can catch up.
    try {
      const record = this.jobsService.findById(job_id);
      for (const event of record.events) {
        socket.emit('job_event', event);
      }
    } catch {
      // Job may not exist yet – that's fine; events will arrive as they are emitted.
    }

    socket.emit('subscribed', { job_id });
    this.logger.debug(`Socket ${socket.id} subscribed to job ${job_id}`);
  }

  /**
   * Unsubscribe a socket from a job's event stream.
   *
   * @param socket - The originating socket.
   * @param payload - Object containing the `job_id` to unsubscribe from.
   */
  @SubscribeMessage('unsubscribe_job')
  handleUnsubscribeJob(
    @ConnectedSocket() socket: Socket,
    @MessageBody() payload: SubscribeJobPayload,
  ): void {
    const { job_id } = payload ?? {};
    if (job_id) {
      (socket.data['subscriptions'] as Set<string>).delete(job_id);
      this.logger.debug(`Socket ${socket.id} unsubscribed from job ${job_id}`);
    }
  }

  /**
   * Handle a keepalive ping from the client.
   *
   * @param socket - The originating socket.
   */
  @SubscribeMessage('ping')
  handlePing(@ConnectedSocket() socket: Socket): void {
    socket.emit('pong', { ts: new Date().toISOString() });
  }

  // ---------------------------------------------------------------------------
  // Broadcast API (called by JobsService)
  // ---------------------------------------------------------------------------

  /**
   * Broadcast a job event to all sockets subscribed to the given job.
   *
   * Called by {@link JobsService} whenever a state transition or progress
   * update occurs.
   *
   * @param jobId - UUID of the job the event belongs to.
   * @param event - The {@link Event} payload to deliver.
   */
  emitJobEvent(jobId: string, event: Event): void {
    const sockets = this.server?.sockets;
    if (!sockets) return;

    sockets.sockets.forEach((socket) => {
      const subs = socket.data['subscriptions'] as Set<string> | undefined;
      if (subs?.has(jobId)) {
        socket.emit('job_event', event);
      }
    });
  }
}
