'use client';

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';

// ---- Types -----------------------------------------------------------------

interface MedicalStandard {
  id?: string;
  standard_id?: string;
  name?: string;
  category: string;
  statement: string;
  evidence_level: 'high' | 'medium' | 'low' | string;
  confidence: number;
  citations?: string[];
  source?: string;
  tags?: string[];
}

interface StandardsResponse {
  standards: MedicalStandard[];
  total?: number;
}

// ---- Helpers ---------------------------------------------------------------

const EVIDENCE_STYLES: Record<string, string> = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-gray-100 text-gray-500',
};

const CATEGORY_COLORS: Record<string, string> = {
  'data-quality': 'bg-blue-100 text-blue-700',
  'clinical-trial': 'bg-purple-100 text-purple-700',
  'laboratory': 'bg-teal-100 text-teal-700',
  'genomics': 'bg-indigo-100 text-indigo-700',
  'regulatory': 'bg-orange-100 text-orange-700',
  'imaging': 'bg-pink-100 text-pink-700',
};

function categoryStyle(cat: string): string {
  const key = cat.toLowerCase().replace(/\s+/g, '-');
  return CATEGORY_COLORS[key] ?? 'bg-gray-100 text-gray-600';
}

// ---- Standard card ---------------------------------------------------------

function StandardCard({ std }: { std: MedicalStandard }) {
  const [expanded, setExpanded] = useState(false);
  const id = std.id ?? std.standard_id ?? '';

  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      {/* Top row */}
      <div className="flex flex-wrap gap-2 items-start justify-between mb-2">
        <div className="flex flex-wrap gap-1.5 items-center">
          <span className={`badge ${categoryStyle(std.category)}`}>
            {std.category}
          </span>
          <span className={`badge ${EVIDENCE_STYLES[std.evidence_level] ?? 'bg-gray-100 text-gray-600'}`}>
            Evidence: {std.evidence_level}
          </span>
          <span className="badge bg-brand-100 text-brand-700">
            {Math.round(std.confidence * (std.confidence <= 1 ? 100 : 1))}% confidence
          </span>
        </div>
        {std.source && (
          <span className="text-xs text-gray-400 font-medium">{std.source}</span>
        )}
      </div>

      {/* Title */}
      {std.name && (
        <h3 className="font-semibold text-gray-800 text-sm mb-1">{std.name}</h3>
      )}

      {/* Statement */}
      <p className="text-sm text-gray-600 leading-relaxed">{std.statement}</p>

      {/* Tags */}
      {std.tags && std.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {std.tags.map((tag) => (
            <span
              key={tag}
              className="text-[10px] bg-gray-50 text-gray-400 border border-gray-100 px-1.5 py-0.5 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Citations */}
      {std.citations && std.citations.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs text-brand-500 hover:text-brand-700 flex items-center gap-1"
          >
            <span className={`transition-transform ${expanded ? 'rotate-90' : ''}`}>
              ▶
            </span>
            {std.citations.length} citation{std.citations.length !== 1 ? 's' : ''}
          </button>
          {expanded && (
            <ul className="mt-2 space-y-1">
              {std.citations.map((c, i) => (
                <li
                  key={i}
                  className="text-xs text-gray-400 font-mono pl-2 border-l-2 border-brand-200"
                >
                  {c}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {id && (
        <p className="mt-2 text-[10px] text-gray-300 font-mono">ID: {id}</p>
      )}
    </div>
  );
}

// ---- Page ------------------------------------------------------------------

export default function KnowledgePage() {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [evidenceFilter, setEvidenceFilter] = useState('all');

  const { data, isLoading, error, refetch } = useQuery<
    StandardsResponse | MedicalStandard[]
  >({
    queryKey: ['knowledge', 'standards'],
    queryFn: () => apiGet('/knowledge/standards'),
    staleTime: 60_000,
  });

  // Normalise the response shape (array or {standards: [...]} object)
  const standards: MedicalStandard[] = useMemo(() => {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    return (data as StandardsResponse).standards ?? [];
  }, [data]);

  // Derived lists for filter dropdowns
  const categories = useMemo(
    () => Array.from(new Set(standards.map((s) => s.category))).sort(),
    [standards],
  );

  const filtered = useMemo(() => {
    return standards.filter((s) => {
      if (
        categoryFilter !== 'all' &&
        s.category !== categoryFilter
      )
        return false;
      if (
        evidenceFilter !== 'all' &&
        s.evidence_level !== evidenceFilter
      )
        return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        const haystack = [
          s.statement,
          s.name ?? '',
          s.category,
          s.source ?? '',
          ...(s.tags ?? []),
        ]
          .join(' ')
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [standards, categoryFilter, evidenceFilter, search]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 animate-slide-up">
      {/* Hero */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Medical Standards Knowledge Base
        </h1>
        <p className="text-gray-500 text-sm max-w-xl mx-auto">
          Browse the evidence-based medical standards used to validate and clean
          your biomedical datasets.
        </p>
      </div>

      {/* Search + filters */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex-1 relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
              🔍
            </span>
            <input
              type="text"
              placeholder="Search standards, categories, tags…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent"
            />
          </div>

          {/* Category filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 text-gray-700"
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          {/* Evidence filter */}
          <select
            value={evidenceFilter}
            onChange={(e) => setEvidenceFilter(e.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 text-gray-700"
          >
            <option value="all">All Evidence Levels</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Stats row */}
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-400">
          <span>
            Showing <strong className="text-gray-600">{filtered.length}</strong> of{' '}
            <strong className="text-gray-600">{standards.length}</strong> standards
          </span>
          {search && (
            <button
              onClick={() => {
                setSearch('');
                setCategoryFilter('all');
                setEvidenceFilter('all');
              }}
              className="text-brand-500 hover:text-brand-700"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex flex-col items-center gap-3 py-20">
          <div className="spinner-lg" />
          <p className="text-brand-600 text-sm">Loading knowledge base&hellip;</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-red-100 bg-red-50 flex flex-col items-center gap-3 py-10 text-center">
          <div className="text-4xl">⚠️</div>
          <p className="text-red-700 font-semibold">Failed to load standards</p>
          <p className="text-red-500 text-sm">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <button onClick={() => refetch()} className="btn-primary text-sm">
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && filtered.length === 0 && (
        <div className="card flex flex-col items-center gap-4 py-16 text-center">
          <div className="text-5xl">🔍</div>
          <h2 className="text-lg font-semibold text-gray-700">
            No standards found
          </h2>
          <p className="text-gray-400 text-sm">
            Try adjusting your search or filters.
          </p>
          <button
            onClick={() => {
              setSearch('');
              setCategoryFilter('all');
              setEvidenceFilter('all');
            }}
            className="btn-secondary text-sm"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Standards grid */}
      {!isLoading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((std, i) => (
            <StandardCard
              key={std.id ?? std.standard_id ?? i}
              std={std}
            />
          ))}
        </div>
      )}
    </div>
  );
}
