"""
Sentiment Analysis utility using VADER for analyzing user messages.
"""

from typing import Dict, Tuple, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    """
    Sentiment analyzer using VADER (Valence Aware Dictionary and sEntiment Reasoner).
    
    VADER is particularly good at analyzing social media text and informal language,
    making it ideal for chat conversations and user feedback.
    """
    
    def __init__(self):
        """Initialize the VADER sentiment analyzer."""
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing:
            - neg: Negative sentiment percentage (0-1)
            - neu: Neutral sentiment percentage (0-1)  
            - pos: Positive sentiment percentage (0-1)
            - compound: Overall sentiment score (-1 to +1)
        """
        if not text or not text.strip():
            return {
                'neg': 0.0,
                'neu': 1.0,
                'pos': 0.0,
                'compound': 0.0
            }
        
        return self.analyzer.polarity_scores(text)
    
    def classify_sentiment(self, compound_score: float) -> str:
        """
        Classify sentiment based on compound score.
        
        Args:
            compound_score: The compound score from VADER analysis
            
        Returns:
            'positive', 'negative', or 'neutral'
        """
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_and_classify(self, text: str) -> Tuple[Dict[str, float], str]:
        """
        Analyze sentiment and classify in one call.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (sentiment_scores, classification)
        """
        scores = self.analyze_sentiment(text)
        classification = self.classify_sentiment(scores['compound'])
        return scores, classification
    
    def calculate_satisfaction_score(self, compound_score: float) -> float:
        """
        Convert compound score to a satisfaction score (1-5 scale).
        
        Args:
            compound_score: The compound score from VADER analysis (-1 to +1)
            
        Returns:
            Satisfaction score on 1-5 scale
        """
        # Convert from -1,1 to 1,5 scale
        # -1 -> 1, 0 -> 3, 1 -> 5
        return round(((compound_score + 1) / 2) * 4 + 1, 1)
    
    def is_escalation_indicator(self, text: str, threshold: float = -0.5) -> bool:
        """
        Check if text indicates need for escalation based on negative sentiment.
        
        Args:
            text: The text to analyze
            threshold: Compound score threshold for escalation (default: -0.5)
            
        Returns:
            True if text indicates strong negative sentiment requiring escalation
        """
        scores = self.analyze_sentiment(text)
        return scores['compound'] <= threshold

# Global instance for reuse
sentiment_analyzer = SentimentAnalyzer()
