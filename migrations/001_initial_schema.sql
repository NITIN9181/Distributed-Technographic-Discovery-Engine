-- Initial schema for TechDetector

CREATE TABLE IF NOT EXISTS scanned_companies (
    canonical_domain VARCHAR(255) PRIMARY KEY,
    corporate_name VARCHAR(255),
    last_successful_crawl TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS technology_installations (
    id SERIAL PRIMARY KEY,
    canonical_domain VARCHAR(255) NOT NULL,
    technology_identifier VARCHAR(100) NOT NULL,
    detection_vector VARCHAR(50) NOT NULL,
    evidence TEXT,
    category VARCHAR(50),
    initial_detection_date TIMESTAMP NOT NULL DEFAULT NOW(),
    latest_verification_date TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_company
        FOREIGN KEY (canonical_domain)
        REFERENCES scanned_companies(canonical_domain)
        ON DELETE CASCADE,
    CONSTRAINT unique_company_tech
        UNIQUE(canonical_domain, technology_identifier)
);
