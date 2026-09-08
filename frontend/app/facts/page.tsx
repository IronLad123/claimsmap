'use client'
import React, { useState, useEffect, useCallback, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || ''

interface Fact {
  id: string
  document_id: string
  entity: string
  metric_name: string
  raw_value: string
  raw_unit: string
  normalized_unit: string
  data_type: string
  temporal_label: string
  accounting_basis: string | null
  verbatim_quote: string
  page_number: number
  confidence: number
  grounding_verified: boolean
  extractor_model: string
}

const TYPE_STYLE: Record<string, { dot: string; text: string; bg: string; label: string }> = {
  currency:           { dot: 'bg-emerald-500', text: 'text-emerald-700', bg: 'bg-emerald-50', label: 'Currency' },
  volume:             { dot: 'bg-blue-500',    text: 'text-blue-700',    bg: 'bg-blue-50',    label: 'Volume' },
  percentage:         { dot: 'bg-violet-500',  text: 'text-violet-700',  bg: 'bg-violet-50',  label: 'Percentage' },
  count:              { dot: 'bg-orange-500',  text: 'text-orange-700',  bg: 'bg-orange-50',  label: 'Count' },
  semantic_statement: { dot: 'bg-gray-400',    text: 'text-gray-600',    bg: 'bg-gray-50',    label: 'Semantic' },
}

function SearchIcon() {
  return (
    <svg className="w-4 h-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
    </svg>
  )
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-150 ${open ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 011.06 0L10 11.94l3.72-3.72a.75.75 0 111.06 1.06l-4.25 4.25a.75.75 0 01-1.06 0L5.22 9.28a.75.75 0 010-1.06z" clipRule="evenodd" />
    </svg>
  )
}

function GroundedBadge({ verified }: { verified: boolean }) {
  return verified ? (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
      <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
      </svg>
      Grounded
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">
      Unverified
    </span>
  )
}

export default function FactsPage() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [loading, setLoading] = useState(true)
  const [entity, setEntity] = useState('')
  const [metric, setMetric] = useState('')
  const [dataType, setDataType] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const load = useCallback(async (e: string, m: string, dt: string) => {
    setLoading(true)
    const p = new URLSearchParams({ limit: '300' })
    if (e) p.set('entity', e)
    if (m) p.set('metric', m)
    if (dt) p.set('data_type', dt)
    try {
      const r = await fetch(`${API}/api/facts?${p}`)
      if (r.ok) setFacts(await r.json())
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => load(entity, metric, dataType), 280)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [entity, metric, dataType, load])

  const typeInfo = (dt: string) => TYPE_STYLE[dt] || TYPE_STYLE.semantic_statement
  const hasFilters = entity || metric || dataType

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Extracted facts</h1>
          <p className="mt-1 text-sm text-gray-500">
            Every fact is grounded to a verbatim source quote. Click any row to inspect the evidence.
          </p>
        </div>
        {!loading && (
          <div className="shrink-0 bg-white border border-gray-200 rounded-lg px-3 py-2 text-center">
            <p className="text-lg font-semibold text-gray-900">{facts.length}</p>
            <p className="text-xs text-gray-400">facts</p>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <SearchIcon />
          </div>
          <input
            type="text"
            placeholder="Filter by entity…"
            value={entity}
            onChange={(e) => setEntity(e.target.value)}
            className="pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent w-48"
          />
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <SearchIcon />
          </div>
          <input
            type="text"
            placeholder="Filter by metric…"
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent w-52"
          />
        </div>
        <select
          value={dataType}
          onChange={(e) => setDataType(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
        >
          <option value="">All types</option>
          <option value="currency">Currency</option>
          <option value="percentage">Percentage</option>
          <option value="count">Count</option>
          <option value="volume">Volume</option>
          <option value="semantic_statement">Semantic</option>
        </select>
        {hasFilters && (
          <button
            onClick={() => { setEntity(''); setMetric(''); setDataType('') }}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-sm text-gray-400">
            <svg className="animate-spin w-4 h-4 mr-2 text-violet-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Loading facts…
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/80">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metric</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Period</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grounded</th>
                <th className="w-8 px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {facts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16 text-sm text-gray-400">
                    <svg className="w-6 h-6 text-gray-300 mx-auto mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803 7.5 7.5 0 0015.803 15.803z" />
                    </svg>
                    {hasFilters ? 'No facts match the current filters.' : 'No facts extracted yet. Upload a PDF to get started.'}
                  </td>
                </tr>
              ) : facts.map((f) => {
                const ti = typeInfo(f.data_type)
                const isOpen = expanded === f.id
                return (
                  <React.Fragment key={f.id}>
                    <tr
                      onClick={() => setExpanded(isOpen ? null : f.id)}
                      className={`hover:bg-gray-50 cursor-pointer transition-colors ${isOpen ? 'bg-gray-50' : ''}`}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900 max-w-[140px] truncate" title={f.entity}>
                        {f.entity}
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-[200px] truncate" title={f.metric_name}>
                        {f.metric_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-900 whitespace-nowrap">
                        {f.raw_value}
                        {f.raw_unit && (
                          <span className="ml-1 text-xs text-gray-400">{f.raw_unit}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap text-xs">
                        {f.temporal_label || '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-md ${ti.text} ${ti.bg}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${ti.dot}`} />
                          {ti.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <GroundedBadge verified={f.grounding_verified} />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <ChevronIcon open={isOpen} />
                      </td>
                    </tr>
                    {isOpen && (
                      <tr>
                        <td colSpan={7} className="bg-slate-50 border-t border-gray-100 px-6 py-5">
                          <div className="flex gap-8 flex-wrap">
                            <div className="flex-1 min-w-[200px]">
                              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                                Verbatim source — page {f.page_number}
                              </p>
                              <blockquote className="text-sm text-gray-700 border-l-2 border-violet-400 pl-3 italic leading-relaxed">
                                {f.verbatim_quote}
                              </blockquote>
                            </div>
                            <div className="flex gap-6 shrink-0 flex-wrap">
                              {f.accounting_basis && (
                                <div>
                                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Basis</p>
                                  <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2 py-1 rounded capitalize">
                                    {f.accounting_basis}
                                  </span>
                                </div>
                              )}
                              <div>
                                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Confidence</p>
                                <div className="flex items-center gap-2">
                                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-violet-500 rounded-full"
                                      style={{ width: `${f.confidence * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-xs text-gray-500">{(f.confidence * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Extractor</p>
                                <span className="text-xs font-mono text-gray-500">{f.extractor_model || '—'}</span>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
