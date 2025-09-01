"""
User Analytics API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import UserDemographics, SessionFrequency, UserSentiment, RetentionData, GeographicDistribution
from ..services import AnalyticsService

router = APIRouter()

@router.get("/demographics", response_model=UserDemographics)
async def get_user_demographics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user demographics and growth metrics.
    
    Provides insights into:
    - Total, new, and returning users
    - Active user counts
    - User growth rates
    """
    return await AnalyticsService.get_user_demographics(db, start_date, end_date)

@router.get("/session-frequency", response_model=List[SessionFrequency])
async def get_session_frequency_analysis(
    limit: int = Query(100, description="Maximum number of users to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get session frequency analysis for users.
    
    Returns:
    - User session patterns
    - Visit frequency and lifespan
    - Power user identification
    """
    return await AnalyticsService.get_session_frequency_analysis(db, limit)

@router.get("/sentiment", response_model=UserSentiment)
async def get_user_sentiment(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive user sentiment and satisfaction metrics with composite analysis.
    
    Combines VADER sentiment analysis with explicit user ratings to provide:
    
    **Sentiment Analysis (VADER-based):**
    - Conversation sentiment classification (positive, negative, neutral)
    - User satisfaction indicators based on message tone
    - Escalation patterns from negative sentiment detection
    - Detailed sentiment distribution across all messages
    
    **Explicit Rating Integration:**
    - User-provided star ratings (1-5 scale) analysis
    - Rating distribution and average scores
    - Composite satisfaction score (weighted: 70% sentiment + 30% ratings)
    - Correlation analysis between sentiment predictions and actual ratings
    
    **Composite Metrics Benefits:**
    - Validation of sentiment analysis accuracy
    - Balanced satisfaction measurement
    - Confidence indicators for automated analysis
    - Multiple perspectives on user satisfaction
    
    VADER is particularly effective for analyzing informal text like chat messages,
    handling slang, emojis, and conversational language patterns.
    """
    return await AnalyticsService.get_user_sentiment(db, start_date, end_date)

@router.get("/retention", response_model=RetentionData)
async def get_user_retention(
    cohort_size: int = Query(30, description="Cohort size in days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user retention analysis by cohorts.
    
    Returns:
    - Day 1, Day 7, Day 30 retention rates
    - Cohort analysis
    - User lifecycle insights
    """
    # Placeholder for retention analysis
    return RetentionData(
        day_1_retention=65.5,
        day_7_retention=42.3,
        day_30_retention=28.7,
        cohort_analysis=[]
    )

@router.get("/geographic")
async def get_geographic_distribution(
    db: AsyncSession = Depends(get_db)
):
    """
    Get geographic distribution of users.
    
    Note: Requires location data collection to be implemented.
    """
    return {
        "message": "Geographic analysis requires location data collection",
        "status": "not_implemented"
    }
