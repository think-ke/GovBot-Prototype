"""
Conversation Analytics API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    IntentAnalysis,
    ConversationFlow,
    DocumentRetrieval,
    DropOffData,
    SentimentTrends,
    KnowledgeGaps,
    ConversationSummary,
    DropOffPoint,
    KnowledgeGap,
    NoAnswerStats,
    CitationStats,
    AnswerLengthStats,
)
from ..services import AnalyticsService

router = APIRouter()

@router.get(
    "/summary",
    response_model=ConversationSummary,
    summary="Conversation summary KPIs",
    description="Totals, average turns, and an estimated completion rate for the selected window.",
    responses={
        200: {
            "description": "Summary KPIs",
            "content": {
                "application/json": {
                    "example": {
                        "total_conversations": 1243,
                        "avg_turns": 4.1,
                        "completion_rate": 76.5
                    }
                }
            },
        }
    },
)
async def get_conversation_summary(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation summary KPIs.
    Returns total conversations, average turns per conversation, and an estimated completion rate.
    """
    # Leverage AnalyticsService for underlying computations where possible
    from ..services import AnalyticsService

    flows = await AnalyticsService.get_conversation_turn_analysis(db, start_date, end_date)

    # Compute totals using Chats within range
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    from sqlalchemy import func, and_
    from ..models import Chat, ChatMessage
    from sqlalchemy.sql import select

    # Total conversations
    total_q = select(func.count(Chat.id)).where(
        and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
    )
    total_res = await db.execute(total_q)
    total_conversations = total_res.scalar() or 0

    # Average turns (messages per chat)
    turns_q = select(Chat.id, func.count(ChatMessage.id).label("msg_count")).join(ChatMessage).where(
        and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
    ).group_by(Chat.id)
    turns_res = await db.execute(turns_q)
    rows = turns_res.fetchall()
    avg_turns = (sum(r.msg_count for r in rows) / len(rows)) if rows else 0.0

    # Completion rate heuristic: reuse completion_rate from flows buckets (weighted average by bucket size not available here), fallback to mean
    completion_rate = (sum(f.completion_rate for f in flows) / len(flows)) if flows else 0.0

    return ConversationSummary(
        total_conversations=total_conversations,
        avg_turns=round(avg_turns, 2),
        completion_rate=round(completion_rate, 1)
    )

@router.get(
    "/flows",
    response_model=List[ConversationFlow],
    summary="Conversation flow analysis",
    description="Turn-number buckets with completion and abandonment rates; averages are illustrative in dev.",
)
async def get_conversation_flows(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation flow analysis.
    
    Analyzes:
    - Turn patterns and completion rates
    - Drop-off points in conversations
    - Multi-turn success rates
    """
    return await AnalyticsService.get_conversation_turn_analysis(db, start_date, end_date)

@router.get(
    "/intents",
    response_model=List[IntentAnalysis],
    summary="Intent analysis (demo)",
    description="Most common intents with success rates. Placeholder values until NLP classification is wired.",
)
async def get_intent_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    limit: int = Query(20, description="Maximum number of intents to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get intent analysis from conversations.
    
    Returns:
    - Most common user intents
    - Intent success rates
    - Query classification patterns
    """
    # Placeholder - would require NLP intent classification
    return [
        IntentAnalysis(
            intent="document_request",
            frequency=150,
            success_rate=85.5,
            average_turns=2.3
        ),
        IntentAnalysis(
            intent="service_inquiry",
            frequency=120,
            success_rate=78.2,
            average_turns=3.1
        ),
        IntentAnalysis(
            intent="technical_support",
            frequency=85,
            success_rate=65.8,
            average_turns=4.2
        )
    ]

@router.get(
    "/document-retrieval",
    response_model=List[DocumentRetrieval],
    summary="Document retrieval patterns (demo)",
    description="Top document types and success rates. Demo values in dev.",
)
async def get_document_retrieval_analysis(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get document retrieval patterns and success rates.
    
    Analyzes:
    - Most accessed document types
    - RAG retrieval success rates
    - Knowledge gap identification
    """
    # Placeholder - would analyze document access patterns
    return [
        DocumentRetrieval(
            document_type="government_forms",
            access_frequency=200,
            success_rate=92.5,
            collection_id="gov_forms_2024"
        ),
        DocumentRetrieval(
            document_type="policy_documents",
            access_frequency=180,
            success_rate=88.7,
            collection_id="policies_2024"
        ),
        DocumentRetrieval(
            document_type="service_guides",
            access_frequency=160,
            success_rate=94.2,
            collection_id="guides_2024"
        )
    ]

@router.get(
    "/drop-offs",
    response_model=DropOffData,
    summary="Drop-off analysis (demo)",
    description="Common abandonment points by turn and typical triggers.",
)
async def get_conversation_drop_offs(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation drop-off analysis.
    
    Identifies:
    - Common abandonment points
    - Turn numbers with highest drop-off
    - Escalation triggers
    """
    return DropOffData(
        drop_off_points=[
            DropOffPoint(turn=1, abandonment_rate=15.2),
            DropOffPoint(turn=2, abandonment_rate=8.7),
            DropOffPoint(turn=3, abandonment_rate=12.1),
            DropOffPoint(turn=5, abandonment_rate=18.9),
        ],
        common_triggers=[
            "complex_query",
            "no_relevant_results",
            "technical_issues",
        ],
    )

@router.get(
    "/sentiment-trends",
    response_model=SentimentTrends,
    summary="Sentiment trends (demo)",
    description="Distribution of positive/neutral/negative over the period.",
)
async def get_conversation_sentiment_trends(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sentiment trends in conversations.
    
    Tracks:
    - Sentiment progression during conversations
    - Satisfaction indicators
    - Emotional journey patterns
    """
    return SentimentTrends(
        sentiment_distribution={
            "positive": 65.5,
            "neutral": 28.3,
            "negative": 6.2,
        },
        satisfaction_indicators=[
            "thank_you_expressions",
            "successful_completion",
            "positive_feedback",
        ],
    )

@router.get(
    "/knowledge-gaps",
    response_model=KnowledgeGaps,
    summary="Knowledge gaps (demo)",
    description="Queries/topics with low success that may need content improvements.",
)
async def get_knowledge_gaps(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    threshold: float = Query(0.3, description="Success rate threshold for identifying gaps"),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify knowledge gaps in the system.
    
    Finds:
    - Queries with poor retrieval results
    - Common unanswered questions
    - Content improvement opportunities
    """
    return KnowledgeGaps(
        knowledge_gaps=[
            KnowledgeGap(
                topic="tax_exemption_process",
                query_frequency=45,
                success_rate=62.5,  # percentage
                example_queries=[
                    "How to apply for tax exemption?",
                    "Tax exemption eligibility criteria",
                ],
            ),
            KnowledgeGap(
                topic="business_permit_renewal",
                query_frequency=38,
                success_rate=71.2,  # percentage
                example_queries=[
                    "Business permit renewal process",
                    "Documents needed for permit renewal",
                ],
            ),
        ],
        recommendations=[
            "Add more content about tax exemption processes",
            "Create detailed business permit guides",
        ],
    )

@router.get(
    "/no-answer",
    response_model=NoAnswerStats,
    summary="No‑answer rate and examples",
    description="Heuristic estimate of no‑answer responses plus example snippets and top error triggers.",
    responses={
        200: {
            "description": "No‑answer stats",
            "content": {
                "application/json": {
                    "example": {
                        "rate": 6.2,
                        "examples": [
                            {
                                "chat_id": 3574,
                                "message_id": "abc-123",
                                "snippet": "I'm sorry, but I don't have that information."
                            }
                        ],
                        "top_triggers": ["missing_policy", "unsupported_service"]
                    }
                }
            },
        }
    },
)
async def get_no_answer_stats(
    examples: int = Query(5, description="Number of example snippets to include"),
    db: AsyncSession = Depends(get_db)
):
    """
    Estimate no-answer rate based on assistant message phrasing and error events.
    Returns percentage rate, example snippets, and top triggers.
    """
    data = await AnalyticsService.get_no_answer_stats(db, examples_limit=examples)
    return NoAnswerStats(**data)

@router.get(
    "/citations",
    response_model=CitationStats,
    summary="Citation coverage",
    description="Share of assistant answers that include sources and average citations per answer; grouped by collection where possible.",
    responses={
        200: {
            "description": "Citation coverage",
            "content": {
                "application/json": {
                    "example": {
                        "coverage_pct": 72.4,
                        "avg_citations": 2.1,
                        "by_collection": [
                            {"collection_id": "odpc", "coverage_pct": 80.0, "avg_citations": 2.3}
                        ]
                    }
                }
            },
        }
    },
)
async def get_citation_stats(
    db: AsyncSession = Depends(get_db)
):
    """Citation coverage (overall and per-collection) derived from assistant message sources."""
    data = await AnalyticsService.get_citation_stats(db)
    return CitationStats(**data)

@router.get(
    "/answer-length",
    response_model=AnswerLengthStats,
    summary="Answer length distribution",
    description="Average, median, and word-count buckets for assistant messages.",
    responses={
        200: {
            "description": "Answer length stats",
            "content": {
                "application/json": {
                    "example": {
                        "avg_words": 85.3,
                        "median_words": 72.0,
                        "distribution": [
                            {"bucket": "0-20", "count": 15, "percentage": 3.2},
                            {"bucket": "21-50", "count": 120, "percentage": 25.0}
                        ]
                    }
                }
            },
        }
    },
)
async def get_answer_length_stats(
    db: AsyncSession = Depends(get_db)
):
    """Answer length distribution and central tendencies for assistant messages."""
    data = await AnalyticsService.get_answer_length_stats(db)
    return AnswerLengthStats(**data)
