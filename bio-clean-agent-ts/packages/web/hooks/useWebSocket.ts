'use client';

import { useEffect, useRef } from 'react';
import { subscribeToJob } from '@/lib/socket-client';

export function useWebSocket(
  jobId: string | null | undefined,
  onEvent: (event: unknown) => void,
) {
  // Keep a stable ref to the callback so the effect doesn't re-run
  const onEventRef = useRef(onEvent);
  useEffect(() => {
    onEventRef.current = onEvent;
  });

  useEffect(() => {
    if (!jobId) return;

    const unsubscribe = subscribeToJob(jobId, (event) => {
      onEventRef.current(event);
    });

    return () => {
      unsubscribe();
    };
  }, [jobId]);
}
