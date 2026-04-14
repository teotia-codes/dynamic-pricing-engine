from fastapi import FastAPI, HTTPException
from api.db import get_connection

app = FastAPI(
    title="Dynamic Pricing Engine API",
    description="Real-time dynamic delivery pricing for Swiggy / Zomato / Blinkit style platforms",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Dynamic Pricing Engine API is running 🚀",
        "project": "Swiggy / Zomato / Blinkit Real-Time Pricing Engine"
    }


@app.get("/health")
def health_check():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        db_time = cur.fetchone()[0]
        cur.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "db_time": str(db_time)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.get("/latest-prices")
def get_latest_prices():
    """
    Get latest price snapshot for all platform-region combinations
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        WITH latest_per_combo AS (
            SELECT
                platform_id,
                region_id,
                MAX(calculated_at) AS latest_time
            FROM pricing_output
            GROUP BY platform_id, region_id
        )
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

        result = []
        for row in rows:
            result.append({
                "platform": row[0],
                "region": row[1],
                "city": row[2],
                "base_fee": float(row[3]),
                "demand_supply_ratio": float(row[4]),
                "peak_multiplier": float(row[5]),
                "weather_multiplier": float(row[6]),
                "traffic_multiplier": float(row[7]),
                "busy_multiplier": float(row[8]),
                "anomaly_multiplier": float(row[9]),
                "platform_multiplier": float(row[10]),
                "final_multiplier": float(row[11]),
                "final_fee": float(row[12]),
                "calculated_at": str(row[13])
            })

        cur.close()
        conn.close()

        return {
            "count": len(result),
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/latest-prices/{platform_name}")
def get_latest_prices_by_platform(platform_name: str):
    """
    Get latest prices for a single platform: swiggy / zomato / blinkit
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        WITH latest_per_combo AS (
            SELECT
                platform_id,
                region_id,
                MAX(calculated_at) AS latest_time
            FROM pricing_output
            GROUP BY platform_id, region_id
        )
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

        if not rows:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"No pricing data found for platform '{platform_name}'")

        result = []
        for row in rows:
            result.append({
                "platform": row[0],
                "region": row[1],
                "city": row[2],
                "base_fee": float(row[3]),
                "demand_supply_ratio": float(row[4]),
                "final_multiplier": float(row[5]),
                "final_fee": float(row[6]),
                "calculated_at": str(row[7])
            })

        cur.close()
        conn.close()

        return {
            "platform": platform_name,
            "count": len(result),
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{platform_name}/{region_name}")
def get_price_history(platform_name: str, region_name: str, limit: int = 20):
    """
    Get recent pricing history for a platform + region
    Example:
    /history/Swiggy/Connaught%20Place
    """
    try:
        conn = get_connection()
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

        if not rows:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"No history found for platform '{platform_name}' in region '{region_name}'"
            )

        result = []
        for row in rows:
            result.append({
                "platform": row[0],
                "region": row[1],
                "city": row[2],
                "base_fee": float(row[3]),
                "demand_supply_ratio": float(row[4]),
                "peak_multiplier": float(row[5]),
                "weather_multiplier": float(row[6]),
                "traffic_multiplier": float(row[7]),
                "busy_multiplier": float(row[8]),
                "anomaly_multiplier": float(row[9]),
                "platform_multiplier": float(row[10]),
                "final_multiplier": float(row[11]),
                "final_fee": float(row[12]),
                "calculated_at": str(row[13])
            })

        cur.close()
        conn.close()

        return {
            "platform": platform_name,
            "region": region_name,
            "count": len(result),
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/top-surges")
def get_top_surges(limit: int = 10):
    """
    Get highest current surge fees across all platform-region combinations
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        WITH latest_per_combo AS (
            SELECT
                platform_id,
                region_id,
                MAX(calculated_at) AS latest_time
            FROM pricing_output
            GROUP BY platform_id, region_id
        )
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

        result = []
        for row in rows:
            result.append({
                "platform": row[0],
                "region": row[1],
                "city": row[2],
                "demand_supply_ratio": float(row[3]),
                "final_multiplier": float(row[4]),
                "final_fee": float(row[5]),
                "calculated_at": str(row[6])
            })

        cur.close()
        conn.close()

        return {
            "count": len(result),
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))