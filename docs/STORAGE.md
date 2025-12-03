# Storage Guide (MinIO and ChromaDB)

GovStack uses MinIO for object storage and ChromaDB for vector embeddings.

## MinIO (Object Storage)

- Purpose: store uploaded documents and processed assets
- Access:
  - API: http://localhost:9000
  - Console: http://localhost:9001
- Credentials: `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` from `.env`
- Bucket: `MINIO_BUCKET_NAME` (default `govstack-docs`)
- Data location: `data/minio` (prod) and `data/minio-dev` (dev)

## ChromaDB (Vector Store)

- Purpose: store embeddings for RAG retrieval
- Access (prod): http://localhost:8050
- Access (dev): http://localhost:8001 (see `CHROMA_DEV_PORT` in `.env.example`)
- Auth: basic auth via `server.htpasswd` (must match `CHROMA_USERNAME`/`CHROMA_PASSWORD`)
- Data location: `data/chroma` (prod) and `data/chroma-dev` (dev)

## Common Issues

- 401 unauthorized to Chroma: regenerate `server.htpasswd` using `CHROMA_USERNAME`/`CHROMA_PASSWORD`
- Missing bucket in MinIO: create the bucket named in `MINIO_BUCKET_NAME` via console
- Permission denied writing `data/`: ensure host paths exist and are writable
