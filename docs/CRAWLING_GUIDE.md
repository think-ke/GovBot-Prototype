# Web Crawling Guide

The crawler fetches and stores website content into the database and can tag content with `collection_id` for RAG.

## Key Concepts

- `collection_id`: groups webpages for indexing and retrieval
- Depth/strategy: configure crawl depth and BFS strategy for coverage

## Typical Flow

1) Start a crawl (examples in root README under Web Crawler Features)
2) Monitor progress via API logs
3) Extract texts or view collection stats
4) Index with the RAG indexer (background or manual)

## Useful Endpoints (examples)

- Start crawl: `POST /crawl/`
- Get webpages by collection: `GET /webpages/collection/{collection_id}`
- Extract texts: `POST /extract-texts/`
- Collection stats: `GET /collection-stats/{collection_id}`

## Scripts

- Update webpage collections: `scripts/update_webpage_collections.py`
- Add indexing columns (migration): `scripts/add_indexing_columns.py`

Also see: `app/core/rag/README.md` for indexing details and `scripts/run_indexing.py` to manually index collections.
