CREATE TABLE IF NOT EXISTS alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    platform_id INT NOT NULL REFERENCES platforms(platform_id),
    region_id INT NOT NULL REFERENCES regions(region_id),
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at
ON alerts (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_platform_region
ON alerts (platform_id, region_id);