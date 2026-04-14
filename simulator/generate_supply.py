import random
from simulator.db import get_connection
def generate_supply():
    conn = get_connection()
    cur = conn.cursor()

    platform_ids = [1, 2, 3]
    region_ids = [1, 2, 3, 4, 5]

    for platform_id in platform_ids:
        for region_id in region_ids:
            if platform_id == 3:  # Blinkit
                available_partners = random.randint(5, 18)
            else:
                available_partners = random.randint(8, 25)

            cur.execute("""
                INSERT INTO delivery_partners (
                    platform_id,
                    region_id,
                    available_partners
                )
                VALUES (%s, %s, %s)
            """, (
                platform_id,
                region_id,
                available_partners
            ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Delivery partner supply inserted successfully")

if __name__ == "__main__":
    generate_supply()