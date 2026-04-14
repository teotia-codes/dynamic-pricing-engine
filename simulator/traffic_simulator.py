import random
from datetime import datetime
from core.db import get_connection, release_connection

REGION_TRAFFIC_FACTOR = {
    1: 1.15,  # Connaught Place
    2: 1.00,  # Sector 18
    3: 1.10,  # Cyber Hub
    4: 1.05,  # HSR Layout
    5: 1.12,  # Andheri West
}


def get_base_congestion(hour: int) -> float:
    if 8 <= hour <= 10:
        return random.uniform(0.60, 0.85)
    elif 12 <= hour <= 14:
        return random.uniform(0.45, 0.70)
    elif 18 <= hour <= 21:
        return random.uniform(0.70, 0.95)
    elif 22 <= hour <= 23:
        return random.uniform(0.35, 0.55)
    return random.uniform(0.18, 0.45)


def simulate_traffic():
    conn = get_connection()

    try:
        cur = conn.cursor()

        hour = datetime.now().hour
        region_ids = [1, 2, 3, 4, 5]

        for region_id in region_ids:
            base = get_base_congestion(hour)
            region_factor = REGION_TRAFFIC_FACTOR.get(region_id, 1.0)
            variance = random.uniform(0.92, 1.08)

            congestion_score = round(min(0.99, base * region_factor * variance), 2)

            cur.execute(
                """
                INSERT INTO traffic_events (
                    region_id,
                    congestion_score
                )
                VALUES (%s, %s)
                """,
                (region_id, congestion_score),
            )

        conn.commit()
        cur.close()

        print("✅ Realistic traffic events inserted successfully")

    except Exception as e:
        print(f"❌ Error in simulate_traffic: {e}")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    simulate_traffic()