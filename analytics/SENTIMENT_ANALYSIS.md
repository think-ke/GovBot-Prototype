# Sentiment Analysis with VADER

This implementation adds comprehensive sentiment analysis capabilities to the GovStack analytics module using VADER (Valence Aware Dictionary and sEntiment Reasoner).

## Overview

VADER is a rule-based sentiment analysis tool that's particularly effective for:
- Social media text and informal language
- Short text messages like chat conversations
- Text containing slang, emojis, and abbreviations
- Real-time sentiment analysis without requiring training data

## Features Implemented

### 1. Sentiment Analysis Utility (`sentiment_analyzer.py`)

The `SentimentAnalyzer` class provides:
- **Basic sentiment analysis**: Returns sentiment scores for negative, neutral, positive, and compound sentiment
- **Sentiment classification**: Categorizes text as positive, negative, or neutral based on compound scores
- **Satisfaction scoring**: Converts sentiment to a 1-5 satisfaction scale
- **Escalation detection**: Identifies messages that may require human intervention

### 2. Enhanced Analytics Service

Added `get_user_sentiment()` method to `AnalyticsService` that:
- Analyzes all user messages in a specified time period
- Calculates conversation-level sentiment patterns
- Provides escalation rate metrics
- Returns detailed sentiment distribution statistics

### 3. Updated API Endpoint

The `/sentiment` endpoint now provides real sentiment analysis instead of placeholder data:
- Analyzes actual user message content
- Returns comprehensive sentiment metrics
- Supports date range filtering
- Provides actionable insights for customer service improvement

## Sentiment Score Interpretation

### Compound Score Ranges
- **Positive**: compound score ≥ 0.05
- **Neutral**: -0.05 < compound score < 0.05  
- **Negative**: compound score ≤ -0.05

### Satisfaction Score Conversion
- Compound score -1.0 → Satisfaction 1.0 (Very Dissatisfied)
- Compound score 0.0 → Satisfaction 3.0 (Neutral)
- Compound score 1.0 → Satisfaction 5.0 (Very Satisfied)

### Escalation Threshold
- Messages with compound score ≤ -0.5 are flagged for potential escalation
- This threshold can be adjusted based on business requirements

## Composite Satisfaction Metrics

### Integration of Explicit Ratings and Sentiment Analysis
The system now combines VADER sentiment analysis with explicit user ratings to provide more comprehensive satisfaction metrics:

### Key Composite Metrics

#### 1. **Composite Satisfaction Score**
- **Formula**: `(sentiment_score × 0.7) + (explicit_rating_score × 0.3)`
- **Weighting**: 70% sentiment analysis, 30% explicit ratings
- **Purpose**: Balanced view combining inferred and explicit satisfaction

#### 2. **Explicit Rating Score**
- **Source**: Direct user ratings from `/chat/rating` API endpoints
- **Scale**: 1-5 stars average
- **Data**: Based on `MessageRating` table entries

#### 3. **Sentiment vs Rating Correlation**
- **Calculation**: Pearson correlation coefficient
- **Range**: -1.0 to 1.0
- **Interpretation**:
  - `> 0.7`: Strong positive correlation (sentiment analysis aligns well with explicit ratings)
  - `0.3 to 0.7`: Moderate correlation
  - `< 0.3`: Weak correlation (may indicate sentiment analysis limitations)

#### 4. **Rating Distribution**
- **Breakdown**: Count and percentage for each star rating (1-5)
- **Purpose**: Understanding rating patterns and user satisfaction distribution

### Business Value of Composite Metrics

#### **Accuracy Validation**
- **Cross-validation**: Compare sentiment predictions with actual user ratings
- **Model Improvement**: Identify cases where sentiment analysis fails
- **Confidence Scoring**: Higher correlation = more reliable sentiment predictions

#### **Comprehensive Insights**
- **Multiple Perspectives**: Both inferred (sentiment) and explicit (ratings) satisfaction
- **User Behavior**: Some users provide ratings, others express satisfaction through text
- **Quality Assurance**: Explicit ratings can validate automated sentiment analysis

#### **Strategic Decision Making**
- **Weighted Satisfaction**: More balanced metric considering multiple data sources
- **Intervention Triggers**: Low correlation may indicate need for human review
- **Performance Benchmarking**: Track both automated and human-validated satisfaction

## Usage Examples

### Basic Sentiment Analysis
```python
from sentiment_analyzer import sentiment_analyzer

# Analyze a single message
scores, classification = sentiment_analyzer.analyze_and_classify("This service is great!")
# Returns: ({'neg': 0.0, 'neu': 0.294, 'pos': 0.706, 'compound': 0.6249}, 'positive')

# Check satisfaction score
satisfaction = sentiment_analyzer.calculate_satisfaction_score(0.6249)
# Returns: 4.2
```

### API Usage for Composite Metrics
```bash
# Get comprehensive sentiment analysis with rating integration
GET /analytics/user/sentiment

# Get sentiment for specific date range
GET /analytics/user/sentiment?start_date=2025-01-01&end_date=2025-01-31
```

### Interpreting Composite Results
```python
# Example API response interpretation
response = {
    "satisfaction_score": 4.1,           # VADER sentiment-based
    "explicit_rating_score": 4.3,       # User-provided ratings
    "composite_satisfaction_score": 4.15, # Weighted combination
    "sentiment_vs_rating_correlation": 0.78, # Strong correlation
    "total_explicit_ratings": 45
}

# Business interpretation
if response["sentiment_vs_rating_correlation"] > 0.7:
    print("High confidence: Sentiment analysis aligns well with user ratings")
    primary_metric = response["composite_satisfaction_score"]
elif response["total_explicit_ratings"] > 10:
    print("Moderate confidence: Prioritize explicit ratings")
    primary_metric = response["explicit_rating_score"]
else:
    print("Low data: Rely on sentiment analysis")
    primary_metric = response["satisfaction_score"]

print(f"Primary satisfaction metric: {primary_metric}")
```

## Response Schema

```json
{
  "positive_conversations": 150,
  "negative_conversations": 25,
  "neutral_conversations": 75,
  "satisfaction_score": 4.1,
  "escalation_rate": 8.2,
  "average_sentiment_score": 0.234,
  "total_analyzed_messages": 1250,
  "sentiment_distribution": [
    {
      "category": "Positive",
      "count": 750,
      "percentage": 60.0
    },
    {
      "category": "Neutral", 
      "count": 350,
      "percentage": 28.0
    },
    {
      "category": "Negative",
      "count": 150,
      "percentage": 12.0
    }
  ],
  "explicit_rating_score": 4.3,
  "total_explicit_ratings": 45,
  "composite_satisfaction_score": 4.15,
  "sentiment_vs_rating_correlation": 0.78,
  "rating_distribution": [
    {
      "category": "1 Star",
      "count": 2,
      "percentage": 4.4
    },
    {
      "category": "2 Stars",
      "count": 3,
      "percentage": 6.7
    },
    {
      "category": "3 Stars",
      "count": 8,
      "percentage": 17.8
    },
    {
      "category": "4 Stars",
      "count": 18,
      "percentage": 40.0
    },
    {
      "category": "5 Stars",
      "count": 14,
      "percentage": 31.1
    }
  ]
}
```

## Installation

Add to your requirements.txt:
```
vaderSentiment==3.3.2
```

Install the package:
```bash
pip install vaderSentiment
```

## Testing

Run the demo script to test sentiment analysis:
```bash
cd analytics
python test_sentiment_demo.py
```

## Business Value

### Customer Service Insights
- **Proactive Support**: Identify frustrated users before they escalate
- **Quality Monitoring**: Track satisfaction trends over time using both sentiment and explicit feedback
- **Response Optimization**: Understand which interactions create positive vs negative sentiment
- **Validation**: Use explicit ratings to validate sentiment analysis accuracy

### Product Improvement
- **Feature Impact**: Measure sentiment changes after feature releases using composite metrics
- **Content Quality**: Identify knowledge gaps that cause user frustration through both data sources
- **User Experience**: Track sentiment patterns and rating trends to improve conversation flows
- **A/B Testing**: Compare sentiment vs rating correlation across different implementations

### Operational Metrics
- **Escalation Prevention**: Reduce human handoff needs through early intervention
- **Performance Benchmarking**: Set sentiment-based KPIs validated by actual user ratings
- **Training Data**: Use sentiment patterns and rating correlations to improve AI responses
- **Quality Assurance**: Monitor correlation between predicted and actual satisfaction

### Strategic Decision Making
- **Multi-Source Intelligence**: Combine automated analysis with explicit user feedback
- **Confidence Scoring**: Use correlation metrics to determine reliability of satisfaction scores
- **Resource Allocation**: Prioritize improvements based on both sentiment trends and rating patterns
- **ROI Measurement**: Track satisfaction improvements through multiple validated metrics

## Considerations

### Accuracy
- VADER is highly effective for informal text but may miss context-specific sentiment
- Consider domain-specific fine-tuning for specialized terminology
- Combine with human review for critical escalation decisions

### Performance
- VADER is fast and doesn't require GPU resources
- Sentiment analysis adds minimal processing overhead
- Consider caching results for frequently accessed time periods

### Privacy
- Sentiment analysis processes message content
- Ensure compliance with data privacy regulations
- Consider anonymization for long-term sentiment trend storage
