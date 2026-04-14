-- Enable extension (safe if already present)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- =========================
-- MASTER TABLES
-- =========================
CREATE TABLE IF NOT EXISTS platforms (
    platform_id SERIAL PRIMARY KEY,
    platform_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) UNIQUE NOT NULL,
    city VARCHAR(100) NOT NULL
);

-- =========================
-- EVENT TABLES
-- =========================
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGSERIAL,
    platform_id INT NOT NULL REFERENCES platforms(platform_id),
    region_id INT NOT NULL REFERENCES regions(region_id),
    order_count INT NOT NULL,
    avg_cart_value NUMERIC(10,2) NOT NULL,
    avg_distance_km NUMERIC(10,2) NOT NULL,
    avg_prep_time_min NUMERIC(10,2) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (order_id, event_time)
);

CREATE TABLE IF NOT EXISTS delivery_partners (
    supply_id BIGSERIAL,
    platform_id INT NOT NULL REFERENCES platforms(platform_id),
    region_id INT NOT NULL REFERENCES regions(region_id),
    available_partners INT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (supply_id, event_time)
);

CREATE TABLE IF NOT EXISTS traffic_events (
    traffic_id BIGSERIAL,
    region_id INT NOT NULL REFERENCES regions(region_id),
    congestion_score NUMERIC(5,2) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (traffic_id, event_time)
);

CREATE TABLE IF NOT EXISTS weather_events (
    weather_id BIGSERIAL,
    region_id INT NOT NULL REFERENCES regions(region_id),
    temperature_c NUMERIC(5,2) NOT NULL,
    rain_mm NUMERIC(8,2) NOT NULL,
    weather_condition VARCHAR(50) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (weather_id, event_time)
);

CREATE TABLE IF NOT EXISTS store_load_events (
    store_load_id BIGSERIAL,
    platform_id INT NOT NULL REFERENCES platforms(platform_id),
    region_id INT NOT NULL REFERENCES regions(region_id),
    busy_score NUMERIC(5,2) NOT NULL,
    inventory_availability NUMERIC(5,2) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (store_load_id, event_time)
);

-- =========================
-- OUTPUT TABLE
-- =========================
CREATE TABLE IF NOT EXISTS pricing_output (
    price_id BIGSERIAL,
    platform_id INT NOT NULL REFERENCES platforms(platform_id),
    region_id INT NOT NULL REFERENCES regions(region_id),
    base_fee NUMERIC(10,2) NOT NULL,
    demand_supply_ratio NUMERIC(10,4) NOT NULL,
    peak_multiplier NUMERIC(10,4) NOT NULL,
    weather_multiplier NUMERIC(10,4) NOT NULL,
    traffic_multiplier NUMERIC(10,4) NOT NULL,
    busy_multiplier NUMERIC(10,4) NOT NULL,
    anomaly_multiplier NUMERIC(10,4) NOT NULL,
    platform_multiplier NUMERIC(10,4) NOT NULL,
    final_multiplier NUMERIC(10,4) NOT NULL,
    final_fee NUMERIC(10,2) NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (price_id, calculated_at)
);

-- =========================
-- CONVERT TO HYPERTABLES
-- =========================
SELECT create_hypertable('orders', 'event_time', if_not_exists => TRUE);
SELECT create_hypertable('delivery_partners', 'event_time', if_not_exists => TRUE);
SELECT create_hypertable('traffic_events', 'event_time', if_not_exists => TRUE);
SELECT create_hypertable('weather_events', 'event_time', if_not_exists => TRUE);
SELECT create_hypertable('store_load_events', 'event_time', if_not_exists => TRUE);
SELECT create_hypertable('pricing_output', 'calculated_at', if_not_exists => TRUE);

-- =========================
-- INDEXES (important for performance)
-- =========================
CREATE INDEX IF NOT EXISTS idx_orders_platform_region_time
ON orders (platform_id, region_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_supply_platform_region_time
ON delivery_partners (platform_id, region_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_traffic_region_time
ON traffic_events (region_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_weather_region_time
ON weather_events (region_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_store_load_platform_region_time
ON store_load_events (platform_id, region_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_pricing_output_platform_region_time
ON pricing_output (platform_id, region_id, calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_pricing_output_time
ON pricing_output (calculated_at DESC);

-- =========================
-- SEED MASTER DATA
-- =========================
INSERT INTO platforms (platform_id, platform_name)
VALUES
    (1, 'Swiggy'),
    (2, 'Zomato'),
    (3, 'Blinkit')
ON CONFLICT (platform_id) DO NOTHING;

INSERT INTO regions (region_id, region_name, city)
VALUES
    (1, 'Connaught Place', 'Delhi'),
    (2, 'Sector 18', 'Noida'),
    (3, 'Cyber Hub', 'Gurgaon'),
    (4, 'HSR Layout', 'Bengaluru'),
    (5, 'Andheri West', 'Mumbai')
ON CONFLICT (region_id) DO NOTHING;