@app.get("/webpages/collection/{collection_id}", response_model=List[WebpageResponse])
async def get_webpages_by_collection(
    collection_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all webpages in a specific collection.
    
    Args:
        collection_id: The collection ID to filter by
        limit: Maximum number of results to return
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of webpages in the collection
    """
    try:
        query = select(Webpage).where(Webpage.collection_id == collection_id).limit(limit).offset(offset)
        result = await db.execute(query)
        webpages = result.scalars().all()
        
        return [WebpageResponse(
            id=webpage.id,
            url=webpage.url,
            title=webpage.title,
            crawl_depth=webpage.crawl_depth,
            last_crawled=webpage.last_crawled.isoformat() if webpage.last_crawled else None,
            status_code=webpage.status_code,
            collection_id=webpage.collection_id
        ) for webpage in webpages]
    except Exception as e:
        logger.error(f"Error fetching webpages by collection: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching webpages: {str(e)}")
