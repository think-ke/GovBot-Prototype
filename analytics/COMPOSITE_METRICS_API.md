# Enhanced User Sentiment API - Composite Metrics

## Endpoint: GET /analytics/user/sentiment

### Enhanced Response Schema with Composite Metrics

```json
{
  // Original VADER sentiment metrics
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
  
  // NEW: Composite metrics integrating explicit ratings
  "explicit_rating_score": 4.3,           // Average of user-provided 1-5 star ratings
  "total_explicit_ratings": 45,           // Number of explicit ratings received
  "composite_satisfaction_score": 4.15,   // Weighted: 70% sentiment + 30% ratings
  "sentiment_vs_rating_correlation": 0.78, // Correlation between sentiment and ratings (-1 to 1)
  "rating_distribution": [                 // Distribution of 1-5 star ratings
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

## Field Descriptions

### Core Sentiment Fields (Unchanged)
- **satisfaction_score**: VADER-based satisfaction on 1-5 scale
- **average_sentiment_score**: Raw VADER compound score (-1 to 1)
- **escalation_rate**: Percentage of messages indicating need for human help

### New Composite Fields

#### explicit_rating_score
- **Type**: `float | null`
- **Description**: Average of explicit user ratings (1-5 stars)
- **Source**: MessageRating table entries
- **Null when**: No explicit ratings in the time period

#### total_explicit_ratings
- **Type**: `integer`
- **Description**: Count of explicit rating submissions
- **Minimum**: 0

#### composite_satisfaction_score
- **Type**: `float | null`
- **Description**: Weighted combination of sentiment and rating scores
- **Formula**: `(satisfaction_score × 0.7) + (explicit_rating_score × 0.3)`
- **Null when**: No explicit ratings available for weighting

#### sentiment_vs_rating_correlation
- **Type**: `float | null`
- **Description**: Pearson correlation coefficient between sentiment and ratings
- **Range**: -1.0 to 1.0
- **Interpretation**:
  - `> 0.7`: Strong positive correlation (high confidence in sentiment analysis)
  - `0.3 to 0.7`: Moderate correlation
  - `< 0.3`: Weak correlation (sentiment analysis may need review)
- **Null when**: Insufficient overlapping data (< 2 data points)

#### rating_distribution
- **Type**: `array | null`
- **Description**: Breakdown of 1-5 star rating counts and percentages
- **Null when**: No explicit ratings in the time period

## Usage Recommendations

### Primary Satisfaction Metric Selection
```javascript
function getPrimarySatisfactionMetric(response) {
  // High correlation and sufficient ratings: use composite
  if (response.sentiment_vs_rating_correlation > 0.7 && response.total_explicit_ratings > 10) {
    return response.composite_satisfaction_score;
  }
  
  // Sufficient explicit ratings but low correlation: prefer explicit ratings
  if (response.total_explicit_ratings > 10) {
    return response.explicit_rating_score;
  }
  
  // Fall back to sentiment analysis
  return response.satisfaction_score;
}
```

### Confidence Assessment
```javascript
function getConfidenceLevel(response) {
  const correlation = response.sentiment_vs_rating_correlation;
  const ratingCount = response.total_explicit_ratings;
  
  if (correlation > 0.7 && ratingCount > 20) return "HIGH";
  if (correlation > 0.5 && ratingCount > 10) return "MEDIUM";
  if (ratingCount > 5) return "LOW";
  return "SENTIMENT_ONLY";
}
```

## Benefits

1. **Validation**: Cross-check sentiment analysis accuracy with explicit feedback
2. **Balanced View**: Combine automated inference with human input
3. **Quality Assurance**: Identify when sentiment analysis may be unreliable
4. **Comprehensive Insights**: Multiple perspectives on user satisfaction
5. **Confidence Scoring**: Understand reliability of satisfaction metrics
