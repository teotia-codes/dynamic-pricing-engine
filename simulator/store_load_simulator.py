import random
from datetime import datetime
from core.db import get_connection, release_connection
from core.config import PLATFORMS


def get_busy_score(platform_id: int, hour: int) -> float:
    if platform_id == PLATFORMS["blinkit"]:
        if 18 <= hour <= 21:
            return random.uniform(0.65, 0.92)
        elif 22 <= hour or hour <= 1:
            return random.uniform(0.70, 0.96)
        elif 9 <= hour <= 11:
            return random.uniform(0.55, 0.82)
        return random.uniform(0.35, 0.70)
    else:
        if 8 <= hour <= 10:
            return random.uniform(0.50, 0.78)
        elif 12 <= hour <= 15:
            return random.uniform(0.65, 0.90)
        elif 19 <= hour <= 22:
            return random.uniform(0.72, 0.95)
        return random.uniform(0.35, 0.68)


def get_inventory_availability(hour: int) -> float:
    if 18 <= hour <= 21:
        return random.uniform(0.45, 0.85)
    elif 22 <= hour or hour <= 1:
        return random.uniform(0.35, 0.78)
    elif 9 <= hour <= 11:
        return random.uniform(0.55, 0.92)
    return random.uniform(0.65, 1.0)


def simulate_store_load():
    conn = get_connection()

    try:
        cur = conn.cursor()

        hour = datetime.now().hour
        platform_ids = list(PLATFORMS.values())
        region_ids = [1, 2, 3, 4, 5]

        for platform_id in platform_ids:
            for region_id in region_ids:
                busy_score = round(get_busy_score(platform_id, hour), 2)

                if platform_id == PLATFORMS["blinkit"]:
                    inventory_availability = round(get_inventory_availability(hour), 2)
                else:
                    inventory_availability = 1.0

                cur.execute(
                    """
                    INSERT INTO store_load_events (
                        platform_id,
                        region_id,
                        busy_score,
                        inventory_availability
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        platform_id,
                        region_id,
                        busy_score,
                        inventory_availability,
                    ),
                )

        conn.commit()
        cur.close()

        print("✅ Realistic store load events inserted successfully")

    except Exception as e:
        print(f"❌ Error in simulate_store_load: {e}")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    simulate_store_load()