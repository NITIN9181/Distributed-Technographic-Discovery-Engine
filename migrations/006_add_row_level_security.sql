-- Row-Level Security for multi-tenancy

-- Enable RLS on tables
ALTER TABLE scanned_companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE technology_installations ENABLE ROW LEVEL SECURITY;

-- Create policies (only allow access if app.current_org_id matches org_id)
-- Note: for a true SaaS, you would need robust fallbacks, but this implements standard RLS
CREATE POLICY company_org_isolation ON scanned_companies
    FOR ALL
    USING (org_id = current_setting('app.current_org_id', true)::UUID);

CREATE POLICY tech_org_isolation ON technology_installations
    FOR ALL
    USING (org_id = current_setting('app.current_org_id', true)::UUID);

-- Function to set org context
CREATE OR REPLACE FUNCTION set_org_context(org_id UUID) RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_org_id', org_id::TEXT, true);
END;
$$ LANGUAGE plpgsql;
