import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    demo_mode: false,
    llm_provider: 'openai_compat',
    model: 'orcarouter/free',
  })
}
