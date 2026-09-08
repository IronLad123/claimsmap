import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'
import { ReactNode } from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Superjoin — Fact Knowledge Layer',
  description: 'Extract, link, and explain facts across PDF documents',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-8 shadow-sm">
          <span className="font-bold text-xl text-indigo-700">⚡ Fact Layer</span>
          <Link href="/" className="text-sm text-gray-600 hover:text-indigo-600 font-medium transition-colors">Upload</Link>
          <Link href="/facts" className="text-sm text-gray-600 hover:text-indigo-600 font-medium transition-colors">Browse Facts</Link>
          <Link href="/compare" className="text-sm text-gray-600 hover:text-indigo-600 font-medium transition-colors">Showcase Cases</Link>
        </nav>
        <main className="container mx-auto px-6 py-8 max-w-7xl">{children}</main>
      </body>
    </html>
  )
}
