# Data Currency and Update SOP

## Ownership
- Data Ops Lead (internal) and Agency POCs (external) co-own updates.

## Cadence
- Weekly incremental crawl and re-index per collection.
- Emergency updates within 24h for critical policy changes.

## Implementation Hooks
- Indexer: `app/core/rag/indexer.py` (extract_texts_by_collection, get_collection_stats).
- APIs: `/collection-stats` endpoints expose latest crawl/index times.
- Knowledge gaps: from `/chat` events to drive backlog.

## User Transparency
- UI badge: “Last updated: <date>”.
- Release notes summary for major content refreshes.

## Safeguards
- If documents are stale beyond SLA, show a caution note and link to official site.