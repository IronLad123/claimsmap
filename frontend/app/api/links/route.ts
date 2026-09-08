import { NextRequest, NextResponse } from 'next/server'
import seedData from '@/app/data/seedData.json'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const relationType = searchParams.get('relation_type')
  const limit = parseInt(searchParams.get('limit') || '200', 10)

  let links = seedData.links
  if (relationType) {
    links = links.filter((l) => l.relation_type === relationType)
  }

  return NextResponse.json(links.slice(0, limit))
}
