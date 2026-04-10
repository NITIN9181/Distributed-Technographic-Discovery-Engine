import Link from 'next/link'

export function Sidebar() {
  return (
    <div className="w-64 bg-gray-900 text-white p-4">
      <h1 className="text-xl font-bold mb-8">TechDetector</h1>
      <nav className="space-y-2">
        <Link href="/companies" className="block text-gray-300 hover:text-white">
          Companies
        </Link>
        <Link href="/trends" className="block text-gray-300 hover:text-white">
          Trends
        </Link>
      </nav>
    </div>
  )
}
