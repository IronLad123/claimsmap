'use client'
import { useState, useEffect } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Fact {
  id: string
  entity: string
  metric_name: string
  raw_value: string
  raw_unit: string
  temporal_label: string
  accounting_basis: string | null
  verbatim_quote: string
  page_number: number
  confidence: number
  document_id: string
}

interface Link {
  id: string
  relation_type: string
  reconciliation_explanation: string
  mathematical_delta: number | null
  confidence: number
}

interface Case {
  case_number: string
  case_type: string
  title: string
  source_a: Fact
  source_b: Fact
  link: Link
}

const RELATION_META: Record<string, {
  label: string
  badgeClass: string
  borderClass: string
  headerClass: string
  iconColor: string
}> = {
  CORROBORATED: {
    label: 'Corroborated',
    badgeClass: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    borderClass: 'border-l-emerald-400',
    headerClass: 'bg-emerald-50/50',
    iconColor: 'text-emerald-500',
  },
  GENUINE_CONTRADICTION: {
    label: 'Contradiction',
    badgeClass: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    borderClass: 'border-l-red-400',
    headerClass: 'bg-red-50/50',
    iconColor: 'text-red-500',
  },
  RECONCILED_SCOPE: {
    label: 'Scope difference',
    badgeClass: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    borderClass: 'border-l-amber-400',
    headerClass: 'bg-amber-50/50',
    iconColor: 'text-amber-500',
  },
  RECONCILED_TEMPORAL: {
    label: 'Different period',
    badgeClass: 'bg-sky-50 text-sky-700 ring-1 ring-sky-200',
    borderClass: 'border-l-sky-400',
    headerClass: 'bg-sky-50/50',
    iconColor: 'text-sky-500',
  },
  RECONCILED_METHODOLOGY: {
    label: 'Methodology diff',
    badgeClass: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200',
    borderClass: 'border-l-violet-400',
    headerClass: 'bg-violet-50/50',
    iconColor: 'text-violet-500',
  },
}

const EXTRACTION_NOTES = [
  {
    id: 'fn-1',
    heading: 'Parenthetical negatives — table column shift',
    document: '03-delhivery-q4-fy24-earnings-presentation.pdf',
    page: 14,
    rawInput: '(217)  (125)  (67)  6  (25)  (13)  92  21',
    naiveOutput: '217   125   67   6   25   13   92   21',
    correctOutput: '-217  -125  -67  6  -25  -13  92   21',
    rootCause:
      'Row-by-row PDF text extraction loses column boundaries. Parenthetical accounting notation (217) becomes the string "217", reversing the sign. When column boundaries are lost, the full-year FY23 aggregate is assigned to the Q4 FY24 column.',
    mitigation:
      "sanitizer.py Pass 1: re.sub(r'\\(([0-9][0-9,\\.]+)\\)', r'-\\1', text). parser.py uses pdfplumber coordinate-aware bounding-box extraction to preserve column-row alignment as a structured matrix before serialising to text.",
    fixed: true,
  },
  {
    id: 'fn-2',
    heading: 'Superscript footnote contamination',
    document: '02-delhivery-annual-report-fy24-excerpt.pdf',
    page: 2,
    rawInput: '18,793(1) PIN codes  >2.8Bn(1) Express parcel shipments',
    naiveOutput: '187,931 PIN codes  >2.81 Bn shipments',
    correctOutput: '18,793 PIN codes  >2.8 Bn shipments',
    rootCause:
      'PDF text streams attach superscript footnote markers directly to number characters with no whitespace. A naive extractor concatenates 18,793 and (1) into 187,931 — a 10× magnitude error — and corrupts the decimal in 2.8Bn(1) to 2.81 Bn.',
    mitigation:
      "sanitizer.py Pass 2: re.sub(r'([0-9,\\.]+)\\s*\\(\\d+\\)', r'\\1', text). This strips the parenthetical footnote index from any number string it directly follows, recovering the correct values.",
    fixed: true,
  },
]

function RelationIcon({ type }: { type: string }) {
  if (type === 'CORROBORATED') return (
    <svg className="w-4 h-4 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
    </svg>
  )
  if (type === 'GENUINE_CONTRADICTION') return (
    <svg className="w-4 h-4 text-red-500" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
    </svg>
  )
  return (
    <svg className="w-4 h-4 text-amber-500" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
    </svg>
  )
}

function EvidenceCard({ fact, docLabel }: { fact: Fact; docLabel: string }) {
  return (
    <div className="flex-1 min-w-0 bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{docLabel}</span>
        <span className="text-xs text-gray-400">pg. {fact.page_number}</span>
      </div>
      <div className="px-4 py-4 space-y-3">
        <blockquote className="text-sm text-gray-700 italic leading-relaxed border-l-2 border-violet-300 pl-3">
          {fact.verbatim_quote}
        </blockquote>
        <div className="flex flex-wrap gap-1.5">
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-xs font-mono font-medium">
            {fact.raw_value}{fact.raw_unit ? ` ${fact.raw_unit}` : ''}
          </span>
          {fact.temporal_label && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-xs">
              {fact.temporal_label}
            </span>
          )}
          {fact.accounting_basis && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-xs capitalize">
              {fact.accounting_basis}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function CaseCard({ sc }: { sc: Case }) {
  const meta = RELATION_META[sc.link.relation_type] ?? RELATION_META.CORROBORATED
  return (
    <div className={`bg-white border border-gray-200 rounded-xl overflow-hidden border-l-4 ${meta.borderClass}`}>
      <div className={`px-5 py-4 border-b border-gray-100 flex items-start justify-between gap-4 ${meta.headerClass}`}>
        <div className="min-w-0 flex items-start gap-3">
          <RelationIcon type={sc.link.relation_type} />
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${meta.badgeClass}`}>
                {meta.label}
              </span>
              <span className="text-xs text-gray-400 font-mono">#{sc.case_number}</span>
            </div>
            <h3 className="text-sm font-semibold text-gray-900">{sc.title}</h3>
          </div>
        </div>
        <div className="text-right shrink-0 space-y-0.5">
          {sc.link.mathematical_delta != null && (
            <p className="text-xs text-gray-400 font-mono">
              Δ {(sc.link.mathematical_delta * 100).toFixed(3)}%
            </p>
          )}
          <p className="text-xs text-gray-400">
            {(sc.link.confidence * 100).toFixed(0)}% confidence
          </p>
        </div>
      </div>

      <div className="p-5 space-y-4">
        <div className="flex gap-4 flex-col md:flex-row">
          <EvidenceCard fact={sc.source_a} docLabel="Source A" />
          <div className="flex items-center justify-center shrink-0 text-gray-300">
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12zm10-4a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z" />
            </svg>
          </div>
          <EvidenceCard fact={sc.source_b} docLabel="Source B" />
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3.5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
            Reconciliation note
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">
            {sc.link.reconciliation_explanation}
          </p>
        </div>
      </div>
    </div>
  )
}

function SummaryBar({ cases }: { cases: Case[] }) {
  const counts = cases.reduce<Record<string, number>>((acc, c) => {
    acc[c.link.relation_type] = (acc[c.link.relation_type] || 0) + 1
    return acc
  }, {})
  const items = [
    { label: 'Corroborated', count: counts['CORROBORATED'] || 0, cls: 'text-emerald-600 bg-emerald-50' },
    { label: 'Contradictions', count: counts['GENUINE_CONTRADICTION'] || 0, cls: 'text-red-600 bg-red-50' },
    { label: 'Reconciled', count: (counts['RECONCILED_SCOPE'] || 0) + (counts['RECONCILED_TEMPORAL'] || 0) + (counts['RECONCILED_METHODOLOGY'] || 0), cls: 'text-amber-600 bg-amber-50' },
  ]
  return (
    <div className="grid grid-cols-3 gap-3">
      {items.map(({ label, count, cls }) => (
        <div key={label} className={`${cls} rounded-xl px-4 py-3 text-center`}>
          <p className="text-2xl font-semibold">{count}</p>
          <p className="text-xs mt-0.5 opacity-80">{label}</p>
        </div>
      ))}
    </div>
  )
}

function ExtractionNotesTab() {
  return (
    <div className="space-y-4">
      {EXTRACTION_NOTES.map((note) => (
        <div key={note.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-200 bg-slate-50 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider mb-1">
                Extraction failure + mitigation
              </p>
              <h3 className="text-sm font-semibold text-gray-900">{note.heading}</h3>
            </div>
            {note.fixed && (
              <span className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-medium rounded-full ring-1 ring-emerald-200">
                <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                </svg>
                Mitigated
              </span>
            )}
          </div>
          <div className="p-5 space-y-5">
            <div>
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Source document</p>
              <p className="text-sm text-gray-600">
                <span className="font-mono text-gray-700 text-xs">{note.document}</span>
                <span className="text-gray-400 ml-2">— page {note.page}</span>
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Raw PDF text</p>
                <code className="block text-xs bg-gray-900 text-gray-300 px-3 py-2.5 rounded-lg font-mono whitespace-pre">{note.rawInput}</code>
              </div>
              <div>
                <p className="text-xs font-medium text-red-400 uppercase tracking-wider mb-1.5">Naive extraction</p>
                <code className="block text-xs bg-red-950 text-red-300 px-3 py-2.5 rounded-lg font-mono whitespace-pre">{note.naiveOutput}</code>
              </div>
              <div>
                <p className="text-xs font-medium text-emerald-500 uppercase tracking-wider mb-1.5">After sanitizer</p>
                <code className="block text-xs bg-emerald-950 text-emerald-300 px-3 py-2.5 rounded-lg font-mono whitespace-pre">{note.correctOutput}</code>
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Root cause</p>
              <p className="text-sm text-gray-600 leading-relaxed">{note.rootCause}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Mitigation</p>
              <p className="text-sm text-gray-600 leading-relaxed">{note.mitigation}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function ComparePage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'analysis' | 'notes'>('analysis')

  useEffect(() => {
    fetch(`${API}/api/showcase`)
      .then((r) => r.json())
      .then((d) => setCases(d.cases || []))
      .catch(() => setCases([]))
      .finally(() => setLoading(false))
  }, [])

  const tabs = [
    { key: 'analysis' as const, label: 'Cross-document analysis' },
    { key: 'notes' as const, label: 'Extraction failures' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Analysis</h1>
          <p className="mt-1 text-sm text-gray-500">
            Cross-document fact relationships — corroborations, contradictions, and context-resolved conflicts with verbatim evidence.
          </p>
        </div>
      </div>

      {/* Summary bar */}
      {!loading && cases.length > 0 && <SummaryBar cases={cases} />}

      {/* Tab bar */}
      <div className="flex items-center gap-1 border-b border-gray-200">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`
              px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px
              ${tab === key
                ? 'border-violet-600 text-violet-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            {label}
            {key === 'analysis' && cases.length > 0 && (
              <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                {cases.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Analysis tab */}
      {tab === 'analysis' && (
        <div className="space-y-5">
          {loading ? (
            <div className="flex items-center justify-center py-20 text-sm text-gray-400">
              <svg className="animate-spin w-4 h-4 mr-2 text-violet-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              Loading analysis…
            </div>
          ) : cases.length === 0 ? (
            <div className="text-center py-20 border border-dashed border-gray-200 rounded-xl bg-white">
              <svg className="w-8 h-8 text-gray-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p className="text-sm font-medium text-gray-500">No analysis cases yet</p>
              <p className="text-xs text-gray-400 mt-1">Upload at least two documents to generate cross-document analysis.</p>
            </div>
          ) : (
            cases.map((sc) => <CaseCard key={sc.link.id} sc={sc} />)
          )}
        </div>
      )}

      {/* Extraction failures tab */}
      {tab === 'notes' && <ExtractionNotesTab />}
    </div>
  )
}
