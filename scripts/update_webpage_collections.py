"""
Script to update collection_id for existing webpages in the database.
This is useful for organizing previously crawled pages into collections.
"""

import argparse
import asyncio
import os
import sys
import logging
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models.webpage import Webpage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def update_collection_by_domain(domain, collection_id, db_url):
    """Update collection_id for all webpages from a specific domain."""
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find webpages by domain
        query = select(Webpage).where(Webpage.url.like(f'%{domain}%'))
        result = await session.execute(query)
        webpages = result.scalars().all()
        
        if not webpages:
            logger.warning(f"No webpages found for domain: {domain}")
            return 0
        
        # Update collection_id for all matching webpages
        count = 0
        for webpage in webpages:
            webpage.collection_id = collection_id
            count += 1
        
        await session.commit()
        logger.info(f"Updated {count} webpages with collection_id: {collection_id}")
        return count

async def update_collection_by_id_range(start_id, end_id, collection_id, db_url):
    """Update collection_id for webpages in a specific ID range."""
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find webpages by ID range
        query = select(Webpage).where(Webpage.id >= start_id).where(Webpage.id <= end_id)
        result = await session.execute(query)
        webpages = result.scalars().all()
        
        if not webpages:
            logger.warning(f"No webpages found in ID range: {start_id} - {end_id}")
            return 0
        
        # Update collection_id for all matching webpages
        count = 0
        for webpage in webpages:
            webpage.collection_id = collection_id
            count += 1
        
        await session.commit()
        logger.info(f"Updated {count} webpages with collection_id: {collection_id}")
        return count

async def list_collections(db_url):
    """List all collection IDs currently in use."""
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find distinct collection_ids
        query = select(Webpage.collection_id).distinct()
        result = await session.execute(query)
        collections = result.scalars().all()
        
        if not collections:
            logger.info("No collections found in the database.")
            return []
        
        logger.info(f"Found {len(collections)} collections:")
        for coll in collections:
            if coll:  # Skip None values
                logger.info(f"  - {coll}")
        
        return collections

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Update collection_id for existing webpages')
    
    # Database URL argument
    parser.add_argument('--db-url', type=str, 
                        default=os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/govstackdb'),
                        help='Database URL (default: from DATABASE_URL env var)')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Update by domain command
    domain_parser = subparsers.add_parser('domain', help='Update webpages by domain')
    domain_parser.add_argument('domain', type=str, help='Domain to match (e.g., ecitizen.go.ke)')
    domain_parser.add_argument('collection_id', type=str, help='Collection ID to assign')
    
    # Update by ID range command
    id_range_parser = subparsers.add_parser('id-range', help='Update webpages by ID range')
    id_range_parser.add_argument('start_id', type=int, help='Starting webpage ID')
    id_range_parser.add_argument('end_id', type=int, help='Ending webpage ID')
    id_range_parser.add_argument('collection_id', type=str, help='Collection ID to assign')
    
    # List collections command
    subparsers.add_parser('list', help='List all collection IDs currently in use')
    
    return parser.parse_args()

async def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    if args.command == 'domain':
        count = await update_collection_by_domain(args.domain, args.collection_id, args.db_url)
        print(f"Updated {count} webpages with collection_id: {args.collection_id}")
    
    elif args.command == 'id-range':
        count = await update_collection_by_id_range(args.start_id, args.end_id, args.collection_id, args.db_url)
        print(f"Updated {count} webpages with collection_id: {args.collection_id}")
    
    elif args.command == 'list':
        await list_collections(args.db_url)
    
    else:
        print("Please provide a valid command. Use --help for more information.")

if __name__ == "__main__":
    asyncio.run(main())
