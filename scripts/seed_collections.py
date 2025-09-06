#!/usr/bin/env python3
"""
Seed initial collections into the database (one time / idempotent).

This imports the legacy agency collections so existing tooling has data:
- kfc  (Kenya Film Commission)
- kfcb (Kenya Film Classification Board)
- brs  (Business Registration Service)
- odpc (Office of the Data Protection Commissioner)

Usage:
  python scripts/seed_collections.py

Environment:
  DATABASE_URL (asyncpg) or default postgresql+asyncpg://postgres:postgres@localhost/govstackdb
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.collection import Collection

LEGACY_COLLECTIONS: Dict[str, Dict[str, str]] = {
    "kfc": {
        "name": "Kenya Film Commission",
        "description": (
            "Kenya Film Commission is a government agency responsible for promoting "
            "and facilitating the growth of the film industry in Kenya. It provides "
            "support to filmmakers, promotes Kenya as a filming destination, and works "
            "to develop local talent and infrastructure."
        ),
        "type": "mixed",
    },
    "kfcb": {
        "name": "Kenya Film Classification Board",
        "description": (
            "The Kenya Film Classification Board (KFCB) is a government agency responsible "
            "for regulating the film and broadcast industry in Kenya. It ensures that films "
            "and broadcasts comply with the law, promotes local content, and protects children "
            "from harmful content."
        ),
        "type": "mixed",
    },
    "brs": {
        "name": "Business Registration Service",
        "description": (
            "The Business Registration Service (BRS) is a government agency responsible for "
            "registering and regulating businesses in Kenya. It provides services such as business "
            "name registration, company registration, and issuance of certificates."
        ),
        "type": "mixed",
    },
    "odpc": {
        "name": "Office of the Data Protection Commissioner",
        "description": (
            "The Office of the Data Protection Commissioner (ODPC) is a government agency responsible "
            "for overseeing data protection and privacy in Kenya. It ensures compliance with data protection "
            "laws and promotes awareness of data rights."
        ),
        "type": "mixed",
    },
}

async def main():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/govstackdb")
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        created = 0
        for cid, data in LEGACY_COLLECTIONS.items():
            # Check if exists by ID or by name (name is unique) without autoflush
            with session.no_autoflush:
                exists_by_id = (await session.execute(
                    select(Collection).where(Collection.id == cid)
                )).scalars().first()
            if exists_by_id:
                continue

            with session.no_autoflush:
                exists_by_name = (await session.execute(
                    select(Collection).where(Collection.name == data["name"])
                )).scalars().first()
            if exists_by_name:
                # Respect existing row (possibly created via API) and skip creating another
                continue

            obj = Collection(
                id=cid,
                name=data["name"],
                description=data.get("description"),
                collection_type=data.get("type", "mixed"),
                api_key_name=None,
            )
            session.add(obj)
            try:
                await session.flush()  # Validate insert without committing all
                created += 1
            except IntegrityError:
                # Another process may have inserted concurrently; ignore
                await session.rollback()
                continue
        if created:
            await session.commit()
        print(f"Seed complete. Created {created} collections.")

if __name__ == "__main__":
    asyncio.run(main())
