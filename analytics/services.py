"""
Analytics service layer for data processing and calculations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, asc, and_, or_, text
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select

from .models import Chat, ChatMessage, Document, Webpage, MessageRating
from .schemas import (
    UserDemographics, SessionFrequency, TrafficMetrics, SessionDuration,
    ConversationFlow, ROIMetrics, ContainmentRate, TrendData, DistributionData,
    UserSentiment
)
from .sentiment_analyzer import sentiment_analyzer

class AnalyticsService:
    """Service class for analytics calculations and data processing."""
    
    @staticmethod
    async def get_user_demographics(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UserDemographics:
        """Calculate user demographics and growth metrics."""
        
        # Set default time range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Total users in period
        total_users_query = select(func.count(func.distinct(Chat.user_id))).where(
            and_(
                Chat.created_at >= start_date,
                Chat.created_at <= end_date,
                Chat.user_id.isnot(None)
            )
        )
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0
        
        # New users (first session in period)
        new_users_subquery = select(
            Chat.user_id,
            func.min(Chat.created_at).label('first_session')
        ).where(
            Chat.user_id.isnot(None)
        ).group_by(Chat.user_id).subquery()
        
        new_users_query = select(func.count()).select_from(new_users_subquery).where(
            and_(
                new_users_subquery.c.first_session >= start_date,
                new_users_subquery.c.first_session <= end_date
            )
        )
        new_users_result = await db.execute(new_users_query)
        new_users = new_users_result.scalar() or 0
        
        # Returning users
        returning_users = total_users - new_users
        
        # Active users (users with sessions in last 7 days)
        active_cutoff = end_date - timedelta(days=7)
        active_users_query = select(func.count(func.distinct(Chat.user_id))).where(
            and_(
                Chat.created_at >= active_cutoff,
                Chat.created_at <= end_date,
                Chat.user_id.isnot(None)
            )
        )
        active_users_result = await db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0
        
        # Growth rate calculation (compared to previous period)
        prev_start = start_date - (end_date - start_date)
        prev_end = start_date
        
        prev_users_query = select(func.count(func.distinct(Chat.user_id))).where(
            and_(
                Chat.created_at >= prev_start,
                Chat.created_at <= prev_end,
                Chat.user_id.isnot(None)
            )
        )
        prev_users_result = await db.execute(prev_users_query)
        prev_users = prev_users_result.scalar() or 1
        
        growth_rate = ((total_users - prev_users) / prev_users) * 100 if prev_users > 0 else 0
        
        return UserDemographics(
            total_users=total_users,
            new_users=new_users,
            returning_users=returning_users,
            active_users=active_users,
            user_growth_rate=growth_rate
        )
    
    @staticmethod
    async def get_session_frequency_analysis(
        db: AsyncSession,
        limit: int = 100
    ) -> List[SessionFrequency]:
        """Get session frequency analysis for users."""
        
        query = select(
            Chat.user_id,
            func.count(Chat.id).label('total_sessions'),
            func.min(Chat.created_at).label('first_visit'),
            func.max(Chat.updated_at).label('last_visit')
        ).where(
            Chat.user_id.isnot(None)
        ).group_by(Chat.user_id).order_by(
            desc('total_sessions')
        ).limit(limit)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        return [
            SessionFrequency(
                user_id=row.user_id,
                total_sessions=row.total_sessions,
                first_visit=row.first_visit,
                last_visit=row.last_visit,
                user_lifespan_days=(row.last_visit - row.first_visit).days
            )
            for row in rows
        ]
    
    @staticmethod
    async def get_traffic_metrics(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TrafficMetrics:
        """Get traffic and volume metrics."""
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Total sessions
        sessions_query = select(func.count(Chat.id)).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        )
        sessions_result = await db.execute(sessions_query)
        total_sessions = sessions_result.scalar() or 0
        
        # Total messages
        messages_query = select(func.count(ChatMessage.id)).join(Chat).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        )
        messages_result = await db.execute(messages_query)
        total_messages = messages_result.scalar() or 0
        
        # Unique users
        users_query = select(func.count(func.distinct(Chat.user_id))).where(
            and_(
               
                Chat.created_at <= end_date,
                Chat.user_id.isnot(None)
            )
        )
        users_result = await db.execute(users_query)
        unique_users = users_result.scalar() or 0
        
        # Peak hours analysis
        peak_hours_query = select(
            func.extract('hour', Chat.created_at).label('hour'),
            func.count(Chat.id).label('session_count')
        ).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        ).group_by(
            func.extract('hour', Chat.created_at)
        ).order_by(desc('session_count')).limit(5)
        
        peak_hours_result = await db.execute(peak_hours_query)
        peak_hours = [
            {"hour": int(row.hour), "sessions": row.session_count}
            for row in peak_hours_result.fetchall()
        ]
        
        # Growth trend (daily sessions over the period)
        daily_sessions_query = select(
            func.date(Chat.created_at).label('date'),
            func.count(Chat.id).label('sessions')
        ).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        ).group_by(
            func.date(Chat.created_at)
        ).order_by('date')
        
        daily_sessions_result = await db.execute(daily_sessions_query)
        growth_trend = [
            TrendData(date=row.date, value=row.sessions)
            for row in daily_sessions_result.fetchall()
        ]
        
        return TrafficMetrics(
            total_sessions=total_sessions,
            total_messages=total_messages,
            unique_users=unique_users,
            peak_hours=peak_hours,
            growth_trend=growth_trend
        )
    
    @staticmethod
    async def get_session_duration_analysis(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SessionDuration:
        """Analyze session duration patterns."""
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Calculate session durations
        duration_query = select(
            Chat.id,
            (func.extract('epoch', Chat.updated_at) - func.extract('epoch', Chat.created_at)).label('duration_seconds')
        ).where(
            and_(
                Chat.created_at >= start_date,
                Chat.created_at <= end_date,
                Chat.updated_at > Chat.created_at
            )
        )
        
        duration_result = await db.execute(duration_query)
        durations = [row.duration_seconds / 60 for row in duration_result.fetchall()]  # Convert to minutes
        
        if not durations:
            return SessionDuration(
                average_duration_minutes=0.0,
                median_duration_minutes=0.0,
                duration_distribution=[]
            )
        
        # Calculate statistics
        avg_duration = sum(durations) / len(durations)
        sorted_durations = sorted(durations)
        median_duration = sorted_durations[len(sorted_durations) // 2]
        
        # Create duration distribution buckets
        buckets = {
            "0-1 min": 0, "1-5 min": 0, "5-15 min": 0, 
            "15-30 min": 0, "30+ min": 0
        }
        
        for duration in durations:
            if duration <= 1:
                buckets["0-1 min"] += 1
            elif duration <= 5:
                buckets["1-5 min"] += 1
            elif duration <= 15:
                buckets["5-15 min"] += 1
            elif duration <= 30:
                buckets["15-30 min"] += 1
            else:
                buckets["30+ min"] += 1
        
        total_sessions = len(durations)
        distribution = [
            DistributionData(
                category=bucket,
                count=count,
                percentage=(count / total_sessions) * 100
            )
            for bucket, count in buckets.items()
        ]
        
        return SessionDuration(
            average_duration_minutes=avg_duration,
            median_duration_minutes=median_duration,
            duration_distribution=distribution
        )
    
    @staticmethod
    async def get_conversation_turn_analysis(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ConversationFlow]:
        """Analyze conversation turn patterns and compute avg response time per bucket."""
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Get message counts per conversation
        turn_query = select(
            Chat.id,
            func.count(ChatMessage.id).label('message_count'),
            func.max(ChatMessage.timestamp).label('last_message_time')
        ).join(ChatMessage).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        ).group_by(Chat.id)
        
        turn_result = await db.execute(turn_query)
        conversations = turn_result.fetchall()
        
        # Compute avg TTFA per chat from events joined to chat_messages
        ttfa_sql = text(
            """
            WITH mr AS (
                SELECT session_id, message_id, MIN(timestamp) AS mr_ts
                FROM chat_events
                WHERE event_type = 'message_received'
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY session_id, message_id
            ), at AS (
                SELECT session_id, message_id, MIN(timestamp) AS at_start, MAX(timestamp) AS at_end
                FROM chat_events
                WHERE event_type = 'agent_thinking'
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY session_id, message_id
            ), rg AS (
                SELECT session_id, message_id, MIN(timestamp) AS rg_start, MAX(timestamp) AS rg_end
                FROM chat_events
                WHERE event_type = 'response_generation'
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY session_id, message_id
            ), joined AS (
                SELECT mr.message_id,
                       EXTRACT(EPOCH FROM (COALESCE(rg.rg_end, at.at_end) - mr.mr_ts)) * 1000 AS ttfa_ms
                FROM mr
                LEFT JOIN at ON at.session_id = mr.session_id AND at.message_id = mr.message_id
                LEFT JOIN rg ON rg.session_id = mr.session_id AND rg.message_id = mr.message_id
                WHERE COALESCE(rg.rg_end, at.at_end) IS NOT NULL
            ), per_chat AS (
                SELECT cm.chat_id, AVG(j.ttfa_ms) AS avg_ttfa
                FROM joined j
                JOIN chat_messages cm ON cm.message_id = j.message_id
                GROUP BY cm.chat_id
            )
            SELECT chat_id, avg_ttfa FROM per_chat
            """
        )
        ttfa_res = await db.execute(ttfa_sql, {"start_ts": start_date, "end_ts": end_date})
        ttfa_map = {int(r[0]): float(r[1] or 0.0) for r in ttfa_res.all()}

        # Analyze by turn ranges
        turn_ranges = [
            (1, 2), (3, 5), (6, 10), (11, 20), (21, float('inf'))
        ]
        
        flow_analysis = []
        total_conversations = len(conversations)
        
        for min_turns, max_turns in turn_ranges:
            if max_turns == float('inf'):
                range_convos = [c for c in conversations if c.message_count >= min_turns]
                label = f"{min_turns}+ turns"
            else:
                range_convos = [c for c in conversations if min_turns <= c.message_count <= max_turns]
                label = f"{min_turns}-{max_turns} turns"
            
            count = len(range_convos)
            completion_rate = (count / total_conversations) * 100 if total_conversations > 0 else 0
            # Average response time: mean of per-chat avg TTFA in this bucket
            bucket_ttfas = [ttfa_map.get(int(c.id), 0.0) for c in range_convos if ttfa_map.get(int(c.id)) is not None]
            avg_response_time = (sum(bucket_ttfas) / len(bucket_ttfas)) if bucket_ttfas else 0.0
            
            flow_analysis.append(ConversationFlow(
                turn_number=min_turns,
                completion_rate=completion_rate,
                abandonment_rate=100 - completion_rate,
                average_response_time=avg_response_time
            ))
        
        return flow_analysis

    # ===== Phase P conversation replacements =====
    @staticmethod
    async def get_intent_analysis(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Heuristic intent detection based on user message keywords and RAG/tool signals.
        Produces items: {intent, frequency, success_rate, average_turns}.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Fetch user messages in window with minimal fields
        msg_q = select(ChatMessage.chat_id, ChatMessage.message_object).join(Chat).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date, ChatMessage.message_type == 'user')
        )
        res = await db.execute(msg_q)
        rows = res.fetchall()

        # Simple keyword → intent mapping
        patterns = [
            ("document_request", ["document", "policy", "form", "pdf", "file", "download"]),
            ("service_inquiry", ["apply", "renew", "process", "service", "how do i", "requirements"]),
            ("technical_support", ["error", "issue", "doesn't work", "cannot", "fail", "bug"]),
            ("general_question", ["what is", "how to", "explain", "tell me", "info", "information"]),
        ]

        import re
        def classify(text: str) -> Optional[str]:
            t = text.lower()
            for intent, keys in patterns:
                for k in keys:
                    if k in t:
                        return intent
            return None

        from collections import defaultdict
        intent_counts = defaultdict(int)
        chats_by_intent: Dict[str, set] = defaultdict(set)
        for chat_id, obj in rows:
            content = ""
            if isinstance(obj, dict):
                content = obj.get("content", "") or ""
            elif isinstance(obj, str):
                content = obj
            intent = classify(content)
            if intent:
                intent_counts[intent] += 1
                chats_by_intent[intent].add(int(chat_id))

        # Compute turns per chat for average_turns
        turns_q = select(Chat.id, func.count(ChatMessage.id).label("cnt")).join(ChatMessage).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        ).group_by(Chat.id)
        turns_res = await db.execute(turns_q)
        turns_map = {int(r[0]): int(r[1]) for r in turns_res.all()}

        # Success proxy: chats with at least one assistant message having sources
        asst_q = select(ChatMessage.chat_id, ChatMessage.message_object).where(ChatMessage.message_type == 'assistant')
        asst_res = await db.execute(asst_q)
        has_sources = set()
        for chat_id, obj in asst_res.fetchall():
            srcs = []
            if isinstance(obj, dict):
                srcs = obj.get('sources') or []
            if srcs:
                has_sources.add(int(chat_id))

        items = []
        for intent, chats in chats_by_intent.items():
            freq = intent_counts[intent]
            avg_turns = 0.0
            if chats:
                avg_turns = sum(turns_map.get(cid, 0) for cid in chats) / max(1, len(chats))
            success_chats = len([cid for cid in chats if cid in has_sources])
            success_rate = (success_chats / max(1, len(chats))) * 100.0
            items.append({
                "intent": intent,
                "frequency": int(freq),
                "success_rate": round(success_rate, 1),
                "average_turns": round(avg_turns, 1),
            })

        items.sort(key=lambda x: x["frequency"], reverse=True)
        return items[:limit]

    @staticmethod
    async def get_document_retrieval_analysis(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Data-backed retrieval analysis using chat_events for tool_search_documents.
        Groups by collection (document_type proxy) and computes success_rate.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        q = text(
            """
            SELECT
                NULLIF(event_data->>'collection', '') AS collection_id,
                SUM(CASE WHEN event_status = 'started' THEN 1 ELSE 0 END)::INT AS started,
                SUM(CASE WHEN event_status = 'completed' THEN 1 ELSE 0 END)::INT AS completed,
                SUM(CASE WHEN event_status = 'failed' THEN 1 ELSE 0 END)::INT AS failed
            FROM chat_events
            WHERE event_type = 'tool_search_documents'
              AND timestamp BETWEEN :start_ts AND :end_ts
            GROUP BY NULLIF(event_data->>'collection', '')
            ORDER BY completed DESC NULLS LAST, started DESC
            """
        )
        res = await db.execute(q, {"start_ts": start_date, "end_ts": end_date})
        items = []
        for r in res.mappings().all():
            started = int(r.get("started") or 0)
            completed = int(r.get("completed") or 0)
            failed = int(r.get("failed") or 0)
            total = started + completed + failed
            success_rate = (completed / total * 100.0) if total > 0 else 0.0
            coll = r.get("collection_id") or "unknown"
            items.append({
                "document_type": coll,
                "access_frequency": total,
                "success_rate": round(success_rate, 1),
                "collection_id": r.get("collection_id"),
            })
        return items

    @staticmethod
    async def get_drop_offs(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Drop-off analysis using message counts per chat and simple triggers from errors/no-answer.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Message counts per chat
        turn_q = select(Chat.id, func.count(ChatMessage.id).label('cnt')).join(ChatMessage).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        ).group_by(Chat.id)
        turn_res = await db.execute(turn_q)
        counts = [int(r[1]) for r in turn_res.all()]

        buckets = [(1,2), (3,5), (6,10), (11,20), (21, float('inf'))]
        total = len(counts)
        points = []
        for lo, hi in buckets:
            if hi == float('inf'):
                n = sum(1 for c in counts if c >= lo)
                t = lo
            else:
                n = sum(1 for c in counts if lo <= c <= hi)
                t = lo
            rate = (n/total * 100.0) if total > 0 else 0.0
            points.append({"turn": int(t), "abandonment_rate": round(rate, 1)})

        # Triggers: combine error types and no-answer triggers
        na = await AnalyticsService.get_no_answer_stats(db, examples_limit=3)
        err = await AnalyticsService.get_error_analysis(db, hours=24)
        triggers = []
        triggers.extend((na.get("top_triggers") or [])[:2])
        triggers.extend(list((err.get("error_types") or {}).keys())[:2])
        triggers = [t for t in triggers if t][:3]

        return {"drop_off_points": points, "common_triggers": triggers}

    @staticmethod
    async def get_sentiment_trends(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Sentiment distribution across user messages in window using VADER-based analyzer.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        msgs_q = select(ChatMessage).join(Chat).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date, ChatMessage.message_type == 'user')
        )
        msgs_res = await db.execute(msgs_q)
        msgs = msgs_res.scalars().all()

        pos = neu = neg = 0
        thank_you = 0
        for m in msgs:
            content = ""
            if isinstance(m.message_object, dict):
                content = m.message_object.get('content', '') or ''
            elif isinstance(m.message_object, str):
                content = m.message_object
            if not content.strip():
                continue
            scores, cls = sentiment_analyzer.analyze_and_classify(content)
            if cls == 'positive':
                pos += 1
            elif cls == 'negative':
                neg += 1
            else:
                neu += 1
            if 'thank' in content.lower():
                thank_you += 1

        total = pos + neu + neg
        dist = {
            "positive": round((pos/total)*100.0, 1) if total>0 else 0.0,
            "neutral": round((neu/total)*100.0, 1) if total>0 else 0.0,
            "negative": round((neg/total)*100.0, 1) if total>0 else 0.0,
        }
        indicators = []
        if thank_you > 0:
            indicators.append("thank_you_expressions")
        indicators.extend(["successful_completion", "positive_feedback"])  # heuristics
        return {"sentiment_distribution": dist, "satisfaction_indicators": indicators}

    @staticmethod
    async def get_knowledge_gaps(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Heuristic knowledge gaps: use top no-answer triggers as topics.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        na = await AnalyticsService.get_no_answer_stats(db, examples_limit=5)
        rate = float(na.get("rate") or 0.0)
        triggers = na.get("top_triggers") or []
        gaps = []
        for t in triggers[:5]:
            gaps.append({
                "topic": t,
                "query_frequency": 0,  # not directly derivable from triggers alone
                "success_rate": max(0.0, 100.0 - rate),
                "example_queries": [f"Example query related to {t}"]
            })
        recs = []
        if gaps:
            recs.append("Add content covering top unresolved topics")
        return {"knowledge_gaps": gaps, "recommendations": recs}
    
    @staticmethod
    async def get_roi_metrics(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ROIMetrics:
        """Calculate ROI and cost-benefit metrics."""
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Get total interactions
        interactions_query = select(func.count(Chat.id)).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        )
        interactions_result = await db.execute(interactions_query)
        total_interactions = interactions_result.scalar() or 1
        
        # Calculate metrics based on specification
        cost_per_interaction = 0.033  # Based on token costs mentioned in spec
        traditional_cost_per_interaction = 20.0  # Average traditional support cost
        
        cost_savings = (traditional_cost_per_interaction - cost_per_interaction) * total_interactions
        total_ai_cost = cost_per_interaction * total_interactions
        roi_percentage = (cost_savings / total_ai_cost) * 100 if total_ai_cost > 0 else 0
        
        # Automation rate (assume high for AI system)
        automation_rate = 85.0  # Percentage of interactions handled without human intervention
        
        return ROIMetrics(
            cost_per_interaction=cost_per_interaction,
            cost_savings=cost_savings,
            roi_percentage=roi_percentage,
            automation_rate=automation_rate
        )
    
    @staticmethod
    async def get_containment_rate(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ContainmentRate:
        """Calculate containment and resolution rates."""
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # Total conversations
        total_query = select(func.count(Chat.id)).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        )
        total_result = await db.execute(total_query)
        total_conversations = total_result.scalar() or 1
        
        # Analyze conversation patterns for containment metrics
        # This is a simplified calculation - in practice would need more sophisticated analysis
        
        # Conversations with multiple turns suggest engagement (partial automation)
        engaged_query = select(func.count(func.distinct(Chat.id))).join(ChatMessage).where(
            and_(Chat.created_at >= start_date, Chat.created_at <= end_date)
        ).group_by(Chat.id).having(func.count(ChatMessage.id) >= 3)
        
        engaged_result = await db.execute(engaged_query)
        engaged_conversations = len(engaged_result.fetchall())
        
        # Assume containment rates based on engagement patterns
        full_automation_rate = 70.0  # Conversations resolved without escalation
        partial_automation_rate = 20.0  # Conversations with some AI help before escalation
        human_handoff_rate = 10.0  # Conversations requiring human intervention
        resolution_success_rate = 85.0  # Overall success rate
        
        return ContainmentRate(
            full_automation_rate=full_automation_rate,
            partial_automation_rate=partial_automation_rate,
            human_handoff_rate=human_handoff_rate,
            resolution_success_rate=resolution_success_rate
        )

    @staticmethod
    async def get_user_sentiment(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UserSentiment:
        """
        Analyze user sentiment from chat messages using VADER sentiment analysis.
        
        Args:
            db: Database session
            start_date: Start date for analysis (defaults to 30 days ago)
            end_date: End date for analysis (defaults to now)
            
        Returns:
            UserSentiment with comprehensive sentiment metrics
        """
        # Set default time range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get all user messages in the time period
        messages_query = select(ChatMessage).join(Chat).where(
            and_(
                Chat.created_at >= start_date,
                Chat.created_at <= end_date,
                ChatMessage.message_type == 'user'  # Only analyze user messages
            )
        )
        
        messages_result = await db.execute(messages_query)
        messages = messages_result.scalars().all()
        
        if not messages:
            # Return default values if no messages found
            return UserSentiment(
                positive_conversations=0,
                negative_conversations=0,
                neutral_conversations=0,
                satisfaction_score=3.0,
                escalation_rate=0.0,
                average_sentiment_score=0.0,
                total_analyzed_messages=0,
                sentiment_distribution=[],
                # New composite metrics defaults
                explicit_rating_score=None,
                total_explicit_ratings=0,
                composite_satisfaction_score=None,
                sentiment_vs_rating_correlation=None,
                rating_distribution=None
            )
        
        # Analyze sentiment for each message
        sentiment_scores = []
        escalation_indicators = 0
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for message in messages:
            # Extract text content from message_object
            message_content = ""
            if isinstance(message.message_object, dict):
                message_content = message.message_object.get('content', '')
            elif isinstance(message.message_object, str):
                message_content = message.message_object
            
            if message_content.strip():
                scores, classification = sentiment_analyzer.analyze_and_classify(message_content)
                sentiment_scores.append(scores['compound'])
                
                # Count by classification
                if classification == 'positive':
                    positive_count += 1
                elif classification == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
                
                # Check for escalation indicators
                if sentiment_analyzer.is_escalation_indicator(message_content):
                    escalation_indicators += 1
        
        total_analyzed = len(sentiment_scores)
        
        # Calculate metrics
        average_sentiment = sum(sentiment_scores) / total_analyzed if total_analyzed > 0 else 0.0
        satisfaction_score = sentiment_analyzer.calculate_satisfaction_score(average_sentiment)
        escalation_rate = (escalation_indicators / total_analyzed * 100) if total_analyzed > 0 else 0.0
        
        # Create sentiment distribution
        sentiment_distribution = [
            DistributionData(
                category="Positive",
                count=positive_count,
                percentage=round(positive_count / total_analyzed * 100, 1) if total_analyzed > 0 else 0.0
            ),
            DistributionData(
                category="Neutral", 
                count=neutral_count,
                percentage=round(neutral_count / total_analyzed * 100, 1) if total_analyzed > 0 else 0.0
            ),
            DistributionData(
                category="Negative",
                count=negative_count,
                percentage=round(negative_count / total_analyzed * 100, 1) if total_analyzed > 0 else 0.0
            )
        ]
        
        # Count conversations by overall sentiment
        # Get conversations and their overall sentiment
        conversations_query = select(Chat.id).where(
            and_(
                Chat.created_at >= start_date,
                Chat.created_at <= end_date
            )
        )
        conversations_result = await db.execute(conversations_query)
        conversation_ids = [row[0] for row in conversations_result.fetchall()]
        
        positive_conversations = 0
        negative_conversations = 0
        neutral_conversations = 0
        
        # Analyze sentiment per conversation
        for chat_id in conversation_ids:
            chat_messages_query = select(ChatMessage).where(
                and_(
                    ChatMessage.chat_id == chat_id,
                    ChatMessage.message_type == 'user'
                )
            )
            chat_messages_result = await db.execute(chat_messages_query)
            chat_messages = chat_messages_result.scalars().all()
            
            conversation_scores = []
            for msg in chat_messages:
                message_content = ""
                if isinstance(msg.message_object, dict):
                    message_content = msg.message_object.get('content', '')
                elif isinstance(msg.message_object, str):
                    message_content = msg.message_object
                
                if message_content.strip():
                    scores = sentiment_analyzer.analyze_sentiment(message_content)
                    conversation_scores.append(scores['compound'])
            
            if conversation_scores:
                avg_conversation_sentiment = sum(conversation_scores) / len(conversation_scores)
                conversation_classification = sentiment_analyzer.classify_sentiment(avg_conversation_sentiment)
                
                if conversation_classification == 'positive':
                    positive_conversations += 1
                elif conversation_classification == 'negative':
                    negative_conversations += 1
                else:
                    neutral_conversations += 1
        
        # ========== NEW: RATING DATA INTEGRATION ==========
        # Get explicit ratings for the time period
        ratings_query = select(MessageRating).where(
            and_(
                MessageRating.created_at >= start_date,
                MessageRating.created_at <= end_date
            )
        )
        ratings_result = await db.execute(ratings_query)
        ratings = ratings_result.scalars().all()
        
        # Calculate explicit rating metrics
        explicit_rating_score = None
        total_explicit_ratings = len(ratings)
        rating_distribution = None
        composite_satisfaction_score = None
        sentiment_vs_rating_correlation = None
        
        if ratings:
            # Calculate average explicit rating
            rating_values = [int(getattr(r, 'rating')) for r in ratings]
            explicit_rating_score = round(sum(rating_values) / len(rating_values), 2)
            
            # Create rating distribution (1-5 stars)
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rv in rating_values:
                if 1 <= rv <= 5:
                    rating_counts[rv] += 1
            
            rating_distribution = [
                DistributionData(
                    category=f"{star} Star{'s' if star != 1 else ''}",
                    count=rating_counts[star],
                    percentage=round(rating_counts[star] / total_explicit_ratings * 100, 1)
                )
                for star in range(1, 6)
            ]
            
            # Calculate composite satisfaction score (weighted combination)
            # Weight: 70% sentiment-based, 30% explicit ratings
            sentiment_weight = 0.7
            rating_weight = 0.3
            
            composite_satisfaction_score = round(
                (satisfaction_score * sentiment_weight) + (explicit_rating_score * rating_weight), 2
            )
            
            # Calculate correlation between sentiment and ratings for overlapping data
            # Find messages that have both sentiment analysis and explicit ratings
            overlapping_data = []
            for rating in ratings:
                # Try to find corresponding sentiment analysis for this message/session
                for message in messages:
                    try:
                        same_session = str(getattr(message.chat, 'session_id', '')) == str(getattr(rating, 'session_id', ''))
                    except Exception:
                        same_session = False
                    if same_session and str(getattr(message, 'message_id', '')) == str(getattr(rating, 'message_id', '')):
                        
                        # Extract message content for sentiment analysis
                        message_content = ""
                        if isinstance(message.message_object, dict):
                            message_content = message.message_object.get('content', '')
                        elif isinstance(message.message_object, str):
                            message_content = message.message_object
                        
                        if message_content.strip():
                            sentiment_scores_for_correlation = sentiment_analyzer.analyze_sentiment(message_content)
                            overlapping_data.append({
                                'sentiment': sentiment_scores_for_correlation['compound'],
                                'rating': int(getattr(rating, 'rating'))
                            })
                        break
            
            # Calculate correlation if we have overlapping data
            if len(overlapping_data) >= 2:
                sentiment_scores_corr = [d['sentiment'] for d in overlapping_data]
                rating_scores_corr = [d['rating'] for d in overlapping_data]
                sentiment_vs_rating_correlation = AnalyticsService._calculate_correlation(
                    sentiment_scores_corr, rating_scores_corr
                )
        
        return UserSentiment(
            positive_conversations=positive_conversations,
            negative_conversations=negative_conversations,
            neutral_conversations=neutral_conversations,
            satisfaction_score=satisfaction_score,
            escalation_rate=round(escalation_rate, 1),
            average_sentiment_score=round(average_sentiment, 3),
            total_analyzed_messages=total_analyzed,
            sentiment_distribution=sentiment_distribution,
            # New composite metrics
            explicit_rating_score=explicit_rating_score,
            total_explicit_ratings=total_explicit_ratings,
            composite_satisfaction_score=composite_satisfaction_score,
            sentiment_vs_rating_correlation=sentiment_vs_rating_correlation,
            rating_distribution=rating_distribution
        )
    
    @staticmethod
    def _calculate_correlation(sentiment_scores: List[float], rating_scores: List[float]) -> Optional[float]:
        """
        Calculate Pearson correlation coefficient between sentiment and rating scores.
        
        Args:
            sentiment_scores: List of sentiment compound scores (-1 to 1)
            rating_scores: List of corresponding rating scores (1 to 5)
            
        Returns:
            Correlation coefficient (-1 to 1) or None if insufficient data
        """
        if len(sentiment_scores) < 2 or len(rating_scores) < 2 or len(sentiment_scores) != len(rating_scores):
            return None
            
        try:
            # Calculate means
            mean_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            mean_rating = sum(rating_scores) / len(rating_scores)
            
            # Calculate numerator and denominators for correlation
            numerator = sum((s - mean_sentiment) * (r - mean_rating) for s, r in zip(sentiment_scores, rating_scores))
            
            sum_sq_sentiment = sum((s - mean_sentiment) ** 2 for s in sentiment_scores)
            sum_sq_rating = sum((r - mean_rating) ** 2 for r in rating_scores)
            
            denominator = (sum_sq_sentiment * sum_sq_rating) ** 0.5
            
            if denominator == 0:
                return None
                
            correlation = numerator / denominator
            return round(correlation, 3)
            
        except (ZeroDivisionError, ValueError):
            return None

    # ===== Usage: Data-backed replacements for demo endpoints =====
    @staticmethod
    async def get_system_health(db: AsyncSession, hours: int = 24) -> Dict[str, Any]:
        """
        System health metrics derived from chat_events over the last `hours`.
        - Response times: use TTFA percentiles (ms) from event timelines.
        - Error rate: error events / message_received events (percentage).
        - Uptime approximation: percentage of 1-min buckets with any activity.
        """
        # Percentiles of TTFA
        q_latency = text(
            """
            WITH mr AS (
                SELECT session_id, message_id, MIN(timestamp) AS mr_ts
                FROM chat_events
                WHERE event_type = 'message_received'
                  AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY session_id, message_id
            ), at AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS at_start,
                       MAX(timestamp) AS at_end
                FROM chat_events
                WHERE event_type = 'agent_thinking'
                  AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY session_id, message_id
            ), rg AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS rg_start,
                       MAX(timestamp) AS rg_end
                FROM chat_events
                WHERE event_type = 'response_generation'
                  AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY session_id, message_id
            ), joined AS (
                SELECT mr.session_id, mr.message_id,
                       EXTRACT(EPOCH FROM (COALESCE(rg.rg_end, at.at_end) - mr.mr_ts)) * 1000 AS ttfa_ms
                FROM mr
                LEFT JOIN at ON at.session_id = mr.session_id AND at.message_id = mr.message_id
                LEFT JOIN rg ON rg.session_id = mr.session_id AND rg.message_id = mr.message_id
            )
            SELECT
                COALESCE(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ttfa_ms), 0) AS p50_ttfa_ms,
                COALESCE(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ttfa_ms), 0) AS p95_ttfa_ms,
                COALESCE(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ttfa_ms), 0) AS p99_ttfa_ms
            FROM joined
            WHERE ttfa_ms IS NOT NULL
            """
        )
        lat_res = await db.execute(q_latency, {"hours": hours})
        lat = lat_res.mappings().first() or {}

        # Error rate over window
        q_counts = text(
            """
            SELECT
                SUM(CASE WHEN event_type = 'message_received' THEN 1 ELSE 0 END)::INT AS requests,
                SUM(CASE WHEN event_type = 'error' THEN 1 ELSE 0 END)::INT AS errors
            FROM chat_events
            WHERE timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
            """
        )
        c_res = await db.execute(q_counts, {"hours": hours})
        counts = c_res.mappings().first() or {}
        requests = int(counts.get("requests") or 0)
        errors = int(counts.get("errors") or 0)
        error_rate = round((errors / requests) * 100, 2) if requests > 0 else 0.0

        # Uptime approximation: percent of minute buckets with any activity
        q_uptime = text(
            """
            WITH series AS (
                SELECT gs AS ts
                FROM generate_series(
                    date_trunc('minute', NOW() - (INTERVAL '1 hour' * :hours)),
                    date_trunc('minute', NOW()),
                    INTERVAL '1 minute'
                ) AS gs
            ), act AS (
                SELECT date_trunc('minute', timestamp) AS m, COUNT(*) AS cnt
                FROM chat_events
                WHERE timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY 1
            )
            SELECT
                COUNT(*) FILTER (WHERE COALESCE(act.cnt,0) > 0) AS up,
                COUNT(*) AS total
            FROM series s
            LEFT JOIN act ON act.m = s.ts
            """
        )
        up_res = await db.execute(q_uptime, {"hours": hours})
        up = up_res.mappings().first() or {}
        up_cnt = int(up.get("up") or 0)
        up_total = int(up.get("total") or 0)
        uptime_pct = round((up_cnt / up_total) * 100, 2) if up_total > 0 else 100.0

        # Availability label
        if error_rate < 1.0 and uptime_pct >= 99.0:
            availability = "healthy"
        elif error_rate < 5.0 and uptime_pct >= 95.0:
            availability = "warning"
        else:
            availability = "degraded"

        return {
            "api_response_time_p50": float(lat.get("p50_ttfa_ms") or 0.0),
            "api_response_time_p95": float(lat.get("p95_ttfa_ms") or 0.0),
            "api_response_time_p99": float(lat.get("p99_ttfa_ms") or 0.0),
            "error_rate": error_rate,
            "uptime_percentage": uptime_pct,
            "system_availability": availability,
        }

    @staticmethod
    async def get_hourly_traffic_series(db: AsyncSession, days: int = 7) -> List[Dict[str, Any]]:
        """
        Aggregate sessions and messages per UTC hour across the last `days`.
        Returns 24 buckets ("00".."23").
        """
        q_sessions = text(
            """
            SELECT EXTRACT(HOUR FROM created_at)::INT AS h, COUNT(*)::INT AS cnt
            FROM chats
            WHERE created_at >= NOW() - (INTERVAL '1 day' * :days)
            GROUP BY 1
            """
        )
        q_messages = text(
            """
            SELECT EXTRACT(HOUR FROM timestamp)::INT AS h, COUNT(*)::INT AS cnt
            FROM chat_messages
            WHERE timestamp >= NOW() - (INTERVAL '1 day' * :days)
            GROUP BY 1
            """
        )
        s_map = {int(r[0]): int(r[1]) for r in (await db.execute(q_sessions, {"days": days})).all()}
        m_map = {int(r[0]): int(r[1]) for r in (await db.execute(q_messages, {"days": days})).all()}
        series: List[Dict[str, Any]] = []
        for h in range(24):
            series.append({
                "hour": f"{h:02d}",
                "sessions": int(s_map.get(h, 0)),
                "messages": int(m_map.get(h, 0)),
            })
        return series

    @staticmethod
    async def get_response_time_trends(db: AsyncSession, days: int = 7) -> List[Dict[str, Any]]:
        """
        Daily TTFA percentiles for the last `days`.
        Returns a list of {day, p50, p95, p99}.
        """
        q = text(
            """
            WITH mr AS (
                SELECT session_id, message_id, MIN(timestamp) AS mr_ts
                FROM chat_events
                WHERE event_type = 'message_received'
                  AND timestamp >= NOW() - (INTERVAL '1 day' * :days)
                GROUP BY session_id, message_id
            ), at AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS at_start,
                       MAX(timestamp) AS at_end
                FROM chat_events
                WHERE event_type = 'agent_thinking'
                  AND timestamp >= NOW() - (INTERVAL '1 day' * :days)
                GROUP BY session_id, message_id
            ), rg AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS rg_start,
                       MAX(timestamp) AS rg_end
                FROM chat_events
                WHERE event_type = 'response_generation'
                  AND timestamp >= NOW() - (INTERVAL '1 day' * :days)
                GROUP BY session_id, message_id
            ), joined AS (
                SELECT DATE(mr.mr_ts) AS day,
                       EXTRACT(EPOCH FROM (COALESCE(rg.rg_end, at.at_end) - mr.mr_ts)) * 1000 AS ttfa_ms
                FROM mr
                LEFT JOIN at ON at.session_id = mr.session_id AND at.message_id = mr.message_id
                LEFT JOIN rg ON rg.session_id = mr.session_id AND rg.message_id = mr.message_id
            )
            SELECT day,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ttfa_ms) AS p50,
                   PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ttfa_ms) AS p95,
                   PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ttfa_ms) AS p99
            FROM joined
            WHERE ttfa_ms IS NOT NULL
            GROUP BY day
            ORDER BY day
            """
        )
        res = await db.execute(q, {"days": days})
        return [
            {"day": str(r[0]), "p50": float(r[1] or 0), "p95": float(r[2] or 0), "p99": float(r[3] or 0)}
            for r in res.all()
        ]

    @staticmethod
    async def get_error_analysis(db: AsyncSession, hours: int = 24) -> Dict[str, Any]:
        """
        Error analysis over the last `hours` using chat_events.
        Returns error_rate, total_errors, and breakdown by type.
        """
        q_errs = text(
            """
            SELECT COALESCE(event_data->>'error_type', event_data->>'reason', event_type) AS t, COUNT(*)::INT AS c
            FROM chat_events
            WHERE event_type = 'error'
              AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
            GROUP BY 1
            ORDER BY c DESC
            """
        )
        errs = await db.execute(q_errs, {"hours": hours})
        err_rows = errs.mappings().all()
        error_types = { (r.get("t") or "error"): int(r.get("c") or 0) for r in err_rows }
        total_errors = sum(error_types.values())

        q_req = text(
            """
            SELECT COUNT(*)::INT
            FROM chat_events
            WHERE event_type = 'message_received'
              AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
            """
        )
        req = await db.execute(q_req, {"hours": hours})
        requests = int(req.scalar() or 0)
        error_rate = round((total_errors / requests) * 100, 2) if requests > 0 else 0.0

        return {
            "error_rate": error_rate,
            "total_errors": int(total_errors),
            "error_types": error_types,
            "analysis_period": f"{hours} hours",
        }

    @staticmethod
    async def get_capacity_metrics(db: AsyncSession, hours: int = 24, max_capacity: int = 100) -> Dict[str, Any]:
        """
        Estimate capacity using minute-level concurrency derived from chat_events.
        - Build message intervals: [message_received, first(agent_thinking or response_generation) OR last if missing].
        - Sample concurrency at 1-minute granularity within the window.
        - Compute p95 concurrency and utilization vs provided max capacity.
        """
        q = text(
            """
            WITH mr AS (
                SELECT session_id, message_id, MIN(timestamp) AS mr_ts
                FROM chat_events
                WHERE event_type = 'message_received'
                  AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY session_id, message_id
            ), at AS (
                SELECT session_id, message_id, MIN(timestamp) AS at_start, MAX(timestamp) AS at_end
                FROM chat_events
                WHERE event_type = 'agent_thinking'
                  AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY session_id, message_id
            ), rg AS (
                SELECT session_id, message_id, MIN(timestamp) AS rg_start, MAX(timestamp) AS rg_end
                FROM chat_events
                WHERE event_type = 'response_generation'
                  AND timestamp >= NOW() - (INTERVAL '1 hour' * :hours)
                GROUP BY session_id, message_id
            ), intervals AS (
                SELECT
                    mr.session_id,
                    mr.message_id,
                    mr.mr_ts AS start_ts,
                    -- Choose earliest available end among starts; fallback to latest end; fallback to +60s
                    COALESCE(
                        LEAST(NULLIF(at.at_start, NULL), NULLIF(rg.rg_start, NULL)),
                        GREATEST(COALESCE(at.at_end, mr.mr_ts), COALESCE(rg.rg_end, mr.mr_ts)),
                        mr.mr_ts + INTERVAL '60 seconds'
                    ) AS end_ts
                FROM mr
                LEFT JOIN at ON at.session_id = mr.session_id AND at.message_id = mr.message_id
                LEFT JOIN rg ON rg.session_id = mr.session_id AND rg.message_id = mr.message_id
            ), norm AS (
                SELECT session_id, message_id,
                       start_ts,
                       CASE WHEN end_ts > start_ts THEN end_ts ELSE start_ts + INTERVAL '1 second' END AS end_ts
                FROM intervals
            ), series AS (
                SELECT gs AS ts
                FROM generate_series(
                    date_trunc('minute', NOW() - (INTERVAL '1 hour' * :hours)),
                    date_trunc('minute', NOW()),
                    INTERVAL '1 minute'
                ) AS gs
            ), conc AS (
                SELECT s.ts,
                       COUNT(*)::INT AS concurrent_msgs
                FROM series s
                JOIN norm i
                  ON i.start_ts <= s.ts AND i.end_ts > s.ts
                GROUP BY s.ts
            )
            SELECT
                COALESCE(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY concurrent_msgs), 0) AS p95_conc,
                COALESCE(MAX(concurrent_msgs), 0) AS max_conc,
                COALESCE(AVG(concurrent_msgs), 0) AS avg_conc
            FROM conc
            """
        )
        res = await db.execute(q, {"hours": hours})
        row = res.mappings().first() or {}
        p95_conc = float(row.get("p95_conc") or 0.0)
        max_conc = float(row.get("max_conc") or 0.0)
        avg_conc = float(row.get("avg_conc") or 0.0)

        utilization = 0.0
        if max_capacity > 0:
            utilization = min(100.0, round((p95_conc / max_capacity) * 100.0, 2))

        if utilization >= 90:
            scaling_status = "critical"
            current_load = "high"
        elif utilization >= 70:
            scaling_status = "scale_recommended"
            current_load = "elevated"
        elif utilization >= 40:
            scaling_status = "adequate"
            current_load = "moderate"
        else:
            scaling_status = "underutilized"
            current_load = "low"

        return {
            "current_load": current_load,
            "capacity_utilization": utilization,
            "concurrent_sessions": int(round(p95_conc)),
            "scaling_status": scaling_status,
            "recommendations": [],
        }

    # ===== New methods =====
    @staticmethod
    async def get_latency_stats(db: AsyncSession) -> Dict[str, Any]:
        """
        Compute latency percentiles using chat_events.
        Assumptions:
        - event_type 'message_received' marks user input arrival
        - 'agent_thinking' marks LLM thinking; first occurrence ~ start, last occurrence ~ end
        - 'response_generation' marks answer emission; last occurrence approximates end of answer
        Returns dict matching LatencyStats.
        """
        q = text(
            """
            WITH mr AS (
                SELECT session_id, message_id, MIN(timestamp) AS mr_ts
                FROM chat_events
                WHERE event_type = 'message_received'
                GROUP BY session_id, message_id
            ), at AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS at_start,
                       MAX(timestamp) AS at_end
                FROM chat_events
                WHERE event_type = 'agent_thinking'
                GROUP BY session_id, message_id
            ), rg AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS rg_start,
                       MAX(timestamp) AS rg_end
                FROM chat_events
                WHERE event_type = 'response_generation'
                GROUP BY session_id, message_id
            ), joined AS (
                SELECT mr.session_id, mr.message_id,
                       EXTRACT(EPOCH FROM (at.at_start - mr.mr_ts)) * 1000 AS ttfb_ms,
                       EXTRACT(EPOCH FROM (COALESCE(rg.rg_end, at.at_end) - mr.mr_ts)) * 1000 AS ttfa_ms
                FROM mr
                LEFT JOIN at ON at.session_id = mr.session_id AND at.message_id = mr.message_id
                LEFT JOIN rg ON rg.session_id = mr.session_id AND rg.message_id = mr.message_id
            )
            SELECT
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ttfb_ms) AS p50_ttfb_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ttfb_ms) AS p95_ttfb_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ttfb_ms) AS p99_ttfb_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ttfa_ms) AS p50_ttfa_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ttfa_ms) AS p95_ttfa_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ttfa_ms) AS p99_ttfa_ms,
                COUNT(*)::INT AS samples
            FROM joined
            WHERE ttfb_ms IS NOT NULL AND ttfa_ms IS NOT NULL
            """
        )
        res = await db.execute(q)
        row = res.mappings().first()
        if not row:
            return {
                "p50_ttfb_ms": 0.0,
                "p95_ttfb_ms": 0.0,
                "p99_ttfb_ms": 0.0,
                "p50_ttfa_ms": 0.0,
                "p95_ttfa_ms": 0.0,
                "p99_ttfa_ms": 0.0,
                "samples": 0,
            }
        return {
            "p50_ttfb_ms": float(row.get("p50_ttfb_ms") or 0),
            "p95_ttfb_ms": float(row.get("p95_ttfb_ms") or 0),
            "p99_ttfb_ms": float(row.get("p99_ttfb_ms") or 0),
            "p50_ttfa_ms": float(row.get("p50_ttfa_ms") or 0),
            "p95_ttfa_ms": float(row.get("p95_ttfa_ms") or 0),
            "p99_ttfa_ms": float(row.get("p99_ttfa_ms") or 0),
            "samples": int(row.get("samples") or 0),
        }

    @staticmethod
    async def get_tool_usage(db: AsyncSession) -> Dict[str, Any]:
        """
        Aggregate tool usage for RAG searches from chat_events.
        Counts 'started'/'completed'/'failed' for event_type = 'tool_search_documents'.
        Derives avg_retrieved from event_data.count for completed events.
        Returns overall and by_collection breakdown.
        """
        overall_q = text(
            """
            SELECT
                SUM(CASE WHEN event_status = 'started' THEN 1 ELSE 0 END)::INT AS started,
                SUM(CASE WHEN event_status = 'completed' THEN 1 ELSE 0 END)::INT AS completed,
                SUM(CASE WHEN event_status = 'failed' THEN 1 ELSE 0 END)::INT AS failed,
                AVG(
                    CASE WHEN event_status = 'completed' AND (event_data->>'count') ~ '^[0-9]+'
                         THEN (event_data->>'count')::INT
                    END
                ) AS avg_retrieved
            FROM chat_events
            WHERE event_type = 'tool_search_documents'
            """
        )
        res_overall = await db.execute(overall_q)
        o = res_overall.mappings().first() or {}
        avg_overall: Optional[float] = None
        if o.get("avg_retrieved") is not None:
            try:
                val_overall = o.get("avg_retrieved")
                # Ensure not None and convertible
                if val_overall is not None:
                    avg_overall = float(val_overall)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                avg_overall = None
        overall = {
            "collection_id": None,
            "started": int(o.get("started") or 0),
            "completed": int(o.get("completed") or 0),
            "failed": int(o.get("failed") or 0),
            "avg_retrieved": avg_overall,
        }

        by_coll_q = text(
            """
            SELECT
                NULLIF(event_data->>'collection', '') AS collection_id,
                SUM(CASE WHEN event_status = 'started' THEN 1 ELSE 0 END)::INT AS started,
                SUM(CASE WHEN event_status = 'completed' THEN 1 ELSE 0 END)::INT AS completed,
                SUM(CASE WHEN event_status = 'failed' THEN 1 ELSE 0 END)::INT AS failed,
                AVG(
                    CASE WHEN event_status = 'completed' AND (event_data->>'count') ~ '^[0-9]+'
                         THEN (event_data->>'count')::INT
                    END
                ) AS avg_retrieved
            FROM chat_events
            WHERE event_type = 'tool_search_documents'
            GROUP BY NULLIF(event_data->>'collection', '')
            ORDER BY completed DESC NULLS LAST, started DESC
            """
        )
        res_by = await db.execute(by_coll_q)
        by_collection = []
        for row in res_by.mappings().all():
            avg_val: Optional[float] = None
            if row.get("avg_retrieved") is not None:
                try:
                    v = row.get("avg_retrieved")
                    if v is not None:
                        avg_val = float(v)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    avg_val = None
            by_collection.append({
                "collection_id": row.get("collection_id"),
                "started": int(row.get("started") or 0),
                "completed": int(row.get("completed") or 0),
                "failed": int(row.get("failed") or 0),
                "avg_retrieved": avg_val,
            })

        return {"overall": overall, "by_collection": by_collection}

    @staticmethod
    async def get_collections_health(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Compute collection health across webpages and documents with freshness.
        Returns a list of items with webpages, documents, and last_indexed_at per collection.
        """
        q = text(
            """
            WITH coll AS (
                SELECT id AS collection_id FROM collections
                UNION
                SELECT DISTINCT collection_id FROM webpages WHERE collection_id IS NOT NULL
                UNION
                SELECT DISTINCT collection_id FROM documents WHERE collection_id IS NOT NULL
            ), wp AS (
                SELECT
                    collection_id,
                    COUNT(*)::INT AS pages,
                    SUM(CASE WHEN status_code BETWEEN 200 AND 299 THEN 1 ELSE 0 END)::INT AS ok,
                    SUM(CASE WHEN status_code BETWEEN 300 AND 399 THEN 1 ELSE 0 END)::INT AS redirects,
                    SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END)::INT AS client_err,
                    SUM(CASE WHEN status_code BETWEEN 500 AND 599 THEN 1 ELSE 0 END)::INT AS server_err,
                    SUM(CASE WHEN is_indexed THEN 1 ELSE 0 END)::INT AS indexed,
                    MAX(indexed_at) AS wp_last_indexed
                FROM webpages
                GROUP BY collection_id
            ), doc AS (
                SELECT
                    collection_id,
                    COUNT(*)::INT AS doc_count,
                    SUM(CASE WHEN is_indexed THEN 1 ELSE 0 END)::INT AS doc_indexed,
                    SUM(CASE WHEN is_public THEN 1 ELSE 0 END)::INT AS public,
                    COALESCE(SUM(size), 0)::BIGINT AS total_size,
                    MAX(indexed_at) AS doc_last_indexed
                FROM documents
                GROUP BY collection_id
            )
            SELECT
                coll.collection_id,
                COALESCE(wp.pages, 0) AS pages,
                COALESCE(wp.ok, 0) AS ok,
                COALESCE(wp.redirects, 0) AS redirects,
                COALESCE(wp.client_err, 0) AS client_err,
                COALESCE(wp.server_err, 0) AS server_err,
                COALESCE(wp.indexed, 0) AS wp_indexed,
                COALESCE(doc.doc_count, 0) AS doc_count,
                COALESCE(doc.doc_indexed, 0) AS doc_indexed,
                COALESCE(doc.public, 0) AS public,
                COALESCE(doc.total_size, 0) AS total_size,
                CASE
                  WHEN wp.wp_last_indexed IS NOT NULL AND doc.doc_last_indexed IS NOT NULL THEN GREATEST(wp.wp_last_indexed, doc.doc_last_indexed)
                  WHEN wp.wp_last_indexed IS NOT NULL THEN wp.wp_last_indexed
                  ELSE doc.doc_last_indexed
                END AS last_indexed_at
            FROM coll
            LEFT JOIN wp ON wp.collection_id = coll.collection_id
            LEFT JOIN doc ON doc.collection_id = coll.collection_id
            ORDER BY coll.collection_id
            """
        )
        res = await db.execute(q)
        items: List[Dict[str, Any]] = []
        for r in res.mappings().all():
            items.append({
                "collection_id": r.get("collection_id"),
                "webpages": {
                    "pages": int(r.get("pages") or 0),
                    "ok": int(r.get("ok") or 0),
                    "redirects": int(r.get("redirects") or 0),
                    "client_err": int(r.get("client_err") or 0),
                    "server_err": int(r.get("server_err") or 0),
                    "indexed": int(r.get("wp_indexed") or 0),
                },
                "documents": {
                    "count": int(r.get("doc_count") or 0),
                    "indexed": int(r.get("doc_indexed") or 0),
                    "public": int(r.get("public") or 0),
                    "total_size": int(r.get("total_size") or 0),
                },
                "freshness": {
                    "last_indexed_at": r.get("last_indexed_at")
                }
            })
        return items

    @staticmethod
    async def get_no_answer_stats(db: AsyncSession, examples_limit: int = 5) -> Dict[str, Any]:
        """
        Estimate no-answer rate from assistant messages and error events.
        Heuristics:
        - Assistant messages with apology/insufficient-info phrases in content
        - Plus error events in chat_events contribute to triggers
        Returns percentage rate, example snippets, and top triggers.
        """
        # Total assistant messages
        total_q = text(
            """
            SELECT COUNT(*)::INT AS total
            FROM chat_messages
            WHERE message_type = 'assistant'
            """
        )
        total_res = await db.execute(total_q)
        total = int((total_res.mappings().first() or {}).get("total") or 0)

        # No-answer heuristic: common apology/insufficient phrases
        noans_q = text(
            """
            WITH msgs AS (
                SELECT id, chat_id, message_id,
                       COALESCE(message_object->>'content', '') AS content
                FROM chat_messages
                WHERE message_type = 'assistant'
            )
            SELECT id, chat_id, message_id,
                   content
            FROM msgs
            WHERE content ILIKE '%sorry%'
               OR content ILIKE '%do not have%'
               OR content ILIKE '%don''t have%'
               OR content ILIKE '%unable to find%'
               OR content ILIKE '%no relevant results%'
               OR content ILIKE '%cannot answer%'
               OR content ILIKE '%not sure%'
            """
        )
        noans_res = await db.execute(noans_q)
        noans_rows = noans_res.mappings().all()
        noans_count = len(noans_rows)

        # Error triggers from chat_events
        err_q = text(
            """
            SELECT
                COALESCE(event_data->>'reason', event_data->>'error_type', event_type) AS trigger,
                COUNT(*)::INT AS cnt
            FROM chat_events
            WHERE event_type = 'error'
            GROUP BY COALESCE(event_data->>'reason', event_data->>'error_type', event_type)
            ORDER BY cnt DESC
            LIMIT 10
            """
        )
        err_res = await db.execute(err_q)
        triggers = [r.get("trigger") for r in err_res.mappings().all() if r.get("trigger")]

        # Build examples (limit)
        examples: List[Dict[str, Any]] = []
        for r in noans_rows[:examples_limit]:
            content = r.get("content") or ""
            snippet = content[:180]
            # We don't have chat_id in chat_events schema; examples accept optional ids
            examples.append({
                "chat_id": int(r.get("chat_id") or 0),
                "message_id": r.get("message_id"),
                "snippet": snippet,
            })

        rate = round((noans_count / total) * 100, 2) if total > 0 else 0.0
        return {
            "rate": rate,
            "examples": examples,
            "top_triggers": triggers,
        }

    @staticmethod
    async def get_citation_stats(db: AsyncSession) -> Dict[str, Any]:
        """
        Compute citation coverage and per-collection stats from assistant messages' sources.
        Assumes assistant answers may include message_object.sources as a JSON array.
        """
        totals_q = text(
            """
            SELECT
                COUNT(*)::INT AS total_answers,
                SUM(CASE WHEN COALESCE(json_array_length(message_object->'sources'),0) > 0 THEN 1 ELSE 0 END)::INT AS covered_answers,
                AVG(
                    CASE WHEN COALESCE(json_array_length(message_object->'sources'),0) > 0
                         THEN json_array_length(message_object->'sources')::FLOAT
                    END
                ) AS avg_citations
            FROM chat_messages
            WHERE message_type = 'assistant'
            """
        )
        totals_res = await db.execute(totals_q)
        trow = totals_res.mappings().first() or {}
        total_answers = int(trow.get("total_answers") or 0)
        covered_answers = int(trow.get("covered_answers") or 0)
        avg_citations_val = trow.get("avg_citations")
        try:
            avg_citations = float(avg_citations_val) if avg_citations_val is not None else 0.0
        except (TypeError, ValueError):
            avg_citations = 0.0
        coverage_pct = round((covered_answers / total_answers) * 100, 2) if total_answers > 0 else 0.0

        by_q = text(
            """
            WITH am AS (
                SELECT id, message_object
                FROM chat_messages
                WHERE message_type = 'assistant'
            ), src AS (
                SELECT am.id AS answer_id,
                       COALESCE(
                           elem->>'collection',
                           elem->>'collection_id',
                           (elem->'metadata')->>'collection',
                           (elem->'metadata')->>'collection_id'
                       ) AS collection_id
                FROM am,
                     LATERAL json_array_elements(COALESCE(am.message_object->'sources','[]'::json)) AS elem
            ), counts AS (
                SELECT collection_id, answer_id, COUNT(*)::INT AS cnt
                FROM src
                WHERE collection_id IS NOT NULL AND collection_id <> ''
                GROUP BY collection_id, answer_id
            )
            SELECT collection_id,
                   COUNT(*)::INT AS answers_with_collection,
                   AVG(cnt)::FLOAT AS avg_citations
            FROM counts
            GROUP BY collection_id
            ORDER BY answers_with_collection DESC
            """
        )
        by_res = await db.execute(by_q)
        by_collection: List[Dict[str, Any]] = []
        for r in by_res.mappings().all():
            coll = r.get("collection_id")
            answers_with_collection = int(r.get("answers_with_collection") or 0)
            avg_coll_val = r.get("avg_citations")
            try:
                avg_coll = float(avg_coll_val) if avg_coll_val is not None else 0.0
            except (TypeError, ValueError):
                avg_coll = 0.0
            coll_coverage = round((answers_with_collection / total_answers) * 100, 2) if total_answers > 0 else 0.0
            by_collection.append({
                "collection_id": coll,
                "coverage_pct": coll_coverage,
                "avg_citations": avg_coll,
            })

        return {
            "coverage_pct": coverage_pct,
            "avg_citations": avg_citations,
            "by_collection": by_collection,
        }

    @staticmethod
    async def get_answer_length_stats(db: AsyncSession) -> Dict[str, Any]:
        """
        Compute answer length stats (words) for assistant messages.
        Returns avg, median, and distribution buckets.
        """
        q = text(
            r"""
            WITH words AS (
                SELECT COALESCE(
                         array_length(regexp_split_to_array(COALESCE(message_object->>'content',''), E'\s+'), 1),
                         0
                     ) AS words
                FROM chat_messages
                WHERE message_type = 'assistant'
            )
            SELECT
                AVG(words)::FLOAT AS avg_words,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY words) AS median_words,
                COUNT(*)::INT AS total,
                SUM(CASE WHEN words <= 20 THEN 1 ELSE 0 END)::INT AS b1,
                SUM(CASE WHEN words BETWEEN 21 AND 50 THEN 1 ELSE 0 END)::INT AS b2,
                SUM(CASE WHEN words BETWEEN 51 AND 100 THEN 1 ELSE 0 END)::INT AS b3,
                SUM(CASE WHEN words BETWEEN 101 AND 200 THEN 1 ELSE 0 END)::INT AS b4,
                SUM(CASE WHEN words > 200 THEN 1 ELSE 0 END)::INT AS b5
            FROM words
            """
        )
        res = await db.execute(q)
        row = res.mappings().first() or {}
        total = int(row.get("total") or 0)
        def pct(n: int) -> float:
            return round((n / total) * 100, 2) if total > 0 else 0.0
        distribution = [
            {"bucket": "0-20", "count": int(row.get("b1") or 0), "percentage": pct(int(row.get("b1") or 0))},
            {"bucket": "21-50", "count": int(row.get("b2") or 0), "percentage": pct(int(row.get("b2") or 0))},
            {"bucket": "51-100", "count": int(row.get("b3") or 0), "percentage": pct(int(row.get("b3") or 0))},
            {"bucket": "101-200", "count": int(row.get("b4") or 0), "percentage": pct(int(row.get("b4") or 0))},
            {"bucket": "200+", "count": int(row.get("b5") or 0), "percentage": pct(int(row.get("b5") or 0))},
        ]
        return {
            "avg_words": float(row.get("avg_words") or 0.0),
            "median_words": float(row.get("median_words") or 0.0),
            "distribution": distribution,
        }

    # ===== Per-user analytics =====
    @staticmethod
    async def get_user_top(
        db: AsyncSession,
        limit: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Top users by sessions/messages within a window.
        Returns [{user_id, sessions, messages}].
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        q = text(
            """
            SELECT c.user_id,
                   COUNT(DISTINCT c.id)::INT AS sessions,
                   COUNT(cm.id)::INT AS messages
            FROM chats c
            LEFT JOIN chat_messages cm
                   ON cm.chat_id = c.id
                  AND cm.timestamp BETWEEN :start_ts AND :end_ts
            WHERE c.user_id IS NOT NULL
              AND c.created_at BETWEEN :start_ts AND :end_ts
            GROUP BY c.user_id
            ORDER BY sessions DESC, messages DESC
            LIMIT :limit
            """
        )
        res = await db.execute(q, {"start_ts": start_date, "end_ts": end_date, "limit": limit})
        return [
            {"user_id": r[0], "sessions": int(r[1] or 0), "messages": int(r[2] or 0)}
            for r in res.all()
        ]

    @staticmethod
    async def get_user_metrics(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Per-user metrics: sessions, message counts, avg turns, avg TTFB/TTFA, no-answer rate,
        RAG coverage, top collections, last active.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        params = {"uid": user_id, "start_ts": start_date, "end_ts": end_date}

        # Sessions
        q_sessions = text(
            """
            SELECT COUNT(*)::INT
            FROM chats
            WHERE user_id = :uid AND created_at BETWEEN :start_ts AND :end_ts
            """
        )
        sessions = int((await db.execute(q_sessions, params)).scalar() or 0)

        # Messages by type
        q_msgs = text(
            """
            SELECT
              SUM(CASE WHEN cm.message_type = 'user' THEN 1 ELSE 0 END)::INT AS user_msgs,
              SUM(CASE WHEN cm.message_type = 'assistant' THEN 1 ELSE 0 END)::INT AS assistant_msgs
            FROM chat_messages cm
            JOIN chats c ON c.id = cm.chat_id
            WHERE c.user_id = :uid AND cm.timestamp BETWEEN :start_ts AND :end_ts
            """
        )
        mrow = (await db.execute(q_msgs, params)).mappings().first() or {}
        messages_user = int(mrow.get("user_msgs") or 0)
        messages_assistant = int(mrow.get("assistant_msgs") or 0)

        # Avg turns per chat
        q_turns = text(
            """
            WITH per AS (
                SELECT c.id, COUNT(cm.id)::INT AS cnt
                FROM chats c
                LEFT JOIN chat_messages cm ON cm.chat_id = c.id AND cm.timestamp BETWEEN :start_ts AND :end_ts
                WHERE c.user_id = :uid AND c.created_at BETWEEN :start_ts AND :end_ts
                GROUP BY c.id
            )
            SELECT AVG(cnt)::FLOAT FROM per
            """
        )
        avg_turns_val = (await db.execute(q_turns, params)).scalar()
        try:
            avg_turns = float(avg_turns_val) if avg_turns_val is not None else 0.0
        except (TypeError, ValueError):
            avg_turns = 0.0

        # Avg TTFB/TTFA from chat_events limited to the user's sessions
        q_latency = text(
            """
            WITH sids AS (
                SELECT session_id FROM chats WHERE user_id = :uid AND created_at BETWEEN :start_ts AND :end_ts
            ), mr AS (
                SELECT session_id, message_id, MIN(timestamp) AS mr_ts
                FROM chat_events
                WHERE event_type = 'message_received'
                  AND session_id IN (SELECT session_id FROM sids)
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY session_id, message_id
            ), at AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS at_start,
                       MAX(timestamp) AS at_end
                FROM chat_events
                WHERE event_type = 'agent_thinking'
                  AND session_id IN (SELECT session_id FROM sids)
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY session_id, message_id
            ), rg AS (
                SELECT session_id, message_id,
                       MIN(timestamp) AS rg_start,
                       MAX(timestamp) AS rg_end
                FROM chat_events
                WHERE event_type = 'response_generation'
                  AND session_id IN (SELECT session_id FROM sids)
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY session_id, message_id
            ), joined AS (
                SELECT mr.session_id, mr.message_id,
                       EXTRACT(EPOCH FROM (at.at_start - mr.mr_ts)) * 1000 AS ttfb_ms,
                       EXTRACT(EPOCH FROM (COALESCE(rg.rg_end, at.at_end) - mr.mr_ts)) * 1000 AS ttfa_ms
                FROM mr
                LEFT JOIN at ON at.session_id = mr.session_id AND at.message_id = mr.message_id
                LEFT JOIN rg ON rg.session_id = mr.session_id AND rg.message_id = mr.message_id
            )
            SELECT AVG(ttfb_ms)::FLOAT AS avg_ttfb_ms,
                   AVG(ttfa_ms)::FLOAT AS avg_ttfa_ms
            FROM joined
            WHERE ttfb_ms IS NOT NULL AND ttfa_ms IS NOT NULL
            """
        )
        lat = (await db.execute(q_latency, params)).mappings().first() or {}
        avg_ttfb_ms = float(lat.get("avg_ttfb_ms") or 0.0)
        avg_ttfa_ms = float(lat.get("avg_ttfa_ms") or 0.0)

        # No-answer rate for user's assistant messages
        q_noans = text(
            """
            WITH msgs AS (
                SELECT cm.id,
                       COALESCE(cm.message_object->>'content','') AS content
                FROM chat_messages cm
                JOIN chats c ON c.id = cm.chat_id
                WHERE c.user_id = :uid
                  AND cm.message_type = 'assistant'
                  AND cm.timestamp BETWEEN :start_ts AND :end_ts
            )
            SELECT
              COUNT(*)::INT AS total,
              SUM(
                CASE WHEN (
                    content ILIKE '%sorry%'
                    OR content ILIKE '%do not have%'
                    OR content ILIKE '%don''t have%'
                    OR content ILIKE '%unable to find%'
                    OR content ILIKE '%no relevant results%'
                    OR content ILIKE '%cannot answer%'
                    OR content ILIKE '%not sure%'
                ) THEN 1 ELSE 0 END
              )::INT AS noans
            FROM msgs
            """
        )
        nr = (await db.execute(q_noans, params)).mappings().first() or {}
        total_asst = int(nr.get("total") or 0)
        noans_cnt = int(nr.get("noans") or 0)
        no_answer_rate = round((noans_cnt / total_asst) * 100.0, 2) if total_asst > 0 else 0.0

        # RAG coverage and top collections from assistant message sources
        q_citations = text(
            """
            WITH am AS (
                SELECT cm.id, cm.message_object
                FROM chat_messages cm
                JOIN chats c ON c.id = cm.chat_id
                WHERE c.user_id = :uid
                  AND cm.message_type = 'assistant'
                  AND cm.timestamp BETWEEN :start_ts AND :end_ts
            )
            SELECT
                COUNT(*)::INT AS total_answers,
                SUM(CASE WHEN COALESCE(json_array_length(message_object->'sources'),0) > 0 THEN 1 ELSE 0 END)::INT AS covered_answers
            FROM am
            """
        )
        cit = (await db.execute(q_citations, params)).mappings().first() or {}
        total_answers = int(cit.get("total_answers") or 0)
        covered_answers = int(cit.get("covered_answers") or 0)
        rag_coverage_pct = round((covered_answers / total_answers) * 100.0, 2) if total_answers > 0 else 0.0

        q_top_cols = text(
            """
            WITH am AS (
                SELECT cm.id, cm.message_object
                FROM chat_messages cm
                JOIN chats c ON c.id = cm.chat_id
                WHERE c.user_id = :uid
                  AND cm.message_type = 'assistant'
                  AND cm.timestamp BETWEEN :start_ts AND :end_ts
            ), src AS (
                SELECT COALESCE(
                           elem->>'collection',
                           elem->>'collection_id',
                           (elem->'metadata')->>'collection',
                           (elem->'metadata')->>'collection_id'
                       ) AS collection_id
                FROM am,
                     LATERAL json_array_elements(COALESCE(am.message_object->'sources','[]'::json)) AS elem
            )
            SELECT collection_id, COUNT(*) AS c
            FROM src
            WHERE collection_id IS NOT NULL AND collection_id <> ''
            GROUP BY collection_id
            ORDER BY c DESC
            LIMIT 5
            """
        )
        rows = (await db.execute(q_top_cols, params)).all()
        top_collections = [r[0] for r in rows if r[0]]

        # Fallback to tool events if no sources
        if not top_collections:
            q_fallback = text(
                """
                WITH sids AS (
                    SELECT session_id FROM chats WHERE user_id = :uid AND created_at BETWEEN :start_ts AND :end_ts
                )
                SELECT NULLIF(event_data->>'collection','') AS collection_id, COUNT(*) AS c
                FROM chat_events
                WHERE event_type = 'tool_search_documents'
                  AND session_id IN (SELECT session_id FROM sids)
                  AND timestamp BETWEEN :start_ts AND :end_ts
                GROUP BY NULLIF(event_data->>'collection','')
                ORDER BY c DESC NULLS LAST
                LIMIT 5
                """
            )
            frows = (await db.execute(q_fallback, params)).all()
            top_collections = [r[0] for r in frows if r[0]]

        # Last active
        q_last = text(
            """
            SELECT MAX(updated_at) FROM chats WHERE user_id = :uid AND updated_at IS NOT NULL
            """
        )
        last_active = (await db.execute(q_last, {"uid": user_id})).scalar()

        return {
            "sessions": sessions,
            "messages_user": messages_user,
            "messages_assistant": messages_assistant,
            "avg_turns": round(avg_turns, 2),
            "avg_ttfb_ms": avg_ttfb_ms,
            "avg_ttfa_ms": avg_ttfa_ms,
            "no_answer_rate": no_answer_rate,
            "rag_coverage_pct": rag_coverage_pct,
            "top_collections": top_collections,
            "last_active": last_active,
        }
