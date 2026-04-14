-- Keep only recent data to avoid unbounded growth

-- Orders: keep 7 days
SELECT add_retention_policy('orders', INTERVAL '7 days', if_not_exists => TRUE);

-- Delivery partner snapshots: keep 7 days
SELECT add_retention_policy('delivery_partners', INTERVAL '7 days', if_not_exists => TRUE);

-- Traffic events: keep 7 days
SELECT add_retention_policy('traffic_events', INTERVAL '7 days', if_not_exists => TRUE);

-- Weather events: keep 7 days
SELECT add_retention_policy('weather_events', INTERVAL '7 days', if_not_exists => TRUE);

-- Store load events: keep 7 days
SELECT add_retention_policy('store_load_events', INTERVAL '7 days', if_not_exists => TRUE);

-- Pricing output history: keep 30 days (longer for analytics/demo)
SELECT add_retention_policy('pricing_output', INTERVAL '30 days', if_not_exists => TRUE);