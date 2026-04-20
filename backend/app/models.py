from pydantic import BaseModel
from typing import List, Optional


# =========================
# Generic / Utility Models
# =========================

class RootResponse(BaseModel):
    message: str
    project: str


class HealthResponse(BaseModel):
    status: str
    database: str
    db_time: str


# =========================
# Core Pricing Models
# =========================

class PricingOutput(BaseModel):
    platform: str
    region: str
    city: str
    base_fee: float
    demand_supply_ratio: float
    peak_multiplier: float
    weather_multiplier: float
    traffic_multiplier: float
    busy_multiplier: float
    anomaly_multiplier: float
    platform_multiplier: float
    final_multiplier: float
    final_fee: float
    calculated_at: str


class PlatformPricingOutput(BaseModel):
    platform: str
    region: str
    city: str
    base_fee: float
    demand_supply_ratio: float
    final_multiplier: float
    final_fee: float
    calculated_at: str


class PriceHistoryItem(BaseModel):
    platform: str
    region: str
    city: str
    base_fee: float
    demand_supply_ratio: float
    peak_multiplier: float
    weather_multiplier: float
    traffic_multiplier: float
    busy_multiplier: float
    anomaly_multiplier: float
    platform_multiplier: float
    final_multiplier: float
    final_fee: float
    calculated_at: str


class SimplePriceHistoryItem(BaseModel):
    final_fee: float
    final_multiplier: float
    calculated_at: str


class SurgeItem(BaseModel):
    platform: str
    region: str
    city: str
    final_fee: float
    final_multiplier: float
    demand_supply_ratio: float
    calculated_at: str


# =========================
# Dashboard Models
# =========================

class SummaryResponse(BaseModel):
    total_rows: int
    avg_fee: float
    max_multiplier: float
    avg_ds_ratio: float
    est_active_orders: int
    platform_count: int
    region_count: int


class HeatmapItem(BaseModel):
    hour: str
    value: int


class DashboardTopSurgeItem(BaseModel):
    platform: str
    region: str
    city: str
    final_fee: float
    final_multiplier: float
    demand_supply_ratio: float
    calculated_at: Optional[str] = None


# =========================
# Envelope / API Response Models
# =========================

class LatestPricesResponse(BaseModel):
    status: str
    count: int
    data: List[PricingOutput]


class PlatformLatestPricesResponse(BaseModel):
    status: str
    platform: str
    count: int
    data: List[PlatformPricingOutput]


class HistoryResponse(BaseModel):
    status: str
    platform: str
    region: str
    count: int
    data: List[PriceHistoryItem]


class TopSurgesResponse(BaseModel):
    status: str
    count: int
    data: List[SurgeItem]


class SummaryEnvelope(BaseModel):
    status: str
    data: SummaryResponse


class HeatmapResponse(BaseModel):
    status: str
    count: int
    data: List[HeatmapItem]


class DashboardTopSurgesResponse(BaseModel):
    status: str
    count: int
    data: List[DashboardTopSurgeItem]

class PredictionItem(BaseModel):
    platform: str
    region: str
    city: str
    current_orders_5min: float
    predicted_orders_next_bucket: float
    effective_orders_5min: float
    risk_level: str
    predicted_at: Optional[str]


class PredictionsResponse(BaseModel):
    status: str
    count: int
    data: List[PredictionItem]