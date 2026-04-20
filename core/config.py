import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# =========================
# Environment / App Config
# =========================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "dynamic_pricing")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

API_KEY = os.getenv("API_KEY", "supersecret123")


# =========================
# Platform Config
# =========================

# Use lowercase keys because pricing_engine.py uses:
# PLATFORMS.get("blinkit", 3)
PLATFORMS = {
    "swiggy": 1,
    "zomato": 2,
    "blinkit": 3,
}

PLATFORM_NAMES = {
    1: "Swiggy",
    2: "Zomato",
    3: "Blinkit",
}


# =========================
# Pricing Engine Config
# =========================

PRICING_CONFIG = {
    "base_fee": {
        1: 25.0,   # Swiggy
        2: 30.0,   # Zomato
        3: 20.0,   # Blinkit
    },

    "platform_multiplier": {
        1: 1.00,
        2: 1.05,
        3: 0.98,
    },

    "peak_hours": {
        1: [  # Swiggy
            {"start": 12, "end": 14, "multiplier": 1.15},
            {"start": 19, "end": 22, "multiplier": 1.20},
        ],
        2: [  # Zomato
            {"start": 12, "end": 14, "multiplier": 1.15},
            {"start": 19, "end": 22, "multiplier": 1.20},
        ],
        3: [  # Blinkit
            {"start": 8, "end": 10, "multiplier": 1.10},
            {"start": 18, "end": 22, "multiplier": 1.18},
        ],
    },

    # Kept for compatibility / future use
    "demand_supply_thresholds": [
        {"max_ratio": 1.0, "multiplier": 1.00},
        {"max_ratio": 1.5, "multiplier": 1.10},
        {"max_ratio": 2.0, "multiplier": 1.25},
        {"max_ratio": 3.0, "multiplier": 1.50},
        {"max_ratio": float("inf"), "multiplier": 1.80},
    ],

    "weather_multiplier": {
        "Clear": 1.00,
        "Cloudy": 1.03,
        "Rain": 1.10,
        "Heavy Rain": 1.15,   # capped realistically in pricing_engine anyway
        "Storm": 1.15,        # capped realistically in pricing_engine anyway
        "Drizzle": 1.05,
        "Mist": 1.03,
        "Fog": 1.04,
        "Haze": 1.02,
        "Thunderstorm": 1.15,
        "Unknown": 1.00,
    },

    # Kept for compatibility / future use
    "traffic_thresholds": [
        {"min_score": 0.85, "multiplier": 1.30},
        {"min_score": 0.70, "multiplier": 1.15},
        {"min_score": 0.50, "multiplier": 1.05},
        {"min_score": 0.00, "multiplier": 1.00},
    ],

    # Kept for compatibility / future use
    "busy_thresholds": [
        {"min_score": 0.80, "increment": 0.20},
        {"min_score": 0.60, "increment": 0.10},
    ],

    # Kept for compatibility / future use
    "blinkit_inventory_thresholds": [
        {"max_inventory": 0.30, "increment": 0.20},
        {"max_inventory": 0.50, "increment": 0.10},
    ],

    # Kept for compatibility / future use
    "anomaly_thresholds": [
        {"ratio": 1.8, "multiplier": 1.25},
        {"ratio": 1.4, "multiplier": 1.10},
    ],
}