from core.db import get_connection, release_connection


LATEST_PER_COMBO_CTE = """
WITH latest_per_combo AS (
    SELECT
        platform_id,
        region_id,
        MAX(calculated_at) AS latest_time
    FROM pricing_output
    GROUP BY platform_id, region_id
)
"""


def fetch_latest_prices():
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = LATEST_PER_COMBO_CTE + """
        SELECT
            p.platform_name,
            r.region_name,
            r.city,
            po.base_fee,
            po.demand_supply_ratio,
            po.peak_multiplier,
            po.weather_multiplier,
            po.traffic_multiplier,
            po.busy_multiplier,
            po.anomaly_multiplier,
            po.platform_multiplier,
            po.final_multiplier,
            po.final_fee,
            po.calculated_at
        FROM pricing_output po
        JOIN latest_per_combo l
            ON po.platform_id = l.platform_id
           AND po.region_id = l.region_id
           AND po.calculated_at = l.latest_time
        JOIN platforms p
            ON po.platform_id = p.platform_id
        JOIN regions r
            ON po.region_id = r.region_id
        ORDER BY p.platform_name, r.region_name;
        """

        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)


def fetch_latest_prices_by_platform(platform_name):
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = LATEST_PER_COMBO_CTE + """
        SELECT
            p.platform_name,
            r.region_name,
            r.city,
            po.base_fee,
            po.demand_supply_ratio,
            po.final_multiplier,
            po.final_fee,
            po.calculated_at
        FROM pricing_output po
        JOIN latest_per_combo l
            ON po.platform_id = l.platform_id
           AND po.region_id = l.region_id
           AND po.calculated_at = l.latest_time
        JOIN platforms p
            ON po.platform_id = p.platform_id
        JOIN regions r
            ON po.region_id = r.region_id
        WHERE LOWER(p.platform_name) = LOWER(%s)
        ORDER BY r.region_name;
        """

        cur.execute(query, (platform_name,))
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)


def fetch_price_history(platform_name, region_name, limit):
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = """
        SELECT
            p.platform_name,
            r.region_name,
            r.city,
            po.base_fee,
            po.demand_supply_ratio,
            po.peak_multiplier,
            po.weather_multiplier,
            po.traffic_multiplier,
            po.busy_multiplier,
            po.anomaly_multiplier,
            po.platform_multiplier,
            po.final_multiplier,
            po.final_fee,
            po.calculated_at
        FROM pricing_output po
        JOIN platforms p ON po.platform_id = p.platform_id
        JOIN regions r ON po.region_id = r.region_id
        WHERE LOWER(p.platform_name) = LOWER(%s)
          AND LOWER(r.region_name) = LOWER(%s)
        ORDER BY po.calculated_at DESC
        LIMIT %s;
        """

        cur.execute(query, (platform_name, region_name, limit))
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)


def fetch_top_surges(limit):
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = LATEST_PER_COMBO_CTE + """
        SELECT
            p.platform_name,
            r.region_name,
            r.city,
            po.demand_supply_ratio,
            po.final_multiplier,
            po.final_fee,
            po.calculated_at
        FROM pricing_output po
        JOIN latest_per_combo l
            ON po.platform_id = l.platform_id
           AND po.region_id = l.region_id
           AND po.calculated_at = l.latest_time
        JOIN platforms p
            ON po.platform_id = p.platform_id
        JOIN regions r
            ON po.region_id = r.region_id
        ORDER BY po.final_fee DESC
        LIMIT %s;
        """

        cur.execute(query, (limit,))
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)


def fetch_dashboard_summary():
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = """
        WITH latest_per_combo AS (
            SELECT DISTINCT ON (platform_id, region_id)
                platform_id,
                region_id,
                demand_supply_ratio,
                final_multiplier,
                final_fee,
                calculated_at
            FROM pricing_output
            ORDER BY platform_id, region_id, calculated_at DESC
        )
        SELECT
            COUNT(*) AS total_rows,
            COALESCE(AVG(final_fee), 0) AS avg_fee,
            COALESCE(MAX(final_multiplier), 1) AS max_multiplier,
            COALESCE(AVG(demand_supply_ratio), 0) AS avg_ds_ratio,
            COALESCE(SUM(ROUND(demand_supply_ratio * 30)), 0) AS est_active_orders,
            COUNT(DISTINCT platform_id) AS platform_count,
            COUNT(DISTINCT region_id) AS region_count
        FROM latest_per_combo;
        """

        cur.execute(query)
        row = cur.fetchone()
        cur.close()
        return row

    finally:
        release_connection(conn)


def fetch_dashboard_heatmap():
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = """
        WITH hours AS (
            SELECT generate_series(0, 23) AS hour
        ),
        pricing_by_hour AS (
            SELECT
                EXTRACT(HOUR FROM calculated_at)::int AS hour,
                COUNT(*) AS event_count
            FROM pricing_output
            WHERE calculated_at >= NOW() - INTERVAL '24 hours'
            GROUP BY 1
        )
        SELECT
            h.hour,
            COALESCE(p.event_count, 0) AS event_count
        FROM hours h
        LEFT JOIN pricing_by_hour p ON h.hour = p.hour
        ORDER BY h.hour;
        """

        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)


def fetch_dashboard_top_surges(limit):
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = """
        WITH latest_per_combo AS (
            SELECT DISTINCT ON (po.platform_id, po.region_id)
                po.price_id,
                po.platform_id,
                po.region_id,
                po.final_fee,
                po.final_multiplier,
                po.demand_supply_ratio,
                po.calculated_at
            FROM pricing_output po
            ORDER BY po.platform_id, po.region_id, po.calculated_at DESC
        )
        SELECT
            p.platform_name,
            r.region_name,
            r.city,
            l.final_fee,
            l.final_multiplier,
            l.demand_supply_ratio,
            l.calculated_at
        FROM latest_per_combo l
        JOIN platforms p ON l.platform_id = p.platform_id
        JOIN regions r ON l.region_id = r.region_id
        ORDER BY l.final_multiplier DESC, l.final_fee DESC
        LIMIT %s;
        """

        cur.execute(query, (limit,))
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)


def check_database_health():
    conn = get_connection()

    try:
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        db_time = cur.fetchone()[0]
        cur.close()
        return db_time

    finally:
        release_connection(conn)

def fetch_latest_predictions(limit=15):
    conn = get_connection()

    try:
        cur = conn.cursor()

        query = """
        WITH latest_per_combo AS (
            SELECT DISTINCT ON (platform_id, region_id)
                platform_id,
                region_id,
                current_orders_5min,
                predicted_orders_next_bucket,
                effective_orders_5min,
                risk_level,
                predicted_at
            FROM predicted_demand_output
            ORDER BY platform_id, region_id, predicted_at DESC
        )
        SELECT
            p.platform_name,
            r.region_name,
            r.city,
            l.current_orders_5min,
            l.predicted_orders_next_bucket,
            l.effective_orders_5min,
            l.risk_level,
            l.predicted_at
        FROM latest_per_combo l
        JOIN platforms p ON l.platform_id = p.platform_id
        JOIN regions r ON l.region_id = r.region_id
        ORDER BY
            CASE l.risk_level
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                ELSE 3
            END,
            l.predicted_orders_next_bucket DESC
        LIMIT %s;
        """

        cur.execute(query, (limit,))
        rows = cur.fetchall()
        cur.close()
        return rows

    finally:
        release_connection(conn)

def create_alert(platform_id, region_id, alert_type, message, severity):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alerts (
                    platform_id,
                    region_id,
                    alert_type,
                    message,
                    severity
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (platform_id, region_id, alert_type, message, severity),
            )
        conn.commit()
    finally:
        release_connection(conn)


def fetch_alerts(limit=20):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.platform_name,
                    r.region_name,
                    r.city,
                    a.alert_type,
                    a.message,
                    a.severity,
                    a.created_at
                FROM alerts a
                JOIN platforms p ON a.platform_id = p.platform_id
                JOIN regions r ON a.region_id = r.region_id
                ORDER BY a.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return rows
    finally:
        release_connection(conn)