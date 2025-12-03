#!/usr/bin/env python
"""
Cleanup script for chat event tracking system.
Removes old events and manages database maintenance.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
import argparse

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.utils.chat_event_service import ChatEventService

async def cleanup_events(hours_old: int = 24, dry_run: bool = False):
    """
    Clean up old chat events.
    
    Args:
        hours_old: Delete events older than this many hours
        dry_run: If True, only count events without deleting
    """
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    
    # Handle Windows-specific issue with localhost
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")

    logger.info(f"Connecting to database: {database_url}")
    
    # Create engine and session
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            if dry_run:
                logger.info(f"DRY RUN: Would delete events older than {hours_old} hours")
                # Count events that would be deleted
                from sqlalchemy import select, func
                from datetime import timedelta
                from app.db.models.chat_event import ChatEvent
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_old)
                count_query = select(func.count(ChatEvent.id)).where(ChatEvent.timestamp < cutoff_time)
                result = await session.execute(count_query)
                count = result.scalar()
                
                logger.info(f"DRY RUN: Found {count} events that would be deleted")
            else:
                deleted_count = await ChatEventService.cleanup_old_events(session, hours_old)
                logger.info(f"Successfully deleted {deleted_count} old events")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise
    finally:
        await engine.dispose()

async def get_event_statistics():
    """Get statistics about chat events in the database."""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            from sqlalchemy import select, func, text
            from app.db.models.chat_event import ChatEvent
            
            # Total events
            total_query = select(func.count(ChatEvent.id))
            total_result = await session.execute(total_query)
            total_events = total_result.scalar()
            
            # Events by type
            type_query = select(ChatEvent.event_type, func.count(ChatEvent.id)).group_by(ChatEvent.event_type)
            type_result = await session.execute(type_query)
            events_by_type = type_result.all()
            
            # Events by status
            status_query = select(ChatEvent.event_status, func.count(ChatEvent.id)).group_by(ChatEvent.event_status)
            status_result = await session.execute(status_query)
            events_by_status = status_result.all()
            
            # Recent events (last 24 hours)
            recent_query = select(func.count(ChatEvent.id)).where(
                ChatEvent.timestamp > func.now() - text("INTERVAL '24 hours'")
            )
            recent_result = await session.execute(recent_query)
            recent_events = recent_result.scalar()
            
            # Active sessions (with events in last 24 hours)
            active_sessions_query = select(func.count(func.distinct(ChatEvent.session_id))).where(
                ChatEvent.timestamp > func.now() - text("INTERVAL '24 hours'")
            )
            active_sessions_result = await session.execute(active_sessions_query)
            active_sessions = active_sessions_result.scalar()
            
            logger.info("=== Chat Event Statistics ===")
            logger.info(f"Total events: {total_events}")
            logger.info(f"Recent events (24h): {recent_events}")
            logger.info(f"Active sessions (24h): {active_sessions}")
            
            logger.info("\nEvents by type:")
            for event_type, count in events_by_type:
                logger.info(f"  {event_type}: {count}")
            
            logger.info("\nEvents by status:")
            for status, count in events_by_status:
                logger.info(f"  {status}: {count}")
                
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise
    finally:
        await engine.dispose()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Chat event tracking cleanup and maintenance")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old events')
    cleanup_parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Delete events older than this many hours (default: 24)'
    )
    cleanup_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    # Statistics command
    subparsers.add_parser('stats', help='Show event statistics')
    
    # Database URL option
    parser.add_argument(
        '--database-url',
        help='Database URL (defaults to DATABASE_URL environment variable)'
    )
    
    return parser.parse_args()

async def main():
    """Main function."""
    args = parse_args()
    
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
    
    try:
        if args.command == 'cleanup':
            await cleanup_events(args.hours, args.dry_run)
        elif args.command == 'stats':
            await get_event_statistics()
        else:
            logger.error("Please specify a command: cleanup or stats")
            return 1
            
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
