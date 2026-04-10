-- Multi-tenancy: Organizations

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(50) DEFAULT 'free'
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    org_id UUID REFERENCES organizations(id),
    role VARCHAR(50) DEFAULT 'member',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add org_id to existing tables
ALTER TABLE scanned_companies ADD COLUMN org_id UUID REFERENCES organizations(id);
ALTER TABLE technology_installations ADD COLUMN org_id UUID REFERENCES organizations(id);

-- Index for org filtering
CREATE INDEX idx_companies_org ON scanned_companies(org_id);
CREATE INDEX idx_installations_org ON technology_installations(org_id);
