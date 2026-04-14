import random
from simulator.db import get_connection

def generate_orders():
    conn = get_connection()
    cur = conn.cursor()

    # platform_id: 1=Swiggy, 2=Zomato, 3=Blinkit
    platform_ids = [1, 2, 3]
    region_ids = [1, 2, 3, 4, 5]

    for platform_id in platform_ids:
        for region_id in region_ids:
            if platform_id == 3:  # Blinkit
                order_count = random.randint(8, 25)
                avg_cart_value = round(random.uniform(300, 1200), 2)
                avg_distance_km = round(random.uniform(1.0, 5.0), 2)
                avg_prep_time_min = round(random.uniform(3.0, 10.0), 2)
            else:  # Swiggy / Zomato
                order_count = random.randint(5, 20)
                avg_cart_value = round(random.uniform(200, 1000), 2)
                avg_distance_km = round(random.uniform(2.0, 10.0), 2)
                avg_prep_time_min = round(random.uniform(10.0, 35.0), 2)

            cur.execute("""
                INSERT INTO orders (
                    platform_id,
                    region_id,
                    order_count,
                    avg_cart_value,
                    avg_distance_km,
                    avg_prep_time_min
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                platform_id,
                region_id,
                order_count,
                avg_cart_value,
                avg_distance_km,
                avg_prep_time_min
            ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Orders inserted successfully")

if __name__ == "__main__":
    generate_orders()