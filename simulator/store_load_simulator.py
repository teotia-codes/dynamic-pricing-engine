import random
from simulator.db import get_connection
def simulate_store_load():
    conn = get_connection()
    cur = conn.cursor()

    platform_ids = [1, 2, 3]
    region_ids = [1, 2, 3, 4, 5]

    for platform_id in platform_ids:
        for region_id in region_ids:
            if platform_id == 3:  # Blinkit
                busy_score = round(random.uniform(0.4, 0.95), 2)
                inventory_availability = round(random.uniform(0.2, 1.0), 2)
            else:
                busy_score = round(random.uniform(0.3, 0.9), 2)
                inventory_availability = 1.0  # not very relevant for food delivery

            cur.execute("""
                INSERT INTO store_load_events (
                    platform_id,
                    region_id,
                    busy_score,
                    inventory_availability
                )
                VALUES (%s, %s, %s, %s)
            """, (
                platform_id,
                region_id,
                busy_score,
                inventory_availability
            ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Store load events inserted successfully")

if __name__ == "__main__":
    simulate_store_load()