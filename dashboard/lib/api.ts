export const api = {
  getCompanies: async (params: { search?: string; page?: number }) => {
    // mock implementation
    return {
      companies: [
        { domain: 'example.com', tech_count: 5, last_scanned: new Date().toISOString() },
        { domain: 'test.org', tech_count: 12, last_scanned: new Date().toISOString() }
      ],
      hasMore: false
    }
  },
  getCompanyProfile: async (domain: string) => {
    // mock implementation
    return {
      domain,
      last_scanned: new Date().toISOString(),
      technologies: [
        { id: 'react', name: 'React', category: 'framework', detection_vector: 'HTML_SOURCE' },
        { id: 'nextjs', name: 'Next.js', category: 'framework', detection_vector: 'HTTP_HEADER' }
      ]
    }
  },
  triggerScan: async (domain: string) => {
    console.log(`Scan triggered for ${domain}`)
  },
  getTrends: async (params: { technologies: string[]; days: number }) => {
    return {
      timeseries: [
        { date: '2024-01-01', react: 100, nextjs: 50 },
        { date: '2024-02-01', react: 120, nextjs: 60 }
      ],
      totals: { react: 120, nextjs: 60 },
      newAdoptions: { react: 20, nextjs: 10 },
      churned: { react: 5, nextjs: 2 }
    }
  }
}
