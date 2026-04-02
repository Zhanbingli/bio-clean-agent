'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';

// ---- Types ---------------------------------------------------------------

export interface JobStep {
  step_id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  error?: string;
  priority?: string;
  evidence_based?: boolean;
}

export interface PendingDecision {
  decision_id: string;
  question: string;
  options: Array<{ value: string; label: string; description?: string }>;
  context?: string;
}

export interface QualityMetrics {
  completeness?: number;
  validity?: number;
  consistency?: number;
  uniqueness?: number;
  overall?: number;
  before?: Record<string, number>;
  after?: Record<string, number>;
}

export interface Job {
  job_id: string;
  status:
    | 'submitted'
    | 'planning'
    | 'running'
    | 'awaiting_decision'
    | 'completed'
    | 'failed';
  data_type?: string;
  file_id?: string;
  created_at: string;
  updated_at?: string;
  steps?: JobStep[];
  pending_decisions?: PendingDecision[];
  quality_metrics?: QualityMetrics;
  error?: string;
  progress?: number;
}

// ---- Hooks ---------------------------------------------------------------

export function useJob(jobId: string) {
  return useQuery<Job>({
    queryKey: ['job', jobId],
    queryFn: () => apiGet<Job>(`/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 3_000;
    },
  });
}

export function useJobs() {
  return useQuery<Job[]>({
    queryKey: ['jobs'],
    queryFn: () => apiGet<Job[]>('/jobs'),
    refetchInterval: 5_000,
  });
}
