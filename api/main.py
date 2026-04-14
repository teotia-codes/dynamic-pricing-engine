from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware

from api.auth import verify_api_key
from api.repository import (
    fetch_latest_prices,
    fetch_latest_prices_by_platform,
    fetch_price_history,
    fetch_top_surges,
    fetch_dashboard_summary,
    fetch_dashboard_heatmap,
    fetch_dashboard_top_surges,
    check_database_health,
)
from backend.app.logger import logger
from backend.app.models import (
    RootResponse,
    HealthResponse,
    PricingOutput,
    PlatformPricingOutput,
    PriceHistoryItem,
    SurgeItem,
    SummaryResponse,
    HeatmapItem,
    DashboardTopSurgeItem,
    LatestPricesResponse,
    PlatformLatestPricesResponse,
    HistoryResponse,
    TopSurgesResponse,
    SummaryEnvelope,
    HeatmapResponse,
    DashboardTopSurgesResponse,
)

app = FastAPI(
    title="Dynamic Pricing Engine API",
    description="Real-time dynamic delivery pricing for Swiggy / Zomato / Blinkit style platforms",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=RootResponse)
def root():
    return RootResponse(
        message="Dynamic Pricing Engine API is running 🚀",
        project="Swiggy / Zomato / Blinkit Real-Time Pricing Engine",
    )


@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        db_time = check_database_health()

        return HealthResponse(
            status="healthy",
            database="connected",
            db_time=str(db_time),
        )

    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.get("/latest-prices", response_model=LatestPricesResponse)
def get_latest_prices_endpoint(_: str = Depends(verify_api_key)):
    """
    Get latest price snapshot for all platform-region combinations
    """
    try:
        rows = fetch_latest_prices()

        result = [
            PricingOutput(
                platform=row[0],
                region=row[1],
                city=row[2],
                base_fee=float(row[3]),
                demand_supply_ratio=float(row[4]),
                peak_multiplier=float(row[5]),
                weather_multiplier=float(row[6]),
                traffic_multiplier=float(row[7]),
                busy_multiplier=float(row[8]),
                anomaly_multiplier=float(row[9]),
                platform_multiplier=float(row[10]),
                final_multiplier=float(row[11]),
                final_fee=float(row[12]),
                calculated_at=str(row[13]),
            )
            for row in rows
        ]

        return LatestPricesResponse(
            status="success",
            count=len(result),
            data=result,
        )

    except Exception as e:
        logger.exception("Failed to fetch latest prices")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/latest-prices/{platform_name}", response_model=PlatformLatestPricesResponse)
def get_latest_prices_by_platform_endpoint(
    platform_name: str,
    _: str = Depends(verify_api_key),
):
    """
    Get latest prices for a single platform: Swiggy / Zomato / Blinkit
    """
    try:
        rows = fetch_latest_prices_by_platform(platform_name)

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No pricing data found for platform '{platform_name}'"
            )

        result = [
            PlatformPricingOutput(
                platform=row[0],
                region=row[1],
                city=row[2],
                base_fee=float(row[3]),
                demand_supply_ratio=float(row[4]),
                final_multiplier=float(row[5]),
                final_fee=float(row[6]),
                calculated_at=str(row[7]),
            )
            for row in rows
        ]

        return PlatformLatestPricesResponse(
            status="success",
            platform=platform_name,
            count=len(result),
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch latest prices by platform")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{platform_name}/{region_name}", response_model=HistoryResponse)
def get_price_history_endpoint(
    platform_name: str,
    region_name: str,
    limit: int = Query(20, ge=1, le=200),
    _: str = Depends(verify_api_key),
):
    """
    Get recent pricing history for a platform + region
    Example:
    /history/Swiggy/Connaught%20Place
    """
    try:
        rows = fetch_price_history(platform_name, region_name, limit)

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No history found for platform '{platform_name}' in region '{region_name}'"
            )

        result = [
            PriceHistoryItem(
                platform=row[0],
                region=row[1],
                city=row[2],
                base_fee=float(row[3]),
                demand_supply_ratio=float(row[4]),
                peak_multiplier=float(row[5]),
                weather_multiplier=float(row[6]),
                traffic_multiplier=float(row[7]),
                busy_multiplier=float(row[8]),
                anomaly_multiplier=float(row[9]),
                platform_multiplier=float(row[10]),
                final_multiplier=float(row[11]),
                final_fee=float(row[12]),
                calculated_at=str(row[13]),
            )
            for row in rows
        ]

        return HistoryResponse(
            status="success",
            platform=platform_name,
            region=region_name,
            count=len(result),
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch price history")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/top-surges", response_model=TopSurgesResponse)
def get_top_surges_endpoint(
    limit: int = Query(10, ge=1, le=50),
    _: str = Depends(verify_api_key),
):
    """
    Get highest current surge fees across all platform-region combinations
    """
    try:
        rows = fetch_top_surges(limit)

        result = [
            SurgeItem(
                platform=row[0],
                region=row[1],
                city=row[2],
                demand_supply_ratio=float(row[3]),
                final_multiplier=float(row[4]),
                final_fee=float(row[5]),
                calculated_at=str(row[6]),
            )
            for row in rows
        ]

        return TopSurgesResponse(
            status="success",
            count=len(result),
            data=result,
        )

    except Exception as e:
        logger.exception("Failed to fetch top surges")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/summary", response_model=SummaryEnvelope)
def dashboard_summary(_: str = Depends(verify_api_key)):
    try:
        row = fetch_dashboard_summary()

        return SummaryEnvelope(
            status="success",
            data=SummaryResponse(
                total_rows=int(row[0]),
                avg_fee=float(row[1]),
                max_multiplier=float(row[2]),
                avg_ds_ratio=float(row[3]),
                est_active_orders=int(row[4]),
                platform_count=int(row[5]),
                region_count=int(row[6]),
            ),
        )

    except Exception as e:
        logger.exception("Failed to fetch dashboard summary")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/heatmap", response_model=HeatmapResponse)
def dashboard_heatmap(_: str = Depends(verify_api_key)):
    try:
        rows = fetch_dashboard_heatmap()

        data = [
            HeatmapItem(
                hour=f"{r[0]}h",
                value=int(r[1]),
            )
            for r in rows
        ]

        return HeatmapResponse(
            status="success",
            count=len(data),
            data=data,
        )

    except Exception as e:
        logger.exception("Failed to fetch dashboard heatmap")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/top-surges", response_model=DashboardTopSurgesResponse)
def dashboard_top_surges(
    limit: int = Query(5, ge=1, le=20),
    _: str = Depends(verify_api_key),
):
    try:
        rows = fetch_dashboard_top_surges(limit)

        data = [
            DashboardTopSurgeItem(
                platform=row[0],
                region=row[1],
                city=row[2],
                final_fee=float(row[3]),
                final_multiplier=float(row[4]),
                demand_supply_ratio=float(row[5]),
                calculated_at=row[6].isoformat() if row[6] else None,
            )
            for row in rows
        ]

        return DashboardTopSurgesResponse(
            status="success",
            count=len(data),
            data=data,
        )

    except Exception as e:
        logger.exception("Failed to fetch dashboard top surges")
        raise HTTPException(status_code=500, detail=str(e))