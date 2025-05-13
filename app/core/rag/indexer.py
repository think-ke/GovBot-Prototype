"""
Indexer module for extracting text content from crawled webpages.
This module provides functions to retrieve and process text content
for use in Retrieval Augmented Generation (RAG) systems.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Union, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.webpage import Webpage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def extract_texts_by_collection(
    db: AsyncSession,
    collection_id: str,
    hours_ago: Optional[int] = 24,
    include_title: bool = True,
    include_url: bool = True
) -> List[Dict[str, str]]:
    """
    Extract text content from webpages in a specific collection that were
    crawled within the specified time period.
    
    Args:
        db: Database session
        collection_id: The collection ID to filter by
        hours_ago: Extract pages from the last N hours (None for all)
        include_title: Whether to include the webpage title in the result
        include_url: Whether to include the webpage URL in the result
        
    Returns:
        List of dictionaries containing webpage content and metadata
    """
    try:
        # Build query base with collection filter
        query = select(Webpage).where(Webpage.collection_id == collection_id)
        
        # Add time filter if hours_ago is specified
        if hours_ago is not None:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            query = query.where(Webpage.last_crawled >= time_threshold)
        
        # Execute query
        result = await db.execute(query)
        webpages = result.scalars().all()
        
        # Process results
        texts = []
        for webpage in webpages:
            if not webpage.content_markdown:
                continue
                
            webpage_data = {}
            
            # Add metadata if requested
            if include_title and webpage.title:
                webpage_data["title"] = webpage.title
            
            if include_url:
                webpage_data["url"] = webpage.url
            
            # Add content
            webpage_data["content"] = webpage.content_markdown
            webpage_data["id"] = webpage.id
            webpage_data["last_crawled"] = webpage.last_crawled.isoformat() if webpage.last_crawled else None
            
            texts.append(webpage_data)
        
        logger.info(f"Extracted {len(texts)} texts from collection '{collection_id}'")
        return texts
    
    except Exception as e:
        logger.error(f"Error extracting texts from collection '{collection_id}': {e}")
        raise

async def extract_text_batch(
    db: AsyncSession,
    collection_id: str,
    hours_ago: Optional[int] = 24,
    output_format: str = "text"
) -> Union[str, List[Dict[str, str]]]:
    """
    Extract and format text content from webpages in a specific collection.
    
    Args:
        db: Database session
        collection_id: The collection ID to filter by
        hours_ago: Extract pages from the last N hours (None for all)
        output_format: Format for the output ("text", "json", "markdown")
        
    Returns:
        Formatted content based on output_format
    """
    texts = await extract_texts_by_collection(
        db=db, 
        collection_id=collection_id,
        hours_ago=hours_ago,
        include_title=True,
        include_url=True
    )
    
    if output_format == "json":
        return texts
    
    elif output_format == "markdown":
        # Format as markdown with document separators
        markdown_content = ""
        for item in texts:
            markdown_content += f"# {item.get('title', 'Untitled Document')}\n"
            markdown_content += f"Source: {item.get('url', 'Unknown')}\n\n"
            markdown_content += f"{item.get('content', '')}\n\n"
            markdown_content += "---\n\n"
        return markdown_content
    
    else:  # Default to raw text
        text_content = ""
        for item in texts:
            if item.get('title'):
                text_content += f"{item['title']}\n\n"
            text_content += f"{item.get('content', '')}\n\n"
            text_content += "------\n\n"
        return text_content

async def get_collection_stats(
    db: AsyncSession,
    collection_id: Optional[str] = None
) -> Dict[str, any]:
    """
    Get statistics about collections or a specific collection.
    
    Args:
        db: Database session
        collection_id: Optional collection ID to filter by
        
    Returns:
        Dictionary of collection statistics
    """
    try:
        if collection_id:
            # Stats for a specific collection
            query = select(Webpage).where(Webpage.collection_id == collection_id)
            result = await db.execute(query)
            webpages = result.scalars().all()
            
            # Find earliest and latest crawl dates
            earliest_crawl = None
            latest_crawl = None
            total_characters = 0
            
            for webpage in webpages:
                if webpage.content_markdown:
                    total_characters += len(webpage.content_markdown)
                
                if webpage.first_crawled:
                    if earliest_crawl is None or webpage.first_crawled < earliest_crawl:
                        earliest_crawl = webpage.first_crawled
                
                if webpage.last_crawled:
                    if latest_crawl is None or webpage.last_crawled > latest_crawl:
                        latest_crawl = webpage.last_crawled
            
            return {
                "collection_id": collection_id,
                "webpage_count": len(webpages),
                "total_characters": total_characters,
                "earliest_crawl": earliest_crawl.isoformat() if earliest_crawl else None,
                "latest_crawl": latest_crawl.isoformat() if latest_crawl else None
            }
        else:
            # Stats for all collections
            from sqlalchemy import func
            
            # Get distinct collection IDs
            query = select(Webpage.collection_id, func.count(Webpage.id).label("count")).\
                group_by(Webpage.collection_id)
            result = await db.execute(query)
            collections = result.fetchall()
            
            collection_stats = []
            for coll_id, count in collections:
                if coll_id:  # Skip None values
                    collection_stats.append({
                        "collection_id": coll_id,
                        "webpage_count": count
                    })
            
            return {
                "total_collections": len(collection_stats),
                "collections": collection_stats
            }
    
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        raise



from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter, 
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache

# create the pipeline with transformations
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=25, chunk_overlap=0),
        TitleExtractor(),
        OpenAIEmbedding(),
    ]
)

# run the pipeline
nodes = pipeline.run(documents=[Document.example()])


index = VectorStoreIndex(nodes)