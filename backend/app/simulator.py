import random
import time
from datetime import datetime
from app.logger import logger

REGION_PROFILES = {
    "Andheri West": {"city": "Mumbai", "base_demand": 85, "base_supply": 40, "peak_boost": 1.25},
    "Connaught Place": {"city": "Delhi", "base_demand": 75, "base_supply": 42, "peak_boost": 1.20},
    "Sector 18": {"city": "Noida", "base_demand": 65, "base_supply": 38, "peak_boost": 1.15},
    "Cyber Hub": {"city": "Gurgaon", "base_demand": 80, "base_supply": 36, "peak_boost": 1.22},
    "HSR Layout": {"city": "Bengaluru", "base_demand": 78, "base_supply": 35, "peak_boost": 1.18},
}

PLATFORMS = ["Swiggy", "Zomato", "Blinkit"]


def get_peak_factor(hour: int):
    if 8 <= hour <= 11:
        return 1.20
    if 13 <= hour <= 15:
        return 1.10
    if 18 <= hour <= 22:
        return 1.30
    return 0.95


def get_weekend_factor(weekday: int):
    # Saturday=5, Sunday=6
    return 1.15 if weekday in [5, 6] else 1.0


def generate_region_metrics(region_name: str):
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()

    profile = REGION_PROFILES[region_name]

    peak_factor = get_peak_factor(hour)
    weekend_factor = get_weekend_factor(weekday)

    demand = int(
        profile["base_demand"]
        * peak_factor
        * weekend_factor
        * random.uniform(0.85, 1.20)
    )

    supply = int(
        profile["base_supply"]
        * random.uniform(0.85, 1.10)
    )

    traffic = round(random.uniform(1.00, 1.25 if 17 <= hour <= 21 else 1.12), 2)
    weather = round(random.uniform(1.00, 1.10), 2)
    busy_store = round(random.uniform(1.00, 1.18), 2)
    anomaly = round(random.choice([1.00, 1.00, 1.00, 1.05, 1.10]), 2)

    return {
        "orders": max(10, demand),
        "drivers_online": max(5, supply),
        "traffic_multiplier": traffic,
        "weather_multiplier": weather,
        "busy_multiplier": busy_store,
        "anomaly_multiplier": anomaly,
    }


def run_simulator():
    logger.info("Starting realistic simulator loop...")

    while True:
        for platform in PLATFORMS:
            for region in REGION_PROFILES.keys():
                metrics = generate_region_metrics(region)

                # TODO: call your existing calculate_prices()/DB insert pipeline here
                logger.info(
                    f"{platform} | {region} | orders={metrics['orders']} | drivers={metrics['drivers_online']}"
                )

        time.sleep(10)


if __name__ == "__main__":
    run_simulator()