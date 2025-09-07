"""
Pydantic schemas for analytics API responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

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
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "total_users": 1200, "new_users": 180, "returning_users": 420,
            "active_users": 560, "user_growth_rate": 12.4
        }],
        "x-tooltip": "Counts may be aggregated across the selected period.",
    })
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
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Composite metrics combine inferred sentiment with explicit ratings when available.",
    })
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
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "total_sessions": 2400, "total_messages": 16800, "unique_users": 1350,
            "peak_hours": [{"hour": 10, "sessions": 180}, {"hour": 11, "sessions": 200}],
            "growth_trend": []
        }],
        "x-tooltip": "peak_hours shows busiest UTC hours over the window.",
    })
    total_sessions: int
    total_messages: int
    unique_users: int
    peak_hours: List[Dict[str, Any]]
    growth_trend: List[TrendData]

class SessionDuration(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Durations are in minutes; distribution buckets vary by range.",
    })
    average_duration_minutes: float
    median_duration_minutes: float
    duration_distribution: List[DistributionData]

class SystemHealth(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "API response times in ms; uptime in % over the last 24h.",
    })
    api_response_time_p50: float
    api_response_time_p95: float
    api_response_time_p99: float
    error_rate: float
    uptime_percentage: float
    system_availability: str

# Conversation Analytics Schemas
class IntentAnalysis(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"intent": "document_request", "frequency": 150, "success_rate": 85.5, "average_turns": 2.3}],
        "x-tooltip": "Intent examples are illustrative in dev until classifiers are enabled.",
    })
    intent: str
    frequency: int
    success_rate: float
    average_turns: float

class ConversationFlow(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Turn-number buckets summarize multi-turn completion/abandonment.",
    })
    turn_number: int
    completion_rate: float
    abandonment_rate: float
    average_response_time: float

class DocumentRetrieval(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "document_type": "policy_documents", "access_frequency": 180,
            "success_rate": 88.7, "collection_id": "policies_2024"
        }],
        "x-tooltip": "collection_id corresponds to the RAG index/collection.",
    })
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
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "day_1_retention": 65.5, "day_7_retention": 42.3, "day_30_retention": 28.7,
            "cohort_analysis": []
        }],
        "x-tooltip": "Retention shown as percentages (0-100).",
    })
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
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Hour is UTC in 24h format; sessions/messages aggregated over the window.",
    })
    hour: str  # "00".."23"
    sessions: int
    messages: int

class ResponseTimesPoint(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Response times in milliseconds; daily percentiles.",
    })
    day: datetime | str  # ISO date or date string
    p50: float
    p95: float
    p99: float

class PeakHoursResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "peak_hours is a ranked list of busy hours across the analysis period.",
    })
    peak_hours: List[Dict[str, int]]  # {hour, sessions}
    analysis_period: str
    timezone: str

class ErrorAnalysis(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "error_rate": 2.1, "total_errors": 15,
            "error_types": {"4xx_errors": 8, "5xx_errors": 7, "timeout_errors": 0},
            "analysis_period": "24 hours"
        }],
    })
    error_rate: float
    total_errors: int
    error_types: Dict[str, int]
    analysis_period: str

# Conversation - Drop-offs, Sentiment trends, Knowledge gaps, Summary
class DropOffPoint(BaseModel):
    turn: int
    abandonment_rate: float

class DropOffData(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Abandonment rates by turn number; demo values in dev.",
    })
    drop_off_points: List[DropOffPoint]
    common_triggers: List[str]

class SentimentTrends(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Percentages across all analyzed messages during the period.",
    })
    sentiment_distribution: Dict[str, float]  # {positive, neutral, negative} as percentages
    satisfaction_indicators: List[str]

class KnowledgeGap(BaseModel):
    topic: str
    query_frequency: int
    success_rate: float  # percentage 0-100
    example_queries: List[str]

class KnowledgeGaps(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "Lower success_rate topics indicate potential content gaps.",
    })
    knowledge_gaps: List[KnowledgeGap]
    recommendations: Optional[List[str]] = None

class ConversationSummary(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "x-tooltip": "completion_rate is an estimate derived from flow buckets.",
    })
    total_conversations: int
    avg_turns: float
    completion_rate: float

# System Capacity metrics (Usage)
class CapacityMetrics(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "current_load": "moderate",
            "capacity_utilization": 65.3,
            "concurrent_sessions": 45,
            "scaling_status": "adequate",
            "recommendations": []
        }]
    })
    current_load: str
    capacity_utilization: float
    concurrent_sessions: int
    scaling_status: str
    recommendations: List[str]

# ===== Additional Schemas for New Metrics (per requirements.md) =====

class LatencyStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "p50_ttfb_ms": 180.0, "p95_ttfb_ms": 520.0, "p99_ttfb_ms": 950.0,
            "p50_ttfa_ms": 650.0, "p95_ttfa_ms": 1800.0, "p99_ttfa_ms": 3200.0,
            "samples": 2750
        }],
        "x-tooltip": "TTFB = first token; TTFA = full answer. Milliseconds.",
    })
    p50_ttfb_ms: float
    p95_ttfb_ms: float
    p99_ttfb_ms: float
    p50_ttfa_ms: float
    p95_ttfa_ms: float
    p99_ttfa_ms: float
    samples: int

class ToolUsageItem(BaseModel):
    collection_id: Optional[str] = None
    started: int
    completed: int
    failed: int
    avg_retrieved: Optional[float] = None

class ToolUsageResponse(BaseModel):
    overall: ToolUsageItem
    by_collection: List[ToolUsageItem]

class CollectionWebpagesHealth(BaseModel):
    pages: int
    ok: int
    redirects: int
    client_err: int
    server_err: int
    indexed: int

class CollectionDocumentsHealth(BaseModel):
    count: int
    indexed: int
    public: int
    total_size: int

class CollectionFreshness(BaseModel):
    last_indexed_at: Optional[datetime] = None

class CollectionHealthItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "collection_id": "odpc",
            "webpages": {"pages": 75, "ok": 69, "redirects": 0, "client_err": 5, "server_err": 0, "indexed": 74},
            "documents": {"count": 1, "indexed": 1, "public": 0, "total_size": 457026},
            "freshness": {"last_indexed_at": "2025-05-22T15:56:26.530Z"}
        }]
    })
    collection_id: Optional[str] = None
    webpages: CollectionWebpagesHealth
    documents: CollectionDocumentsHealth
    freshness: CollectionFreshness

class NoAnswerExample(BaseModel):
    chat_id: Optional[int] = None
    message_id: Optional[str] = None
    snippet: str

class NoAnswerStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "rate": 6.2,
            "examples": [{"chat_id": 3574, "message_id": "abc-123", "snippet": "I'm sorry, but I don't have that information."}],
            "top_triggers": ["missing_policy", "unsupported_service"]
        }]
    })
    rate: float  # percentage 0-100
    examples: List[NoAnswerExample]
    top_triggers: List[str]

class CollectionCitationStats(BaseModel):
    collection_id: Optional[str] = None
    coverage_pct: float
    avg_citations: float

class CitationStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "coverage_pct": 72.4,
            "avg_citations": 2.1,
            "by_collection": [
                {"collection_id": "odpc", "coverage_pct": 80.0, "avg_citations": 2.3}
            ]
        }]
    })
    coverage_pct: float
    avg_citations: float
    by_collection: List[CollectionCitationStats]

class AnswerLengthBucket(BaseModel):
    bucket: str
    count: int
    percentage: float

class AnswerLengthStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "avg_words": 85.3,
            "median_words": 72.0,
            "distribution": [
                {"bucket": "0-20", "count": 15, "percentage": 3.2},
                {"bucket": "21-50", "count": 120, "percentage": 25.0}
            ]
        }]
    })
    avg_words: float
    median_words: float
    distribution: List[AnswerLengthBucket]

class UserTopItem(BaseModel):
    user_id: str
    sessions: int
    messages: int

class UserMetrics(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "sessions": 12,
            "messages_user": 48,
            "messages_assistant": 41,
            "avg_turns": 7.4,
            "avg_ttfb_ms": 210.0,
            "avg_ttfa_ms": 1550.0,
            "no_answer_rate": 4.8,
            "rag_coverage_pct": 70.2,
            "top_collections": ["odpc", "kfcb"],
            "last_active": "2025-08-22T08:36:58.387Z"
        }]
    })
    sessions: int
    messages_user: int
    messages_assistant: int
    avg_turns: float
    avg_ttfb_ms: Optional[float] = None
    avg_ttfa_ms: Optional[float] = None
    no_answer_rate: float
    rag_coverage_pct: float
    top_collections: List[str]
    last_active: Optional[datetime] = None
