#!/usr/bin/env python3
"""
Script to manually index uploaded documents for specific collections.
"""

import asyncio
import logging
import argparse
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.core.rag.indexer import index_uploaded_documents_by_collection, has_unindexed_uploaded_documents
    from app.db.database import async_session
    from sqlalchemy import select
    from app.db.models.document import Document as DocumentModel
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running this script from the project root directory")
    sys.exit(1)

async def check_indexing_status(collection_id: str = None):
    """Check the indexing status of uploaded documents."""
    async with async_session() as db:
        try:
            if collection_id:
                # Check specific collection
                has_unindexed, count = await has_unindexed_uploaded_documents(db, collection_id)
                logger.info(f"Collection '{collection_id}': {count} unindexed documents")
                
                # Get total count for the collection
                total_query = select(DocumentModel).where(DocumentModel.collection_id == collection_id)
                total_result = await db.execute(total_query)
                total_count = len(total_result.scalars().all())
                indexed_count = total_count - count
                
                logger.info(f"Collection '{collection_id}': {indexed_count}/{total_count} documents indexed")
                
            else:
                # Check all collections
                collections_query = select(DocumentModel.collection_id).distinct()
                collections_result = await db.execute(collections_query)
                collections = [row[0] for row in collections_result.fetchall() if row[0]]
                
                if not collections:
                    logger.info("No documents found in any collection")
                    return
                
                logger.info(f"Found {len(collections)} collections with uploaded documents")
                
                for coll_id in collections:
                    has_unindexed, count = await has_unindexed_uploaded_documents(db, coll_id)
                    
                    # Get total count for the collection
                    total_query = select(DocumentModel).where(DocumentModel.collection_id == coll_id)
                    total_result = await db.execute(total_query)
                    total_count = len(total_result.scalars().all())
                    indexed_count = total_count - count
                    
                    status = "❌ Has unindexed" if has_unindexed else "✅ All indexed"
                    logger.info(f"  {coll_id}: {indexed_count}/{total_count} indexed - {status}")
                    
        except Exception as e:
            logger.error(f"Error checking indexing status: {e}")

async def run_document_indexing(collection_id: str = None):
    """Run document indexing for uploaded documents."""
    try:
        if collection_id:
            # Index specific collection
            logger.info(f"Starting document indexing for collection: {collection_id}")
            result = await index_uploaded_documents_by_collection(collection_id)
            
            if result["status"] == "completed":
                logger.info(f"✅ Indexing completed successfully!")
                logger.info(f"   Documents processed: {result['documents_processed']}")
                logger.info(f"   Documents indexed: {result['documents_indexed']}")
                logger.info(f"   Processing time: {result.get('processing_time_seconds', 0):.2f} seconds")
            else:
                logger.error(f"❌ Indexing failed: {result.get('error', 'Unknown error')}")
                
        else:
            # Index all collections with unindexed documents
            async with async_session() as db:
                collections_query = select(DocumentModel.collection_id).distinct()
                collections_result = await db.execute(collections_query)
                collections = [row[0] for row in collections_result.fetchall() if row[0]]
                
                if not collections:
                    logger.info("No documents found in any collection")
                    return
                
                logger.info(f"Checking {len(collections)} collections for unindexed documents")
                
                indexed_collections = 0
                for coll_id in collections:
                    has_unindexed, count = await has_unindexed_uploaded_documents(db, coll_id)
                    
                    if has_unindexed:
                        logger.info(f"Indexing collection '{coll_id}' ({count} documents)...")
                        result = await index_uploaded_documents_by_collection(coll_id)
                        
                        if result["status"] == "completed":
                            logger.info(f"✅ Collection '{coll_id}' indexed successfully")
                            indexed_collections += 1
                        else:
                            logger.error(f"❌ Failed to index collection '{coll_id}': {result.get('error', 'Unknown error')}")
                    else:
                        logger.info(f"✅ Collection '{coll_id}' already fully indexed")
                
                logger.info(f"Completed indexing {indexed_collections} collections")
                
    except Exception as e:
        logger.error(f"Error during document indexing: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Index uploaded documents for GovStack RAG system")
    parser.add_argument("--collection", "-c", type=str, help="Collection ID to index (if not specified, indexes all collections)")
    parser.add_argument("--status", "-s", action="store_true", help="Check indexing status without running indexing")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    start_time = datetime.now(timezone.utc)
    logger.info(f"Document indexing script started at {start_time.isoformat()}")
    
    if args.status:
        await check_indexing_status(args.collection)
    else:
        await run_document_indexing(args.collection)
    
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Script completed in {duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
