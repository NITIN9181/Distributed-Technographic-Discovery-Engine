'use client'

import { useQuery } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import { TechProfile } from '@/components/TechProfile'
import { TechTimeline } from '@/components/TechTimeline'
import { api } from '@/lib/api'

export default function CompanyDetailPage() {
  const params = useParams()
  const domain = params?.domain as string
  
  const { data, isLoading } = useQuery({
    queryKey: ['company', domain],
    queryFn: () => api.getCompanyProfile(domain)
  })
  
  if (isLoading) return <div className="p-8 text-xl font-medium text-gray-500 animate-pulse">Loading company profile...</div>
  if (!data) return <div className="p-8 text-xl font-medium text-red-500">Company not found</div>
  
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div>
          <h1 className="text-4xl font-black text-gray-900 tracking-tight">{data.domain}</h1>
          <p className="text-gray-500 mt-1 font-medium">
            Last scanned: {new Date(data.last_scanned).toLocaleDateString()}
          </p>
        </div>
        <button 
          onClick={() => api.triggerScan(domain)}
          className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:shadow-lg hover:shadow-blue-500/30 transition-all active:scale-95"
        >
          Rescan Now
        </button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">Technology Stack</h2>
          <TechProfile technologies={data.technologies} />
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">Detection Timeline</h2>
          <TechTimeline 
            technologies={data.technologies}
            domain={domain}
          />
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-2xl font-bold mb-6 text-gray-800">Technologies by Vector</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['HTML_SOURCE', 'HTTP_HEADER', 'DNS_RECORD', 'JOB_POSTING_NLP'].map(vector => (
            <div key={vector} className="p-6 border rounded-xl hover:border-blue-200 hover:bg-blue-50/50 transition-colors">
              <h3 className="font-medium text-xs text-blue-500 tracking-wider mb-2">{vector.replace('_', ' ')}</h3>
              <p className="text-3xl font-black text-gray-900">
                {data.technologies.filter((t: any) => t.detection_vector === vector).length}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
