'use client'

interface TechnologySelectorProps {
  selected: string[]
  onChange: (selected: string[]) => void
  maxSelections?: number
}

const ALL_TECHS = ['react', 'nextjs', 'vue', 'angular', 'svelte', 'snowflake', 'databricks', 'bigquery', 'postgresql', 'mysql']

export function TechnologySelector({ selected, onChange, maxSelections = 5 }: TechnologySelectorProps) {
  const toggle = (tech: string) => {
    if (selected.includes(tech)) {
      onChange(selected.filter(t => t !== tech))
    } else {
      if (selected.length < maxSelections) {
        onChange([...selected, tech])
      }
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {ALL_TECHS.map(tech => (
        <button
          key={tech}
          onClick={() => toggle(tech)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            selected.includes(tech) 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {tech}
        </button>
      ))}
    </div>
  )
}
