CREATE TABLE IF NOT EXISTS predicted_demand_output (
    prediction_id BIGSERIAL,
    platform_id INT NOT NULL REFERENCES platforms(platform_id),
    region_id INT NOT NULL REFERENCES regions(region_id),
    current_orders_5min NUMERIC(10,2) NOT NULL,
    predicted_orders_next_bucket NUMERIC(10,2) NOT NULL,
    effective_orders_5min NUMERIC(10,2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (prediction_id, predicted_at)
);

CREATE INDEX IF NOT EXISTS idx_predicted_demand_platform_region_time
ON predicted_demand_output (platform_id, region_id, predicted_at DESC);

CREATE INDEX IF NOT EXISTS idx_predicted_demand_time
ON predicted_demand_output (predicted_at DESC);