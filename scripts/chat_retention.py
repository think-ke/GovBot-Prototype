#!/usr/bin/env python
"""
Chat retention cleanup script.
Purges chat sessions and messages older than a configured retention period.

Usage examples:
  - Cleanup chats older than 90 days (default):
      ./scripts/chat_retention.py cleanup --days 90
  - Dry run (no deletes):
      ./scripts/chat_retention.py cleanup --days 90 --dry-run
  - Show statistics:
      ./scripts/chat_retention.py stats
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
import argparse

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func

from app.db.models.chat import Chat, ChatMessage
from app.utils.chat_persistence import ChatPersistenceService


async def cleanup_chats(days: int = 90, dry_run: bool = False):
    """Cleanup chats older than the given number of days."""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")

    # Handle Windows-specific issue with localhost
    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")

    logger.info(f"Connecting to database: {database_url}")

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        async with async_session() as session:
            if dry_run:
                logger.info(f"DRY RUN: Would delete chats last updated before {cutoff.isoformat()}")

                # Count chats and messages that would be deleted
                chat_count_q = select(func.count(Chat.id)).where(Chat.updated_at < cutoff)
                msg_count_q = select(func.count(ChatMessage.id)).where(
                    ChatMessage.chat_id.in_(select(Chat.id).where(Chat.updated_at < cutoff))
                )

                chat_count = (await session.execute(chat_count_q)).scalar() or 0
                msg_count = (await session.execute(msg_count_q)).scalar() or 0

                logger.info(f"DRY RUN: Found {chat_count} chats and {msg_count} messages eligible for deletion")
                return {"messages_deleted": 0, "chats_deleted": 0, "eligible_chats": chat_count, "eligible_messages": msg_count}
            else:
                result = await ChatPersistenceService.cleanup_old_chats(session, retention_days=days)
                logger.info(
                    f"Deleted {result['messages_deleted']} messages and {result['chats_deleted']} chats older than {days} days"
                )
                return result
    except Exception as e:
        logger.error(f"Error during chat cleanup: {e}")
        raise
    finally:
        await engine.dispose()


async def get_chat_statistics():
    """Get basic statistics about chats and messages in the database."""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")

    if "localhost" in database_url and os.name == "nt":
        database_url = database_url.replace("localhost", "127.0.0.1")

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            total_chats = (await session.execute(select(func.count(Chat.id)))).scalar() or 0
            total_messages = (await session.execute(select(func.count(ChatMessage.id)))).scalar() or 0

            logger.info("=== Chat Retention Statistics ===")
            logger.info(f"Total chats: {total_chats}")
            logger.info(f"Total messages: {total_messages}")

    except Exception as e:
        logger.error(f"Error getting chat statistics: {e}")
        raise
    finally:
        await engine.dispose()


def parse_args():
    parser = argparse.ArgumentParser(description="Chat retention cleanup and statistics")

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old chats')
    cleanup_parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Delete chats older than this many days (default: 90)'
    )
    cleanup_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )

    # Statistics command
    subparsers.add_parser('stats', help='Show chat statistics')

    # Database URL option
    parser.add_argument(
        '--database-url',
        help='Database URL (defaults to DATABASE_URL environment variable)'
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url

    try:
        if args.command == 'cleanup':
            await cleanup_chats(args.days, args.dry_run)
        elif args.command == 'stats':
            await get_chat_statistics()
        else:
            logger.error("Please specify a command: cleanup or stats")
            return 1

        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
