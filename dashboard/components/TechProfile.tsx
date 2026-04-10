'use client'

import { Technology } from '@/lib/types'

interface TechProfileProps {
  technologies: Technology[]
}

const categoryColors: Record<string, string> = {
  analytics: 'bg-blue-100 text-blue-800',
  framework: 'bg-purple-100 text-purple-800',
  database: 'bg-orange-100 text-orange-800',
  cloud: 'bg-cyan-100 text-cyan-800',
}

export function TechProfile({ technologies }: TechProfileProps) {
  const grouped = technologies.reduce((acc, tech) => {
    const cat = tech.category || 'other'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(tech)
    return acc
  }, {} as Record<string, Technology[]>)
  
  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([category, techs]) => (
        <div key={category}>
          <h3 className="text-sm font-medium text-gray-500 uppercase mb-2">
            {category}
          </h3>
          <div className="flex flex-wrap gap-2">
            {techs.map(tech => (
              <span 
                key={tech.id}
                className={`px-3 py-1 rounded-full text-sm ${categoryColors[category] || 'bg-gray-100 text-gray-800'}`}
                title={`Detected via ${tech.detection_vector}`}
              >
                {tech.name}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
