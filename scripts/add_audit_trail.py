#!/usr/bin/env python3
"""
Migration script to add audit trail columns to existing tables.
Run this script to add user tracking fields to documents and webpages tables.
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine
from app.db.models.audit_log import Base as AuditBase

async def add_audit_columns():
    """Add audit trail columns to existing tables."""
    
    print("Starting audit trail migration...")
    
    async with engine.begin() as conn:
        try:
            # Create audit_logs table
            print("Creating audit_logs table...")
            await conn.run_sync(AuditBase.metadata.create_all)
            print("✓ Audit logs table created")
            
            # Add columns to documents table
            print("Adding audit columns to documents table...")
            
            # Check if columns already exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name IN ('created_by', 'updated_by', 'api_key_name')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'created_by' not in existing_columns:
                await conn.execute(text("ALTER TABLE documents ADD COLUMN created_by VARCHAR(100)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_created_by ON documents(created_by)"))
                print("✓ Added created_by column to documents")
            else:
                print("✓ created_by column already exists in documents")
                
            if 'updated_by' not in existing_columns:
                await conn.execute(text("ALTER TABLE documents ADD COLUMN updated_by VARCHAR(100)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_updated_by ON documents(updated_by)"))
                print("✓ Added updated_by column to documents")
            else:
                print("✓ updated_by column already exists in documents")
                
            if 'api_key_name' not in existing_columns:
                await conn.execute(text("ALTER TABLE documents ADD COLUMN api_key_name VARCHAR(100)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_api_key_name ON documents(api_key_name)"))
                print("✓ Added api_key_name column to documents")
            else:
                print("✓ api_key_name column already exists in documents")
            
            # Add columns to webpages table
            print("Adding audit columns to webpages table...")
            
            # Check if columns already exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'webpages' AND column_name IN ('created_by', 'updated_by', 'api_key_name')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'created_by' not in existing_columns:
                await conn.execute(text("ALTER TABLE webpages ADD COLUMN created_by VARCHAR(100)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_webpages_created_by ON webpages(created_by)"))
                print("✓ Added created_by column to webpages")
            else:
                print("✓ created_by column already exists in webpages")
                
            if 'updated_by' not in existing_columns:
                await conn.execute(text("ALTER TABLE webpages ADD COLUMN updated_by VARCHAR(100)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_webpages_updated_by ON webpages(updated_by)"))
                print("✓ Added updated_by column to webpages")
            else:
                print("✓ updated_by column already exists in webpages")
                
            if 'api_key_name' not in existing_columns:
                await conn.execute(text("ALTER TABLE webpages ADD COLUMN api_key_name VARCHAR(100)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_webpages_api_key_name ON webpages(api_key_name)"))
                print("✓ Added api_key_name column to webpages")
            else:
                print("✓ api_key_name column already exists in webpages")
            
            print("Migration completed successfully! 🎉")
            
        except OperationalError as e:
            if "already exists" in str(e).lower():
                print(f"Column already exists, skipping: {e}")
            else:
                raise e

async def main():
    """Main migration function."""
    try:
        await add_audit_columns()
        print("\n✅ Audit trail migration completed successfully!")
        print("\nThe following features are now available:")
        print("- All document uploads will be tracked with user information")
        print("- All webpage crawls will be tracked with user information")
        print("- Complete audit log of all API operations")
        print("- User identification for all data modifications")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
