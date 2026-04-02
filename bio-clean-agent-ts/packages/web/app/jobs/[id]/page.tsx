'use client';

import React, { useCallback, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useJob, type Job, type JobStep, type PendingDecision } from '@/hooks/useJob';
import { useWebSocket } from '@/hooks/useWebSocket';
import { apiPut } from '@/lib/api-client';

// ---- helpers ---------------------------------------------------------------

const STEP_STATUS_STYLES: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-500',
  running: 'bg-purple-100 text-purple-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  skipped: 'bg-gray-50 text-gray-400',
};

const STEP_ICONS: Record<string, string> = {
  pending: '○',
  running: '⚙',
  completed: '✓',
  failed: '✗',
  skipped: '—',
};

const JOB_STATUS_COLORS: Record<string, string> = {
  submitted: 'text-blue-600',
  planning: 'text-yellow-600',
  running: 'text-purple-600',
  awaiting_decision: 'text-orange-600',
  completed: 'text-green-600',
  failed: 'text-red-600',
};

function formatDate(d?: string) {
  if (!d) return '—';
  try {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'short',
      timeStyle: 'medium',
    }).format(new Date(d));
  } catch {
    return d;
  }
}

// ---- Step timeline ---------------------------------------------------------

function StepTimeline({ steps }: { steps: JobStep[] }) {
  return (
    <div className="space-y-2">
      {steps.map((step, idx) => (
        <div key={step.step_id ?? idx} className="flex gap-3 items-start">
          {/* Icon circle */}
          <div
            className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-0.5 ${STEP_STATUS_STYLES[step.status] ?? 'bg-gray-100 text-gray-500'}`}
          >
            {step.status === 'running' ? (
              <span className="spinner w-3.5 h-3.5" />
            ) : (
              STEP_ICONS[step.status] ?? '•'
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0 pb-3 border-b border-gray-50 last:border-0">
            <div className="flex flex-wrap items-center gap-2">
              <p
                className={`text-sm font-semibold ${
                  step.status === 'failed'
                    ? 'text-red-700'
                    : step.status === 'completed'
                    ? 'text-gray-700'
                    : step.status === 'running'
                    ? 'text-purple-700'
                    : 'text-gray-500'
                }`}
              >
                {step.name}
              </p>
              {step.priority && (
                <span className="badge bg-gray-100 text-gray-500 text-[10px]">
                  {step.priority}
                </span>
              )}
              {step.evidence_based && (
                <span className="badge bg-green-50 text-green-600 text-[10px]">
                  evidence
                </span>
              )}
            </div>
            {step.started_at && (
              <p className="text-xs text-gray-400 mt-0.5">
                {step.status === 'completed'
                  ? `Completed ${formatDate(step.completed_at)}`
                  : `Started ${formatDate(step.started_at)}`}
              </p>
            )}
            {step.error && (
              <p className="text-xs text-red-500 mt-0.5">{step.error}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- Decision dialog -------------------------------------------------------

function DecisionDialog({
  decisions,
  jobId,
  onDecisionMade,
}: {
  decisions: PendingDecision[];
  jobId: string;
  onDecisionMade: () => void;
}) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDecision(decisionId: string, value: string) {
    setLoading(decisionId + value);
    setError(null);
    try {
      await apiPut(`/jobs/${jobId}/decisions/${decisionId}`, { value });
      onDecisionMade();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit decision.');
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-4">
      {decisions.map((decision) => (
        <div
          key={decision.decision_id}
          className="bg-orange-50 border border-orange-200 rounded-xl p-4"
        >
          <div className="flex gap-2 items-start mb-3">
            <span className="text-xl">❓</span>
            <div>
              <p className="text-sm font-semibold text-orange-900">
                {decision.question}
              </p>
              {decision.context && (
                <p className="text-xs text-orange-600 mt-0.5">
                  {decision.context}
                </p>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {decision.options.map((opt) => (
              <button
                key={opt.value}
                disabled={loading !== null}
                onClick={() => handleDecision(decision.decision_id, opt.value)}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-white border border-orange-300 text-orange-800 hover:bg-orange-100 disabled:opacity-60 transition-all"
                title={opt.description}
              >
                {loading === decision.decision_id + opt.value ? (
                  <span className="spinner w-3.5 h-3.5 inline-block" />
                ) : (
                  opt.label
                )}
              </button>
            ))}
          </div>
        </div>
      ))}
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
    </div>
  );
}

// ---- Quality Metrics -------------------------------------------------------

function QualityMetricsPanel({
  metrics,
}: {
  metrics: NonNullable<Job['quality_metrics']>;
}) {
  const dimensions = [
    { key: 'completeness', label: 'Completeness', color: '#667eea' },
    { key: 'validity', label: 'Validity', color: '#764ba2' },
    { key: 'consistency', label: 'Consistency', color: '#48bb78' },
    { key: 'uniqueness', label: 'Uniqueness', color: '#ed8936' },
  ] as const;

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {dimensions.map(({ key, label, color }) => {
          const val = metrics[key];
          if (val === undefined) return null;
          const pct = Math.round(val * (val <= 1 ? 100 : 1));
          return (
            <div key={key} className="bg-gray-50 rounded-xl p-4 text-center">
              {/* Mini circular progress */}
              <div className="relative inline-flex items-center justify-center mb-2">
                <svg width="56" height="56" viewBox="0 0 56 56">
                  <circle
                    cx="28" cy="28" r="22"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="5"
                  />
                  <circle
                    cx="28" cy="28" r="22"
                    fill="none"
                    stroke={color}
                    strokeWidth="5"
                    strokeLinecap="round"
                    strokeDasharray={`${(pct / 100) * 138.2} 138.2`}
                    transform="rotate(-90 28 28)"
                  />
                </svg>
                <span
                  className="absolute text-xs font-bold"
                  style={{ color }}
                >
                  {pct}%
                </span>
              </div>
              <p className="text-xs text-gray-500">{label}</p>
            </div>
          );
        })}
      </div>

      {metrics.overall !== undefined && (
        <div className="mt-4 bg-gray-50 rounded-xl p-4 text-center">
          <p className="text-3xl font-extrabold gradient-text">
            {Math.round(metrics.overall * (metrics.overall <= 1 ? 100 : 1))}%
          </p>
          <p className="text-xs text-gray-500 mt-1">Overall Quality Score</p>
        </div>
      )}
    </div>
  );
}

// ---- Main page -------------------------------------------------------------

export default function JobDetailPage() {
  const { id: jobId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { data: job, isLoading, error, refetch } = useJob(jobId);

  // Real-time updates via WebSocket
  const handleWsEvent = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['job', jobId] });
  }, [queryClient, jobId]);

  useWebSocket(jobId, handleWsEvent);

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="spinner-lg" />
        <p className="text-brand-600 text-sm">Loading job details&hellip;</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-8">
        <div className="text-5xl">⚠️</div>
        <h2 className="text-xl font-semibold text-gray-800">
          Failed to load job
        </h2>
        <p className="text-gray-500 text-sm">{error?.message ?? 'Job not found'}</p>
        <button onClick={() => refetch()} className="btn-primary">
          Retry
        </button>
      </div>
    );
  }

  const isActive =
    job.status !== 'completed' && job.status !== 'failed';

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 animate-slide-up space-y-6">
      {/* Breadcrumb + header */}
      <div>
        <Link
          href="/jobs"
          className="text-xs text-brand-500 hover:text-brand-700 flex items-center gap-1 mb-3"
        >
          ← All Jobs
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 font-mono truncate">
              {job.job_id}
            </h1>
            <div className="flex flex-wrap items-center gap-2 mt-1">
              <span
                className={`text-sm font-semibold ${JOB_STATUS_COLORS[job.status] ?? 'text-gray-600'}`}
              >
                {job.status.replace('_', ' ').toUpperCase()}
              </span>
              {isActive && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 gradient-bg" />
                </span>
              )}
              {job.data_type && (
                <span className="badge bg-gray-100 text-gray-500">
                  {job.data_type}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="btn-secondary text-sm py-2 px-4"
            >
              Refresh
            </button>
            {job.status === 'completed' && (
              <Link
                href={`/reports/${job.job_id}`}
                className="btn-primary text-sm py-2 px-4"
              >
                View Report →
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {job.progress !== undefined && (
        <div className="card py-4">
          <div className="flex justify-between text-xs text-gray-500 mb-2">
            <span>Progress</span>
            <span>{job.progress}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full">
            <div
              className="h-2 gradient-bg rounded-full transition-all duration-500"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Awaiting Decision */}
      {job.status === 'awaiting_decision' &&
        job.pending_decisions &&
        job.pending_decisions.length > 0 && (
          <div className="card border-orange-200">
            <h2 className="text-base font-semibold text-orange-800 mb-4 flex items-center gap-2">
              <span>⏳</span> Decision Required
            </h2>
            <DecisionDialog
              decisions={job.pending_decisions}
              jobId={job.job_id}
              onDecisionMade={() => refetch()}
            />
          </div>
        )}

      {/* Error */}
      {job.status === 'failed' && job.error && (
        <div className="card bg-red-50 border-red-200">
          <h2 className="text-sm font-semibold text-red-700 mb-1">
            Job Failed
          </h2>
          <p className="text-sm text-red-600">{job.error}</p>
        </div>
      )}

      {/* Steps timeline */}
      {job.steps && job.steps.length > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">
            Cleaning Steps
          </h2>
          <StepTimeline steps={job.steps} />
        </div>
      )}

      {/* Quality metrics */}
      {job.status === 'completed' && job.quality_metrics && (
        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">
            Quality Metrics
          </h2>
          <QualityMetricsPanel metrics={job.quality_metrics} />
        </div>
      )}

      {/* Job metadata */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-700 mb-3">Details</h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          {[
            { label: 'Job ID', value: job.job_id },
            { label: 'Status', value: job.status },
            { label: 'Data Type', value: job.data_type ?? '—' },
            { label: 'File ID', value: job.file_id ?? '—' },
            { label: 'Created', value: formatDate(job.created_at) },
            { label: 'Updated', value: formatDate(job.updated_at) },
          ].map(({ label, value }) => (
            <div key={label} className="flex gap-2">
              <dt className="text-gray-400 w-24 shrink-0">{label}:</dt>
              <dd className="text-gray-700 font-mono text-xs break-all">
                {value}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
