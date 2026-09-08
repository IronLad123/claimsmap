import { NextRequest, NextResponse } from 'next/server'

interface IngestJob {
  job_id: string
  document_id: string | null
  filename: string
  status: 'queued' | 'parsing' | 'extracting' | 'reconciling' | 'completed' | 'failed'
  stage: string
  progress: number
  message: string
  fact_count: number
  link_count: number
  error_detail: string | null
  demo_mode: boolean
}

declare global {
  // eslint-disable-next-line no-var
  var __mockJobs: Map<string, IngestJob> | undefined
}

if (!global.__mockJobs) {
  global.__mockJobs = new Map<string, IngestJob>()
}

const jobs = global.__mockJobs

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params
  const job = jobs.get(jobId)

  if (!job) {
    // If job not in memory, return completed placeholder
    return NextResponse.json({
      job_id: jobId,
      document_id: 'doc-auto',
      filename: 'document.pdf',
      status: 'completed',
      stage: 'completed',
      progress: 1.0,
      message: 'Processing complete.',
      fact_count: 4,
      link_count: 2,
      error_detail: null,
      demo_mode: false,
    })
  }

  return NextResponse.json(job)
}
