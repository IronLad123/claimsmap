'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || ''

const NAV = [
  { href: '/',        label: 'Ingest' },
  { href: '/facts',   label: 'Facts' },
  { href: '/compare', label: 'Analysis' },
]

export default function NavBar() {
  const path = usePathname()

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo + Nav */}
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-violet-600 rounded-md flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 2h4v4H2zM8 2h4v4H8zM2 8h4v4H2zM8 8h4v4H8z" fill="white" fillOpacity="0.9"/>
              </svg>
            </div>
            <span className="font-semibold text-gray-900 text-sm">ClaimsMap</span>
          </Link>

          <nav className="flex items-center gap-1">
            {NAV.map(({ href, label }) => {
              const isActive = path === href
              return (
                <Link
                  key={href}
                  href={href}
                  className={`
                    px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                    ${isActive
                      ? 'bg-violet-50 text-violet-700'
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                >
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          <a
            href={API ? `${API}/docs` : 'http://localhost:8000/docs'}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1"
          >
            API docs
            <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" clipRule="evenodd" />
            </svg>
          </a>
          <div className="h-4 w-px bg-gray-200" />
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-gray-400">Live</span>
          </div>
        </div>
      </div>
    </header>
  )
}
