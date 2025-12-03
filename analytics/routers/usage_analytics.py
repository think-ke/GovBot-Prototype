"""
Usage Analytics API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import TrafficMetrics, SessionDuration, SystemHealth, PeakHoursResponse, ErrorAnalysis, HourlyTrafficPoint, ResponseTimesPoint, CapacityMetrics, LatencyStats, ToolUsageResponse, CollectionHealthItem
from ..services import AnalyticsService

router = APIRouter()

@router.get(
    "/traffic",
    response_model=TrafficMetrics,
    summary="Traffic and volume",
    description=(
        "Totals for sessions/messages, unique users, peak hours, and growth trend over the period.\n\n"
        "Date parameters accept ISO 8601 UTC strings, e.g., 2025-09-01T00:00:00Z"
    ),
)
async def get_traffic_metrics(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for analysis (ISO 8601, UTC)",
        example="2025-09-01T00:00:00Z",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for analysis (ISO 8601, UTC)",
        example="2025-09-07T23:59:59Z",
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get traffic and volume metrics.
    
    Provides:
    - Total sessions and messages
    - Unique user counts
    - Peak usage hours
    - Growth trends
    """
    return await AnalyticsService.get_traffic_metrics(db, start_date, end_date)

@router.get(
    "/session-duration",
    response_model=SessionDuration,
    summary="Session duration analysis",
    description=(
        "Average/median session durations and distribution buckets (minutes).\n\n"
        "Date parameters accept ISO 8601 UTC strings, e.g., 2025-09-01T00:00:00Z"
    ),
)
async def get_session_duration_analysis(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for analysis (ISO 8601, UTC)",
        example="2025-09-01T00:00:00Z",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for analysis (ISO 8601, UTC)",
        example="2025-09-07T23:59:59Z",
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get session duration analysis.
    
    Returns:
    - Average and median session duration
    - Duration distribution patterns
    - Session depth analysis
    """
    return await AnalyticsService.get_session_duration_analysis(db, start_date, end_date)

@router.get(
    "/system-health",
    response_model=SystemHealth,
    summary="System health",
    description="API response times (TTFA P50/P95/P99), error rate, and uptime approximation over a recent window.",
)
async def get_system_health(
    hours: int = Query(24, description="Hours of activity to analyze (uptime/error window)"),
    db: AsyncSession = Depends(get_db)
):
    data = await AnalyticsService.get_system_health(db, hours=hours)
    return SystemHealth(**data)

@router.get(
    "/peak-hours",
    response_model=PeakHoursResponse,
    summary="Peak hours",
    description="Ranked busy hours across the period; timezone is UTC.",
)
async def get_peak_hours_analysis(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed peak hours analysis.
    
    Returns:
    - Hourly traffic patterns
    - Day-of-week analysis
    - Seasonal trends
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    traffic_data = await AnalyticsService.get_traffic_metrics(db, start_date, end_date)
    
    return PeakHoursResponse(
        peak_hours=traffic_data.peak_hours,
        analysis_period=f"{days} days",
        timezone="UTC"
    )

@router.get(
    "/capacity",
    response_model=CapacityMetrics,
    summary="System capacity & scaling",
    description="Current load, utilization and scaling recommendations (p95 concurrency vs configured capacity).",
)
async def get_capacity_metrics(
    hours: int = Query(24, description="Hours of activity to analyze"),
    max_capacity: int = Query(100, description="Configured max concurrent sessions capacity for utilization calc"),
    db: AsyncSession = Depends(get_db)
):
    data = await AnalyticsService.get_capacity_metrics(db, hours=hours, max_capacity=max_capacity)
    return CapacityMetrics(**data)

@router.get(
    "/hourly-traffic",
    response_model=List[HourlyTrafficPoint],
    summary="Hourly traffic",
    description="24 UTC buckets with sessions and messages aggregated over the last N days.",
)
async def get_hourly_traffic(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    rows = await AnalyticsService.get_hourly_traffic_series(db, days=days)
    return [HourlyTrafficPoint(**r) for r in rows]

@router.get(
    "/response-times",
    response_model=List[ResponseTimesPoint],
    summary="Response time trends",
    description="Daily P50/P95/P99 (TTFA) for the last N days computed from chat events.",
)
async def get_response_time_trends(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    rows = await AnalyticsService.get_response_time_trends(db, days=days)
    return [ResponseTimesPoint(**r) for r in rows]

@router.get(
    "/errors",
    response_model=ErrorAnalysis,
    summary="Error analysis",
    description="Error rate, total errors, and breakdown by type computed from chat events.",
)
async def get_error_analysis(
    hours: int = Query(24, description="Hours of error data to analyze"),
    db: AsyncSession = Depends(get_db)
):
    data = await AnalyticsService.get_error_analysis(db, hours=hours)
    return ErrorAnalysis(**data)

@router.get(
    "/latency",
    response_model=LatencyStats,
    summary="Latency percentiles",
    description="Percentiles for time-to-first-byte (TTFB) and time-to-full-answer (TTFA) computed from chat events.",
    responses={
        200: {
            "description": "Latency stats",
            "content": {
                "application/json": {
                    "example": {
                        "p50_ttfb_ms": 180.0,
                        "p95_ttfb_ms": 520.0,
                        "p99_ttfb_ms": 950.0,
                        "p50_ttfa_ms": 650.0,
                        "p95_ttfa_ms": 1800.0,
                        "p99_ttfa_ms": 3200.0,
                        "samples": 2750
                    }
                }
            },
        }
    },
)
async def get_latency(
    db: AsyncSession = Depends(get_db)
):
    stats = await AnalyticsService.get_latency_stats(db)
    return LatencyStats(**stats)

@router.get(
    "/tool-usage",
    response_model=ToolUsageResponse,
    summary="RAG tool usage",
    description="Aggregates tool_search_documents events with started/completed/failed counts and average retrieved docs (overall and by collection).",
)
async def get_tool_usage(
    db: AsyncSession = Depends(get_db)
):
    data = await AnalyticsService.get_tool_usage(db)
    return ToolUsageResponse(**data)

@router.get(
    "/collections-health",
    response_model=List[CollectionHealthItem],
    summary="Collections health",
    description="Webpages/documents counts and indexing freshness per collection.",
)
async def get_collections_health(
    db: AsyncSession = Depends(get_db)
):
    items = await AnalyticsService.get_collections_health(db)
    return [CollectionHealthItem(**i) for i in items]
