import { NextRequest, NextResponse } from 'next/server'
import seedData from '@/app/data/seedData.json'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const entity = searchParams.get('entity')?.toLowerCase().trim() || ''
  const metric = searchParams.get('metric')?.toLowerCase().trim() || ''
  const dataType = searchParams.get('data_type')?.trim() || ''
  const limit = parseInt(searchParams.get('limit') || '300', 10)

  let results = seedData.facts

  if (entity) {
    results = results.filter((f) => f.entity.toLowerCase().includes(entity))
  }
  if (metric) {
    results = results.filter((f) => f.metric_name.toLowerCase().includes(metric))
  }
  if (dataType) {
    results = results.filter((f) => f.data_type === dataType)
  }

  return NextResponse.json(results.slice(0, limit))
}
