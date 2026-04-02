'use client';

import { useMutation } from '@tanstack/react-query';
import { apiPost } from '@/lib/api-client';

export interface DataIssue {
  issue_id?: string;
  field?: string;
  column?: string;
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  description: string;
  affected_rows?: number;
  suggestion?: string;
}

export interface CleaningStep {
  step_id?: string;
  name: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  evidence_based?: boolean;
  standard?: string;
  estimated_improvement?: number;
  estimated_data_loss?: number;
}

export interface Recommendation {
  title: string;
  description: string;
  evidence_level?: 'high' | 'medium' | 'low';
  confidence?: number;
  citations?: string[];
}

export interface AnalysisResult {
  file_id: string;
  data_profile: {
    records: number;
    columns: number;
    issues_count: number;
    data_type?: string;
    sample_columns?: string[];
  };
  issues: DataIssue[];
  plan: {
    total_steps: number;
    evidence_based_steps: number;
    quality_improvement_estimate: number;
    data_loss_estimate: number;
    steps: CleaningStep[];
  };
  recommendations: Recommendation[];
}

export function useAnalysis() {
  return useMutation<AnalysisResult, Error, string>({
    mutationFn: (fileId: string) =>
      apiPost<AnalysisResult>(`/analyze?file_id=${fileId}`),
  });
}
