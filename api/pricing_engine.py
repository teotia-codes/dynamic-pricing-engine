from datetime import datetime
from core.db import get_connection, release_connection
from core.config import PRICING_CONFIG, PLATFORMS
from backend.app.logger import logger


def get_peak_multiplier(platform_id):
    hour = datetime.now().hour
    peak_windows = PRICING_CONFIG["peak_hours"].get(platform_id, [])

    for window in peak_windows:
        if window["start"] <= hour <= window["end"]:
            return window["multiplier"]

    return 1.00


def get_base_fee(platform_id):
    return PRICING_CONFIG["base_fee"].get(platform_id, 25.0)


def get_platform_multiplier(platform_id):
    return PRICING_CONFIG["platform_multiplier"].get(platform_id, 1.00)


def get_demand_supply_multiplier(ratio):
    for threshold in PRICING_CONFIG["demand_supply_thresholds"]:
        if ratio < threshold["max_ratio"]:
            return threshold["multiplier"]
    return 1.00


def get_weather_multiplier(weather_condition):
    return PRICING_CONFIG["weather_multiplier"].get(weather_condition, 1.00)


def get_traffic_multiplier(congestion_score):
    for threshold in PRICING_CONFIG["traffic_thresholds"]:
        if congestion_score > threshold["min_score"]:
            return threshold["multiplier"]
    return 1.00


def get_busy_multiplier(platform_id, busy_score, inventory_availability):
    multiplier = 1.00

    for threshold in PRICING_CONFIG["busy_thresholds"]:
        if busy_score > threshold["min_score"]:
            multiplier += threshold["increment"]
            break

    if platform_id == PLATFORMS["BLINKIT"]:
        for threshold in PRICING_CONFIG["blinkit_inventory_thresholds"]:
            if inventory_availability < threshold["max_inventory"]:
                multiplier += threshold["increment"]
                break

    return round(multiplier, 2)


def get_anomaly_multiplier(current_orders, historical_avg):
    if historical_avg is None or historical_avg == 0:
        return 1.00

    for threshold in PRICING_CONFIG["anomaly_thresholds"]:
        if current_orders > threshold["ratio"] * historical_avg:
            return threshold["multiplier"]

    return 1.00


def fetch_latest_data(conn):
    cur = conn.cursor()

    try:
        query = """
        WITH current_orders AS (
            SELECT
                platform_id,
                region_id,
                SUM(order_count) AS orders_5min
            FROM orders
            WHERE event_time >= NOW() - INTERVAL '5 minutes'
            GROUP BY platform_id, region_id
        ),
        latest_supply AS (
            SELECT DISTINCT ON (platform_id, region_id)
                platform_id,
                region_id,
                available_partners
            FROM delivery_partners
            ORDER BY platform_id, region_id, event_time DESC
        ),
        latest_weather AS (
            SELECT DISTINCT ON (region_id)
                region_id,
                weather_condition
            FROM weather_events
            ORDER BY region_id, event_time DESC
        ),
        latest_traffic AS (
            SELECT DISTINCT ON (region_id)
                region_id,
                congestion_score
            FROM traffic_events
            ORDER BY region_id, event_time DESC
        ),
        latest_store_load AS (
            SELECT DISTINCT ON (platform_id, region_id)
                platform_id,
                region_id,
                busy_score,
                inventory_availability
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
            o.platform_id,
            o.region_id,
            o.orders_5min,
            s.available_partners,
            w.weather_condition,
            t.congestion_score,
            l.busy_score,
            l.inventory_availability,
            h.avg_orders_5min
        FROM current_orders o
        JOIN latest_supply s
            ON o.platform_id = s.platform_id AND o.region_id = s.region_id
        JOIN latest_weather w
            ON o.region_id = w.region_id
        JOIN latest_traffic t
            ON o.region_id = t.region_id
        JOIN latest_store_load l
            ON o.platform_id = l.platform_id AND o.region_id = l.region_id
        LEFT JOIN historical_avg h
            ON o.platform_id = h.platform_id AND o.region_id = h.region_id
        ORDER BY o.platform_id, o.region_id;
        """

        cur.execute(query)
        rows = cur.fetchall()
        logger.info("Fetched latest data rows: %s", len(rows))
        return rows

    finally:
        cur.close()


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

        for record in records:
            cur.execute(insert_query, record)

        conn.commit()
        logger.info("Inserted %s pricing records into pricing_output", len(records))

    finally:
        cur.close()


def calculate_prices():
    conn = get_connection()

    try:
        rows = fetch_latest_data(conn)
        pricing_records = []

        if not rows:
            logger.warning("No pricing records found. Make sure simulator is generating data.")
            return

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
                historical_avg
            ) = row

            ratio = round(orders_5min / max(available_partners, 1), 4)

            base_fee = get_base_fee(platform_id)
            demand_supply_multiplier = get_demand_supply_multiplier(ratio)
            peak_multiplier = get_peak_multiplier(platform_id)
            weather_multiplier = get_weather_multiplier(weather_condition)
            traffic_multiplier = get_traffic_multiplier(float(congestion_score))
            busy_multiplier = get_busy_multiplier(
                platform_id,
                float(busy_score),
                float(inventory_availability)
            )
            anomaly_multiplier = get_anomaly_multiplier(
                orders_5min,
                float(historical_avg) if historical_avg is not None else None
            )
            platform_multiplier = get_platform_multiplier(platform_id)

            final_multiplier = round(
                demand_supply_multiplier *
                peak_multiplier *
                weather_multiplier *
                traffic_multiplier *
                busy_multiplier *
                anomaly_multiplier *
                platform_multiplier,
                4
            )

            final_fee = round(base_fee * final_multiplier, 2)

            pricing_records.append((
                platform_id,
                region_id,
                base_fee,
                ratio,
                peak_multiplier,
                weather_multiplier,
                traffic_multiplier,
                busy_multiplier,
                anomaly_multiplier,
                platform_multiplier,
                final_multiplier,
                final_fee
            ))

            logger.info(
                "Calculated price | platform_id=%s region_id=%s ratio=%s final_multiplier=%s final_fee=%s",
                platform_id,
                region_id,
                ratio,
                final_multiplier,
                final_fee,
            )

        insert_pricing_output(conn, pricing_records)

    except Exception:
        logger.exception("Pricing engine failed while calculating prices")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    calculate_prices()