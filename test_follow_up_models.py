#!/usr/bin/env python3
"""
Test script to verify the follow-up questions models work correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.follow_up_questions import (
    FollowUpQuestion, 
    FollowUpQuestions, 
    QuestionPriority, 
    QuestionCategory,
    create_simple_question,
    create_questions_from_list
)

def test_follow_up_question():
    """Test individual follow-up question creation."""
    print("Testing FollowUpQuestion...")
    
    question = FollowUpQuestion(
        question="What are the fees for business registration?",
        category=QuestionCategory.MORE_DETAILS,
        priority=QuestionPriority.HIGH,
        confidence=0.95,
        related_sources=["brs_guidelines", "fee_schedule"]
    )
    
    print(f"Created question: {question.question}")
    print(f"Category: {question.category}")
    print(f"Priority: {question.priority}")
    print(f"Confidence: {question.confidence}")
    print(f"Related sources: {question.related_sources}")
    print(f"JSON: {question.dict()}")
    print()

def test_follow_up_questions():
    """Test the FollowUpQuestions container."""
    print("Testing FollowUpQuestions...")
    
    questions = FollowUpQuestions()
    
    # Add questions
    questions.add_question(FollowUpQuestion(
        question="What documents are required?",
        category=QuestionCategory.NEXT_STEPS,
        priority=QuestionPriority.HIGH
    ))
    
    questions.add_question(FollowUpQuestion(
        question="How long does the process take?",
        category=QuestionCategory.MORE_DETAILS,
        priority=QuestionPriority.MEDIUM
    ))
    
    questions.add_question(FollowUpQuestion(
        question="Are there any alternatives?",
        category=QuestionCategory.ALTERNATIVE,
        priority=QuestionPriority.LOW
    ))
    
    print(f"Total questions: {questions.total_count}")
    print(f"High priority questions: {len(questions.get_by_priority(QuestionPriority.HIGH))}")
    print(f"More details questions: {len(questions.get_by_category(QuestionCategory.MORE_DETAILS))}")
    print(f"As simple list: {questions.to_simple_list()}")
    print(f"JSON: {questions.dict()}")
    print()

def test_backward_compatibility():
    """Test backward compatibility functions."""
    print("Testing backward compatibility...")
    
    # Test creating from list
    simple_list = [
        "What are the requirements?",
        "How much does it cost?",
        "Where can I apply?"
    ]
    
    questions = create_questions_from_list(simple_list)
    print(f"Created from list: {questions.total_count} questions")
    print(f"Back to list: {questions.to_simple_list()}")
    print()

def test_json_serialization():
    """Test JSON serialization and deserialization."""
    print("Testing JSON serialization...")
    
    questions = create_questions_from_list([
        "What are the fees for business registration?",
        "How long does the process take?",
        "What documents are required?"
    ])
    
    # Set some additional metadata
    questions.generation_confidence = 0.92
    
    # Test serialization
    json_data = questions.dict()
    print(f"Serialized: {json_data}")
    
    # Test deserialization
    recreated = FollowUpQuestions(**json_data)
    print(f"Recreated total_count: {recreated.total_count}")
    print(f"Recreated confidence: {recreated.generation_confidence}")
    print()

if __name__ == "__main__":
    print("Testing Follow-up Questions Models")
    print("=" * 50)
    
    test_follow_up_question()
    test_follow_up_questions()
    test_backward_compatibility()
    test_json_serialization()
    
    print("All tests completed successfully!")
