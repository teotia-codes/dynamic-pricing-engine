import random
from datetime import datetime
from core.db import get_connection, release_connection
from core.config import PLATFORMS

# Region demand tendency
REGION_DEMAND_FACTOR = {
    1: 1.15,  # Connaught Place
    2: 1.00,  # Sector 18
    3: 1.20,  # Cyber Hub
    4: 1.10,  # HSR Layout
    5: 1.08,  # Andheri West
}


def is_weekend() -> bool:
    return datetime.now().weekday() >= 5  # Sat/Sun


def get_food_hour_multiplier(hour: int) -> float:
    if 8 <= hour <= 10:
        return 1.35  # breakfast
    elif 12 <= hour <= 15:
        return 1.65  # lunch
    elif 19 <= hour <= 22:
        return 1.85  # dinner peak
    elif 23 <= hour or hour <= 1:
        return 0.75  # late night
    return 1.0


def get_blinkit_hour_multiplier(hour: int) -> float:
    if 9 <= hour <= 11:
        return 1.25  # morning essentials
    elif 18 <= hour <= 21:
        return 1.45  # evening restock
    elif 22 <= hour or hour <= 1:
        return 1.55  # late-night convenience
    elif 13 <= hour <= 15:
        return 1.10
    return 0.95


def get_platform_hour_multiplier(platform_id: int, hour: int) -> float:
    if platform_id == PLATFORMS["blinkit"]:
        return get_blinkit_hour_multiplier(hour)
    return get_food_hour_multiplier(hour)


def get_weekend_multiplier(platform_id: int) -> float:
    if not is_weekend():
        return 1.0

    if platform_id == PLATFORMS["blinkit"]:
        return 1.08
    return 1.18


def get_region_special_boost(platform_id: int, region_id: int, hour: int) -> float:
    if region_id == 1 and 12 <= hour <= 15:  # Connaught Place lunch
        return 1.18
    if region_id == 3 and 19 <= hour <= 22:  # Cyber Hub evening
        return 1.15
    if region_id == 4 and 19 <= hour <= 22:  # HSR evening
        return 1.12
    if region_id == 5 and (22 <= hour or hour <= 1):  # Andheri late-night
        return 1.18 if platform_id == PLATFORMS["blinkit"] else 1.08
    return 1.0


def generate_orders():
    conn = get_connection()

    try:
        cur = conn.cursor()

        hour = datetime.now().hour
        platform_ids = list(PLATFORMS.values())
        region_ids = [1, 2, 3, 4, 5]

        for platform_id in platform_ids:
            for region_id in region_ids:
                region_factor = REGION_DEMAND_FACTOR.get(region_id, 1.0)
                hour_factor = get_platform_hour_multiplier(platform_id, hour)
                weekend_factor = get_weekend_multiplier(platform_id)
                special_boost = get_region_special_boost(platform_id, region_id, hour)

                combined_factor = region_factor * hour_factor * weekend_factor * special_boost

                if platform_id == PLATFORMS["blinkit"]:
                    base_orders = random.randint(8, 18)
                    order_count = max(3, round(base_orders * combined_factor))

                    avg_cart_value = round(
                        random.uniform(250, 650) * random.uniform(0.95, 1.10), 2
                    )
                    avg_distance_km = round(
                        random.uniform(1.0, 4.0) * random.uniform(0.9, 1.1), 2
                    )
                    avg_prep_time_min = round(
                        random.uniform(3.0, 9.0) * random.uniform(0.95, 1.15), 2
                    )
                else:
                    base_orders = random.randint(6, 16)
                    order_count = max(2, round(base_orders * combined_factor))

                    meal_cart_boost = 1.15 if (12 <= hour <= 15 or 19 <= hour <= 22) else 1.0

                    avg_cart_value = round(
                        random.uniform(220, 900) * meal_cart_boost * random.uniform(0.95, 1.10), 2
                    )
                    avg_distance_km = round(
                        random.uniform(2.0, 8.0) * random.uniform(0.9, 1.15), 2
                    )
                    avg_prep_time_min = round(
                        random.uniform(12.0, 30.0) * random.uniform(0.95, 1.15), 2
                    )

                cur.execute(
                    """
                    INSERT INTO orders (
                        platform_id,
                        region_id,
                        order_count,
                        avg_cart_value,
                        avg_distance_km,
                        avg_prep_time_min
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        platform_id,
                        region_id,
                        order_count,
                        avg_cart_value,
                        avg_distance_km,
                        avg_prep_time_min,
                    ),
                )

        conn.commit()
        cur.close()

        print("✅ Realistic orders inserted successfully")

    except Exception as e:
        print(f"❌ Error in generate_orders: {e}")

    finally:
        release_connection(conn)


if __name__ == "__main__":
    generate_orders()