'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAnalysis } from '@/hooks/useAnalysis';
import type { AnalysisResult, DataIssue, CleaningStep } from '@/hooks/useAnalysis';
import { apiPost } from '@/lib/api-client';

// ---- helpers ---------------------------------------------------------------

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  info: 'badge-info',
};

const EVIDENCE_STYLES: Record<string, string> = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-gray-100 text-gray-600',
};

const PRIORITY_STYLES: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-blue-100 text-blue-700',
};

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`badge ${SEVERITY_STYLES[severity] ?? 'badge-info'}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={`badge ${PRIORITY_STYLES[priority] ?? 'bg-gray-100 text-gray-600'}`}
    >
      {priority.toUpperCase()}
    </span>
  );
}

// ---- components ------------------------------------------------------------

function IssueRow({ issue }: { issue: DataIssue }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-2 py-3 border-b border-gray-50 last:border-0">
      <div className="sm:w-28 shrink-0">
        <SeverityBadge severity={issue.severity} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800">{issue.description}</p>
        {(issue.field ?? issue.column) && (
          <p className="text-xs text-gray-400 mt-0.5">
            Field: <span className="font-mono">{issue.field ?? issue.column}</span>
          </p>
        )}
        {issue.suggestion && (
          <p className="text-xs text-brand-600 mt-0.5 italic">
            Suggestion: {issue.suggestion}
          </p>
        )}
      </div>
      {issue.affected_rows !== undefined && (
        <div className="text-xs text-gray-400 shrink-0">
          {issue.affected_rows.toLocaleString()} rows
        </div>
      )}
    </div>
  );
}

function StepRow({ step, idx }: { step: CleaningStep; idx: number }) {
  return (
    <div className="flex gap-3 py-3 border-b border-gray-50 last:border-0">
      <div className="w-7 h-7 rounded-full gradient-bg text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
        {idx + 1}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <p className="text-sm font-semibold text-gray-800">{step.name}</p>
          <PriorityBadge priority={step.priority} />
          {step.evidence_based && (
            <span className="badge bg-green-100 text-green-700">Evidence-based</span>
          )}
        </div>
        <p className="text-xs text-gray-500">{step.description}</p>
        {step.standard && (
          <p className="text-xs text-brand-500 mt-0.5">Standard: {step.standard}</p>
        )}
        {(step.estimated_improvement !== undefined ||
          step.estimated_data_loss !== undefined) && (
          <div className="flex gap-4 mt-1">
            {step.estimated_improvement !== undefined && (
              <p className="text-xs text-green-600">
                +{step.estimated_improvement}% quality
              </p>
            )}
            {step.estimated_data_loss !== undefined && (
              <p className="text-xs text-orange-500">
                -{step.estimated_data_loss}% data loss
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---- main page -------------------------------------------------------------

export default function AnalysisPage() {
  const { fileId } = useParams<{ fileId: string }>();
  const router = useRouter();
  const { mutate: runAnalysis, data, isPending, error, isSuccess } = useAnalysis();
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    if (fileId) {
      runAnalysis(fileId);
    }
  }, [fileId, runAnalysis]);

  async function handleStartCleaning() {
    if (!data) return;
    setStarting(true);
    setStartError(null);
    try {
      const job = await apiPost<{ job_id: string }>('/jobs', {
        file_id: data.file_id,
      });
      router.push(`/jobs/${job.job_id}`);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : 'Failed to start job.');
      setStarting(false);
    }
  }

  // Loading state
  if (isPending) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
        <div className="spinner-lg" />
        <div className="text-center">
          <p className="text-brand-600 font-semibold text-lg">Analysing your dataset&hellip;</p>
          <p className="text-gray-400 text-sm mt-1">
            Checking data quality against 50+ medical standards
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-8">
        <div className="text-5xl">⚠️</div>
        <h2 className="text-xl font-semibold text-gray-800">Analysis failed</h2>
        <p className="text-gray-500 text-sm max-w-sm text-center">
          {error.message}
        </p>
        <button
          onClick={() => fileId && runAnalysis(fileId)}
          className="btn-primary mt-2"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!isSuccess || !data) return null;

  const { data_profile, issues, plan, recommendations } = data;

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 animate-slide-up space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis Results</h1>
          <p className="text-gray-400 text-sm mt-0.5">File ID: {data.file_id}</p>
        </div>
        <button
          onClick={handleStartCleaning}
          disabled={starting}
          className="btn-primary flex items-center gap-2 disabled:opacity-60"
        >
          {starting ? <span className="spinner w-4 h-4" /> : '✨'}
          {starting ? 'Starting…' : 'Start Cleaning'}
        </button>
      </div>

      {startError && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
          {startError}
        </div>
      )}

      {/* Data Profile */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Data Profile</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Records', value: data_profile.records.toLocaleString(), color: 'text-brand-600' },
            { label: 'Columns', value: data_profile.columns.toLocaleString(), color: 'text-brand-600' },
            { label: 'Issues Found', value: data_profile.issues_count.toLocaleString(), color: 'text-red-500' },
            { label: 'Data Type', value: data_profile.data_type ?? 'Unknown', color: 'text-gray-700' },
          ].map((m) => (
            <div key={m.label} className="bg-gray-50 rounded-xl p-4 text-center">
              <p className={`text-2xl font-extrabold ${m.color}`}>{m.value}</p>
              <p className="text-xs text-gray-500 mt-1">{m.label}</p>
            </div>
          ))}
        </div>
        {data_profile.sample_columns && data_profile.sample_columns.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-1">Sample columns:</p>
            <div className="flex flex-wrap gap-1.5">
              {data_profile.sample_columns.map((col) => (
                <span
                  key={col}
                  className="font-mono text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                >
                  {col}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Issues */}
      {issues.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-700">
              Data Issues{' '}
              <span className="text-gray-400 font-normal text-sm">
                ({issues.length})
              </span>
            </h2>
          </div>
          <div className="divide-y divide-gray-50">
            {issues.map((issue, i) => (
              <IssueRow key={issue.issue_id ?? i} issue={issue} />
            ))}
          </div>
        </div>
      )}

      {/* Intelligent Plan */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-700 mb-4">
          Intelligent Cleaning Plan
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Steps', value: plan.total_steps, color: 'text-brand-600' },
            { label: 'Evidence-based', value: plan.evidence_based_steps, color: 'text-green-600' },
            {
              label: 'Quality Improvement',
              value: `+${plan.quality_improvement_estimate}%`,
              color: 'text-green-600',
            },
            {
              label: 'Estimated Data Loss',
              value: `${plan.data_loss_estimate}%`,
              color: 'text-orange-500',
            },
          ].map((m) => (
            <div key={m.label} className="bg-gray-50 rounded-xl p-4 text-center">
              <p className={`text-2xl font-extrabold ${m.color}`}>{m.value}</p>
              <p className="text-xs text-gray-500 mt-1">{m.label}</p>
            </div>
          ))}
        </div>
        <div>
          {plan.steps.map((step, i) => (
            <StepRow key={step.step_id ?? i} step={step} idx={i} />
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-gray-700 mb-4">
            Recommendations
          </h2>
          <div className="space-y-4">
            {recommendations.map((rec, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-4">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-gray-800">
                    {rec.title}
                  </h3>
                  {rec.evidence_level && (
                    <span
                      className={`badge ${EVIDENCE_STYLES[rec.evidence_level] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      Evidence: {rec.evidence_level}
                    </span>
                  )}
                  {rec.confidence !== undefined && (
                    <span className="badge bg-brand-100 text-brand-700">
                      {Math.round(rec.confidence * 100)}% confidence
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{rec.description}</p>
                {rec.citations && rec.citations.length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-brand-500 cursor-pointer hover:text-brand-700">
                      {rec.citations.length} citation(s)
                    </summary>
                    <ul className="mt-1 space-y-0.5">
                      {rec.citations.map((c, ci) => (
                        <li
                          key={ci}
                          className="text-xs text-gray-400 font-mono pl-2 border-l-2 border-gray-200"
                        >
                          {c}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA bottom */}
      <div className="flex justify-end pb-6">
        <button
          onClick={handleStartCleaning}
          disabled={starting}
          className="btn-primary flex items-center gap-2 disabled:opacity-60"
        >
          {starting ? <span className="spinner w-4 h-4" /> : '✨'}
          {starting ? 'Starting…' : 'Start Cleaning Now'}
        </button>
      </div>
    </div>
  );
}
