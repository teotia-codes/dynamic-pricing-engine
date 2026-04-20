from datetime import datetime, timezone
from core.db import get_connection, release_connection
from core.config import PRICING_CONFIG, PLATFORMS
from backend.app.logger import logger

# ML forecaster is optional-safe
try:
    from ml.demand_forecaster import predict_next_demand
except Exception:
    predict_next_demand = None


# =========================
# Core Multiplier Helpers
# =========================

def get_peak_multiplier(platform_id):
    """
    Use UTC hour for consistency with DB timestamps.
    """
    hour = datetime.now(timezone.utc).hour
    peak_windows = PRICING_CONFIG["peak_hours"].get(platform_id, [])

    for window in peak_windows:
        # inclusive start, exclusive end => cleaner hourly windows
        if window["start"] <= hour < window["end"]:
            return float(window["multiplier"])

    return 1.00


def get_base_fee(platform_id):
    return float(PRICING_CONFIG["base_fee"].get(platform_id, 25.0))


def get_platform_multiplier(platform_id):
    return float(PRICING_CONFIG["platform_multiplier"].get(platform_id, 1.00))


def get_demand_supply_multiplier(normalized_ratio):
    """
    Wider, more expressive tiers so chart is not flat.
    """
    if normalized_ratio <= 0.80:
        return 0.98
    elif normalized_ratio <= 1.00:
        return 1.00
    elif normalized_ratio <= 1.20:
        return 1.06
    elif normalized_ratio <= 1.50:
        return 1.14
    elif normalized_ratio <= 1.80:
        return 1.24
    elif normalized_ratio <= 2.20:
        return 1.38
    elif normalized_ratio <= 2.80:
        return 1.55
    elif normalized_ratio <= 3.50:
        return 1.72
    else:
        return 1.90


def get_weather_multiplier(weather_condition):
    """
    Use config directly (do not over-cap too aggressively).
    """
    return float(PRICING_CONFIG["weather_multiplier"].get(weather_condition, 1.00))


def get_traffic_multiplier(congestion_score):
    """
    Slightly stronger traffic effect for better real-world variation.
    """
    if congestion_score >= 0.90:
        return 1.22
    elif congestion_score >= 0.80:
        return 1.15
    elif congestion_score >= 0.65:
        return 1.09
    elif congestion_score >= 0.50:
        return 1.05
    elif congestion_score >= 0.35:
        return 1.02
    return 1.00


def get_busy_multiplier(platform_id, busy_score, inventory_availability):
    """
    Busy store / kitchen / inventory pressure.
    For Blinkit, inventory_availability may be ratio (0-1) OR absolute stock.
    """
    multiplier = 1.00

    # Busy score impact
    if busy_score >= 0.90:
        multiplier += 0.20
    elif busy_score >= 0.80:
        multiplier += 0.14
    elif busy_score >= 0.65:
        multiplier += 0.09
    elif busy_score >= 0.50:
        multiplier += 0.05

    blinkit_id = PLATFORMS.get("BLINKIT", 3)

    # Blinkit inventory pressure
    if platform_id == blinkit_id:
        if inventory_availability <= 1.0:
            # ratio style
            if inventory_availability <= 0.20:
                multiplier += 0.22
            elif inventory_availability <= 0.35:
                multiplier += 0.14
            elif inventory_availability <= 0.50:
                multiplier += 0.08
        else:
            # absolute stock style
            if inventory_availability <= 10:
                multiplier += 0.22
            elif inventory_availability <= 25:
                multiplier += 0.14
            elif inventory_availability <= 50:
                multiplier += 0.08

    return round(min(multiplier, 1.40), 4)


def get_anomaly_multiplier(current_orders, historical_avg):
    """
    Spike detection vs recent historical average.
    """
    if historical_avg is None or historical_avg <= 0:
        return 1.00

    spike_ratio = current_orders / historical_avg

    if spike_ratio >= 2.50:
        return 1.18
    elif spike_ratio >= 2.00:
        return 1.12
    elif spike_ratio >= 1.50:
        return 1.06
    elif spike_ratio <= 0.60:
        return 0.98  # slight downward correction for unusually low demand

    return 1.00


# =========================
# Ratio Normalization
# =========================

def normalize_demand_supply_ratio(orders_5min, available_partners, platform_id):
    """
    Convert 5-min demand into effective partner load.
    This is intentionally platform-aware.

    Food delivery:
      ~1 partner can handle ~2-3 active 5-min demand units
    Quick commerce (Blinkit):
      usually faster turnover, so scale differently
    """
    partners = max(float(available_partners), 1.0)
    orders_5min = max(float(orders_5min), 0.0)

    blinkit_id = PLATFORMS.get("BLINKIT", 3)

    if platform_id == blinkit_id:
        # Quick commerce can turn faster, so ratio should be a bit softer
        effective_load = orders_5min / 3.0
    else:
        # Food delivery load is more expensive operationally
        effective_load = orders_5min / 2.5

    normalized_ratio = effective_load / partners
    return round(max(normalized_ratio, 0.0), 4)


def cap_final_multiplier(multiplier):
    """
    Keep pricing realistic but not flat.
    """
    return min(max(float(multiplier), 0.85), 3.50)


# =========================
# ML Forecast Helpers
# =========================

def get_forecast_map():
    if predict_next_demand is None:
        logger.warning("ML forecaster not available. Using reactive pricing only.")
        return {}

    try:
        forecast_map = predict_next_demand()
        logger.info("Loaded ML demand forecast for %s platform-region pairs", len(forecast_map))
        return forecast_map or {}
    except Exception:
        logger.exception("Failed to load ML demand forecast. Falling back to reactive pricing only.")
        return {}


def blend_current_and_predicted_demand(current_orders_5min, predicted_orders_next_bucket):
    """
    IMPORTANT:
    Your ML model currently predicts the NEXT 1-MINUTE bucket
    (because train_demand_forecaster.py uses floor('1min')).

    So to convert predicted next bucket to 5-minute equivalent:
        predicted_5min_equivalent = predicted_1min * 5
    """
    current_orders_5min = max(float(current_orders_5min), 0.0)
    predicted_orders_next_bucket = max(float(predicted_orders_next_bucket), 0.0)

    predicted_5min_equivalent = predicted_orders_next_bucket * 5.0

    # Slightly stronger ML influence than before
    effective_orders = (0.65 * current_orders_5min) + (0.35 * predicted_5min_equivalent)

    return round(max(effective_orders, 1.0), 4)


def get_risk_level(normalized_ratio):
    if normalized_ratio >= 2.8:
        return "High"
    elif normalized_ratio >= 1.6:
        return "Medium"
    return "Low"


# =========================
# Data Fetch
# =========================

def fetch_latest_data(conn):
    """
    Fetch latest operational state for every platform-region combo.
    Orders use rolling 5-min sum.
    Supply/weather/traffic/store-load use latest snapshot.
    Historical avg uses last 24h 5-min buckets.
    """
    cur = conn.cursor()

    try:
        query = """
        WITH combos AS (
            SELECT DISTINCT platform_id, region_id FROM orders
            UNION
            SELECT DISTINCT platform_id, region_id FROM delivery_partners
            UNION
            SELECT DISTINCT platform_id, region_id FROM store_load_events
        ),
        current_orders AS (
            SELECT
                platform_id,
                region_id,
                COALESCE(SUM(order_count), 0) AS orders_5min
            FROM orders
            WHERE event_time >= NOW() - INTERVAL '5 minutes'
            GROUP BY platform_id, region_id
        ),
        latest_supply AS (
            SELECT DISTINCT ON (platform_id, region_id)
                platform_id,
                region_id,
                available_partners,
                event_time AS supply_event_time
            FROM delivery_partners
            ORDER BY platform_id, region_id, event_time DESC
        ),
        latest_weather AS (
            SELECT DISTINCT ON (region_id)
                region_id,
                weather_condition,
                event_time AS weather_event_time
            FROM weather_events
            ORDER BY region_id, event_time DESC
        ),
        latest_traffic AS (
            SELECT DISTINCT ON (region_id)
                region_id,
                congestion_score,
                event_time AS traffic_event_time
            FROM traffic_events
            ORDER BY region_id, event_time DESC
        ),
        latest_store_load AS (
            SELECT DISTINCT ON (platform_id, region_id)
                platform_id,
                region_id,
                busy_score,
                inventory_availability,
                event_time AS store_event_time
            FROM store_load_events
            ORDER BY platform_id, region_id, event_time DESC
        ),
        historical_avg AS (
            SELECT
                platform_id,
                region_id,
                AVG(bucket_orders) AS avg_orders_5min
            FROM (
                SELECT
                    platform_id,
                    region_id,
                    time_bucket('5 minutes', event_time) AS bucket,
                    SUM(order_count) AS bucket_orders
                FROM orders
                WHERE event_time >= NOW() - INTERVAL '1 day'
                GROUP BY platform_id, region_id, bucket
            ) x
            GROUP BY platform_id, region_id
        )
        SELECT
            c.platform_id,
            c.region_id,
            COALESCE(o.orders_5min, 0) AS orders_5min,
            COALESCE(s.available_partners, 1) AS available_partners,
            COALESCE(w.weather_condition, 'Unknown') AS weather_condition,
            COALESCE(t.congestion_score, 0.0) AS congestion_score,
            COALESCE(l.busy_score, 0.0) AS busy_score,
            COALESCE(l.inventory_availability, 1.0) AS inventory_availability,
            h.avg_orders_5min,
            s.supply_event_time,
            w.weather_event_time,
            t.traffic_event_time,
            l.store_event_time
        FROM combos c
        LEFT JOIN current_orders o
            ON c.platform_id = o.platform_id AND c.region_id = o.region_id
        LEFT JOIN latest_supply s
            ON c.platform_id = s.platform_id AND c.region_id = s.region_id
        LEFT JOIN latest_weather w
            ON c.region_id = w.region_id
        LEFT JOIN latest_traffic t
            ON c.region_id = t.region_id
        LEFT JOIN latest_store_load l
            ON c.platform_id = l.platform_id AND c.region_id = l.region_id
        LEFT JOIN historical_avg h
            ON c.platform_id = h.platform_id AND c.region_id = h.region_id
        ORDER BY c.platform_id, c.region_id;
        """

        cur.execute(query)
        rows = cur.fetchall()
        logger.info("Fetched latest data rows: %s", len(rows))
        return rows

    finally:
        cur.close()


# =========================
# Insert Output
# =========================

def insert_pricing_output(conn, records):
    cur = conn.cursor()

    try:
        insert_query = """
        INSERT INTO pricing_output (
            platform_id,
            region_id,
            base_fee,
            demand_supply_ratio,
            peak_multiplier,
            weather_multiplier,
            traffic_multiplier,
            busy_multiplier,
            anomaly_multiplier,
            platform_multiplier,
            final_multiplier,
            final_fee
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cur.executemany(insert_query, records)
        conn.commit()
        logger.info("Inserted %s pricing records into pricing_output", len(records))

    finally:
        cur.close()


def insert_prediction_output(conn, records):
    cur = conn.cursor()

    try:
        insert_query = """
        INSERT INTO predicted_demand_output (
            platform_id,
            region_id,
            current_orders_5min,
            predicted_orders_next_bucket,
            effective_orders_5min,
            risk_level
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cur.executemany(insert_query, records)
        conn.commit()
        logger.info("Inserted %s prediction records into predicted_demand_output", len(records))

    finally:
        cur.close()


# =========================
# Main Pricing Engine
# =========================

def calculate_prices():
    conn = get_connection()

    try:
        rows = fetch_latest_data(conn)
        pricing_records = []
        prediction_records = []

        if not rows:
            logger.warning("No source data found from simulator tables.")
            return

        forecast_map = get_forecast_map()

        for row in rows:
            (
                platform_id,
                region_id,
                orders_5min,
                available_partners,
                weather_condition,
                congestion_score,
                busy_score,
                inventory_availability,
                historical_avg,
                supply_event_time,
                weather_event_time,
                traffic_event_time,
                store_event_time
            ) = row

            current_orders_5min = float(orders_5min)
            available_partners = max(float(available_partners), 1.0)
            congestion_score = float(congestion_score)
            busy_score = float(busy_score)
            inventory_availability = float(inventory_availability)
            historical_avg = float(historical_avg) if historical_avg is not None else None

            # Fallback only when absolutely necessary
            if current_orders_5min <= 0 and historical_avg is not None:
                current_orders_5min = max(1.0, historical_avg * 0.40)
            elif current_orders_5min <= 0:
                current_orders_5min = 1.0

            # Default forecast fallback = current 5-min demand converted to 1-min estimate
            predicted_orders_next_bucket = forecast_map.get(
                (int(platform_id), int(region_id)),
                max(current_orders_5min / 5.0, 0.2)
            )

            effective_orders_5min = blend_current_and_predicted_demand(
                current_orders_5min=current_orders_5min,
                predicted_orders_next_bucket=predicted_orders_next_bucket
            )

            ratio = normalize_demand_supply_ratio(
                orders_5min=effective_orders_5min,
                available_partners=available_partners,
                platform_id=platform_id
            )

            risk_level = get_risk_level(ratio)

            prediction_records.append((
                platform_id,
                region_id,
                round(current_orders_5min, 2),
                round(float(predicted_orders_next_bucket), 2),
                round(effective_orders_5min, 2),
                risk_level
            ))

            base_fee = get_base_fee(platform_id)
            demand_supply_multiplier = get_demand_supply_multiplier(ratio)
            peak_multiplier = get_peak_multiplier(platform_id)
            weather_multiplier = get_weather_multiplier(weather_condition)
            traffic_multiplier = get_traffic_multiplier(congestion_score)
            busy_multiplier = get_busy_multiplier(
                platform_id,
                busy_score,
                inventory_availability
            )
            anomaly_multiplier = get_anomaly_multiplier(
                current_orders_5min,
                historical_avg
            )
            platform_multiplier = get_platform_multiplier(platform_id)

            final_multiplier = (
                demand_supply_multiplier *
                peak_multiplier *
                weather_multiplier *
                traffic_multiplier *
                busy_multiplier *
                anomaly_multiplier *
                platform_multiplier
            )

            final_multiplier = round(cap_final_multiplier(final_multiplier), 4)
            final_fee = round(base_fee * final_multiplier, 2)

            pricing_records.append((
                platform_id,
                region_id,
                round(base_fee, 2),
                round(ratio, 4),
                round(peak_multiplier, 4),
                round(weather_multiplier, 4),
                round(traffic_multiplier, 4),
                round(busy_multiplier, 4),
                round(anomaly_multiplier, 4),
                round(platform_multiplier, 4),
                round(final_multiplier, 4),
                round(final_fee, 2)
            ))

            logger.info(
                (
                    "Calculated price | platform_id=%s region_id=%s "
                    "orders_5min=%s predicted_next_1min=%s effective_5min=%s partners=%s "
                    "weather=%s traffic=%.2f busy=%.2f inventory=%.2f hist_avg=%s "
                    "ratio=%s risk=%s multipliers=[ds=%s peak=%s weather=%s traffic=%s busy=%s anomaly=%s platform=%s] "
                    "final_multiplier=%s final_fee=%s"
                ),
                platform_id,
                region_id,
                round(current_orders_5min, 2),
                round(float(predicted_orders_next_bucket), 2),
                round(effective_orders_5min, 2),
                round(available_partners, 2),
                weather_condition,
                congestion_score,
                busy_score,
                inventory_availability,
                round(historical_avg, 2) if historical_avg is not None else None,
                ratio,
                risk_level,
                round(demand_supply_multiplier, 4),
                round(peak_multiplier, 4),
                round(weather_multiplier, 4),
                round(traffic_multiplier, 4),
                round(busy_multiplier, 4),
                round(anomaly_multiplier, 4),
                round(platform_multiplier, 4),
                final_multiplier,
                final_fee,
            )

            # Optional stale data warning
            if not supply_event_time or not weather_event_time or not traffic_event_time or not store_event_time:
                logger.warning(
                    "Some simulator inputs missing for platform_id=%s region_id=%s "
                    "(supply=%s weather=%s traffic=%s store=%s)",
                    platform_id,
                    region_id,
                    supply_event_time,
                    weather_event_time,
                    traffic_event_time,
                    store_event_time,
                )

        if prediction_records:
            insert_prediction_output(conn, prediction_records)

        if pricing_records:
            insert_pricing_output(conn, pricing_records)
        else:
            logger.warning("No pricing records generated in this cycle.")

    except Exception:
        logger.exception("Pricing engine failed while calculating prices")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    calculate_prices()