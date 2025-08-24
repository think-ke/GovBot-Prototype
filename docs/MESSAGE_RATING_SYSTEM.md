# Message Rating System

## Overview

The GovStack message rating system allows users to provide feedback on AI assistant responses, enabling continuous improvement of the service quality and user satisfaction measurement.

## Features

### ⭐ **Star Rating System**
- 1-5 star ratings for assistant messages
- Optional written feedback for detailed insights
- User identification for personalized analytics
- Metadata support for categorization

### 📊 **Rating Analytics**
- Aggregated rating statistics
- Trend analysis over time
- Rating distribution insights
- User-specific rating patterns

### 🔒 **Privacy & Security**
- Optional user identification
- Secure API key-based access
- Rating update capabilities
- Data retention controls

## Database Schema

### Message Rating Table
```sql
CREATE TABLE message_ratings (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,         -- Links to Chat.session_id
    message_id VARCHAR(64) NOT NULL,         -- Links to ChatMessage.message_id
    user_id VARCHAR(64),                     -- Optional user identification
    rating INTEGER NOT NULL,                 -- Star rating 1-5
    feedback_text TEXT,                      -- Optional written feedback
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rating_metadata JSON                     -- Additional rating metadata
);

-- Indexes for performance
CREATE INDEX idx_session_message_rating ON message_ratings(session_id, message_id);
CREATE INDEX idx_rating_timestamp ON message_ratings(rating, created_at);
CREATE INDEX idx_user_ratings ON message_ratings(user_id, created_at);
```

## API Endpoints

All rating endpoints support standard REST operations with proper authentication.

### Submit Rating
```http
POST /chat/ratings
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message_id": "msg_123",
  "rating": 5,
  "feedback_text": "Very helpful and accurate response!",
  "user_id": "user123",
  "metadata": {
    "category": "helpful",
    "source": "web_interface"
  }
}
```

### Get Rating Statistics
```http
GET /chat/ratings/stats
X-API-Key: your-api-key-here
```

**Response:**
```json
{
  "total_ratings": 150,
  "average_rating": 4.2,
  "rating_distribution": {
    "1": 5,
    "2": 10,
    "3": 25,
    "4": 60,
    "5": 50
  },
  "recent_ratings_trend": [
    {
      "date": "2023-10-20",
      "average_rating": 4.3,
      "count": 15
    }
  ]
}
```

## Implementation Guide

### 1. Database Setup

Run the migration script to create the rating tables:

```bash
python scripts/add_message_rating_table.py
```

### 2. Frontend Integration

#### Simple Rating Widget

```javascript
// Submit a rating
async function submitRating(sessionId, messageId, rating, feedback) {
    const response = await fetch('/chat/ratings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your-api-key'
        },
        body: JSON.stringify({
            session_id: sessionId,
            message_id: messageId,
            rating: rating,
            feedback_text: feedback,
            user_id: getCurrentUserId(),
            metadata: {
                source: 'web_interface',
                timestamp: new Date().toISOString()
            }
        })
    });
    
    if (response.ok) {
        console.log('Rating submitted successfully');
    }
}

// Get rating statistics
async function getRatingStats() {
    const response = await fetch('/chat/ratings/stats', {
        headers: { 'X-API-Key': 'your-api-key' }
    });
    
    const stats = await response.json();
    console.log(`Average rating: ${stats.average_rating}`);
    console.log(`Total ratings: ${stats.total_ratings}`);
}
```

#### React Rating Component Example

```jsx
import React, { useState } from 'react';

const MessageRating = ({ sessionId, messageId, onRatingSubmitted }) => {
    const [rating, setRating] = useState(0);
    const [feedback, setFeedback] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const submitRating = async () => {
        setIsSubmitting(true);
        try {
            const response = await fetch('/chat/ratings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': process.env.REACT_APP_API_KEY
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message_id: messageId,
                    rating: rating,
                    feedback_text: feedback
                })
            });
            
            if (response.ok) {
                onRatingSubmitted?.(rating);
            }
        } catch (error) {
            console.error('Failed to submit rating:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="rating-widget">
            <div className="stars">
                {[1, 2, 3, 4, 5].map(star => (
                    <button
                        key={star}
                        onClick={() => setRating(star)}
                        className={star <= rating ? 'star filled' : 'star'}
                    >
                        ⭐
                    </button>
                ))}
            </div>
            <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Optional feedback..."
                rows={3}
            />
            <button 
                onClick={submitRating}
                disabled={rating === 0 || isSubmitting}
            >
                {isSubmitting ? 'Submitting...' : 'Submit Rating'}
            </button>
        </div>
    );
};
```

## Analytics Integration

### Rating Metrics for Analytics Dashboard

The rating system integrates with the analytics module to provide insights:

- **User Satisfaction Scores**: Average ratings over time
- **Feedback Analysis**: Sentiment analysis of feedback text
- **Quality Trends**: Rating patterns by topic/service area
- **User Engagement**: Rating participation rates

### Composite Metrics

The analytics system can calculate composite metrics combining ratings with other data:

```python
# Example: Service Quality Score
def calculate_service_quality_score(ratings, response_times, accuracy_scores):
    weighted_rating = ratings.mean() * 0.4
    speed_score = (1 - normalize(response_times.mean())) * 0.3
    accuracy_score = accuracy_scores.mean() * 0.3
    return weighted_rating + speed_score + accuracy_score
```

## Best Practices

### 1. Rating Collection
- **Timing**: Ask for ratings after successful interactions
- **Context**: Provide context about what's being rated
- **Optional**: Make ratings optional to avoid friction
- **Feedback**: Encourage but don't require written feedback

### 2. Privacy Considerations
- **Anonymous Options**: Allow anonymous ratings
- **Data Retention**: Implement retention policies for personal data
- **Consent**: Ensure users understand how ratings are used

### 3. Quality Assurance
- **Validation**: Validate rating values (1-5 range)
- **Spam Prevention**: Implement rate limiting
- **Moderation**: Review feedback text for inappropriate content

### 4. Analytics Usage
- **Trends**: Track rating trends over time
- **Segmentation**: Analyze ratings by user groups or topics
- **Actionable Insights**: Use ratings to identify improvement areas
- **Response**: Act on feedback to show users their input matters

## Troubleshooting

### Common Issues

1. **Ratings not appearing**: Check API key permissions (requires `write` permission)
2. **Stats showing zero**: Ensure ratings are being submitted successfully
3. **WebSocket errors**: Verify session IDs match between chat and rating calls
4. **Performance issues**: Check database indexes are properly created

### Monitoring

Monitor these metrics for rating system health:
- Rating submission success rate
- Average response time for rating endpoints
- Database query performance
- User participation rates

## Security Considerations

- **Authentication**: All endpoints require valid API keys
- **Authorization**: Rating submission requires `write` permission
- **Input Validation**: All inputs are validated and sanitized
- **Rate Limiting**: Prevent spam and abuse
- **Audit Trail**: Rating actions are logged for security

## Future Enhancements

Potential future improvements to the rating system:

- **Multi-dimensional Ratings**: Rate different aspects (accuracy, helpfulness, clarity)
- **Comparative Ratings**: Compare responses for A/B testing
- **Automated Quality Scoring**: ML-based quality assessment
- **Real-time Alerts**: Notifications for low ratings or negative feedback
- **Integration with Training**: Use ratings to improve model performance
