export interface Technology {
  id: string
  name: string
  category: string
  description?: string
  detection_vector?: string
  evidence?: string
  first_detected_at?: string
  last_verified_at?: string
}

export interface Company {
  domain: string
  org_id: string
  last_scanned: string
  tech_count: number
}
