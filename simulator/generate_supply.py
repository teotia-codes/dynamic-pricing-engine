import random
from datetime import datetime
from core.db import get_connection, release_connection
from core.config import PLATFORMS

REGION_SUPPLY_FACTOR = {
    1: 1.10,  # Connaught Place
    2: 1.00,  # Sector 18
    3: 1.12,  # Cyber Hub
    4: 1.08,  # HSR Layout
    5: 1.05,  # Andheri West
}


def get_supply_hour_factor(platform_id: int, hour: int) -> float:
    if platform_id == PLATFORMS["blinkit"]:
        if 18 <= hour <= 21:
            return 1.20
        elif 22 <= hour or hour <= 1:
            return 0.95
        elif 9 <= hour <= 11:
            return 1.10
        return 1.0
    else:
        if 12 <= hour <= 15:
            return 1.15
        elif 19 <= hour <= 22:
            return 1.18
        elif 8 <= hour <= 10:
            return 1.08
        return 1.0


def generate_supply():
    conn = get_connection()

    try:
        cur = conn.cursor()

        hour = datetime.now().hour
        platform_ids = list(PLATFORMS.values())
        region_ids = [1, 2, 3, 4, 5]

        for platform_id in platform_ids:
            for region_id in region_ids:
                region_factor = REGION_SUPPLY_FACTOR.get(region_id, 1.0)
                hour_factor = get_supply_hour_factor(platform_id, hour)
                combined_factor = region_factor * hour_factor

                if platform_id == PLATFORMS["blinkit"]:
                    base_supply = random.randint(6, 14)
                else:
                    base_supply = random.randint(8, 20)

                lag_factor = random.uniform(0.85, 1.08)
                available_partners = max(3, round(base_supply * combined_factor * lag_factor))

                cur.execute(
                    """
                    INSERT INTO delivery_partners (
                        platform_id,
                        region_id,
                        available_partners
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (platform_id, region_id, available_partners),
                )

        conn.commit()
        cur.close()

        print("✅ Realistic delivery partner supply inserted successfully")

    except Exception as e:
        print(f"❌ Error in generate_supply: {e}")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    generate_supply()