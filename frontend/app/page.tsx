'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface DocItem {
  id: string
  filename: string
  domain: string
  upload_timestamp: string
  page_count: number
}

interface IngestResult {
  document_id: string
  filename: string
  page_count: number
  fact_count: number
  link_count: number
  demo_mode: boolean
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  )
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  )
}

export default function HomePage() {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<IngestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [docs, setDocs] = useState<DocItem[]>([])
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/documents`)
      if (res.ok) setDocs(await res.json())
    } catch { /* server may not be up yet */ }
  }, [])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const uploadFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported.')
      return
    }
    setUploading(true)
    setError(null)
    setResult(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${API}/api/ingest`, { method: 'POST', body: form })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `HTTP ${res.status}`)
      }
      const data: IngestResult = await res.json()
      setResult(data)
      fetchDocs()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed. Is the backend running?')
    } finally {
      setUploading(false)
    }
  }, [fetchDocs])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }, [uploadFile])

  const domainLabel: Record<string, string> = {
    delhivery: 'Delhivery',
    'india-macroeconomy': 'India Macro',
    custom: 'Custom',
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Document Ingestion</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload a PDF to extract structured facts and run cross-document reconciliation.
          </p>
        </div>
        {docs.length > 0 && (
          <Link
            href="/compare"
            className="text-sm font-medium text-violet-600 hover:text-violet-700 transition-colors"
          >
            View analysis →
          </Link>
        )}
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-xl transition-all cursor-pointer select-none
          ${dragging
            ? 'border-violet-400 bg-violet-50'
            : 'border-gray-200 bg-white hover:border-violet-300 hover:bg-gray-50'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="sr-only"
          disabled={uploading}
          onChange={(e) => { if (e.target.files?.[0]) uploadFile(e.target.files[0]) }}
        />
        <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${dragging ? 'bg-violet-100' : 'bg-gray-100'}`}>
            <UploadIcon className={`w-6 h-6 ${dragging ? 'text-violet-600' : 'text-gray-500'}`} />
          </div>
          <p className="text-sm font-medium text-gray-700">
            {uploading ? 'Processing document…' : 'Drop a PDF here, or click to browse'}
          </p>
          <p className="mt-1 text-xs text-gray-400">
            {uploading ? 'Extracting facts and running reconciliation' : 'Any financial report, policy document, or research PDF'}
          </p>
          {!uploading && (
            <button
              type="button"
              className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg hover:bg-violet-700 transition-colors"
            >
              <UploadIcon className="w-4 h-4" />
              Choose file
            </button>
          )}
          {uploading && (
            <div className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-lg opacity-80 cursor-not-allowed">
              <Spinner />
              Processing…
            </div>
          )}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-start gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <svg className="w-4 h-4 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}

      {/* Success state */}
      {result && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                <svg className="w-4 h-4 text-green-600" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">{result.filename}</p>
                {result.demo_mode && (
                  <p className="text-xs text-amber-600 mt-0.5">Running in demo mode — no API key required</p>
                )}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-3 divide-x divide-gray-100">
            {[
              { label: 'Pages', value: result.page_count },
              { label: 'Facts extracted', value: result.fact_count },
              { label: 'Cross-doc links', value: result.link_count },
            ].map(({ label, value }) => (
              <div key={label} className="px-5 py-4 text-center">
                <p className="text-2xl font-semibold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
          <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex gap-3">
            <button
              onClick={() => router.push('/compare')}
              className="text-sm font-medium text-violet-600 hover:text-violet-700 transition-colors"
            >
              View cross-document analysis →
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={() => router.push('/facts')}
              className="text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
            >
              Browse extracted facts
            </button>
          </div>
        </div>
      )}

      {/* Document library */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700">
            Loaded documents
            {docs.length > 0 && (
              <span className="ml-2 text-xs font-normal text-gray-400">{docs.length} total</span>
            )}
          </h2>
        </div>

        {docs.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-gray-200 rounded-xl bg-white">
            <FileIcon className="w-8 h-8 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-400">No documents yet</p>
            <p className="text-xs text-gray-300 mt-1">
              Run <code className="bg-gray-100 px-1 rounded font-mono">make seed</code> to load sample data
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {docs.map((doc) => (
              <div key={doc.id} className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <FileIcon className="w-4 h-4 text-gray-500" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate" title={doc.filename}>
                      {doc.filename.replace(/\d+-/, '').replace(/-excerpt\.pdf$/, '').replace(/-/g, ' ').replace('.pdf', '')}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {doc.page_count} pages
                      {doc.domain !== 'custom' && (
                        <span className="ml-2 px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">
                          {domainLabel[doc.domain] || doc.domain}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
