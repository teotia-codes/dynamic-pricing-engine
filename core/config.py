PLATFORMS = {
    "SWIGGY": 1,
    "ZOMATO": 2,
    "BLINKIT": 3
}

PLATFORM_NAMES = {
    1: "Swiggy",
    2: "Zomato",
    3: "Blinkit"
}

PRICING_CONFIG = {
    "base_fee": {
        1: 25.0,   # Swiggy
        2: 30.0,   # Zomato
        3: 20.0    # Blinkit
    },

    "platform_multiplier": {
        1: 1.00,
        2: 1.05,
        3: 0.98
    },

    "peak_hours": {
        1: [  # Swiggy
            {"start": 12, "end": 14, "multiplier": 1.15},
            {"start": 19, "end": 22, "multiplier": 1.20}
        ],
        2: [  # Zomato
            {"start": 12, "end": 14, "multiplier": 1.15},
            {"start": 19, "end": 22, "multiplier": 1.20}
        ],
        3: [  # Blinkit
            {"start": 8, "end": 10, "multiplier": 1.10},
            {"start": 18, "end": 22, "multiplier": 1.18}
        ]
    },

    "demand_supply_thresholds": [
        {"max_ratio": 1.0, "multiplier": 1.00},
        {"max_ratio": 1.5, "multiplier": 1.10},
        {"max_ratio": 2.0, "multiplier": 1.25},
        {"max_ratio": 3.0, "multiplier": 1.50},
        {"max_ratio": float("inf"), "multiplier": 1.80}
    ],

    "weather_multiplier": {
        "Clear": 1.00,
        "Cloudy": 1.03,
        "Rain": 1.10,
        "Heavy Rain": 1.25,
        "Storm": 1.40,
        "Unknown": 1.00
    },

    "traffic_thresholds": [
        {"min_score": 0.85, "multiplier": 1.30},
        {"min_score": 0.70, "multiplier": 1.15},
        {"min_score": 0.50, "multiplier": 1.05},
        {"min_score": 0.00, "multiplier": 1.00}
    ],

    "busy_thresholds": [
        {"min_score": 0.80, "increment": 0.20},
        {"min_score": 0.60, "increment": 0.10}
    ],

    "blinkit_inventory_thresholds": [
        {"max_inventory": 0.30, "increment": 0.20},
        {"max_inventory": 0.50, "increment": 0.10}
    ],

    "anomaly_thresholds": [
        {"ratio": 1.8, "multiplier": 1.25},
        {"ratio": 1.4, "multiplier": 1.10}
    ]
}