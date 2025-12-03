"""
Demo script to test VADER sentiment analysis implementation.
Run this after installing vaderSentiment to verify the implementation works.
"""

from sentiment_analyzer import sentiment_analyzer

def test_sentiment_analysis():
    """Test the sentiment analyzer with various message types."""
    
    test_messages = [
        "This chatbot is amazing! It helped me solve my problem quickly.",
        "I'm really frustrated with this service. Nothing works properly.",
        "The information provided was helpful.",
        "This is the worst experience I've ever had!",
        "Thank you for your assistance.",
        "I don't understand what's happening.",
        "Perfect! Exactly what I needed! 😊",
        "This sucks 😡",
        "The response was okay, not great but not terrible either."
    ]
    
    print("=== VADER Sentiment Analysis Demo ===\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"{i}. Message: \"{message}\"")
        
        # Analyze sentiment
        scores, classification = sentiment_analyzer.analyze_and_classify(message)
        satisfaction = sentiment_analyzer.calculate_satisfaction_score(scores['compound'])
        escalation_needed = sentiment_analyzer.is_escalation_indicator(message)
        
        print(f"   Sentiment Scores: {scores}")
        print(f"   Classification: {classification}")
        print(f"   Satisfaction Score (1-5): {satisfaction}")
        print(f"   Escalation Needed: {escalation_needed}")
        print()

if __name__ == "__main__":
    try:
        test_sentiment_analysis()
    except ImportError as e:
        print(f"Please install vaderSentiment first: pip install vaderSentiment")
        print(f"Error: {e}")
