-- Performance indexes

CREATE INDEX IF NOT EXISTS idx_tech_by_vector 
ON technology_installations(detection_vector);

CREATE INDEX IF NOT EXISTS idx_tech_by_tech_id 
ON technology_installations(technology_identifier);

CREATE INDEX IF NOT EXISTS idx_tech_by_category
ON technology_installations(category);

CREATE INDEX IF NOT EXISTS idx_company_last_crawl
ON scanned_companies(last_successful_crawl);

CREATE INDEX IF NOT EXISTS idx_tech_initial_detection
ON technology_installations(initial_detection_date);
