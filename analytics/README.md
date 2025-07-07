# Analytics Microservice

This microservice provides comprehensive analytics capabilities for the GovStack AI-powered eCitizen Services platform.

## Overview

The analytics service is organized into four key analytics categories based on the dashboard specification:

1. **User Analytics** - Understanding citizen demographics, behavior patterns, and satisfaction
2. **Usage Analytics** - Monitoring system health, traffic patterns, and operational metrics  
3. **Conversation Analytics** - Analyzing dialogue flows, intent patterns, and conversation quality
4. **Business Analytics** - Measuring ROI, automation rates, and business-critical objectives

## API Endpoints

### User Analytics (`/analytics/user`)
- `GET /demographics` - User demographics and growth metrics
- `GET /session-frequency` - Session frequency analysis
- `GET /sentiment` - User sentiment and satisfaction metrics
- `GET /retention` - User retention analysis by cohorts
- `GET /geographic` - Geographic distribution of users

### Usage Analytics (`/analytics/usage`)
- `GET /traffic` - Traffic and volume metrics
- `GET /session-duration` - Session duration analysis
- `GET /system-health` - Real-time system health metrics
- `GET /peak-hours` - Peak hours analysis
- `GET /capacity` - System capacity and scaling metrics
- `GET /errors` - Error analysis and monitoring

### Conversation Analytics (`/analytics/conversation`)
- `GET /flows` - Conversation flow analysis
- `GET /intents` - Intent analysis from conversations
- `GET /document-retrieval` - Document retrieval patterns
- `GET /drop-offs` - Conversation drop-off analysis
- `GET /sentiment-trends` - Sentiment trends in conversations
- `GET /knowledge-gaps` - Knowledge gap identification

### Business Analytics (`/analytics/business`)
- `GET /roi` - ROI and cost-benefit analysis
- `GET /containment` - Containment rate analysis
- `GET /business-flow-success` - Business flow success metrics
- `GET /cost-analysis` - Detailed cost analysis
- `GET /performance-benchmarks` - Performance benchmarks

### Dashboard Endpoints
- `GET /analytics/business/dashboard/executive` - Executive dashboard
- `GET /analytics/business/dashboard/operations` - Operations dashboard
- `GET /analytics/business/dashboard/product-optimization` - Product optimization dashboard
- `GET /analytics/business/dashboard/business-intelligence` - Business intelligence dashboard

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/govstackdb"
```

## Running the Service

### Development
```bash
python -m analytics.main
```

### Production
```bash
uvicorn analytics.main:app --host 0.0.0.0 --port 8005
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8005/analytics/docs
- ReDoc: http://localhost:8005/analytics/redoc

## Key Features

### Real-time Analytics
- Live system health monitoring
- Current session tracking
- Real-time error rate monitoring

### Historical Analysis
- Trend analysis over custom date ranges
- User behavior pattern identification
- Performance benchmarking

### Business Intelligence
- ROI calculations and cost-benefit analysis
- Automation rate tracking
- Service effectiveness measurement

### Predictive Insights
- User growth forecasting
- Capacity planning recommendations
- Performance trend predictions

## Data Sources

The analytics service leverages the following database tables:
- `chats` - Chat conversation records
- `chat_messages` - Individual message records
- `documents` - Document access tracking
- `webpages` - Webpage content and access patterns

## Success Metrics

### Government Digital Transformation KPIs
- **Citizen Experience**: Reduced wait times, 24/7 availability, higher satisfaction
- **Operational Efficiency**: Cost reduction, increased throughput, reduced agent burden
- **Strategic Value**: Digital adoption rates, service modernization, public trust

### Technical Performance Metrics
- **Containment Rate**: 85%+ automation without human intervention
- **Cost Savings**: 99%+ reduction in cost per interaction vs traditional channels
- **Response Time**: <1 second average API response time
- **Availability**: 99.9% uptime target

## Integration

The analytics service integrates with:
- Main GovStack database for conversation and document data
- System monitoring for health metrics
- Token tracking system for cost analysis
- Future: External BI tools and dashboards
