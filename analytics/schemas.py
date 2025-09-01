"""
Pydantic schemas for analytics API responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Base response models
class TimeRange(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class MetricResponse(BaseModel):
    value: float
    period: str
    timestamp: datetime

class TrendData(BaseModel):
    date: datetime
    value: float

class DistributionData(BaseModel):
    category: str
    count: int
    percentage: float

# User Analytics Schemas
class UserDemographics(BaseModel):
    total_users: int
    new_users: int
    returning_users: int
    active_users: int
    user_growth_rate: float

class SessionFrequency(BaseModel):
    user_id: str
    total_sessions: int
    first_visit: datetime
    last_visit: datetime
    user_lifespan_days: int

class UserSentiment(BaseModel):
    positive_conversations: int
    negative_conversations: int
    neutral_conversations: int
    satisfaction_score: float
    escalation_rate: float
    average_sentiment_score: float
    total_analyzed_messages: int
    sentiment_distribution: List[DistributionData]
    # Composite metrics integrating explicit ratings with sentiment analysis
    explicit_rating_score: Optional[float] = None  # Average from MessageRating table
    total_explicit_ratings: int = 0
    composite_satisfaction_score: Optional[float] = None  # Weighted combination
    sentiment_vs_rating_correlation: Optional[float] = None  # Correlation analysis
    rating_distribution: Optional[List[DistributionData]] = None  # 1-5 star distribution

# Usage Analytics Schemas
class TrafficMetrics(BaseModel):
    total_sessions: int
    total_messages: int
    unique_users: int
    peak_hours: List[Dict[str, Any]]
    growth_trend: List[TrendData]

class SessionDuration(BaseModel):
    average_duration_minutes: float
    median_duration_minutes: float
    duration_distribution: List[DistributionData]

class SystemHealth(BaseModel):
    api_response_time_p50: float
    api_response_time_p95: float
    api_response_time_p99: float
    error_rate: float
    uptime_percentage: float
    system_availability: str

# Conversation Analytics Schemas
class IntentAnalysis(BaseModel):
    intent: str
    frequency: int
    success_rate: float
    average_turns: float

class ConversationFlow(BaseModel):
    turn_number: int
    completion_rate: float
    abandonment_rate: float
    average_response_time: float

class DocumentRetrieval(BaseModel):
    document_type: str
    access_frequency: int
    success_rate: float
    collection_id: Optional[str]

# Business Analytics Schemas
class ROIMetrics(BaseModel):
    cost_per_interaction: float
    cost_savings: float
    roi_percentage: float
    automation_rate: float

class ContainmentRate(BaseModel):
    full_automation_rate: float
    partial_automation_rate: float
    human_handoff_rate: float
    resolution_success_rate: float

class BusinessFlowSuccess(BaseModel):
    service_completion_rate: float
    document_access_success: float
    information_accuracy: float
    citizen_satisfaction_proxy: float

# Dashboard response schemas
class ExecutiveDashboard(BaseModel):
    containment_rate: float
    cost_savings: float
    user_growth: float
    roi_percentage: float
    service_availability: float

class OperationsDashboard(BaseModel):
    current_sessions: int
    system_health: SystemHealth
    error_monitoring: Dict[str, Any]
    capacity_utilization: float

class ProductOptimizationDashboard(BaseModel):
    conversation_flows: List[ConversationFlow]
    drop_off_patterns: List[Dict[str, Any]]
    content_performance: List[DocumentRetrieval]
    knowledge_gaps: List[str]

class BusinessIntelligenceDashboard(BaseModel):
    strategic_metrics: Dict[str, float]
    comparative_analysis: Dict[str, Any]
    predictive_insights: Dict[str, Any]
    forecasting: Dict[str, Any]

# ===== New/Extended Schemas for Frontend Alignment =====

# User - Retention
class RetentionData(BaseModel):
    day_1_retention: float
    day_7_retention: float
    day_30_retention: float
    cohort_analysis: List[Dict[str, Any]] = []

# User - Geographic / Devices (optional)
class GeographicDistribution(BaseModel):
    location: str
    users: int
    percentage: float

class DeviceDistribution(BaseModel):
    name: str
    value: float  # percentage 0-100

# Usage - Hourly traffic and response times
class HourlyTrafficPoint(BaseModel):
    hour: str  # "00".."23"
    sessions: int
    messages: int

class ResponseTimesPoint(BaseModel):
    day: datetime | str  # ISO date or date string
    p50: float
    p95: float
    p99: float

class PeakHoursResponse(BaseModel):
    peak_hours: List[Dict[str, int]]  # {hour, sessions}
    analysis_period: str
    timezone: str

class ErrorAnalysis(BaseModel):
    error_rate: float
    total_errors: int
    error_types: Dict[str, int]
    analysis_period: str

# Conversation - Drop-offs, Sentiment trends, Knowledge gaps, Summary
class DropOffPoint(BaseModel):
    turn: int
    abandonment_rate: float

class DropOffData(BaseModel):
    drop_off_points: List[DropOffPoint]
    common_triggers: List[str]

class SentimentTrends(BaseModel):
    sentiment_distribution: Dict[str, float]  # {positive, neutral, negative} as percentages
    satisfaction_indicators: List[str]

class KnowledgeGap(BaseModel):
    topic: str
    query_frequency: int
    success_rate: float  # percentage 0-100
    example_queries: List[str]

class KnowledgeGaps(BaseModel):
    knowledge_gaps: List[KnowledgeGap]
    recommendations: Optional[List[str]] = None

class ConversationSummary(BaseModel):
    total_conversations: int
    avg_turns: float
    completion_rate: float
