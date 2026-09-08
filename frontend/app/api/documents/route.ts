import { NextResponse } from 'next/server'
import seedData from '@/app/data/seedData.json'

export async function GET() {
  return NextResponse.json(seedData.documents)
}
