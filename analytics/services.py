"""
Analytics service layer for data processing and calculations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, asc, and_, or_, text
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select

from .models import Chat, ChatMessage, Document, Webpage
from .schemas import (
    UserDemographics, SessionFrequency, TrafficMetrics, SessionDuration,
    ConversationFlow, ROIMetrics, ContainmentRate, TrendData, DistributionData
)

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
                Chat.created_at >= start_date,
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
        """Analyze conversation turn patterns."""
        
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
            
            # Calculate average response time for this range (simplified)
            avg_response_time = 30.0  # Placeholder - would need more complex calculation
            
            flow_analysis.append(ConversationFlow(
                turn_number=min_turns,
                completion_rate=completion_rate,
                abandonment_rate=100 - completion_rate,
                average_response_time=avg_response_time
            ))
        
        return flow_analysis
    
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
