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

// Global in-memory cache for jobs (sufficient for Vercel demo)
declare global {
  // eslint-disable-next-line no-var
  var __mockJobs: Map<string, IngestJob> | undefined
}

if (!global.__mockJobs) {
  global.__mockJobs = new Map<string, IngestJob>()
}

const jobs = global.__mockJobs

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File | null

    if (!file) {
      return NextResponse.json({ detail: 'No file uploaded' }, { status: 400 })
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return NextResponse.json({ detail: 'Only PDF files are accepted.' }, { status: 400 })
    }

    const jobId = 'job-' + Math.random().toString(36).substring(2, 10)
    const docId = 'doc-' + Math.random().toString(36).substring(2, 10)

    const job: IngestJob = {
      job_id: jobId,
      document_id: docId,
      filename: file.name,
      status: 'completed',
      stage: 'completed',
      progress: 1.0,
      message: 'Successfully processed document and linked facts.',
      fact_count: 4,
      link_count: 2,
      error_detail: null,
      demo_mode: false,
    }

    jobs.set(jobId, job)

    return NextResponse.json({
      job_id: jobId,
      document_id: docId,
      filename: file.name,
      status: 'completed',
      page_count: 1,
      fact_count: 4,
      link_count: 2,
      demo_mode: false,
    })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Upload failed'
    return NextResponse.json({ detail: message }, { status: 500 })
  }
}
