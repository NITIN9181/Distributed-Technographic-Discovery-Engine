'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { SearchBar } from '@/components/SearchBar'
import { DataTable } from '@/components/DataTable'
import { api } from '@/lib/api'

export default function CompaniesPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  
  const { data, isLoading } = useQuery({
    queryKey: ['companies', search, page],
    queryFn: () => api.getCompanies({ search, page })
  })
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-gray-50 p-4 rounded shadow-sm border border-gray-100">
        <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Companies</h1>
        <SearchBar 
          value={search} 
          onChange={setSearch}
          placeholder="Search by domain..."
        />
      </div>
      
      <DataTable
        columns={[
          { key: 'domain', header: 'Domain' },
          { key: 'tech_count', header: 'Technologies' },
          { key: 'last_scanned', header: 'Last Scanned' },
        ]}
        data={data?.companies || []}
        isLoading={isLoading}
        onRowClick={(row) => window.location.href = `/companies/${row.domain}`}
      />
      
      <div className="flex justify-center gap-2 mt-8">
        <button 
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-6 py-2 border rounded-full font-medium hover:bg-gray-100 disabled:opacity-50 transition-colors"
        >
          Previous
        </button>
        <span className="px-4 py-2 font-medium">Page {page}</span>
        <button 
          onClick={() => setPage(p => p + 1)}
          disabled={!data?.hasMore}
          className="px-6 py-2 border rounded-full font-medium hover:bg-gray-100 disabled:opacity-50 transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  )
}
