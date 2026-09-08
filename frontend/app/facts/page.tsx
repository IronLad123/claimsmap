'use client'
import React, { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Fact {
  id: string
  document_id: string
  entity: string
  metric_name: string
  raw_value: string
  raw_unit: string
  data_type: string
  temporal_label: string
  accounting_basis: string | null
  verbatim_quote: string
  page_number: number
  confidence: number
}

const TYPE_COLORS: Record<string, string> = {
  currency: 'bg-emerald-100 text-emerald-800',
  volume: 'bg-blue-100 text-blue-800',
  percentage: 'bg-purple-100 text-purple-800',
  count: 'bg-orange-100 text-orange-800',
  semantic_statement: 'bg-gray-100 text-gray-700',
}

export default function FactsPage() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [loading, setLoading] = useState(true)
  const [entity, setEntity] = useState('')
  const [metric, setMetric] = useState('')
  const [dataType, setDataType] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    const p = new URLSearchParams({ limit: '300' })
    if (entity) p.set('entity', entity)
    if (metric) p.set('metric', metric)
    if (dataType) p.set('data_type', dataType)
    try {
      const r = await fetch(`${API}/api/facts?${p}`)
      setFacts(await r.json())
    } catch { setFacts([]) }
    finally { setLoading(false) }
  }, [entity, metric, dataType])

  useEffect(() => { load() }, [load])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Browse Facts</h1>
        <p className="text-gray-500 text-sm mt-1">All extracted facts with source citations. Click any row to reveal the verbatim quote.</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <input type="text" placeholder="Filter by entity…" value={entity}
          onChange={(e) => setEntity(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-52 focus:ring-2 focus:ring-indigo-300 outline-none" />
        <input type="text" placeholder="Filter by metric…" value={metric}
          onChange={(e) => setMetric(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-52 focus:ring-2 focus:ring-indigo-300 outline-none" />
        <select value={dataType} onChange={(e) => setDataType(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-300 outline-none">
          <option value="">All types</option>
          <option value="currency">Currency</option>
          <option value="volume">Volume</option>
          <option value="percentage">Percentage</option>
          <option value="count">Count</option>
          <option value="semantic_statement">Semantic</option>
        </select>
      </div>

      {loading ? <p className="text-gray-400">Loading facts…</p> : (
        <div className="bg-white border rounded-2xl overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-left">
              <tr>
                {['Entity','Metric','Value','Period','Type','Page','Conf.'].map(h => (
                  <th key={h} className="px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {facts.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-12 text-gray-400">No facts found.</td></tr>
              ) : facts.map((f) => (
                <React.Fragment key={f.id}>
                  <tr onClick={() => setExpanded(expanded === f.id ? null : f.id)}
                    className="hover:bg-indigo-50 cursor-pointer transition">
                    <td className="px-4 py-3 font-medium text-gray-800 max-w-[150px] truncate" title={f.entity}>{f.entity}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-[180px] truncate" title={f.metric_name}>{f.metric_name}</td>
                    <td className="px-4 py-3 font-mono text-indigo-700 whitespace-nowrap">
                      {f.raw_value} <span className="text-gray-400 text-xs">{f.raw_unit}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{f.temporal_label}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TYPE_COLORS[f.data_type] || 'bg-gray-100 text-gray-600'}`}>
                        {f.data_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{f.page_number}</td>
                    <td className="px-4 py-3 text-gray-400">{(f.confidence * 100).toFixed(0)}%</td>
                  </tr>
                  {expanded === f.id && (
                    <tr key={`${f.id}-exp`}>
                      <td colSpan={7} className="px-6 py-4 bg-indigo-50">
                        <div className="border-l-4 border-indigo-400 pl-4">
                          <p className="text-xs font-bold text-indigo-600 mb-1 uppercase tracking-wide">Verbatim Quote — Page {f.page_number}</p>
                          <p className="text-sm text-gray-700 italic">&ldquo;{f.verbatim_quote}&rdquo;</p>
                          {f.accounting_basis && (
                            <p className="text-xs text-gray-400 mt-2">Accounting basis: <span className="font-medium">{f.accounting_basis}</span></p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-2 border-t text-xs text-gray-400">{facts.length} facts shown</div>
        </div>
      )}
    </div>
  )
}
