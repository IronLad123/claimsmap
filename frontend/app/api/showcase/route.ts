import { NextResponse } from 'next/server'
import seedData from '@/app/data/seedData.json'

const TYPE_MAP: Record<string, [string, string]> = {
  CORROBORATED:           ['1',  'Corroborated Fact — expressed differently'],
  GENUINE_CONTRADICTION:  ['2',  'Genuine Contradiction'],
  RECONCILED_SCOPE:       ['3A', 'Apparent Contradiction — Reconciled by Scope'],
  RECONCILED_TEMPORAL:    ['3B', 'Apparent Contradiction — Reconciled by Time'],
  RECONCILED_METHODOLOGY: ['3C', 'Apparent Contradiction — Reconciled by Methodology'],
}

export async function GET() {
  const factsMap = new Map(seedData.facts.map((f) => [f.id, f]))
  const cases = []
  const seen = new Set<string>()

  const sortedLinks = [...seedData.links].sort((a, b) => b.confidence - a.confidence)

  for (const link of sortedLinks) {
    const rt = link.relation_type
    if (!TYPE_MAP[rt] || seen.has(rt)) continue

    const f1 = factsMap.get(link.source_fact_id)
    const f2 = factsMap.get(link.target_fact_id)
    if (!f1 || !f2) continue

    const [caseNumber, caseType] = TYPE_MAP[rt]
    cases.push({
      case_number: caseNumber,
      case_type: caseType,
      title: `${f1.entity} — ${f1.metric_name}`,
      source_a: f1,
      source_b: f2,
      link: {
        id: link.id,
        source_fact_id: link.source_fact_id,
        target_fact_id: link.target_fact_id,
        relation_type: link.relation_type,
        reconciliation_explanation: link.reconciliation_explanation,
        mathematical_delta: link.mathematical_delta,
        confidence: link.confidence,
      },
    })
    seen.add(rt)
    if (cases.length >= 5) break
  }

  return NextResponse.json({ cases })
}
