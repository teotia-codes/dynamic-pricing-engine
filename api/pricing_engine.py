from datetime import datetime
from api.db import get_connection

def get_peak_multiplier(platform_id):
    """
    platform_id:
    1 = Swiggy
    2 = Zomato
    3 = Blinkit
    """
    hour = datetime.now().hour

    if platform_id in [1, 2]:  # Swiggy / Zomato
        if 12 <= hour <= 14:
            return 1.15
        elif 19 <= hour <= 22:
            return 1.20
        else:
            return 1.00

    elif platform_id == 3:  # Blinkit
        if 8 <= hour <= 10:
            return 1.10
        elif 18 <= hour <= 22:
            return 1.18
        else:
            return 1.00

    return 1.00


def get_base_fee(platform_id):
    if platform_id == 1:   # Swiggy
        return 25.0
    elif platform_id == 2: # Zomato
        return 30.0
    elif platform_id == 3: # Blinkit
        return 20.0
    return 25.0


def get_platform_multiplier(platform_id):
    if platform_id == 1:   # Swiggy
        return 1.00
    elif platform_id == 2: # Zomato
        return 1.05
    elif platform_id == 3: # Blinkit
        return 0.98
    return 1.00


def get_demand_supply_multiplier(ratio):
    if ratio < 1.0:
        return 1.00
    elif ratio < 1.5:
        return 1.10
    elif ratio < 2.0:
        return 1.25
    elif ratio < 3.0:
        return 1.50
    else:
        return 1.80


def get_weather_multiplier(weather_condition):
    if weather_condition == "Clear":
        return 1.00
    elif weather_condition == "Cloudy":
        return 1.03
    elif weather_condition == "Rain":
        return 1.10
    elif weather_condition == "Heavy Rain":
        return 1.25
    elif weather_condition == "Storm":
        return 1.40
    return 1.00


def get_traffic_multiplier(congestion_score):
    if congestion_score > 0.85:
        return 1.30
    elif congestion_score > 0.70:
        return 1.15
    elif congestion_score > 0.50:
        return 1.05
    return 1.00


def get_busy_multiplier(platform_id, busy_score, inventory_availability):
    # Common busy logic
    multiplier = 1.00

    if busy_score > 0.80:
        multiplier += 0.20
    elif busy_score > 0.60:
        multiplier += 0.10

    # Blinkit special inventory pressure
    if platform_id == 3:
        if inventory_availability < 0.30:
            multiplier += 0.20
        elif inventory_availability < 0.50:
            multiplier += 0.10

    return round(multiplier, 2)


def get_anomaly_multiplier(current_orders, historical_avg):
    if historical_avg is None or historical_avg == 0:
        return 1.00

    if current_orders > 1.8 * historical_avg:
        return 1.25
    elif current_orders > 1.4 * historical_avg:
        return 1.10
    return 1.00


def fetch_latest_data(conn):
    """
    Fetch latest pricing inputs for each (platform_id, region_id)
    """
    cur = conn.cursor()

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
    cur.close()
    return rows


def insert_pricing_output(conn, records):
    cur = conn.cursor()

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
    cur.close()


def calculate_prices():
    conn = get_connection()

    try:
        rows = fetch_latest_data(conn)

        pricing_records = []

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

            print(
                f"✅ Platform {platform_id}, Region {region_id} | "
                f"Ratio={ratio}, Final Multiplier={final_multiplier}, Final Fee=₹{final_fee}"
            )

        if pricing_records:
            insert_pricing_output(conn, pricing_records)
            print(f"\n🎉 Inserted {len(pricing_records)} pricing records into pricing_output")
        else:
            print("⚠️ No pricing records found. Make sure simulator is generating data.")

    except Exception as e:
        print(f"❌ Pricing engine error: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    calculate_prices()