#!/usr/bin/env python
"""
Test script to demonstrate composite satisfaction metrics integration.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.services import AnalyticsService
from analytics.sentiment_analyzer import sentiment_analyzer

async def test_composite_metrics():
    """
    Test the composite satisfaction metrics functionality.
    """
    print("=== Composite Satisfaction Metrics Test ===\n")
    
    # Test correlation calculation
    print("1. Testing Correlation Calculation:")
    sentiment_scores = [0.8, 0.2, -0.3, 0.5, -0.1]  # Sentiment compound scores
    rating_scores = [5, 4, 2, 4, 3]  # Corresponding user ratings
    
    correlation = AnalyticsService._calculate_correlation(sentiment_scores, rating_scores)
    print(f"   Sentiment scores: {sentiment_scores}")
    print(f"   Rating scores: {rating_scores}")
    print(f"   Correlation coefficient: {correlation}")
    
    # Test satisfaction score conversions
    print("\n2. Testing Satisfaction Score Conversions:")
    test_sentiments = [-0.8, -0.2, 0.0, 0.3, 0.7]
    test_ratings = [1, 2, 3, 4, 5]
    
    for sentiment, rating in zip(test_sentiments, test_ratings):
        sentiment_satisfaction = sentiment_analyzer.calculate_satisfaction_score(sentiment)
        
        # Calculate composite score (70% sentiment, 30% rating)
        composite = round((sentiment_satisfaction * 0.7) + (rating * 0.3), 2)
        
        print(f"   Sentiment: {sentiment:+.1f} → Satisfaction: {sentiment_satisfaction}")
        print(f"   Rating: {rating} → Composite: {composite}")
        print()
    
    # Test edge cases
    print("3. Testing Edge Cases:")
    
    # Empty lists
    correlation_empty = AnalyticsService._calculate_correlation([], [])
    print(f"   Empty lists correlation: {correlation_empty}")
    
    # Single values
    correlation_single = AnalyticsService._calculate_correlation([0.5], [4])
    print(f"   Single value correlation: {correlation_single}")
    
    # Perfect correlation
    correlation_perfect = AnalyticsService._calculate_correlation([0.8, 0.4, 0.0, -0.4], [5, 4, 3, 2])
    print(f"   Perfect correlation: {correlation_perfect}")
    
    # No correlation
    correlation_none = AnalyticsService._calculate_correlation([0.8, -0.8, 0.8, -0.8], [1, 1, 1, 1])
    print(f"   No correlation: {correlation_none}")
    
    print("\n=== Test Complete ===")
    print("\nComposite metrics provide:")
    print("• Validation of sentiment analysis accuracy")
    print("• Balanced satisfaction scoring")
    print("• Confidence indicators for automated analysis")
    print("• Multiple perspectives on user satisfaction")

if __name__ == "__main__":
    asyncio.run(test_composite_metrics())
