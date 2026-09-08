'use client'
import { useState, useEffect } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Fact {
  id: string; entity: string; metric_name: string;
  raw_value: string; raw_unit: string; temporal_label: string;
  accounting_basis: string | null; verbatim_quote: string;
  page_number: number; confidence: number; document_id: string;
}
interface Link {
  id: string; relation_type: string;
  reconciliation_explanation: string;
  mathematical_delta: number | null; confidence: number;
}
interface Case {
  case_number: string; case_type: string; title: string;
  source_a: Fact; source_b: Fact; link: Link;
}

const CFG: Record<string, { label: string; icon: string; border: string; header: string; badge: string }> = {
  CORROBORATED:           { label: 'Corroborated',                icon: '✅', border: 'border-emerald-200', header: 'bg-emerald-50',  badge: 'bg-emerald-100 text-emerald-800' },
  GENUINE_CONTRADICTION:  { label: 'Genuine Contradiction',       icon: '❌', border: 'border-red-200',     header: 'bg-red-50',     badge: 'bg-red-100 text-red-800' },
  RECONCILED_SCOPE:       { label: 'Reconciled by Scope',         icon: '📐', border: 'border-amber-200',   header: 'bg-amber-50',   badge: 'bg-amber-100 text-amber-800' },
  RECONCILED_TEMPORAL:    { label: 'Reconciled by Time',          icon: '⏱️', border: 'border-blue-200',    header: 'bg-blue-50',    badge: 'bg-blue-100 text-blue-800' },
  RECONCILED_METHODOLOGY: { label: 'Reconciled by Methodology',   icon: '🔬', border: 'border-purple-200',  header: 'bg-purple-50',  badge: 'bg-purple-100 text-purple-800' },
}

const FAILURES = [
  {
    title: 'Failure Mode 1 — Parenthetical Negatives (Table Column Shift)',
    source: '03-delhivery-q4-fy24-earnings-presentation.pdf · Page 14',
    failure: 'Naive PDF text extractors dump table contents row-by-row, destroying column alignment. The Adjusted EBITDA table contains values like (217), (125), (67), 6, (25), (13), 92, 21 across 8 quarters. Two failures happen simultaneously: (1) parentheses are stripped, turning −217 into 217 — a sign error that converts a loss into a profit; and (2) the full-year FY23 aggregate (404) gets misassigned to the Q4 FY24 column because column boundaries are lost.',
    fix: 'sanitizer.py Pass 1 applies regex \\(([0-9][0-9,\\.]+)\\) → −N before any text reaches the LLM. parser.py uses pdfplumber coordinate-aware bounding-box extraction to serialize tables as structured row/column matrices, preserving column alignment.',
  },
  {
    title: 'Failure Mode 2 — Footnote Superscript Contamination',
    source: '02-delhivery-annual-report-fy24-excerpt.pdf · Page 2',
    failure: 'PDF text streams attach superscript footnote markers directly to numbers without whitespace. The raw text reads "18,793(1) Pin codes" and ">2.8Bn(1) Express parcel shipments". A naive extractor reads 18,7931 (one hundred eighty-seven thousand, nine hundred thirty-one) — a 10× magnitude error — or >2.81 Bn, corrupting both the value and decimal point.',
    fix: 'sanitizer.py Pass 2 applies re.sub(r\'([0-9,\\.]+)\\s*\\(\\d+\\)\', r\'\\1\', text), stripping the parenthetical footnote index from any number it immediately follows and recovering the correct value 18,793.',
  },
]

function EvidenceBlock({ fact, label }: { fact: Fact; label: string }) {
  return (
    <div className="flex-1 min-w-0 bg-white rounded-xl border p-5 space-y-3">
      <div className="flex items-start gap-2">
        <span className="text-xl">📄</span>
        <div>
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Source {label}</p>
          <p className="text-xs text-gray-400">Page {fact.page_number}</p>
        </div>
      </div>
      <blockquote className="border-l-4 border-indigo-400 pl-3 italic text-sm text-gray-700">
        &ldquo;{fact.verbatim_quote}&rdquo;
      </blockquote>
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full font-semibold">
          {fact.raw_value} {fact.raw_unit}
        </span>
        {fact.temporal_label && <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{fact.temporal_label}</span>}
        {fact.accounting_basis && <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{fact.accounting_basis}</span>}
      </div>
    </div>
  )
}

function CaseCard({ sc }: { sc: Case }) {
  const cfg = CFG[sc.link.relation_type] || CFG.CORROBORATED
  return (
    <div className={`border-2 rounded-2xl overflow-hidden ${cfg.border}`}>
      <div className={`px-6 py-4 flex items-center justify-between ${cfg.header}`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">{cfg.icon}</span>
          <div>
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${cfg.badge}`}>{cfg.label}</span>
            <h3 className="font-bold text-gray-900 mt-1">{sc.title}</h3>
          </div>
        </div>
        <span className="text-xs text-gray-400 font-mono">Case {sc.case_number}</span>
      </div>

      <div className="p-6 space-y-4">
        <div className="flex gap-4 flex-col md:flex-row">
          <EvidenceBlock fact={sc.source_a} label="A" />
          <div className="flex items-center justify-center text-3xl text-gray-300 select-none">↔</div>
          <EvidenceBlock fact={sc.source_b} label="B" />
        </div>

        <div className="bg-gray-50 rounded-xl border p-5">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">🧠 System Reasoning</p>
          <p className="text-sm text-gray-800 leading-relaxed">{sc.link.reconciliation_explanation}</p>
          <div className="flex gap-6 mt-3 text-xs text-gray-400">
            {sc.link.mathematical_delta != null && (
              <span>Δ {(sc.link.mathematical_delta * 100).toFixed(3)}%</span>
            )}
            <span>Confidence: {(sc.link.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ComparePage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'cases' | 'failures'>('cases')

  useEffect(() => {
    fetch(`${API}/api/showcase`)
      .then(r => r.json())
      .then(d => setCases(d.cases || []))
      .catch(() => setCases([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Showcase Cases</h1>
        <p className="text-gray-500 text-sm mt-1">The 4 mandatory cross-document fact relationship types — with full source evidence, verbatim quotes, and system reasoning.</p>
      </div>

      <div className="flex gap-2">
        {(['cases', 'failures'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t ? 'bg-indigo-600 text-white shadow' : 'bg-white border text-gray-600 hover:bg-gray-50'
            }`}>
            {t === 'cases' ? '🔗 Cross-Document Cases' : '⚫ Case 4 — Failure Modes'}
          </button>
        ))}
      </div>

      {tab === 'cases' && (
        <div className="space-y-6">
          {loading ? <p className="text-gray-400">Loading showcase cases…</p>
            : cases.length === 0 ? (
              <div className="text-center py-20 text-gray-400">
                <div className="text-6xl mb-4">🔍</div>
                <p className="text-lg">No showcase cases yet.</p>
                <p className="text-sm mt-1">Upload PDFs or run <code className="bg-gray-100 px-1.5 py-0.5 rounded">make seed && make demo</code> for instant demo data.</p>
              </div>
            ) : cases.map(sc => <CaseCard key={sc.link.id} sc={sc} />)
          }
        </div>
      )}

      {tab === 'failures' && (
        <div className="space-y-5">
          {FAILURES.map((fm, i) => (
            <div key={i} className="bg-gray-900 text-gray-100 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Extraction Failure + Mitigation</span>
                  <h3 className="font-bold text-white mt-0.5">{fm.title}</h3>
                </div>
                <span className="text-xs bg-emerald-800 text-emerald-200 px-2 py-0.5 rounded-full font-medium">✓ Fixed</span>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <p className="text-xs text-gray-400 font-bold uppercase mb-1">📄 Source</p>
                  <p className="text-sm text-indigo-300">{fm.source}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 font-bold uppercase mb-1">💥 The Failure</p>
                  <p className="text-sm text-gray-200 leading-relaxed">{fm.failure}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 font-bold uppercase mb-1">🛡️ Our Mitigation</p>
                  <p className="text-sm text-emerald-300 leading-relaxed">{fm.fix}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
