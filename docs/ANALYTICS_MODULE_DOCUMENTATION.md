# GovStack Analytics Module - Technical Documentation

## Executive Summary

The GovStack Analytics Module provides comprehensive insights into AI assistant performance, user behavior, and business impact. The module is implemented as a separate FastAPI microservice that connects to the main GovStack database to analyze chat interactions, user patterns, and service quality metrics.

## Architecture Overview

### Microservice Design
- **Service**: Standalone FastAPI application (`/analytics/`)
- **Database**: Connects to main GovStack PostgreSQL database
- **API Structure**: RESTful endpoints organized by analytics category
- **Documentation**: Auto-generated Swagger UI at `/analytics/docs`

### Core Components
1. **Analytics API** (`analytics/main.py`) - FastAPI application
2. **Service Layer** (`analytics/services.py`) - Business logic and calculations  
3. **Database Models** (`analytics/models.py`) - SQLAlchemy models
4. **Router Modules** (`analytics/routers/`) - Endpoint organization
5. **Sentiment Analysis** (`analytics/sentiment_analyzer.py`) - ML-powered sentiment analysis

## Analytics Categories

### 1. User Analytics (`/analytics/user/`)
*Understanding user demographics, behavior patterns, and satisfaction*

#### Endpoints:
- `GET /analytics/user/demographics` - User growth and demographic metrics
- `GET /analytics/user/session-frequency` - Session patterns and power user analysis
- `GET /analytics/user/sentiment` - User satisfaction and sentiment analysis

#### Key Metrics:
- **Total Users**: Unique users over time period
- **New vs Returning Users**: User acquisition and retention analysis
- **Session Frequency**: User engagement patterns and power user identification
- **User Sentiment**: Satisfaction analysis from message ratings and feedback

### 2. Usage Analytics (`/analytics/usage/`)
*Monitoring system health, traffic patterns, and operational metrics*

#### Endpoints:
- `GET /analytics/usage/traffic` - Traffic patterns and request volumes
- `GET /analytics/usage/session-duration` - Session length analysis
- `GET /analytics/usage/peak-hours` - Peak usage time identification

#### Key Metrics:
- **Traffic Volume**: Messages per hour/day/week
- **Session Duration**: Average and median session lengths
- **Peak Hours**: High-traffic time periods
- **System Performance**: Response times and throughput

### 3. Conversation Analytics (`/analytics/conversation/`)
*Analyzing dialogue flows, intent patterns, and conversation quality*

#### Endpoints:
- `GET /analytics/conversation/flow` - Conversation pattern analysis
- `GET /analytics/conversation/intent-analysis` - Intent classification and trends
- `GET /analytics/conversation/quality-metrics` - Response quality assessment

#### Key Metrics:
- **Conversation Flow**: Message exchange patterns
- **Intent Distribution**: Popular topics and service areas
- **Quality Scores**: Response accuracy and helpfulness ratings
- **Resolution Rates**: Successful conversation outcomes

### 4. Business Analytics (`/analytics/business/`)
*Measuring ROI, automation rates, and business impact*

#### Endpoints:
- `GET /analytics/business/roi` - Return on investment calculations
- `GET /analytics/business/containment-rate` - Self-service success rates
- `GET /analytics/business/cost-savings` - Operational cost reduction metrics

#### Key Metrics:
- **ROI Calculation**: Cost savings vs implementation costs
- **Containment Rate**: Percentage of queries resolved without human intervention
- **Cost per Interaction**: Economic efficiency metrics
- **Service Automation**: Human workload reduction

## Implementation Details

### Database Schema Integration

The analytics module leverages existing GovStack tables:

```sql
-- Primary tables for analytics
Chat (session_id, user_id, created_at, updated_at)
ChatMessage (chat_id, message_type, message_object, timestamp)
MessageRating (session_id, message_id, rating, feedback_text)
Document (collection_id, upload_date, created_by)
Webpage (collection_id, last_crawled, created_by)
```

### Service Layer Architecture

```python
class AnalyticsService:
    """Main service class for analytics calculations."""
    
    @staticmethod
    async def get_user_demographics(db, start_date, end_date):
        """Calculate user demographics and growth metrics."""
        
    @staticmethod
    async def get_session_frequency_analysis(db, limit):
        """Analyze user session patterns."""
        
    @staticmethod
    async def calculate_roi_metrics(db, start_date, end_date):
        """Calculate business ROI metrics."""
```

### Sentiment Analysis Integration

The module includes ML-powered sentiment analysis:

```python
from .sentiment_analyzer import sentiment_analyzer

# Analyze feedback sentiment
sentiment_score = sentiment_analyzer.analyze(feedback_text)
# Returns: positive, negative, neutral with confidence scores
```

---

## 1. User Analytics
*Identify who your assistant's users are and how they feel about the assistant*

### 1.1 User Demographics & Identification
**Data Source**: `Chat.user_id`, `ChatMessage` patterns, API access logs

#### Core Metrics:
- **Unique Users**: Distinct `user_id` counts over time periods
- **New vs. Returning Users**: First-time vs. repeat session analysis
- **User Geographic Distribution**: Based on API access patterns (if location data available)
- **Device/Platform Analytics**: User agent analysis from API requests
- **Access Patterns**: Time zones and preferred interaction hours

#### Implementation Approach:
```sql
-- Example: User session frequency analysis
SELECT 
    user_id,
    COUNT(DISTINCT session_id) as total_sessions,
    MIN(created_at) as first_visit,
    MAX(updated_at) as last_visit,
    EXTRACT(DAYS FROM MAX(updated_at) - MIN(created_at)) as user_lifespan_days
FROM Chat 
WHERE user_id IS NOT NULL
GROUP BY user_id
```

### 1.2 Session Frequency Analysis
**Data Source**: `Chat` table temporal patterns

#### Core Metrics:
- **Sessions per User**: Distribution of session counts across user base
- **Return Frequency**: Time between user sessions
- **Power User Identification**: Users with high session counts
- **User Lifecycle Stage**: New, Active, At-Risk, Dormant classification
- **Seasonal Usage Patterns**: User behavior changes over time

#### Key Calculations:
- Average sessions per user per week/month
- User retention rates (Day 1, Day 7, Day 30)
- Session frequency distribution curves
- User cohort analysis

### 1.3 Feedback & Sentiment Analysis
**Data Source**: `ChatMessage.message_object`, conversation outcomes

#### Core Metrics:
- **Conversation Completion Rate**: Sessions ending positively vs. abandonment
- **User Satisfaction Indicators**: 
  - Successful document retrieval
  - Conversation length as proxy for engagement
  - Return user behavior patterns
- **Sentiment Analysis**: Natural language processing of user messages
- **Escalation Requests**: Users asking for human assistance
- **Issue Resolution Success**: Conversations ending with successful outcomes

#### Implementation Strategy:
- Analyze final messages in conversations for satisfaction indicators
- Track patterns like "thank you," "this helped," vs. "I need human help"
- Monitor session completion vs. abandonment rates
- Implement post-conversation satisfaction surveys (future enhancement)

---

## 2. Usage Analytics
*Discover overall traffic and assistant health*

### 2.1 Traffic & Volume Metrics
**Data Source**: `Chat`, `ChatMessage`, API logs

#### Core Metrics:
- **Total Sessions**: Daily/weekly/monthly session counts
- **Total Messages**: Volume of user and assistant messages
- **Peak Usage Hours**: Traffic distribution throughout the day
- **Growth Trends**: User base and session volume growth over time
- **Channel Activity**: API endpoint usage patterns

#### Key Performance Indicators:
```sql
-- Example: Daily session metrics
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT session_id) as daily_sessions,
    COUNT(DISTINCT user_id) as daily_unique_users,
    AVG(EXTRACT(MINUTES FROM updated_at - created_at)) as avg_session_duration_minutes
FROM Chat
GROUP BY DATE(created_at)
ORDER BY date DESC
```

### 2.2 Session Duration Analysis
**Data Source**: `Chat.created_at` and `Chat.updated_at`

#### Core Metrics:
- **Average Session Duration**: Mean time from first to last message
- **Session Duration Distribution**: Short, medium, long conversation buckets
- **Duration by Outcome**: Successful vs. unsuccessful session lengths
- **Time to First Response**: AI response latency
- **Session Depth**: Messages per session analysis

### 2.3 System Health & Error Rates
**Data Source**: API logs, system monitoring, token tracking

#### Core Metrics:
- **API Response Times**: P50, P95, P99 latency percentiles
- **Error Rates**: HTTP 4xx/5xx responses, failed AI responses
- **System Availability**: Uptime and downtime tracking
- **Token Usage Health**: Cost and consumption rate monitoring
- **Database Performance**: Query response times and connection health

#### Critical Health Indicators:
- **Service Level Agreement Metrics**: Response time targets
- **Error Budget Tracking**: Acceptable failure rates
- **Capacity Utilization**: System load and scaling indicators
- **Alert Thresholds**: Automated monitoring and alerting

---

## 3. Conversation Analytics
*Gain insights into how dialogues unfold*

### 3.1 Top Flows & Intent Analysis (RAG-Based)
**Data Source**: `ChatMessage.message_object`, `Document` access patterns

#### Core Metrics:
- **Document Retrieval Patterns**: Most accessed document types and categories
- **Query Classification**: Common citizen service request types
- **Successful Retrieval Flows**: Queries leading to relevant document access
- **Search Intent Analysis**: Natural language processing of user queries
- **Topic Clustering**: Grouping similar conversation themes

#### RAG-Specific Analytics:
- **Retrieval Success Rate**: Queries finding relevant documents
- **Context Relevance Score**: Quality of retrieved content
- **Knowledge Gap Identification**: Queries with poor retrieval results
- **Collection Performance**: Document collection usage effectiveness

### 3.2 Conversation Turn Analysis
**Data Source**: `ChatMessage` sequence analysis

#### Core Metrics:
- **Average Turns per Conversation**: Message exchange patterns
- **Turn Distribution**: Short vs. long conversation analysis
- **Multi-turn Success Rate**: Complex queries requiring multiple exchanges
- **Clarification Patterns**: When users ask follow-up questions
- **Conversation Progression**: How dialogues develop over time

#### Implementation Example:
```sql
-- Conversation turn analysis
SELECT 
    c.session_id,
    COUNT(cm.id) as total_messages,
    COUNT(CASE WHEN cm.message_type = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN cm.message_type = 'assistant' THEN 1 END) as assistant_messages,
    MAX(cm.timestamp) - MIN(cm.timestamp) as conversation_duration
FROM Chat c
JOIN ChatMessage cm ON c.id = cm.chat_id
GROUP BY c.session_id
```

### 3.3 Drop-off & Escalation Patterns
**Data Source**: `ChatMessage` sequence analysis, conversation outcomes

#### Core Metrics:
- **Abandonment Points**: Where users typically leave conversations
- **Drop-off by Turn Number**: Conversation length vs. completion rate
- **Escalation Triggers**: Messages indicating need for human help
- **Incomplete Resolution Rate**: Conversations ending without clear resolution
- **Re-engagement Patterns**: Users returning after abandonment

#### Escalation Indicators:
- Messages containing "speak to human," "transfer to agent"
- Repeated unsuccessful queries
- Expression of frustration in user messages
- Complex queries beyond AI capability

---

## 4. Business Analytics
*Measure how the assistant performs against business-critical objectives*

### 4.1 ROI & Cost-Benefit Analysis
**Data Source**: Token tracking, operational cost data, traditional service costs

#### Core Metrics:
- **Cost per Citizen Interaction**: AI service delivery cost vs. traditional channels
- **Operational Cost Savings**: Reduced human agent time and overhead
- **Total Cost of Ownership**: Infrastructure, API, and operational expenses
- **Cost per Successful Resolution**: Financial efficiency of automated service
- **Budget Performance**: Actual vs. projected costs

#### ROI Calculations:
```
ROI = (Cost Savings from Automation - AI System Costs) / AI System Costs × 100
```

**Example ROI Metrics**:
- Traditional phone support: $15-25 per interaction
- GovStack AI interaction: $0.033 per request (based on current token costs)
- Potential savings: 99%+ cost reduction per interaction

### 4.2 Containment Rate Analysis
**Data Source**: Conversation completion analysis, escalation tracking

#### Core Metrics:
- **Full Automation Rate**: Conversations resolved without human intervention
- **Partial Automation Rate**: AI provides useful information before escalation
- **Human Handoff Rate**: Percentage requiring human agent assistance
- **Resolution Success Rate**: Conversations ending with successful outcomes
- **Self-Service Adoption**: Citizens successfully using automated services

#### Containment Calculation:
```
Containment Rate = (Fully Automated Resolutions / Total Conversations) × 100
```

### 4.3 Business Flow Success Rates
**Data Source**: Conversation outcome analysis, document access success

#### Core Metrics:
- **Service Request Completion**: Successful fulfillment of citizen needs
- **Document Access Success**: Users finding and accessing needed documents
- **Information Accuracy**: Quality and relevance of AI responses
- **Process Efficiency**: Time to resolution for different service types
- **Citizen Satisfaction Proxy**: Indicators of successful service delivery

#### Government-Specific Business Metrics:
- **Digital Service Adoption**: Migration from traditional to AI-powered services
- **Service Accessibility**: Reaching underserved populations
- **Compliance Success**: Meeting government service level standards
- **Public Trust Indicators**: Continued usage and positive outcomes

### 4.4 Interruption & Quality Metrics
**Data Source**: Conversation flow analysis, error tracking

#### Core Metrics:
- **Conversation Interruption Rate**: Unexpected terminations or errors
- **Technical Failure Impact**: System errors affecting user experience
- **Response Quality Degradation**: When AI provides poor responses
- **Recovery Success Rate**: Users continuing after interruptions
- **Service Continuity**: Maintaining quality during high-load periods

---

## Implementation Priorities for Government Agencies

### Phase 1: Essential Metrics (Month 1-2)
1. **Usage Analytics**: Basic traffic, session, and health metrics
2. **User Analytics**: User identification and session frequency
3. **Cost Tracking**: Real-time token usage and cost monitoring
4. **Basic Business Metrics**: Containment rate and resolution success

### Phase 2: Advanced Analytics (Month 3-4)
1. **Conversation Analytics**: Turn analysis and flow optimization
2. **Sentiment Analysis**: User satisfaction measurement
3. **ROI Calculations**: Comprehensive cost-benefit analysis
4. **Predictive Metrics**: Forecasting and trend analysis

### Phase 3: Strategic Insights (Month 5-6)
1. **Advanced User Segmentation**: Citizen persona development
2. **Service Optimization**: Flow improvements based on drop-off analysis
3. **Policy Impact Measurement**: Analytics supporting policy decisions
4. **Cross-channel Integration**: Holistic citizen service analytics

## Dashboard Implementation Strategy

### Executive Dashboard
- High-level KPIs: Containment rate, cost savings, user growth
- ROI metrics and budget performance
- Service availability and quality indicators

### Operations Dashboard  
- Real-time system health and performance
- Current session activity and error monitoring
- Capacity utilization and scaling alerts

### Product Optimization Dashboard
- Conversation flow analysis and drop-off patterns
- User journey optimization insights
- Content performance and knowledge gap identification

### Business Intelligence Dashboard
- Deep-dive analytics for strategic planning
- Comparative analysis and benchmarking
- Predictive analytics and forecasting

## Success Metrics for Government Digital Transformation

### Citizen Experience Metrics
- Reduced wait times for government services
- Increased service accessibility (24/7 availability)
- Higher citizen satisfaction with digital services

### Operational Efficiency Metrics
- Cost reduction compared to traditional service delivery
- Increased throughput of citizen requests
- Reduced burden on human agents

### Strategic Value Metrics
- Digital adoption rates across citizen demographics
- Service delivery modernization progress
- Public trust and engagement with digital government services





# GovStack Analytics Module - Technical Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Module Structure](#module-structure)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Services Layer](#services-layer)
6. [Schemas](#schemas)
7. [Database Configuration](#database-configuration)
8. [Usage Examples](#usage-examples)
9. [Performance Considerations](#performance-considerations)
10. [Security](#security)

## Architecture Overview

The GovStack Analytics Module is a microservice built with FastAPI that provides comprehensive analytics capabilities for the GovStack chatbot system. It offers four main analytical domains:

- **User Analytics**: Demographics, retention, and behavior patterns
- **Usage Analytics**: Traffic patterns, system performance, and capacity metrics
- **Conversation Analytics**: Dialog flows, intent analysis, and content performance
- **Business Analytics**: ROI metrics, cost analysis, and operational efficiency

### Technology Stack
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL with asyncpg driver
- **ORM**: SQLAlchemy (async)
- **Data Validation**: Pydantic
- **Containerization**: Docker
- **API Documentation**: OpenAPI/Swagger

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Router Layer  │    │  Service Layer  │
│                 │───▶│                 │───▶│                 │
│  main.py        │    │  /routers/      │    │  services.py    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Data Models   │    │    Schemas      │
│                 │    │                 │    │                 │
│  database.py    │    │   models.py     │    │  schemas.py     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Module Structure

```
analytics/
├── __init__.py                 # Module initialization
├── main.py                     # FastAPI application entry point
├── database.py                 # Database configuration and session management
├── models.py                   # SQLAlchemy database models
├── schemas.py                  # Pydantic response schemas
├── services.py                 # Business logic and data processing
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── test_config.py             # Test configuration
├── test-docker.sh             # Docker test script
└── routers/                   # API endpoint routers
    ├── __init__.py
    ├── user_analytics.py       # User analytics endpoints
    ├── usage_analytics.py      # Usage analytics endpoints
    ├── conversation_analytics.py # Conversation analytics endpoints
    └── business_analytics.py   # Business analytics endpoints
```

## API Endpoints

### Base URL Structure
- **Base URL**: `/analytics`
- **Documentation**: `/analytics/docs` (Swagger UI)
- **ReDoc**: `/analytics/redoc`
- **Health Check**: `/analytics/health`

### User Analytics Endpoints

#### 1. User Demographics
**Endpoint**: `GET /analytics/user/demographics`

**Description**: Provides comprehensive user demographics and growth metrics.

**Parameters**:
- `start_date` (optional): Start date for analysis (ISO format)
- `end_date` (optional): End date for analysis (ISO format)

**Response Schema**: `UserDemographics`
```json
{
  "total_users": 1250,
  "new_users": 150,
  "returning_users": 1100,
  "active_users": 850,
  "user_growth_rate": 12.5
}
```

**Use Cases**:
- Executive dashboards
- Growth tracking
- User acquisition analysis
- Retention monitoring

#### 2. Session Frequency Analysis
**Endpoint**: `GET /analytics/user/session-frequency`

**Description**: Analyzes user session patterns and identifies power users.

**Parameters**:
- `limit` (optional): Maximum number of users to return (default: 100)

**Response Schema**: `List[SessionFrequency]`
```json
[
  {
    "user_id": "user123",
    "total_sessions": 25,
    "first_visit": "2024-01-15T10:30:00Z",
    "last_visit": "2024-02-15T14:45:00Z",
    "user_lifespan_days": 31
  }
]
```

**Use Cases**:
- Power user identification
- Engagement analysis
- User lifecycle tracking
- Retention strategies

#### 3. User Sentiment Analysis
**Endpoint**: `GET /analytics/user/sentiment`

**Description**: Analyzes user sentiment and satisfaction indicators.

**Parameters**:
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis

**Response Schema**: `UserSentiment`
```json
{
  "positive_conversations": 150,
  "negative_conversations": 30,
  "neutral_conversations": 120,
  "satisfaction_score": 4.2,
  "escalation_rate": 8.5
}
```

#### 4. User Retention Analysis
**Endpoint**: `GET /analytics/user/retention`

**Description**: Cohort-based retention analysis.

**Parameters**:
- `cohort_size` (optional): Cohort size in days (default: 30)

**Response**:
```json
{
  "day_1_retention": 65.5,
  "day_7_retention": 42.3,
  "day_30_retention": 28.7,
  "cohort_analysis": []
}
```

#### 5. Geographic Distribution
**Endpoint**: `GET /analytics/user/geographic`

**Description**: Geographic distribution of users (requires location data).

### Usage Analytics Endpoints

#### 1. Traffic Metrics
**Endpoint**: `GET /analytics/usage/traffic`

**Description**: Comprehensive traffic and volume metrics.

**Parameters**:
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis

**Response Schema**: `TrafficMetrics`
```json
{
  "total_sessions": 5420,
  "total_messages": 18650,
  "unique_users": 1250,
  "peak_hours": [
    {"hour": 14, "sessions": 245},
    {"hour": 10, "sessions": 220}
  ],
  "growth_trend": [
    {"date": "2024-01-01", "value": 150},
    {"date": "2024-01-02", "value": 175}
  ]
}
```

#### 2. Session Duration Analysis
**Endpoint**: `GET /analytics/usage/session-duration`

**Description**: Session duration patterns and distribution.

**Response Schema**: `SessionDuration`
```json
{
  "average_duration_minutes": 8.5,
  "median_duration_minutes": 5.2,
  "duration_distribution": [
    {"category": "0-1 min", "count": 120, "percentage": 15.5},
    {"category": "1-5 min", "count": 350, "percentage": 45.2}
  ]
}
```

#### 3. System Health
**Endpoint**: `GET /analytics/usage/system-health`

**Description**: Real-time system health and performance metrics.

**Response Schema**: `SystemHealth`
```json
{
  "api_response_time_p50": 150.5,
  "api_response_time_p95": 450.2,
  "api_response_time_p99": 850.7,
  "error_rate": 2.1,
  "uptime_percentage": 99.8,
  "system_availability": "healthy"
}
```

#### 4. Peak Hours Analysis
**Endpoint**: `GET /analytics/usage/peak-hours`

**Description**: Detailed peak hours and traffic pattern analysis.

**Parameters**:
- `days` (optional): Number of days to analyze (default: 7)

#### 5. Capacity Metrics
**Endpoint**: `GET /analytics/usage/capacity`

**Description**: System capacity and scaling metrics.

#### 6. Error Analysis
**Endpoint**: `GET /analytics/usage/errors`

**Description**: Error analysis and monitoring data.

**Parameters**:
- `hours` (optional): Hours of error data to analyze (default: 24)

### Conversation Analytics Endpoints

#### 1. Conversation Flows
**Endpoint**: `GET /analytics/conversation/flows`

**Description**: Conversation flow analysis and turn patterns.

**Response Schema**: `List[ConversationFlow]`
```json
[
  {
    "turn_number": 1,
    "completion_rate": 85.5,
    "abandonment_rate": 14.5,
    "average_response_time": 1.2
  }
]
```

#### 2. Intent Analysis
**Endpoint**: `GET /analytics/conversation/intents`

**Description**: User intent analysis and classification patterns.

**Parameters**:
- `limit` (optional): Maximum number of intents to return (default: 20)

**Response Schema**: `List[IntentAnalysis]`
```json
[
  {
    "intent": "document_request",
    "frequency": 150,
    "success_rate": 85.5,
    "average_turns": 2.3
  }
]
```

#### 3. Document Retrieval Analysis
**Endpoint**: `GET /analytics/conversation/document-retrieval`

**Description**: Document retrieval patterns and RAG success rates.

**Response Schema**: `List[DocumentRetrieval]`
```json
[
  {
    "document_type": "government_forms",
    "access_frequency": 200,
    "success_rate": 92.5,
    "collection_id": "gov_forms_2024"
  }
]
```

#### 4. Conversation Drop-offs
**Endpoint**: `GET /analytics/conversation/drop-offs`

**Description**: Conversation abandonment analysis.

#### 5. Sentiment Trends
**Endpoint**: `GET /analytics/conversation/sentiment-trends`

**Description**: Sentiment trends within conversations.

### Business Analytics Endpoints

#### 1. ROI Metrics
**Endpoint**: `GET /analytics/business/roi`

**Description**: Return on investment and cost-benefit analysis.

**Response Schema**: `ROIMetrics`
```json
{
  "cost_per_interaction": 0.033,
  "cost_savings": 108540.75,
  "roi_percentage": 6057.8,
  "automation_rate": 85.0
}
```

#### 2. Containment Rate
**Endpoint**: `GET /analytics/business/containment`

**Description**: Service containment and automation rates.

**Response Schema**: `ContainmentRate`
```json
{
  "full_automation_rate": 70.0,
  "partial_automation_rate": 20.0,
  "human_handoff_rate": 10.0,
  "resolution_success_rate": 85.0
}
```

#### 3. Business Flow Success
**Endpoint**: `GET /analytics/business/business-flow-success`

**Description**: Business process completion and success metrics.

**Response Schema**: `BusinessFlowSuccess`
```json
{
  "service_completion_rate": 87.5,
  "document_access_success": 92.3,
  "information_accuracy": 89.1,
  "citizen_satisfaction_proxy": 4.2
}
```

#### 4. Cost Analysis
**Endpoint**: `GET /analytics/business/cost-analysis`

**Description**: Detailed cost breakdown analysis.

## Data Models

### Core Database Models

#### Chat Model
```python
class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
```

#### ChatMessage Model
```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    message_id = Column(String(64), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    message_object = Column(JSON, nullable=False)
    history = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    chat = relationship("Chat", back_populates="messages")
```

#### Document Model
```python
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    object_name = Column(String(255), unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    upload_date = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    meta_data = Column(JSON, nullable=True)
    collection_id = Column(String(64), nullable=True, index=True)
```

#### Webpage Model
```python
class Webpage(Base):
    __tablename__ = "webpages"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=True)
    content_hash = Column(String(64), nullable=True)
    content_markdown = Column(Text, nullable=True)
    last_crawled = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    first_crawled = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    crawl_depth = Column(Integer, default=0)
    status_code = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    is_seed = Column(Boolean, default=False)
    content_type = Column(String(100), nullable=True)
    collection_id = Column(String(64), nullable=True, index=True)
    is_indexed = Column(Boolean, default=False, nullable=False)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
```

## Services Layer

### AnalyticsService Class

The `AnalyticsService` class contains static methods for data processing and analytics calculations:

#### Key Methods:

1. **`get_user_demographics(db, start_date, end_date)`**
   - Calculates user demographics and growth metrics
   - Returns total, new, returning, and active users
   - Computes growth rate compared to previous period

2. **`get_session_frequency_analysis(db, limit)`**
   - Analyzes user session patterns
   - Identifies power users and engagement levels
   - Returns user lifecycle information

3. **`get_traffic_metrics(db, start_date, end_date)`**
   - Calculates traffic and volume metrics
   - Identifies peak hours and growth trends
   - Returns comprehensive traffic analysis

4. **`get_session_duration_analysis(db, start_date, end_date)`**
   - Analyzes session duration patterns
   - Creates duration distribution buckets
   - Calculates average and median session times

5. **`get_conversation_turn_analysis(db, start_date, end_date)`**
   - Analyzes conversation flow patterns
   - Calculates completion and abandonment rates
   - Groups conversations by turn ranges

6. **`get_roi_metrics(db, start_date, end_date)`**
   - Calculates ROI and cost-benefit metrics
   - Compares AI costs vs traditional support costs
   - Returns automation rates and savings

7. **`get_containment_rate(db, start_date, end_date)`**
   - Calculates service containment metrics
   - Analyzes automation vs human handoff rates
   - Returns resolution success rates

## Schemas

### Response Schema Categories

#### User Analytics Schemas
- `UserDemographics`: User growth and demographic data
- `SessionFrequency`: User session patterns and lifecycle
- `UserSentiment`: Sentiment analysis and satisfaction metrics

#### Usage Analytics Schemas
- `TrafficMetrics`: Traffic volume and patterns
- `SessionDuration`: Session duration analysis
- `SystemHealth`: System performance metrics

#### Conversation Analytics Schemas
- `IntentAnalysis`: User intent classification and success rates
- `ConversationFlow`: Dialog flow and completion patterns
- `DocumentRetrieval`: Document access and retrieval metrics

#### Business Analytics Schemas
- `ROIMetrics`: Return on investment calculations
- `ContainmentRate`: Service containment and automation rates
- `BusinessFlowSuccess`: Business process completion metrics

#### Supporting Schemas
- `TimeRange`: Date range specification
- `MetricResponse`: Generic metric response
- `TrendData`: Time-series trend data
- `DistributionData`: Distribution and percentage data

## Database Configuration

### Connection Setup
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### Session Management
- Async database sessions using SQLAlchemy
- Automatic session cleanup and connection pooling
- Dependency injection for database sessions

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- Configuration supports async PostgreSQL with asyncpg driver

## Usage Examples

### Python Client Example
```python
import httpx
import asyncio

async def get_user_demographics():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8005/analytics/user/demographics",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            }
        )
        return response.json()

# Usage
demographics = asyncio.run(get_user_demographics())
print(f"Total users: {demographics['total_users']}")
```

### cURL Examples
```bash
# Get user demographics
curl -X GET "http://localhost:8005/analytics/user/demographics?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z" \
  -H "X-API-Key: your-api-key-here"

# Get traffic metrics
curl -X GET "http://localhost:8005/analytics/usage/traffic?start_date=2024-01-01T00:00:00Z" \
  -H "X-API-Key: your-api-key-here"

# Get ROI metrics
curl -X GET "http://localhost:8005/analytics/business/roi" \
  -H "X-API-Key: your-api-key-here"

# Health check (no API key required)
curl -X GET "http://localhost:8005/analytics/health"
```

### Dashboard Integration Example
```javascript
// React/JavaScript example
const fetchAnalytics = async () => {
  const endpoints = [
    '/analytics/user/demographics',
    '/analytics/usage/traffic',
    '/analytics/business/roi',
    '/analytics/business/containment'
  ];
  
  const results = await Promise.all(
    endpoints.map(endpoint => 
      fetch(`http://localhost:8005${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'your-api-key-here'
        }
      }).then(r => r.json())
    )
  );
  
  return {
    demographics: results[0],
    traffic: results[1],
    roi: results[2],
    containment: results[3]
  };
};
```

## Performance Considerations

### Database Optimization
- **Indexing**: Key columns are indexed for query performance
  - `session_id`, `user_id` on chats table
  - `chat_id`, `message_id` on chat_messages table
  - `collection_id` on documents and webpages tables

- **Query Optimization**: 
  - Use of aggregation functions for metrics calculation
  - Efficient JOIN operations with proper foreign keys
  - Pagination support with LIMIT clauses

### Caching Strategy
- Consider implementing Redis caching for frequently accessed metrics
- Cache expensive calculations like ROI metrics and user demographics
- Implement cache invalidation based on data freshness requirements

### Async Performance
- All database operations are async for better concurrency
- Non-blocking I/O operations for multiple concurrent requests
- Efficient connection pooling with SQLAlchemy

### Monitoring Recommendations
- Track query execution times
- Monitor database connection pool usage
- Implement rate limiting for resource-intensive endpoints

## Security

### Authentication & Authorization
- Current implementation lacks authentication (development only)
- Production deployment should implement:
  - JWT token validation
  - Role-based access control (RBAC)
  - API key authentication for service-to-service calls

### Data Privacy
- User IDs should be anonymized or hashed
- Implement data retention policies
- Consider GDPR compliance for user data

### Network Security
- CORS configuration should be restricted in production
- Use HTTPS in production environments
- Implement rate limiting and DDoS protection

### Recommended Security Headers
```python
# Add to FastAPI middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    headers={
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block"
    }
)
```

## Development and Testing

### Running the Service
```bash
# Development mode
cd analytics/
python -m uvicorn main:app --reload --port 8005

# Docker mode
docker build -t analytics .
docker run -p 8005:8005 analytics
```

### Testing
```bash
# Run tests
python -m pytest

# Test with Docker
./test-docker.sh
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/govstackdb"
```

## Future Enhancements

### Planned Features
1. **Real-time Analytics**: WebSocket support for live metrics
2. **Advanced ML Models**: Sentiment analysis, intent classification
3. **Custom Dashboards**: User-configurable dashboard layouts
4. **Data Export**: CSV, JSON, and PDF export capabilities
5. **Alert System**: Threshold-based alerts and notifications
6. **A/B Testing**: Experiment tracking and analysis

### Integration Opportunities
1. **Metabase Integration**: Pre-built dashboards and visualizations
2. **Prometheus/Grafana**: Metrics collection and monitoring
3. **Data Warehouse**: ETL processes for long-term analytics storage
4. **Machine Learning Pipeline**: Predictive analytics and forecasting

This documentation provides a comprehensive overview of the GovStack Analytics Module, covering architecture, implementation details, and usage guidelines for developers and system administrators.
