import { io, Socket } from 'socket.io-client';

const SOCKET_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000';

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    socket.on('connect', () => {
      console.log('[socket] connected:', socket?.id);
    });

    socket.on('disconnect', (reason) => {
      console.log('[socket] disconnected:', reason);
    });

    socket.on('connect_error', (err) => {
      console.warn('[socket] connection error:', err.message);
    });
  }

  return socket;
}

export function disconnectSocket(): void {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

// Subscribe to all events for a specific job.
// Returns an unsubscribe function.
export function subscribeToJob(
  jobId: string,
  onEvent: (event: unknown) => void,
): () => void {
  const s = getSocket();

  // Join the job room
  s.emit('join:job', { jobId });

  const handler = (event: unknown) => {
    onEvent(event);
  };

  // Listen on a namespaced channel, e.g. "job:update:<jobId>"
  const channel = `job:update:${jobId}`;
  s.on(channel, handler);

  // Also listen on generic "job:event" and filter by jobId
  const genericHandler = (event: Record<string, unknown>) => {
    if (event?.jobId === jobId || event?.job_id === jobId) {
      onEvent(event);
    }
  };
  s.on('job:event', genericHandler);

  return () => {
    s.emit('leave:job', { jobId });
    s.off(channel, handler);
    s.off('job:event', genericHandler);
  };
}
