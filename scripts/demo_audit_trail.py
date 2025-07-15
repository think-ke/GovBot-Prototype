#!/usr/bin/env python3
"""
Example demonstrating the audit trail in action.
"""

import asyncio
import sys
import os
import tempfile
import aiohttp
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "http://localhost:5000"
API_KEY = "gs-dev-master-key-12345"  # Default master key

async def create_test_file():
    """Create a temporary test file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(f"Test document created at {datetime.now()}\n")
        f.write("This is a test document for audit trail demonstration.\n")
        f.write("The audit system will track who uploaded this file.\n")
        return f.name

async def upload_document(file_path):
    """Upload a document and demonstrate audit trail."""
    
    headers = {"X-API-Key": API_KEY}
    
    async with aiohttp.ClientSession() as session:
        # Upload document
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='test_audit_demo.txt', content_type='text/plain')
            data.add_field('description', 'Test document for audit trail demo')
            data.add_field('collection_id', 'audit-demo')
            data.add_field('is_public', 'false')
            
            print("📤 Uploading test document...")
            async with session.post(f"{API_BASE}/documents/", headers=headers, data=data) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    document_id = result['id']
                    print(f"✅ Document uploaded successfully! ID: {document_id}")
                    return document_id
                else:
                    text = await resp.text()
                    print(f"❌ Upload failed: {resp.status} - {text}")
                    return None

async def check_audit_logs():
    """Check the audit logs for our actions."""
    
    headers = {"X-API-Key": "gs-dev-admin-key-67890"}  # Admin key for audit access
    
    async with aiohttp.ClientSession() as session:
        print("\n🔍 Checking recent audit logs...")
        
        # Get recent audit summary
        async with session.get(f"{API_BASE}/admin/audit-logs/summary?hours_ago=1", headers=headers) as resp:
            if resp.status == 200:
                summary = await resp.json()
                print(f"📊 Audit Summary (last hour):")
                print(f"   Total actions: {summary['total_actions']}")
                print(f"   Unique users: {summary['unique_users']}")
                print(f"   Action counts: {summary['action_counts']}")
                
                if summary['recent_activity']:
                    print(f"\n📋 Recent activity:")
                    for activity in summary['recent_activity'][:3]:  # Show last 3
                        print(f"   • {activity['action']} on {activity['resource_type']} by {activity['user_id']}")
                        print(f"     at {activity['timestamp']}")
            else:
                print(f"❌ Failed to get audit summary: {resp.status}")
        
        # Get detailed logs for master user
        print(f"\n🔍 Getting logs for master user...")
        async with session.get(f"{API_BASE}/admin/audit-logs/user/master?limit=5", headers=headers) as resp:
            if resp.status == 200:
                logs = await resp.json()
                print(f"📝 Found {len(logs)} recent actions by master user:")
                for log in logs:
                    print(f"   • {log['timestamp']}: {log['action']} on {log['resource_type']}")
                    if log['details']:
                        print(f"     Details: {log['details']}")
            else:
                print(f"❌ Failed to get user logs: {resp.status}")

async def delete_document(document_id):
    """Delete the document and show audit trail."""
    
    headers = {"X-API-Key": API_KEY}
    
    async with aiohttp.ClientSession() as session:
        print(f"\n🗑️ Deleting document {document_id}...")
        async with session.delete(f"{API_BASE}/documents/{document_id}", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ {result['message']}")
            else:
                text = await resp.text()
                print(f"❌ Delete failed: {resp.status} - {text}")

async def main():
    """Demonstrate the audit trail system."""
    
    print("🎯 GovStack Audit Trail Demonstration")
    print("=" * 50)
    
    try:
        # Create test file
        file_path = await create_test_file()
        print(f"📄 Created test file: {file_path}")
        
        # Upload document
        document_id = await upload_document(file_path)
        
        if document_id:
            # Check audit logs
            await check_audit_logs()
            
            # Delete document to show more audit activity
            await delete_document(document_id)
            
            # Check audit logs again
            print(f"\n🔍 Checking audit logs after deletion...")
            await check_audit_logs()
        
        # Clean up
        os.unlink(file_path)
        
        print(f"\n" + "=" * 50)
        print("🎉 Audit trail demonstration completed!")
        print("\n💡 Key takeaways:")
        print("   • Every document upload is tracked with user information")
        print("   • All API operations create audit log entries")
        print("   • Audit logs include detailed context and metadata")
        print("   • Admin users can query audit logs for compliance/security")
        print("   • User identification is based on API key names")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
