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
    description="Totals for sessions/messages, unique users, peak hours, and growth trend over the period.",
)
async def get_traffic_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
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
    description="Average/median session durations and distribution buckets (minutes).",
)
async def get_session_duration_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
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
    summary="System health (demo)",
    description="API response times, error rate, and uptime. Demo values in dev.",
)
async def get_system_health(
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time system health metrics.
    
    Monitors:
    - API response times (P50, P95, P99)
    - Error rates and uptime
    - System availability status
    """
    # Placeholder - would integrate with monitoring systems
    return SystemHealth(
        api_response_time_p50=150.5,
        api_response_time_p95=450.2,
        api_response_time_p99=850.7,
        error_rate=2.1,
        uptime_percentage=99.8,
        system_availability="healthy"
    )

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
    description="Current load, utilization and scaling recommendations.",
)
async def get_capacity_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get system capacity and scaling metrics.
    
    Returns:
    - Current load levels
    - Capacity utilization
    - Scaling recommendations
    """
    return CapacityMetrics(
        current_load="moderate",
        capacity_utilization=65.3,
        concurrent_sessions=45,
        scaling_status="adequate",
        recommendations=[],
    )

@router.get(
    "/hourly-traffic",
    response_model=List[HourlyTrafficPoint],
    summary="Hourly traffic (demo)",
    description="24 UTC buckets with sessions and messages; demo shape in dev.",
)
async def get_hourly_traffic(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated hourly traffic across the analysis window.
    Returns 24 buckets with total sessions and messages per hour (UTC).
    """
    # Placeholder aggregation: derive from total trend shape if needed; here we return a stable demo shape
    series = [
        HourlyTrafficPoint(hour=f"{h:02d}", sessions=max(20, int(200 * (0.6 if 8<=h<=18 else 0.3))), messages=max(60, int(600 * (0.6 if 8<=h<=18 else 0.3))))
        for h in range(24)
    ]
    return series

@router.get(
    "/response-times",
    response_model=List[ResponseTimesPoint],
    summary="Response time trends (demo)",
    description="Daily P50/P95/P99 response time points; demo series in dev.",
)
async def get_response_time_trends(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get response time percentile trends (P50/P95/P99) per day.
    """
    from datetime import date, timedelta
    today = date.today()
    points: List[ResponseTimesPoint] = []
    base = [180, 450, 680]
    for i in range(days):
        d = today - timedelta(days=days-1-i)
        jitter = (i % 3) * 5
        points.append(ResponseTimesPoint(day=str(d), p50=base[0]-jitter, p95=base[1]-jitter*2, p99=base[2]-jitter*3))
    return points

@router.get(
    "/errors",
    response_model=ErrorAnalysis,
    summary="Error analysis (demo)",
    description="Error rates, total errors, and breakdown by type.",
)
async def get_error_analysis(
    hours: int = Query(24, description="Hours of error data to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get error analysis and monitoring data.
    
    Returns:
    - Error rates by type
    - Failed request patterns
    - Recovery metrics
    """
    return ErrorAnalysis(
        error_rate=2.1,
        total_errors=15,
        error_types={
            "4xx_errors": 8,
            "5xx_errors": 7,
            "timeout_errors": 0,
        },
        analysis_period=f"{hours} hours",
    )

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
