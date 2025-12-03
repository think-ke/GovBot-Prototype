"""
Audit log endpoints for viewing system activity and user actions.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.db.models.audit_log import AuditLog
from app.utils.security import require_read_permission, require_admin_permission, APIKeyInfo

router = APIRouter()

class AuditLogResponse(BaseModel):
    """Response model for audit log data."""
    id: int
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_key_name: str
    timestamp: str

class AuditLogSummary(BaseModel):
    """Summary statistics for audit logs."""
    total_actions: int
    unique_users: int
    action_counts: dict
    resource_type_counts: dict
    recent_activity: List[AuditLogResponse]

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    hours_ago: Optional[int] = Query(None, ge=1, le=8760, description="Filter by hours ago (max 1 year)"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_admin_permission)
):
    """
    List audit logs with filtering and pagination.
    Requires admin permission.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        user_id: Filter by user ID
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by specific resource ID
        hours_ago: Filter by hours ago (e.g., 24 for last 24 hours)
        db: Database session
        
    Returns:
        List of audit log entries
    """
    try:
        # Build query with filters
        query = select(AuditLog)
        
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if hours_ago:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            conditions.append(AuditLog.timestamp >= cutoff_time)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                api_key_name=log.api_key_name,
                timestamp=log.timestamp.isoformat() if log.timestamp else ""
            )
            for log in audit_logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit logs: {str(e)}")

@router.get("/audit-logs/summary", response_model=AuditLogSummary)
async def get_audit_summary(
    hours_ago: int = Query(24, ge=1, le=8760, description="Time period in hours (default: 24, max: 1 year)"),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_admin_permission)
):
    """
    Get audit log summary statistics.
    Requires admin permission.
    
    Args:
        hours_ago: Time period in hours to analyze
        db: Database session
        
    Returns:
        Summary statistics for audit logs
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        
        # Get all logs in the time period
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_time)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Calculate summary statistics
        total_actions = len(logs)
        unique_users = len(set(log.user_id for log in logs))
        
        # Count actions by type
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        # Count resource types
        resource_type_counts = {}
        for log in logs:
            resource_type_counts[log.resource_type] = resource_type_counts.get(log.resource_type, 0) + 1
        
        # Get recent activity (last 10 actions)
        recent_query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(10)
        recent_result = await db.execute(recent_query)
        recent_logs = recent_result.scalars().all()
        
        recent_activity = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                api_key_name=log.api_key_name,
                timestamp=log.timestamp.isoformat() if log.timestamp else ""
            )
            for log in recent_logs
        ]
        
        return AuditLogSummary(
            total_actions=total_actions,
            unique_users=unique_users,
            action_counts=action_counts,
            resource_type_counts=resource_type_counts,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audit summary: {str(e)}")

@router.get("/audit-logs/user/{user_id}", response_model=List[AuditLogResponse])
async def get_user_audit_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    hours_ago: Optional[int] = Query(None, ge=1, le=8760),
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_admin_permission)
):
    """
    Get audit logs for a specific user.
    Requires admin permission.
    
    Args:
        user_id: The user ID to get logs for
        skip: Number of records to skip
        limit: Maximum number of records to return
        hours_ago: Optional filter by hours ago
        db: Database session
        
    Returns:
        List of audit log entries for the user
    """
    try:
        query = select(AuditLog).where(AuditLog.user_id == user_id)
        
        if hours_ago:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            query = query.where(AuditLog.timestamp >= cutoff_time)
        
        query = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                api_key_name=log.api_key_name,
                timestamp=log.timestamp.isoformat() if log.timestamp else ""
            )
            for log in audit_logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user audit logs: {str(e)}")

@router.get("/audit-logs/resource/{resource_type}/{resource_id}", response_model=List[AuditLogResponse])
async def get_resource_audit_logs(
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    api_key_info: APIKeyInfo = Depends(require_read_permission)
):
    """
    Get audit logs for a specific resource.
    Requires read permission.
    
    Args:
        resource_type: Type of resource (e.g., 'document', 'webpage', 'collection')
        resource_id: ID of the resource
        db: Database session
        
    Returns:
        List of audit log entries for the resource
    """
    try:
        query = select(AuditLog).where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
        ).order_by(desc(AuditLog.timestamp))
        
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                api_key_name=log.api_key_name,
                timestamp=log.timestamp.isoformat() if log.timestamp else ""
            )
            for log in audit_logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving resource audit logs: {str(e)}")
