'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

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

export default function HomePage() {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<IngestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [docs, setDocs] = useState<DocItem[]>([])
  const [dragging, setDragging] = useState(false)
  const router = useRouter()

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/documents`)
      setDocs(await res.json())
    } catch { setDocs([]) }
  }, [])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const uploadFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.'); return
    }
    setUploading(true); setError(null); setResult(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${API}/api/ingest`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data: IngestResult = await res.json()
      setResult(data)
      fetchDocs()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally { setUploading(false) }
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Fact Knowledge Layer</h1>
        <p className="mt-2 text-gray-500 max-w-2xl">Upload any PDF. The system extracts structured facts, links them across documents, and explains corroborations, contradictions, and context-resolved conflicts.</p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-2xl p-14 text-center transition-colors cursor-pointer ${
          dragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 bg-white hover:border-indigo-400'
        }`}
      >
        <div className="text-6xl mb-4">📄</div>
        <p className="text-lg font-semibold text-gray-700">Drag & drop a PDF here</p>
        <p className="text-sm text-gray-400 mt-1 mb-4">or click to choose a file</p>
        <label className="cursor-pointer">
          <span className={`px-6 py-2.5 rounded-lg text-sm font-medium text-white transition ${
            uploading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
          }`}>
            {uploading ? 'Processing…' : 'Choose PDF'}
          </span>
          <input
            type="file" accept=".pdf" className="hidden"
            disabled={uploading}
            onChange={(e) => { if (e.target.files?.[0]) uploadFile(e.target.files[0]) }}
          />
        </label>
      </div>

      {result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6">
          <h2 className="font-bold text-emerald-800 text-lg">✅ Ingested: {result.filename}</h2>
          {result.demo_mode && (
            <p className="mt-2 inline-block text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1">
              ⚡ Demo mode — pre-seeded data loaded (no Gemini API key required)
            </p>
          )}
          <div className="grid grid-cols-3 gap-4 mt-5">
            {[['Pages', result.page_count], ['Facts Extracted', result.fact_count], ['Cross-Doc Links', result.link_count]].map(([label, val]) => (
              <div key={String(label)} className="bg-white rounded-xl border p-4 text-center">
                <div className="text-3xl font-bold text-indigo-700">{val}</div>
                <div className="text-xs text-gray-500 mt-1">{label}</div>
              </div>
            ))}
          </div>
          <button
            onClick={() => router.push('/compare')}
            className="mt-5 px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
          >View Showcase Cases →</button>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">{error}</div>
      )}

      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-4">Document Library</h2>
        {docs.length === 0 ? (
          <p className="text-gray-400 text-sm">No documents yet. Upload a PDF or run <code className="bg-gray-100 px-1 rounded">make seed</code> for demo data.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {docs.map((doc) => (
              <div key={doc.id} className="bg-white border rounded-2xl p-5 hover:shadow-md transition">
                <div className="text-3xl mb-2">📋</div>
                <p className="font-semibold text-gray-800 text-sm truncate" title={doc.filename}>{doc.filename}</p>
                <p className="text-xs text-gray-400 mt-1">{doc.page_count} pages · {doc.domain}</p>
                <p className="text-xs text-gray-300">{new Date(doc.upload_timestamp).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
