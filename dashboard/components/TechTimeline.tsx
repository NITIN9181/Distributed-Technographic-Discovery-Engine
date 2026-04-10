'use client'

import { Technology } from '@/lib/types'

interface TechTimelineProps {
  technologies: Technology[]
  domain: string
}

export function TechTimeline({ technologies, domain }: TechTimelineProps) {
  return (
    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
      {technologies.map((tech, i) => (
        <div key={tech.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
          <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-300 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
             <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
          </div>
          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between space-x-2 mb-1">
              <div className="font-bold text-slate-900">{tech.name}</div>
              <time className="font-caveat font-medium text-blue-500">{tech.first_detected_at ? new Date(tech.first_detected_at).toLocaleDateString() : 'Unknown'}</time>
            </div>
            <div className="text-slate-500 text-sm">Detected via {tech.detection_vector || 'Manual'}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
