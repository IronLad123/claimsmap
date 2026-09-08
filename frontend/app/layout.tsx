import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ReactNode } from 'react'
import NavBar from './components/NavBar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ClaimsMap — Cross-Document Fact Verification',
  description: 'Map, extract, and verify claims across multiple PDF documents',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-[#f8f9fb]`}>
        <div className="min-h-screen flex flex-col">
          <NavBar />
          <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
