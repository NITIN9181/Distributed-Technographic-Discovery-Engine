'use client'

import { useState } from 'react'
import { TechnologySelector } from '@/components/TechnologySelector'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function TrendsPage() {
  const [selectedTech, setSelectedTech] = useState<string[]>(['react', 'nextjs'])
  const [days, setDays] = useState(90)
  
  const { data, isLoading } = useQuery({
    queryKey: ['trends', selectedTech, days],
    queryFn: () => api.getTrends({ technologies: selectedTech, days })
  })
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-gray-50 p-4 rounded shadow-sm border border-gray-100">
        <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-teal-500 to-emerald-600">Technology Trends</h1>
        <select 
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border rounded px-4 py-2 bg-white"
        >
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 180 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>
      
      <div className="h-[400px] border rounded bg-white p-6 shadow-sm">
        {isLoading ? (
          <div className="w-full h-full flex items-center justify-center">Loading chart data...</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data?.timeseries || []}>
              <XAxis dataKey="date" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Legend />
              {selectedTech.map((tech, i) => (
                <Line 
                  key={tech}
                  type="monotone"
                  dataKey={tech}
                  stroke={`hsl(${i * 120}, 70%, 50%)`}
                  strokeWidth={3}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      
      <div>
        <h2 className="text-xl font-bold mb-4 text-gray-800">Compare Technologies</h2>
        <TechnologySelector 
          selected={selectedTech}
          onChange={setSelectedTech}
          maxSelections={3}
        />
      </div>
    </div>
  )
}
