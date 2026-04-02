'use client';

import React, { useCallback, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiUpload } from '@/lib/api-client';

interface UploadResponse {
  file_id: string;
  filename: string;
  size?: number;
  records?: number;
  columns?: number;
}

const ACCEPTED = ['.csv', '.xlsx', '.xls'];

const FEATURES = [
  {
    icon: '📋',
    title: '50+ Medical Standards',
    description:
      'Validated against WHO, CDISC, HL7 FHIR, ICH E6(R2), and more. Every cleaning step is grounded in official biomedical guidelines.',
  },
  {
    icon: '🤖',
    title: 'Intelligent Planning',
    description:
      'AI-powered analysis identifies data quality issues and generates a prioritised, evidence-based cleaning plan tailored to your dataset.',
  },
  {
    icon: '🔬',
    title: 'Scientific Validation',
    description:
      'Each transformation is backed by peer-reviewed literature and regulatory standards, with full audit trails for compliance.',
  },
];

export default function HomePage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!ext || !['csv', 'xlsx', 'xls'].includes(ext)) {
        setError('Please upload a CSV or Excel (.xlsx / .xls) file.');
        return;
      }

      setError(null);
      setUploading(true);
      setProgress(10);

      try {
        // Simulate incremental progress while uploading
        const progressTimer = setInterval(() => {
          setProgress((p) => Math.min(p + 10, 85));
        }, 200);

        const result = await apiUpload<UploadResponse>('/upload', file);

        clearInterval(progressTimer);
        setProgress(100);

        // Short delay so user sees 100%
        await new Promise((r) => setTimeout(r, 300));
        router.push(`/analysis/${result.file_id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
        setUploading(false);
        setProgress(0);
      }
    },
    [router],
  );

  // Drag handlers
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };
  const onDragLeave = () => setDragging(false);
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };
  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="min-h-full">
      {/* Hero */}
      <section className="gradient-bg text-white py-20 px-4">
        <div className="max-w-3xl mx-auto text-center animate-fade-in">
          <div className="text-6xl mb-6">🧬</div>
          <h1 className="text-4xl sm:text-5xl font-extrabold mb-4 tracking-tight">
            Bio Clean Agent
          </h1>
          <p className="text-xl sm:text-2xl text-white/85 font-light mb-2">
            Intelligent Biomedical Data Cleaning
          </p>
          <p className="text-white/70 max-w-xl mx-auto text-sm sm:text-base">
            Upload your clinical or laboratory dataset. Our AI analyses data
            quality, generates an evidence-based cleaning plan, and guides you
            step-by-step to research-grade data.
          </p>
        </div>
      </section>

      {/* Upload area */}
      <section className="max-w-2xl mx-auto px-4 -mt-10 animate-slide-up">
        <div className="card shadow-xl">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">
            Upload your dataset
          </h2>

          {/* Drop zone */}
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => !uploading && inputRef.current?.click()}
            className={[
              'border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer select-none',
              dragging
                ? 'border-brand-500 bg-brand-50 scale-[1.01]'
                : 'border-gray-200 hover:border-brand-400 hover:bg-gray-50',
              uploading ? 'pointer-events-none opacity-70' : '',
            ].join(' ')}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED.join(',')}
              className="hidden"
              onChange={onInputChange}
              disabled={uploading}
            />

            {uploading ? (
              <div className="flex flex-col items-center gap-4">
                <div className="spinner-lg" />
                <p className="text-brand-600 font-semibold text-sm">
                  Uploading&hellip; {progress}%
                </p>
                <div className="w-full max-w-xs bg-gray-100 rounded-full h-2">
                  <div
                    className="gradient-bg h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            ) : (
              <>
                <div className="text-5xl mb-3">📂</div>
                <p className="text-gray-700 font-medium mb-1">
                  Drag &amp; drop your file here
                </p>
                <p className="text-gray-400 text-sm mb-4">
                  or click to browse
                </p>
                <span className="badge bg-gray-100 text-gray-500 text-xs">
                  CSV &bull; XLSX &bull; XLS
                </span>
              </>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-start gap-2">
              <span className="text-red-500 mt-0.5">⚠️</span>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <p className="mt-4 text-xs text-gray-400 text-center">
            Maximum file size: 100 MB &mdash; All data is processed locally and
            never shared.
          </p>
        </div>
      </section>

      {/* Feature cards */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-2">
          Why Bio Clean Agent?
        </h2>
        <p className="text-center text-gray-500 mb-10 text-sm">
          Built for researchers, clinicians, and data scientists who need
          publication-ready biomedical datasets.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="card hover:shadow-md transition-shadow duration-200"
            >
              <div className="text-4xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-gray-800 mb-2">{f.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
