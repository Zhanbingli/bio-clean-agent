'use client';

import React from 'react';
import Link from 'next/link';
import { useJobs, type Job } from '@/hooks/useJob';

// ---- Status badge ----------------------------------------------------------

const STATUS_CONFIG: Record<
  string,
  { label: string; className: string; icon: string }
> = {
  submitted: {
    label: 'Submitted',
    className: 'bg-blue-100 text-blue-700',
    icon: '📨',
  },
  planning: {
    label: 'Planning',
    className: 'bg-yellow-100 text-yellow-700',
    icon: '🧠',
  },
  running: {
    label: 'Running',
    className: 'bg-purple-100 text-purple-700',
    icon: '⚙️',
  },
  awaiting_decision: {
    label: 'Awaiting Decision',
    className: 'bg-orange-100 text-orange-700',
    icon: '⏳',
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-100 text-green-700',
    icon: '✅',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-700',
    icon: '❌',
  },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? {
    label: status,
    className: 'bg-gray-100 text-gray-600',
    icon: '•',
  };
  return (
    <span className={`badge ${cfg.className} gap-1`}>
      <span>{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}

function formatDate(dateStr: string | undefined) {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

// ---- Job card (mobile) / row (desktop) ------------------------------------

function JobRow({ job }: { job: Job }) {
  const isLive =
    job.status !== 'completed' && job.status !== 'failed';

  return (
    <Link href={`/jobs/${job.job_id}`} className="block group">
      <div className="card hover:shadow-md transition-all duration-200 group-hover:border-brand-200">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          {/* Left: ID + type */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-mono text-sm font-semibold text-gray-800 truncate">
                {job.job_id}
              </p>
              {isLive && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 gradient-bg" />
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              {job.data_type ? `Type: ${job.data_type}` : 'Unknown data type'}
            </p>
          </div>

          {/* Middle: status */}
          <div className="sm:w-48">
            <StatusBadge status={job.status} />
          </div>

          {/* Progress bar if running */}
          {job.progress !== undefined && isLive && (
            <div className="sm:w-32">
              <div className="h-1.5 bg-gray-100 rounded-full">
                <div
                  className="h-1.5 gradient-bg rounded-full transition-all duration-500"
                  style={{ width: `${job.progress}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-0.5 text-right">
                {job.progress}%
              </p>
            </div>
          )}

          {/* Right: date */}
          <div className="text-xs text-gray-400 sm:text-right shrink-0">
            {formatDate(job.created_at)}
          </div>

          {/* Arrow */}
          <div className="hidden sm:block text-gray-300 group-hover:text-brand-400 transition-colors">
            →
          </div>
        </div>
      </div>
    </Link>
  );
}

// ---- Page -----------------------------------------------------------------

export default function JobsPage() {
  const { data: jobs, isLoading, error, refetch } = useJobs();

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 animate-slide-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cleaning Jobs</h1>
          <p className="text-gray-400 text-sm mt-0.5">
            Auto-refreshes every 5 seconds
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="btn-secondary text-sm py-2 px-4"
          >
            Refresh
          </button>
          <Link href="/" className="btn-primary text-sm py-2 px-4">
            + New Job
          </Link>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex flex-col items-center gap-3 py-20">
          <div className="spinner-lg" />
          <p className="text-brand-600 text-sm">Loading jobs&hellip;</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-red-100 bg-red-50 flex flex-col items-center gap-3 py-10 text-center">
          <div className="text-4xl">⚠️</div>
          <p className="text-red-700 font-semibold">Failed to load jobs</p>
          <p className="text-red-500 text-sm">{error.message}</p>
          <button onClick={() => refetch()} className="btn-primary text-sm">
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && jobs?.length === 0 && (
        <div className="card flex flex-col items-center gap-4 py-16 text-center">
          <div className="text-5xl">📭</div>
          <h2 className="text-lg font-semibold text-gray-700">No jobs yet</h2>
          <p className="text-gray-400 text-sm max-w-xs">
            Upload a dataset from the home page to create your first cleaning
            job.
          </p>
          <Link href="/" className="btn-primary">
            Upload Dataset
          </Link>
        </div>
      )}

      {/* Jobs list */}
      {!isLoading && !error && jobs && jobs.length > 0 && (
        <div className="space-y-3">
          {/* Summary bar */}
          <div className="flex gap-4 flex-wrap mb-2">
            {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
              const count = jobs.filter((j) => j.status === status).length;
              if (count === 0) return null;
              return (
                <div key={status} className="flex items-center gap-1.5 text-xs text-gray-500">
                  <span>{cfg.icon}</span>
                  <span>{cfg.label}:</span>
                  <span className="font-semibold text-gray-700">{count}</span>
                </div>
              );
            })}
          </div>

          {jobs.map((job) => (
            <JobRow key={job.job_id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
