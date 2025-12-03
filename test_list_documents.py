#!/usr/bin/env python3

import os
import requests
import pytest


BASE_URL = os.getenv("GOVSTACK_BASE_URL", "http://localhost:5000").rstrip("/")
API_KEY = os.getenv("GOVSTACK_API_KEY", os.getenv("GOVSTACK_ADMIN_API_KEY", "gs-dev-master-key-12345"))


def test_list_documents_includes_indexing_fields():
    """List documents and verify indexing fields are present in items when any exist."""
    url = f"{BASE_URL}/documents/"
    headers = {"X-API-Key": API_KEY}

    resp = requests.get(url, headers=headers, timeout=15)
    assert resp.status_code == 200, f"GET /documents/ failed: {resp.status_code} {resp.text}"

    data = resp.json()
    assert isinstance(data, list)

    if not data:
        pytest.skip("No documents available to validate indexing fields")

    doc = data[0]
    assert "is_indexed" in doc, "Expected 'is_indexed' key in document payload"
    assert "indexed_at" in doc, "Expected 'indexed_at' key in document payload"
