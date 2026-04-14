import random
from datetime import datetime
from simulator.db import get_connection
def get_base_congestion():
    hour = datetime.now().hour

    # Simulate peak hours
    if 8 <= hour <= 10:
        return random.uniform(0.6, 0.9)
    elif 12 <= hour <= 14:
        return random.uniform(0.5, 0.8)
    elif 18 <= hour <= 22:
        return random.uniform(0.7, 0.95)
    else:
        return random.uniform(0.2, 0.6)

def simulate_traffic():
    conn = get_connection()
    cur = conn.cursor()

    region_ids = [1, 2, 3, 4, 5]

    for region_id in region_ids:
        congestion_score = round(get_base_congestion(), 2)

        cur.execute("""
            INSERT INTO traffic_events (
                region_id,
                congestion_score
            )
            VALUES (%s, %s)
        """, (
            region_id,
            congestion_score
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Traffic events inserted successfully")

if __name__ == "__main__":
    simulate_traffic()