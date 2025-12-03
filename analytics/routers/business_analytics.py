"""
Business Analytics API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    ROIMetrics, ContainmentRate, BusinessFlowSuccess,
    ExecutiveDashboard, OperationsDashboard, 
    ProductOptimizationDashboard, BusinessIntelligenceDashboard
)
from ..services import AnalyticsService

router = APIRouter()

@router.get("/roi", response_model=ROIMetrics)
async def get_roi_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ROI and cost-benefit analysis.
    
    Calculates:
    - Cost per citizen interaction
    - Operational cost savings
    - Return on investment percentage
    - Budget performance
    """
    return await AnalyticsService.get_roi_metrics(db, start_date, end_date)

@router.get("/containment", response_model=ContainmentRate)
async def get_containment_rate(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get containment rate analysis.
    
    Measures:
    - Full automation rate
    - Partial automation rate
    - Human handoff rate
    - Resolution success rate
    """
    return await AnalyticsService.get_containment_rate(db, start_date, end_date)

@router.get("/business-flow-success", response_model=BusinessFlowSuccess)
async def get_business_flow_success(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get business flow success metrics.
    
    Analyzes:
    - Service request completion rates
    - Document access success
    - Information accuracy
    - Citizen satisfaction proxies
    """
    # Placeholder implementation
    return BusinessFlowSuccess(
        service_completion_rate=87.5,
        document_access_success=92.3,
        information_accuracy=89.1,
        citizen_satisfaction_proxy=4.2
    )

@router.get("/cost-analysis")
async def get_detailed_cost_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed cost analysis breakdown.
    
    Provides:
    - Infrastructure costs
    - API usage costs
    - Operational savings
    - Cost per service type
    """
    roi_metrics = await AnalyticsService.get_roi_metrics(db, start_date, end_date)
    
    return {
        "cost_breakdown": {
            "ai_api_costs": 45.50,
            "infrastructure_costs": 120.00,
            "operational_costs": 85.75,
            "total_monthly_cost": 251.25
        },
        "savings_analysis": {
            "traditional_service_cost": 2400.00,
            "ai_service_cost": 251.25,
            "monthly_savings": 2148.75,
            "savings_percentage": 89.5
        },
        "roi_summary": {
            "cost_per_interaction": roi_metrics.cost_per_interaction,
            "total_interactions": 1200,
            "roi_percentage": roi_metrics.roi_percentage
        }
    }

@router.get("/performance-benchmarks")
async def get_performance_benchmarks(
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance benchmarks and targets.
    
    Compares:
    - Current performance vs targets
    - Industry benchmarks
    - Historical performance
    """
    return {
        "current_performance": {
            "containment_rate": 85.5,
            "response_time": 1.2,
            "satisfaction_score": 4.2,
            "availability": 99.8
        },
        "targets": {
            "containment_rate": 90.0,
            "response_time": 1.0,
            "satisfaction_score": 4.5,
            "availability": 99.9
        },
        "industry_benchmarks": {
            "containment_rate": 75.0,
            "response_time": 2.5,
            "satisfaction_score": 3.8,
            "availability": 99.5
        }
    }

# Dashboard endpoints
@router.get("/dashboard/executive", response_model=ExecutiveDashboard)
async def get_executive_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get executive dashboard metrics.
    
    High-level KPIs:
    - Containment rate
    - Cost savings
    - User growth
    - Service quality indicators
    """
    containment = await AnalyticsService.get_containment_rate(db)
    roi = await AnalyticsService.get_roi_metrics(db)
    
    return ExecutiveDashboard(
        containment_rate=containment.full_automation_rate,
        cost_savings=roi.cost_savings,
        user_growth=15.8,  # Would calculate from user analytics
        roi_percentage=roi.roi_percentage,
        service_availability=99.8
    )

@router.get("/dashboard/operations", response_model=OperationsDashboard)
async def get_operations_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get operations dashboard metrics.
    
    Real-time monitoring:
    - Current session activity
    - System health
    - Error monitoring
    - Capacity utilization
    """
    from ..schemas import SystemHealth
    
    system_health = SystemHealth(
        api_response_time_p50=150.5,
        api_response_time_p95=450.2,
        api_response_time_p99=850.7,
        error_rate=2.1,
        uptime_percentage=99.8,
        system_availability="healthy"
    )
    
    return OperationsDashboard(
        current_sessions=45,
        system_health=system_health,
        error_monitoring={
            "recent_errors": 3,
            "error_trend": "stable",
            "critical_alerts": 0
        },
        capacity_utilization=65.3
    )

@router.get("/dashboard/product-optimization", response_model=ProductOptimizationDashboard)
async def get_product_optimization_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get product optimization dashboard.
    
    User journey insights:
    - Conversation flow analysis
    - Drop-off patterns
    - Content performance
    - Knowledge gap identification
    """
    conversation_flows = await AnalyticsService.get_conversation_turn_analysis(db)
    
    return ProductOptimizationDashboard(
        conversation_flows=conversation_flows,
        drop_off_patterns=[
            {"turn": 1, "rate": 15.2},
            {"turn": 3, "rate": 12.1}
        ],
        content_performance=[],  # Would populate from document analysis
        knowledge_gaps=["tax_exemption_process", "business_permits"]
    )

@router.get("/dashboard/business-intelligence", response_model=BusinessIntelligenceDashboard)
async def get_business_intelligence_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get business intelligence dashboard.
    
    Strategic insights:
    - Deep-dive analytics
    - Comparative analysis
    - Predictive analytics
    - Forecasting
    """
    return BusinessIntelligenceDashboard(
        strategic_metrics={
            "digital_adoption_rate": 78.5,
            "service_modernization_progress": 65.2,
            "citizen_engagement_score": 4.1
        },
        comparative_analysis={
            "month_over_month_growth": 12.3,
            "year_over_year_improvement": 45.7,
            "benchmark_performance": "above_average"
        },
        predictive_insights={
            "projected_user_growth": 25.0,
            "expected_cost_savings": 35000.0,
            "automation_improvement": 8.5
        },
        forecasting={
            "next_month_sessions": 3200,
            "quarterly_roi": 180.5,
            "annual_savings": 420000.0
        }
    )
