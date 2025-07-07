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
