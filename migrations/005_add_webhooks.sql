-- Webhook configuration

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    secret VARCHAR(255) NOT NULL,  -- For HMAC signing
    events TEXT[] NOT NULL,        -- Array of event types
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_triggered_at TIMESTAMP,
    failure_count INT DEFAULT 0
);

CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID REFERENCES webhooks(id) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INT,
    response_body TEXT,
    delivered_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN
);

CREATE INDEX idx_webhooks_org ON webhooks(org_id);
CREATE INDEX idx_deliveries_webhook ON webhook_deliveries(webhook_id);
