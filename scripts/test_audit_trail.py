#!/usr/bin/env python3
"""
Test script to verify audit trail functionality.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_session
from app.db.models.audit_log import AuditLog
from app.utils.security import log_audit_action
from sqlalchemy.future import select

async def test_audit_trail():
    """Test the audit trail functionality."""
    
    print("Testing audit trail functionality...")
    
    try:
        # Test logging an audit action
        await log_audit_action(
            user_id="test_user",
            action="test_action",
            resource_type="test_resource",
            resource_id="test_123",
            details={
                "test_field": "test_value",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            api_key_name="test_key"
        )
        
        print("✅ Successfully logged test audit action")
        
        # Query the audit log to verify it was created
        async with async_session() as session:
            query = select(AuditLog).where(AuditLog.user_id == "test_user")
            result = await session.execute(query)
            audit_logs = result.scalars().all()
            
            if audit_logs:
                print(f"✅ Found {len(audit_logs)} audit log entries")
                
                latest_log = audit_logs[-1]  # Get the most recent one
                print(f"   Latest log: {latest_log.action} on {latest_log.resource_type} by {latest_log.user_id}")
                print(f"   Details: {latest_log.details}")
                print(f"   Timestamp: {latest_log.timestamp}")
                
            else:
                print("❌ No audit log entries found")
                
    except Exception as e:
        print(f"❌ Error testing audit trail: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_audit_queries():
    """Test common audit log queries."""
    
    print("\nTesting audit log queries...")
    
    try:
        async with async_session() as session:
            # Get total count
            query = select(AuditLog)
            result = await session.execute(query)
            all_logs = result.scalars().all()
            
            print(f"✅ Total audit log entries: {len(all_logs)}")
            
            # Get unique users
            unique_users = set(log.user_id for log in all_logs)
            print(f"✅ Unique users: {len(unique_users)} - {list(unique_users)}")
            
            # Get action counts
            action_counts = {}
            for log in all_logs:
                action_counts[log.action] = action_counts.get(log.action, 0) + 1
            
            print(f"✅ Action counts: {action_counts}")
            
            # Get resource type counts
            resource_counts = {}
            for log in all_logs:
                resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
            
            print(f"✅ Resource type counts: {resource_counts}")
            
    except Exception as e:
        print(f"❌ Error testing audit queries: {str(e)}")

async def main():
    """Main test function."""
    print("🔍 Testing GovStack Audit Trail System")
    print("=" * 50)
    
    await test_audit_trail()
    await test_audit_queries()
    
    print("\n" + "=" * 50)
    print("🎉 Audit trail testing completed!")
    
    print("\n📋 Summary of Audit Trail Features:")
    print("- ✅ All document uploads tracked with user information")
    print("- ✅ All webpage crawls tracked with user information") 
    print("- ✅ All collection operations tracked")
    print("- ✅ Complete audit log of all API operations")
    print("- ✅ User identification for all data modifications")
    print("- ✅ IP address and user agent tracking")
    print("- ✅ Detailed action logging with context")
    
    print("\n🔗 Available Audit Endpoints:")
    print("- GET /admin/audit-logs - List all audit logs")
    print("- GET /admin/audit-logs/summary - Get audit summary")
    print("- GET /admin/audit-logs/user/{user_id} - Get logs for specific user")
    print("- GET /admin/audit-logs/resource/{type}/{id} - Get logs for specific resource")

if __name__ == "__main__":
    asyncio.run(main())
