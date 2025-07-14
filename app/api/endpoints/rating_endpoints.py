"""
Message rating endpoints for the GovStack API.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from app.db.database import get_db
from app.db.models.message_rating import MessageRating
from app.db.models.chat import Chat, ChatMessage
from app.utils.security import require_write_permission, require_read_permission, APIKeyInfo

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request and response
class RatingRequest(BaseModel):
    """Request model for submitting a rating."""
    session_id: str = Field(description="Chat session ID")
    message_id: str = Field(description="Message ID being rated")
    rating: int = Field(ge=1, le=5, description="Star rating from 1 to 5")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Optional written feedback")
    user_id: Optional[str] = Field(None, description="Optional user identification")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional rating metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message_id": "msg_12345",
                "rating": 4,
                "feedback_text": "Good response, but could be more detailed.",
                "user_id": "user123",
                "metadata": {"platform": "web", "language": "en"}
            }
        }

class RatingResponse(BaseModel):
    """Response model for rating operations."""
    id: int
    session_id: str
    message_id: str
    user_id: Optional[str]
    rating: int
    feedback_text: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message_id": "msg_12345",
                "user_id": "user123",
                "rating": 4,
                "feedback_text": "Good response, but could be more detailed.",
                "created_at": "2023-10-20T14:30:15.123456Z",
                "updated_at": "2023-10-20T14:30:15.123456Z",
                "metadata": {"platform": "web", "language": "en"}
            }
        }

class RatingUpdateRequest(BaseModel):
    """Request model for updating a rating."""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating from 1 to 5")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Optional written feedback")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional rating metadata")

class RatingStatsResponse(BaseModel):
    """Response model for rating statistics."""
    session_id: Optional[str]
    message_id: Optional[str]
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[int, int]  # {1: count, 2: count, ...}
    recent_feedback: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message_id": None,
                "total_ratings": 25,
                "average_rating": 4.2,
                "rating_distribution": {1: 1, 2: 2, 3: 5, 4: 10, 5: 7},
                "recent_feedback": [
                    {
                        "rating": 5,
                        "feedback_text": "Excellent response!",
                        "created_at": "2023-10-20T14:30:15.123456Z"
                    }
                ]
            }
        }

@router.post("/ratings", response_model=RatingResponse)
async def create_rating(
    request: RatingRequest,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
) -> RatingResponse:
    """
    Submit a rating for an assistant message.
    """
    try:
        # Validate that the session and message exist
        stmt = select(ChatMessage).join(Chat).where(
            and_(
                Chat.session_id == request.session_id,
                ChatMessage.message_id == request.message_id,
                ChatMessage.message_type == "assistant"  # Only allow rating assistant messages
            )
        )
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=404, 
                detail=f"Assistant message {request.message_id} not found in session {request.session_id}"
            )
        
        # Check if a rating already exists for this user/session/message combination
        existing_rating_stmt = select(MessageRating).where(
            and_(
                MessageRating.session_id == request.session_id,
                MessageRating.message_id == request.message_id,
                MessageRating.user_id == request.user_id if request.user_id else True
            )
        )
        existing_result = await db.execute(existing_rating_stmt)
        existing_rating = existing_result.scalar_one_or_none()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = request.rating
            existing_rating.feedback_text = request.feedback_text
            existing_rating.rating_metadata = request.metadata
            existing_rating.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(existing_rating)
            
            logger.info(f"Updated rating for message {request.message_id} in session {request.session_id}")
            
            return RatingResponse(
                id=existing_rating.id,
                session_id=existing_rating.session_id,
                message_id=existing_rating.message_id,
                user_id=existing_rating.user_id,
                rating=existing_rating.rating,
                feedback_text=existing_rating.feedback_text,
                created_at=existing_rating.created_at,
                updated_at=existing_rating.updated_at,
                metadata=existing_rating.rating_metadata
            )
        else:
            # Create new rating
            new_rating = MessageRating(
                session_id=request.session_id,
                message_id=request.message_id,
                user_id=request.user_id,
                rating=request.rating,
                feedback_text=request.feedback_text,
                rating_metadata=request.metadata
            )
            
            db.add(new_rating)
            await db.commit()
            await db.refresh(new_rating)
            
            logger.info(f"Created new rating for message {request.message_id} in session {request.session_id}")
            
            return RatingResponse(
                id=new_rating.id,
                session_id=new_rating.session_id,
                message_id=new_rating.message_id,
                user_id=new_rating.user_id,
                rating=new_rating.rating,
                feedback_text=new_rating.feedback_text,
                created_at=new_rating.created_at,
                updated_at=new_rating.updated_at,
                metadata=new_rating.rating_metadata
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create rating")

@router.get("/ratings/{rating_id}", response_model=RatingResponse)
async def get_rating(
    rating_id: int = Path(..., description="The ID of the rating to retrieve"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
) -> RatingResponse:
    """
    Retrieve a specific rating by ID.
    """
    try:
        stmt = select(MessageRating).where(MessageRating.id == rating_id)
        result = await db.execute(stmt)
        rating = result.scalar_one_or_none()
        
        if not rating:
            raise HTTPException(status_code=404, detail=f"Rating {rating_id} not found")
        
        return RatingResponse(
            id=rating.id,
            session_id=rating.session_id,
            message_id=rating.message_id,
            user_id=rating.user_id,
            rating=rating.rating,
            feedback_text=rating.feedback_text,
            created_at=rating.created_at,
            updated_at=rating.updated_at,
            metadata=rating.rating_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rating")

@router.put("/ratings/{rating_id}", response_model=RatingResponse)
async def update_rating(
    rating_id: int = Path(..., description="The ID of the rating to update"),
    request: RatingUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
) -> RatingResponse:
    """
    Update an existing rating.
    """
    try:
        stmt = select(MessageRating).where(MessageRating.id == rating_id)
        result = await db.execute(stmt)
        rating = result.scalar_one_or_none()
        
        if not rating:
            raise HTTPException(status_code=404, detail=f"Rating {rating_id} not found")
        
        # Update fields if provided
        if request.rating is not None:
            rating.rating = request.rating
        if request.feedback_text is not None:
            rating.feedback_text = request.feedback_text
        if request.metadata is not None:
            rating.rating_metadata = request.metadata
        
        rating.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(rating)
        
        logger.info(f"Updated rating {rating_id}")
        
        return RatingResponse(
            id=rating.id,
            session_id=rating.session_id,
            message_id=rating.message_id,
            user_id=rating.user_id,
            rating=rating.rating,
            feedback_text=rating.feedback_text,
            created_at=rating.created_at,
            updated_at=rating.updated_at,
            metadata=rating.rating_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update rating")

@router.delete("/ratings/{rating_id}")
async def delete_rating(
    rating_id: int = Path(..., description="The ID of the rating to delete"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_write_permission)
) -> Dict[str, str]:
    """
    Delete a rating.
    """
    try:
        stmt = select(MessageRating).where(MessageRating.id == rating_id)
        result = await db.execute(stmt)
        rating = result.scalar_one_or_none()
        
        if not rating:
            raise HTTPException(status_code=404, detail=f"Rating {rating_id} not found")
        
        await db.delete(rating)
        await db.commit()
        
        logger.info(f"Deleted rating {rating_id}")
        
        return {"message": f"Rating {rating_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete rating")

@router.get("/ratings", response_model=List[RatingResponse])
async def list_ratings(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating filter"),
    max_rating: Optional[int] = Query(None, ge=1, le=5, description="Maximum rating filter"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of ratings to return"),
    offset: int = Query(0, ge=0, description="Number of ratings to skip"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
) -> List[RatingResponse]:
    """
    List ratings with optional filtering.
    """
    try:
        stmt = select(MessageRating)
        
        # Apply filters
        conditions = []
        if session_id:
            conditions.append(MessageRating.session_id == session_id)
        if message_id:
            conditions.append(MessageRating.message_id == message_id)
        if user_id:
            conditions.append(MessageRating.user_id == user_id)
        if min_rating is not None:
            conditions.append(MessageRating.rating >= min_rating)
        if max_rating is not None:
            conditions.append(MessageRating.rating <= max_rating)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply ordering, limit, and offset
        stmt = stmt.order_by(desc(MessageRating.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        ratings = result.scalars().all()
        
        return [
            RatingResponse(
                id=rating.id,
                session_id=rating.session_id,
                message_id=rating.message_id,
                user_id=rating.user_id,
                rating=rating.rating,
                feedback_text=rating.feedback_text,
                created_at=rating.created_at,
                updated_at=rating.updated_at,
                metadata=rating.rating_metadata
            )
            for rating in ratings
        ]
        
    except Exception as e:
        logger.error(f"Error listing ratings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list ratings")

@router.get("/ratings/stats", response_model=RatingStatsResponse)
async def get_rating_stats(
    session_id: Optional[str] = Query(None, description="Get stats for specific session"),
    message_id: Optional[str] = Query(None, description="Get stats for specific message"),
    user_id: Optional[str] = Query(None, description="Get stats for specific user"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
) -> RatingStatsResponse:
    """
    Get rating statistics with optional filtering.
    """
    try:
        # Build base query conditions
        conditions = []
        if session_id:
            conditions.append(MessageRating.session_id == session_id)
        if message_id:
            conditions.append(MessageRating.message_id == message_id)
        if user_id:
            conditions.append(MessageRating.user_id == user_id)
        
        # Add date filter
        from datetime import timedelta
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        conditions.append(MessageRating.created_at >= since_date)
        
        # Get total count and average rating
        count_stmt = select(func.count(MessageRating.id), func.avg(MessageRating.rating))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        
        count_result = await db.execute(count_stmt)
        total_ratings, avg_rating = count_result.first()
        
        if total_ratings == 0:
            return RatingStatsResponse(
                session_id=session_id,
                message_id=message_id,
                total_ratings=0,
                average_rating=0.0,
                rating_distribution={},
                recent_feedback=[]
            )
        
        # Get rating distribution
        dist_stmt = select(MessageRating.rating, func.count(MessageRating.rating)).group_by(MessageRating.rating)
        if conditions:
            dist_stmt = dist_stmt.where(and_(*conditions))
        
        dist_result = await db.execute(dist_stmt)
        rating_distribution = {rating: count for rating, count in dist_result.all()}
        
        # Get recent feedback (with text)
        feedback_stmt = (
            select(MessageRating)
            .where(MessageRating.feedback_text.isnot(None))
        )
        if conditions:
            feedback_stmt = feedback_stmt.where(and_(*conditions))
        
        feedback_stmt = feedback_stmt.order_by(desc(MessageRating.created_at)).limit(10)
        feedback_result = await db.execute(feedback_stmt)
        recent_feedback_records = feedback_result.scalars().all()
        
        recent_feedback = [
            {
                "rating": record.rating,
                "feedback_text": record.feedback_text,
                "created_at": record.created_at.isoformat(),
                "user_id": record.user_id
            }
            for record in recent_feedback_records
        ]
        
        return RatingStatsResponse(
            session_id=session_id,
            message_id=message_id,
            total_ratings=total_ratings,
            average_rating=float(avg_rating),
            rating_distribution=rating_distribution,
            recent_feedback=recent_feedback
        )
        
    except Exception as e:
        logger.error(f"Error getting rating stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get rating statistics")
