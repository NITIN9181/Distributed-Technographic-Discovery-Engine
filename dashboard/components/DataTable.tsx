'use client'

interface DataTableProps {
  columns: { key: string; header: string }[]
  data: any[]
  isLoading?: boolean
  onRowClick?: (row: any) => void
}

export function DataTable({ columns, data, isLoading, onRowClick }: DataTableProps) {
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="overflow-x-auto rounded border">
      <table className="min-w-full divide-y bg-white">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {data.map((row, i) => (
            <tr 
              key={i} 
              onClick={() => onRowClick?.(row)}
              className={onRowClick ? "cursor-pointer hover:bg-gray-50" : ""}
            >
              {columns.map(col => (
                <td key={col.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
