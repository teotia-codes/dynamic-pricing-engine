import os
import sys

# Make project root importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.pricing_engine import (
    get_base_fee,
    get_platform_multiplier,
    get_demand_supply_multiplier,
    get_weather_multiplier,
    get_traffic_multiplier,
    get_busy_multiplier,
    get_anomaly_multiplier,
)


def test_get_base_fee_returns_number():
    result = get_base_fee(1)
    assert isinstance(result, (int, float))
    assert result > 0


def test_get_platform_multiplier_returns_number():
    result = get_platform_multiplier(1)
    assert isinstance(result, (int, float))
    assert result > 0


def test_get_demand_supply_multiplier_low_ratio():
    result = get_demand_supply_multiplier(0.5)
    assert isinstance(result, (int, float))
    assert result >= 1.0


def test_get_demand_supply_multiplier_high_ratio():
    result = get_demand_supply_multiplier(10.0)
    assert isinstance(result, (int, float))
    assert result >= 1.0


def test_get_weather_multiplier_known():
    result = get_weather_multiplier("Rain")
    assert isinstance(result, (int, float))
    assert result >= 1.0


def test_get_weather_multiplier_unknown():
    result = get_weather_multiplier("AlienStorm")
    assert result == 1.0


def test_get_traffic_multiplier_low():
    result = get_traffic_multiplier(0.1)
    assert isinstance(result, (int, float))
    assert result >= 1.0


def test_get_traffic_multiplier_high():
    result = get_traffic_multiplier(0.95)
    assert isinstance(result, (int, float))
    assert result >= 1.0


def test_get_busy_multiplier_non_blinkit():
    result = get_busy_multiplier(1, 0.9, 50)
    assert isinstance(result, float)
    assert result >= 1.0


def test_get_busy_multiplier_blinkit():
    # Assumes Blinkit platform id is 3 in many configs, but test only checks output shape
    result = get_busy_multiplier(3, 0.9, 5)
    assert isinstance(result, float)
    assert result >= 1.0


def test_get_anomaly_multiplier_no_history():
    result = get_anomaly_multiplier(100, None)
    assert result == 1.0


def test_get_anomaly_multiplier_zero_history():
    result = get_anomaly_multiplier(100, 0)
    assert result == 1.0


def test_get_anomaly_multiplier_normal_case():
    result = get_anomaly_multiplier(100, 100)
    assert isinstance(result, (int, float))
    assert result >= 1.0


def test_get_anomaly_multiplier_spike_case():
    result = get_anomaly_multiplier(500, 100)
    assert isinstance(result, (int, float))
    assert result >= 1.0