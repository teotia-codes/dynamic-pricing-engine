import random
from core.db import get_connection, release_connection
from core.config import PLATFORMS

def generate_supply():
    conn = get_connection()

    try:
        cur = conn.cursor()

        platform_ids = list(PLATFORMS.values())
        region_ids = [1, 2, 3, 4, 5]

        for platform_id in platform_ids:
            for region_id in region_ids:
                if platform_id == 3:  # Blinkit
                    available_partners = random.randint(5, 18)
                else:  # Swiggy / Zomato
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

        print("✅ Delivery partner supply inserted successfully")

    except Exception as e:
        print(f"❌ Error in generate_supply: {e}")

    finally:
        release_connection(conn)

if __name__ == "__main__":
    generate_supply()