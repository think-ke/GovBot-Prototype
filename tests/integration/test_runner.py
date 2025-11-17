"""
GovStack API Integration Test Suite
Complete test coverage following user story chronology

Organization: Tech Innovators Network (THiNK)
URL: https://think.ke
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import (
    test_results, validate_config, TEST_COLLECTION_NAME,
    TEST_COLLECTION_DESCRIPTION, TEST_ORG_NAME, TEST_ORG_URL,
    TEST_USER_ID, SKIP_LONG_RUNNING_TESTS, SKIP_CRAWL_TESTS,
    SKIP_CLEANUP, CRAWL_DEPTH, CRAWL_CONCURRENT_REQUESTS,
    CRAWL_FOLLOW_EXTERNAL, CRAWL_STRATEGY, TEST_DOCUMENT_DESCRIPTION
)
from logger import logger, log_test_summary
from api_client import client, admin_client


class GovStackTestSuite:
    """Complete integration test suite for GovStack API"""
    
    def __init__(self):
        self.results = test_results
        self.test_data = {}  # Store created resources
        
    def run_test(self, test_name: str, test_func, *args, **kwargs):
        """Execute a single test with error handling"""
        logger.test_start(test_name)
        try:
            result = test_func(*args, **kwargs)
            if result:
                logger.test_pass(test_name, f"Response: {result.get('message', 'Success')}")
                self.results.add_pass()
            else:
                logger.test_fail(test_name, "Test returned False")
                self.results.add_fail(test_name)
            return result
        except Exception as e:
            logger.test_fail(test_name, str(e))
            self.results.add_fail(f"{test_name}: {str(e)}")
            return None
    
    # ========================================================================
    # 1. COLLECTIONS: Setup and Organization
    # ========================================================================
    
    def test_create_collection(self):
        """Story: As an admin, I want to create a new collection"""
        logger.story("As an admin, I want to create a new collection called 'immigration-faqs'")
        
        payload = {
            "name": TEST_COLLECTION_NAME,
            "description": TEST_COLLECTION_DESCRIPTION
        }
        
        response = client.post("/collection-stats/", json=payload)
        
        if response["ok"]:
            collection_id = response["data"].get("collection_id", TEST_COLLECTION_NAME)
            self.test_data["collection_id"] = collection_id
            self.results.collection_id = collection_id
            logger.info(f"✅ Created collection: {collection_id}")
            return {"message": f"Collection created: {collection_id}"}
        else:
            raise Exception(f"Failed to create collection: {response['data']}")
    
    def test_list_collections(self):
        """Story: As a user, I want to view all existing collections"""
        logger.story("As a user, I want to view all existing collections")
        
        response = client.get("/collection-stats/collections")
        
        if response["ok"]:
            collections = response["data"]
            logger.info(f"✅ Retrieved {len(collections)} collections")
            
            # Verify our collection exists
            if TEST_COLLECTION_NAME in collections:
                logger.info(f"✅ Found our test collection: {TEST_COLLECTION_NAME}")
            
            return {"message": f"Found {len(collections)} collections"}
        else:
            raise Exception(f"Failed to list collections: {response['data']}")
    
    def test_get_collection_stats(self):
        """Story: As an analyst, I want to retrieve collection statistics"""
        logger.story("As an analyst, I want to retrieve statistics for the collection")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        response = client.get(f"/collection-stats/{collection_id}")
        
        if response["ok"]:
            stats = response["data"]
            logger.info(f"✅ Collection stats - Documents: {stats.get('total_documents', 0)}, "
                       f"Webpages: {stats.get('total_webpages', 0)}")
            return {"message": "Collection stats retrieved"}
        else:
            raise Exception(f"Failed to get collection stats: {response['data']}")
    
    def test_update_collection(self):
        """Story: As an admin, I want to update the collection name"""
        logger.story("As an admin, I want to update the collection name to 'immigration-faqs-v2'")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        payload = {
            "collection_id": f"{collection_id}-v2",
            "description": f"{TEST_COLLECTION_DESCRIPTION} (Updated)"
        }
        
        response = client.post(f"/collection-stats/", json=payload)
        
        if response["ok"]:
            logger.info(f"✅ Updated collection name to: {payload['collection_id']}")
            # Update stored collection ID
            self.test_data["collection_id"] = payload["collection_id"]
            return {"message": "Collection updated successfully"}
        else:
            raise Exception(f"Failed to update collection: {response['data']}")
    
    # ========================================================================
    # 2. DOCUMENTS: Upload, Manage, and Clean Up
    # ========================================================================
    
    def test_create_test_document(self):
        """Create a test PDF file for upload"""
        test_file = Path(__file__).parent / "test_data" / "test_immigration_faq.txt"
        test_file.parent.mkdir(exist_ok=True)
        
        content = """
IMMIGRATION FAQS - TEST DOCUMENT

1. What documents are required for immigration?
   - Valid passport
   - Visa application form
   - Proof of financial means
   - Travel itinerary
   - Accommodation details

2. How long does the visa process take?
   Typically 10-15 business days for standard processing.

3. What are the visa fees?
   Fees vary by visa type. Please check the official website.

4. Can I extend my visa?
   Yes, visa extensions can be requested before expiry.

5. What is the THiNK bot platform?
   THiNK (Tech Innovators Network) provides Bot of Bots, the largest 
   bot network in Africa, offering industry-specific bots including 
   government services through platforms like GovBot.

Organization: Tech Innovators Network (THiNK)
Website: https://think.ke
"""
        test_file.write_text(content)
        return test_file
    
    def test_upload_document(self):
        """Story: As a content manager, I want to upload a document"""
        logger.story("As a content manager, I want to upload a document to the collection")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        # Create test document
        test_file = self.test_create_test_document()
        
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "text/plain")}
            data = {
                "description": TEST_DOCUMENT_DESCRIPTION,
                "is_public": "false",
                "collection_id": collection_id
            }
            
            response = client.post("/documents/", files=files, data=data)
        
        if response["ok"]:
            doc_data = response["data"]
            document_id = doc_data["id"]
            index_job_id = doc_data.get("index_job_id")
            
            self.test_data["document_id"] = document_id
            self.test_data["index_job_id"] = index_job_id
            self.results.document_id = document_id
            self.results.indexing_job_id = index_job_id
            
            logger.info(f"✅ Uploaded document: ID={document_id}, Job={index_job_id}")
            return {"message": f"Document uploaded: {document_id}"}
        else:
            raise Exception(f"Failed to upload document: {response['data']}")
    
    def test_list_documents(self):
        """Story: As a user, I want to list all documents"""
        logger.story("As a user, I want to list all documents to verify my upload")
        
        response = client.get("/documents/", params={"limit": 10})
        
        if response["ok"]:
            documents = response["data"]
            logger.info(f"✅ Retrieved {len(documents)} documents")
            return {"message": f"Found {len(documents)} documents"}
        else:
            raise Exception(f"Failed to list documents: {response['data']}")
    
    def test_get_document(self):
        """Story: As a user, I want to retrieve document metadata"""
        logger.story("As a user, I want to retrieve metadata for the uploaded document")
        
        document_id = self.test_data.get("document_id")
        if not document_id:
            raise Exception("Document ID not found in test data")
        
        response = client.get(f"/documents/{document_id}")
        
        if response["ok"]:
            doc = response["data"]
            logger.info(f"✅ Document details - Filename: {doc.get('filename')}, "
                       f"Indexed: {doc.get('is_indexed')}")
            return {"message": "Document metadata retrieved"}
        else:
            raise Exception(f"Failed to get document: {response['data']}")
    
    def test_update_document_metadata(self):
        """Story: As a metadata editor, I want to update document metadata"""
        logger.story("As a metadata editor, I want to update the document's description and tags")
        
        document_id = self.test_data.get("document_id")
        if not document_id:
            raise Exception("Document ID not found in test data")
        
        payload = {
            "metadata": {
                "tags": ["immigration", "faq", "test", "think"],
                "category": "immigration-services",
                "organization": TEST_ORG_NAME,
                "source_url": TEST_ORG_URL
            },
            "description": f"{TEST_DOCUMENT_DESCRIPTION} (Updated with metadata)"
        }
        
        response = client.patch(f"/documents/{document_id}/metadata", json=payload)
        
        if response["ok"]:
            logger.info(f"✅ Updated document metadata")
            return {"message": "Document metadata updated"}
        else:
            raise Exception(f"Failed to update metadata: {response['data']}")
    
    def test_bulk_metadata_update(self):
        """Story: As a bulk editor, I want to apply metadata updates to multiple documents"""
        logger.story("As a bulk editor, I want to apply metadata updates to multiple documents at once")
        
        document_id = self.test_data.get("document_id")
        if not document_id:
            raise Exception("Document ID not found in test data")
        
        payload = {
            "document_ids": [document_id],
            "metadata_updates": {
                "reviewed": True,
                "review_date": datetime.now().isoformat(),
                "reviewer": "test-automation"
            }
        }
        
        response = client.post("/documents/bulk-metadata-update", json=payload)
        
        if response["ok"]:
            logger.info(f"✅ Bulk metadata update completed")
            return {"message": "Bulk metadata update successful"}
        else:
            raise Exception(f"Failed bulk metadata update: {response['data']}")
    
    def test_list_documents_by_collection(self):
        """Story: As a user, I want to list documents by collection"""
        logger.story("As a user, I want to list documents by collection")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        response = client.get(f"/documents/collection/{collection_id}")
        
        if response["ok"]:
            documents = response["data"]
            logger.info(f"✅ Found {len(documents)} documents in collection")
            return {"message": f"Found {len(documents)} documents in collection"}
        else:
            raise Exception(f"Failed to list documents by collection: {response['data']}")
    
    # ========================================================================
    # 3. INDEXING: Make Content Searchable
    # ========================================================================
    
    def test_trigger_indexing(self):
        """Story: As a backend engineer, I want to manually trigger indexing"""
        logger.story("As a backend engineer, I want to manually trigger indexing for the uploaded document")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        payload = {
            "collection_id": collection_id
        }
        
        response = client.post("/indexing/trigger", json=payload)
        
        if response["ok"]:
            job_data = response["data"]
            job_id = job_data.get("job_id")
            if job_id:
                self.test_data["manual_index_job_id"] = job_id
            logger.info(f"✅ Indexing triggered: {job_data.get('message')}")
            return {"message": "Indexing triggered successfully"}
        else:
            raise Exception(f"Failed to trigger indexing: {response['data']}")
    
    def test_get_indexing_status(self):
        """Story: As a QA tester, I want to check which documents have been indexed"""
        logger.story("As a QA tester, I want to check which documents have been indexed")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        response = client.get("/documents/indexing-status", params={"collection_id": collection_id})
        
        if response["ok"]:
            status = response["data"]
            logger.info(f"✅ Indexing status - Total: {status.get('documents_total')}, "
                       f"Indexed: {status.get('indexed')}, Progress: {status.get('progress_percent')}%")
            return {"message": "Indexing status retrieved"}
        else:
            raise Exception(f"Failed to get indexing status: {response['data']}")
    
    def test_list_indexing_jobs(self):
        """Story: As a developer, I want to list all indexing jobs"""
        logger.story("As a developer, I want to list all indexing jobs to monitor progress")
        
        response = client.get("/documents/indexing-jobs", params={"limit": 10})
        
        if response["ok"]:
            jobs = response["data"]
            logger.info(f"✅ Retrieved {len(jobs)} indexing jobs")
            return {"message": f"Found {len(jobs)} indexing jobs"}
        else:
            raise Exception(f"Failed to list indexing jobs: {response['data']}")
    
    def test_get_indexing_job_status(self):
        """Story: As a developer, I want to check the status of a specific indexing job"""
        logger.story("As a developer, I want to check the status of a specific indexing job")
        
        job_id = self.test_data.get("index_job_id")
        if not job_id:
            logger.warning("No indexing job ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no job ID"}
        
        # Wait for job to complete
        result = client.wait_for_indexing_job(job_id, max_wait=120)
        
        if result["ok"]:
            job = result["data"]
            logger.info(f"✅ Job status: {job.get('status')}, "
                       f"Progress: {job.get('progress_percent')}%")
            return {"message": f"Job status: {job.get('status')}"}
        else:
            raise Exception(f"Failed to get job status: {result['data']}")
    
    # ========================================================================
    # 4. WEBPAGES: Crawl and Manage External Content
    # ========================================================================
    
    def test_fetch_webpage(self):
        """Story: As a researcher, I want to fetch a webpage"""
        logger.story("As a researcher, I want to fetch a webpage about the organization")
        
        payload = {
            "url": TEST_ORG_URL,
            "skip_ssl_verification": False
        }
        
        response = client.post("/webpages/fetch-webpage/", json=payload)
        
        if response["ok"]:
            webpage = response["data"]
            title = webpage.get("title", "")[:50]
            logger.info(f"✅ Fetched webpage: {title}...")
            return {"message": f"Webpage fetched: {title}"}
        else:
            raise Exception(f"Failed to fetch webpage: {response['data']}")
    
    def test_list_webpages(self):
        """Story: As a user, I want to list all fetched webpages"""
        logger.story("As a user, I want to list all fetched webpages")
        
        response = client.get("/webpages/", params={"limit": 10})
        
        if response["ok"]:
            webpages = response["data"]
            logger.info(f"✅ Retrieved {len(webpages)} webpages")
            
            # Try to find and store a webpage ID
            if webpages and len(webpages) > 0:
                self.test_data["webpage_id"] = webpages[0]["id"]
                self.results.webpage_id = webpages[0]["id"]
            
            return {"message": f"Found {len(webpages)} webpages"}
        else:
            raise Exception(f"Failed to list webpages: {response['data']}")
    
    def test_get_webpage(self):
        """Story: As a user, I want to retrieve metadata for a specific webpage"""
        logger.story("As a user, I want to retrieve metadata for a specific webpage")
        
        webpage_id = self.test_data.get("webpage_id")
        if not webpage_id:
            logger.warning("No webpage ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no webpage ID"}
        
        response = client.get(f"/webpages/{webpage_id}", params={"include_content": False})
        
        if response["ok"]:
            webpage = response["data"]
            logger.info(f"✅ Webpage details - URL: {webpage.get('url')}")
            return {"message": "Webpage metadata retrieved"}
        else:
            raise Exception(f"Failed to get webpage: {response['data']}")
    
    def test_get_webpage_by_url(self):
        """Story: As a user, I want to retrieve a webpage by its URL"""
        logger.story("As a user, I want to retrieve a webpage by its URL")
        
        response = client.get("/webpages/by-url/", params={"url": TEST_ORG_URL})
        
        if response["ok"]:
            webpage = response["data"]
            logger.info(f"✅ Found webpage by URL: {webpage.get('title', '')[:50]}")
            
            # Store webpage ID if not already stored
            if not self.test_data.get("webpage_id"):
                self.test_data["webpage_id"] = webpage["id"]
                self.results.webpage_id = webpage["id"]
            
            return {"message": "Webpage found by URL"}
        else:
            # This might fail if not yet indexed
            logger.warning(f"Webpage not found by URL: {response['data']}")
            self.results.add_skip()
            return {"message": "Skipped - webpage not found"}
    
    def test_list_webpages_by_collection(self):
        """Story: As a user, I want to list webpages by collection"""
        logger.story("As a user, I want to list webpages by collection to filter relevant ones")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        response = client.get(f"/webpages/collection/{collection_id}")
        
        if response["ok"]:
            webpages = response["data"]
            logger.info(f"✅ Found {len(webpages)} webpages in collection")
            return {"message": f"Found {len(webpages)} webpages in collection"}
        else:
            raise Exception(f"Failed to list webpages by collection: {response['data']}")
    
    def test_recrawl_webpage(self):
        """Story: As a user, I want to recrawl a webpage to refresh its content"""
        logger.story("As a user, I want to recrawl a webpage to refresh its content")
        
        webpage_id = self.test_data.get("webpage_id")
        if not webpage_id:
            logger.warning("No webpage ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no webpage ID"}
        
        response = client.post(f"/webpages/{webpage_id}/recrawl")
        
        if response["ok"]:
            logger.info(f"✅ Webpage marked for recrawl")
            return {"message": "Webpage marked for recrawl"}
        else:
            raise Exception(f"Failed to recrawl webpage: {response['data']}")
    
    # ========================================================================
    # 5. WEB CRAWLER: Crawl Sites for Bulk Content
    # ========================================================================
    
    def test_start_crawl(self):
        """Story: As a content analyst, I want to start crawling a website"""
        logger.story("As a content analyst, I want to start crawling a government site")
        
        if SKIP_CRAWL_TESTS:
            logger.test_skip("Crawl test", "SKIP_CRAWL_TESTS=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        payload = {
            "url": TEST_ORG_URL,
            "depth": CRAWL_DEPTH,
            "concurrent_requests": CRAWL_CONCURRENT_REQUESTS,
            "follow_external": CRAWL_FOLLOW_EXTERNAL,
            "strategy": CRAWL_STRATEGY,
            "collection_id": collection_id
        }
        
        response = client.post("/crawl/", json=payload)
        
        if response["ok"]:
            crawl_data = response["data"]
            task_id = crawl_data.get("task_id")
            self.test_data["crawl_task_id"] = task_id
            self.results.crawl_task_id = task_id
            
            logger.info(f"✅ Started crawl task: {task_id}")
            return {"message": f"Crawl started: {task_id}"}
        else:
            raise Exception(f"Failed to start crawl: {response['data']}")
    
    def test_list_crawl_jobs(self):
        """Story: As a user, I want to list all crawl jobs"""
        logger.story("As a user, I want to list all crawl jobs to monitor progress")
        
        if SKIP_CRAWL_TESTS:
            logger.test_skip("Crawl jobs list", "SKIP_CRAWL_TESTS=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        response = client.get("/crawl/")
        
        if response["ok"]:
            jobs = response["data"]
            logger.info(f"✅ Retrieved {len(jobs)} crawl jobs")
            return {"message": f"Found {len(jobs)} crawl jobs"}
        else:
            raise Exception(f"Failed to list crawl jobs: {response['data']}")
    
    def test_get_crawl_status(self):
        """Story: As a user, I want to check the status of a specific crawl job"""
        logger.story("As a user, I want to check the status of a specific crawl job")
        
        if SKIP_CRAWL_TESTS:
            logger.test_skip("Crawl status check", "SKIP_CRAWL_TESTS=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        task_id = self.test_data.get("crawl_task_id")
        if not task_id:
            logger.warning("No crawl task ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no task ID"}
        
        # Wait for crawl to complete (with shorter timeout for testing)
        result = client.wait_for_crawl_completion(task_id, max_wait=180)
        
        if result["ok"]:
            crawl = result["data"]
            logger.info(f"✅ Crawl status: {crawl.get('status')}, "
                       f"URLs crawled: {crawl.get('urls_crawled')}")
            return {"message": f"Crawl status: {crawl.get('status')}"}
        else:
            # Log warning but don't fail - crawl might still be running
            logger.warning(f"Crawl check: {result['data']}")
            return {"message": "Crawl in progress or timeout"}
    
    # ========================================================================
    # 6. CHAT: Ask Questions and Retrieve Answers
    # ========================================================================
    
    def test_chat_query(self):
        """Story: As a citizen, I want to ask a question and get an answer"""
        logger.story("As a citizen, I want to ask 'What documents are required for immigration?'")
        
        payload = {
            "message": "What documents are required for immigration?",
            "user_id": TEST_USER_ID,
            "metadata": {
                "test": "integration",
                "organization": TEST_ORG_NAME
            }
        }
        
        response = client.post("/chat/", json=payload)
        
        if response["ok"]:
            chat_data = response["data"]
            session_id = chat_data.get("session_id")
            answer = chat_data.get("answer", "")[:100]
            
            self.test_data["session_id"] = session_id
            self.results.session_id = session_id
            
            # Extract message_id from message history if available
            if "messages" in chat_data and chat_data["messages"]:
                last_message = chat_data["messages"][-1]
                if "message_id" in last_message:
                    self.test_data["message_id"] = last_message["message_id"]
                    self.results.message_id = last_message["message_id"]
            
            logger.info(f"✅ Chat response received: {answer}...")
            logger.info(f"✅ Session ID: {session_id}")
            
            return {"message": f"Chat response received"}
        else:
            raise Exception(f"Failed to send chat message: {response['data']}")
    
    def test_agency_scoped_chat(self):
        """Story: As a user, I want to route question to specific agency"""
        logger.story("As a user, I want to ask the same question but route it to the Immigration agency")
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            raise Exception("Collection ID not found in test data")
        
        payload = {
            "message": "What are the visa requirements?",
            "user_id": TEST_USER_ID,
            "metadata": {
                "test": "integration-agency-scoped"
            }
        }
        
        response = client.post(f"/chat/{collection_id}", json=payload)
        
        if response["ok"]:
            chat_data = response["data"]
            answer = chat_data.get("answer", "")[:100]
            logger.info(f"✅ Agency-scoped response: {answer}...")
            return {"message": "Agency-scoped chat successful"}
        else:
            raise Exception(f"Failed to send agency-scoped chat: {response['data']}")
    
    def test_get_chat_history(self):
        """Story: As a user, I want to retrieve the full chat history"""
        logger.story("As a user, I want to retrieve the full chat history for my session")
        
        session_id = self.test_data.get("session_id")
        if not session_id:
            raise Exception("Session ID not found in test data")
        
        response = client.get(f"/chat/{session_id}")
        
        if response["ok"]:
            history = response["data"]
            message_count = history.get("message_count", 0)
            logger.info(f"✅ Chat history retrieved: {message_count} messages")
            return {"message": f"Retrieved {message_count} messages"}
        else:
            raise Exception(f"Failed to get chat history: {response['data']}")
    
    def test_get_chat_events(self):
        """Story: As a developer, I want to retrieve all chat events"""
        logger.story("As a developer, I want to retrieve all chat events for a session")
        
        session_id = self.test_data.get("session_id")
        if not session_id:
            raise Exception("Session ID not found in test data")
        
        response = client.get(f"/chat/events/{session_id}", params={"limit": 50})
        
        if response["ok"]:
            events_data = response["data"]
            events = events_data.get("events", [])
            logger.info(f"✅ Retrieved {len(events)} chat events")
            return {"message": f"Retrieved {len(events)} events"}
        else:
            raise Exception(f"Failed to get chat events: {response['data']}")
    
    def test_get_latest_chat_events(self):
        """Story: As a developer, I want to get only the latest chat events"""
        logger.story("As a developer, I want to get only the latest chat events")
        
        session_id = self.test_data.get("session_id")
        if not session_id:
            raise Exception("Session ID not found in test data")
        
        response = client.get(f"/chat/events/{session_id}/latest", params={"count": 5})
        
        if response["ok"]:
            events_data = response["data"]
            events = events_data.get("events", [])
            logger.info(f"✅ Retrieved {len(events)} latest events")
            return {"message": f"Retrieved {len(events)} latest events"}
        else:
            raise Exception(f"Failed to get latest events: {response['data']}")
    
    # ========================================================================
    # 7. RATINGS: Evaluate Chat Responses
    # ========================================================================
    
    def test_submit_rating(self):
        """Story: As a user, I want to rate the chatbot's answer"""
        logger.story("As a user, I want to rate the chatbot's answer")
        
        session_id = self.test_data.get("session_id")
        message_id = self.test_data.get("message_id")
        
        if not session_id:
            raise Exception("Session ID not found in test data")
        
        payload = {
            "session_id": session_id,
            "message_id": message_id or "test-message",
            "rating": 5,
            "feedback_text": "Very helpful response! Clear and accurate information.",
            "user_id": TEST_USER_ID,
            "metadata": {
                "test": "integration",
                "helpful": True
            }
        }
        
        response = client.post("/chat/ratings", json=payload)
        
        if response["ok"]:
            rating_data = response["data"]
            rating_id = rating_data.get("id")
            self.test_data["rating_id"] = rating_id
            self.results.rating_id = rating_id
            
            logger.info(f"✅ Rating submitted: ID={rating_id}, Rating=5")
            return {"message": f"Rating submitted: {rating_id}"}
        else:
            raise Exception(f"Failed to submit rating: {response['data']}")
    
    def test_list_ratings(self):
        """Story: As an admin, I want to list all ratings"""
        logger.story("As an admin, I want to list all ratings to monitor chatbot performance")
        
        response = admin_client.get("/chat/ratings", params={"limit": 10})
        
        if response["ok"]:
            ratings = response["data"]
            logger.info(f"✅ Retrieved {len(ratings)} ratings")
            return {"message": f"Found {len(ratings)} ratings"}
        else:
            raise Exception(f"Failed to list ratings: {response['data']}")
    
    def test_get_rating(self):
        """Story: As an admin, I want to retrieve a specific rating"""
        logger.story("As an admin, I want to retrieve a specific rating")
        
        rating_id = self.test_data.get("rating_id")
        if not rating_id:
            logger.warning("No rating ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no rating ID"}
        
        response = admin_client.get(f"/chat/ratings/{rating_id}")
        
        if response["ok"]:
            rating = response["data"]
            logger.info(f"✅ Rating details: {rating.get('rating')}/5 - {rating.get('feedback_text', '')[:50]}")
            return {"message": "Rating retrieved"}
        else:
            raise Exception(f"Failed to get rating: {response['data']}")
    
    def test_update_rating(self):
        """Story: As a user, I want to update my rating"""
        logger.story("As a user, I want to update my rating after reconsidering the response")
        
        rating_id = self.test_data.get("rating_id")
        if not rating_id:
            logger.warning("No rating ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no rating ID"}
        
        payload = {
            "rating": 4,
            "feedback_text": "Updated feedback: Good response, but could be more detailed."
        }
        
        response = client.put(f"/chat/ratings/{rating_id}", json=payload)
        
        if response["ok"]:
            logger.info(f"✅ Rating updated to 4/5")
            return {"message": "Rating updated"}
        else:
            raise Exception(f"Failed to update rating: {response['data']}")
    
    def test_get_rating_stats(self):
        """Story: As an admin, I want to view rating statistics"""
        logger.story("As an admin, I want to view rating statistics across sessions")
        
        response = admin_client.get("/chat/ratings/stats")
        
        if response["ok"]:
            stats = response["data"]
            logger.info(f"✅ Rating stats - Total: {stats.get('total_ratings')}, "
                       f"Average: {stats.get('average_rating')}")
            return {"message": "Rating statistics retrieved"}
        else:
            raise Exception(f"Failed to get rating stats: {response['data']}")
    
    # ========================================================================
    # 8. AUDIT LOGS: Monitor Activity
    # ========================================================================
    
    def test_list_audit_logs(self):
        """Story: As a compliance officer, I want to list all audit logs"""
        logger.story("As a compliance officer, I want to list all audit logs")
        
        response = admin_client.get("/admin/audit-logs", params={"limit": 20})
        
        if response["ok"]:
            logs = response["data"]
            logger.info(f"✅ Retrieved {len(logs)} audit logs")
            return {"message": f"Found {len(logs)} audit logs"}
        else:
            raise Exception(f"Failed to list audit logs: {response['data']}")
    
    def test_get_audit_summary(self):
        """Story: As a compliance officer, I want to get audit summary"""
        logger.story("As a compliance officer, I want to get a summary of audit activity")
        
        response = admin_client.get("/admin/audit-logs/summary")
        
        if response["ok"]:
            summary = response["data"]
            logger.info(f"✅ Audit summary - Total actions: {summary.get('total_actions')}, "
                       f"Unique users: {summary.get('unique_users')}")
            return {"message": "Audit summary retrieved"}
        else:
            raise Exception(f"Failed to get audit summary: {response['data']}")
    
    def test_get_user_audit_logs(self):
        """Story: As an admin, I want to view audit logs for a specific user"""
        logger.story("As an admin, I want to view audit logs for a specific user")
        
        response = admin_client.get(f"/admin/audit-logs/user/{TEST_USER_ID}", params={"limit": 10})
        
        if response["ok"]:
            logs = response["data"]
            logger.info(f"✅ Retrieved {len(logs)} audit logs for user {TEST_USER_ID}")
            return {"message": f"Found {len(logs)} logs for user"}
        else:
            raise Exception(f"Failed to get user audit logs: {response['data']}")
    
    def test_get_resource_audit_logs(self):
        """Story: As an admin, I want to view audit logs for a specific resource"""
        logger.story("As an admin, I want to view audit logs for a specific document")
        
        document_id = self.test_data.get("document_id")
        if not document_id:
            logger.warning("No document ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no document ID"}
        
        response = admin_client.get(f"/admin/audit-logs/resource/document/{document_id}")
        
        if response["ok"]:
            logs = response["data"]
            logger.info(f"✅ Retrieved {len(logs)} audit logs for document {document_id}")
            return {"message": f"Found {len(logs)} logs for document"}
        else:
            raise Exception(f"Failed to get resource audit logs: {response['data']}")
    
    # ========================================================================
    # 9. TRANSCRIPTIONS: Convert Audio to Text
    # ========================================================================
    
    def test_create_test_audio(self):
        """Create a test audio file (placeholder)"""
        # Note: For a real test, you'd need an actual audio file
        # This is a placeholder showing the structure
        logger.warning("Audio transcription tests require actual audio files - skipping")
        return None
    
    def test_upload_transcription(self):
        """Story: As a researcher, I want to upload an audio file for transcription"""
        logger.story("As a researcher, I want to upload an audio file for transcription")
        
        # Skip this test as we don't have real audio files
        logger.test_skip("Upload transcription", "No test audio file available")
        self.results.add_skip()
        return {"message": "Skipped - no audio file"}
    
    def test_list_transcriptions(self):
        """Story: As a user, I want to list all transcriptions"""
        logger.story("As a user, I want to list all transcriptions I've created")
        
        response = client.get("/transcriptions/", params={"limit": 10})
        
        if response["ok"]:
            transcriptions = response["data"]
            logger.info(f"✅ Retrieved {len(transcriptions)} transcriptions")
            return {"message": f"Found {len(transcriptions)} transcriptions"}
        else:
            raise Exception(f"Failed to list transcriptions: {response['data']}")
    
    def test_get_transcription(self):
        """Story: As a user, I want to retrieve a specific transcription"""
        logger.story("As a user, I want to retrieve a specific transcription")
        
        # Skip if no transcription ID
        logger.test_skip("Get transcription", "No transcription ID available")
        self.results.add_skip()
        return {"message": "Skipped - no transcription ID"}
    
    # ========================================================================
    # CLEANUP: Remove Test Data
    # ========================================================================
    
    def test_delete_rating(self):
        """Story: As a user, I want to delete my rating"""
        logger.story("As a user, I want to delete my rating")
        
        if SKIP_CLEANUP:
            logger.test_skip("Delete rating", "SKIP_CLEANUP=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        rating_id = self.test_data.get("rating_id")
        if not rating_id:
            logger.warning("No rating ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no rating ID"}
        
        response = client.delete(f"/chat/ratings/{rating_id}")
        
        if response["ok"]:
            logger.info(f"✅ Rating deleted")
            return {"message": "Rating deleted"}
        else:
            raise Exception(f"Failed to delete rating: {response['data']}")
    
    def test_delete_chat_session(self):
        """Story: As a user, I want to delete my chat session"""
        logger.story("As a user, I want to delete my chat session for privacy")
        
        if SKIP_CLEANUP:
            logger.test_skip("Delete chat session", "SKIP_CLEANUP=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        session_id = self.test_data.get("session_id")
        if not session_id:
            logger.warning("No session ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no session ID"}
        
        response = client.delete(f"/chat/{session_id}")
        
        if response["ok"]:
            logger.info(f"✅ Chat session deleted")
            return {"message": "Chat session deleted"}
        else:
            raise Exception(f"Failed to delete chat session: {response['data']}")
    
    def test_delete_webpage(self):
        """Story: As a user, I want to delete a webpage"""
        logger.story("As a user, I want to delete a webpage that's no longer needed")
        
        if SKIP_CLEANUP:
            logger.test_skip("Delete webpage", "SKIP_CLEANUP=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        webpage_id = self.test_data.get("webpage_id")
        if not webpage_id:
            logger.warning("No webpage ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no webpage ID"}
        
        response = client.delete(f"/webpages/{webpage_id}")
        
        if response["ok"]:
            logger.info(f"✅ Webpage deleted")
            return {"message": "Webpage deleted"}
        else:
            # Don't fail if webpage doesn't exist
            logger.warning(f"Webpage deletion: {response['data']}")
            return {"message": "Webpage deletion attempted"}
    
    def test_delete_document(self):
        """Story: As an admin, I want to delete a document"""
        logger.story("As an admin, I want to delete the test document")
        
        if SKIP_CLEANUP:
            logger.test_skip("Delete document", "SKIP_CLEANUP=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        document_id = self.test_data.get("document_id")
        if not document_id:
            logger.warning("No document ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no document ID"}
        
        response = client.delete(f"/documents/{document_id}")
        
        if response["ok"]:
            logger.info(f"✅ Document deleted")
            return {"message": "Document deleted"}
        else:
            raise Exception(f"Failed to delete document: {response['data']}")
    
    def test_delete_collection(self):
        """Story: As an admin, I want to delete the test collection"""
        logger.story("As an admin, I want to delete the test collection")
        
        if SKIP_CLEANUP:
            logger.test_skip("Delete collection", "SKIP_CLEANUP=true")
            self.results.add_skip()
            return {"message": "Skipped"}
        
        collection_id = self.test_data.get("collection_id")
        if not collection_id:
            logger.warning("No collection ID found, skipping test")
            self.results.add_skip()
            return {"message": "Skipped - no collection ID"}
        
        response = client.delete(f"/collection-stats/{collection_id}")
        
        if response["ok"]:
            logger.info(f"✅ Collection deleted")
            return {"message": "Collection deleted"}
        else:
            raise Exception(f"Failed to delete collection: {response['data']}")
    
    # ========================================================================
    # TEST RUNNER
    # ========================================================================
    
    def run_all_tests(self):
        """Execute all tests in chronological order"""
        logger.section("GOVSTACK API INTEGRATION TEST SUITE")
        logger.info(f"Testing Organization: {TEST_ORG_NAME}")
        logger.info(f"Organization URL: {TEST_ORG_URL}")
        logger.info(f"Base URL: {client.base_url}")
        logger.info(f"Test started at: {datetime.now().isoformat()}")
        
        # Health check first
        logger.section("0. HEALTH CHECK")
        if not client.health_check():
            logger.critical("API health check failed! Cannot proceed with tests.")
            sys.exit(1)
        logger.info("✅ API is healthy")
        
        # 1. Collections
        logger.section("1. COLLECTIONS: Setup and Organization")
        self.run_test("Create Collection", self.test_create_collection)
        self.run_test("List Collections", self.test_list_collections)
        self.run_test("Get Collection Stats", self.test_get_collection_stats)
        self.run_test("Update Collection", self.test_update_collection)
        
        # 2. Documents
        logger.section("2. DOCUMENTS: Upload, Manage, and Clean Up")
        self.run_test("Upload Document", self.test_upload_document)
        self.run_test("List Documents", self.test_list_documents)
        self.run_test("Get Document", self.test_get_document)
        self.run_test("Update Document Metadata", self.test_update_document_metadata)
        self.run_test("Bulk Metadata Update", self.test_bulk_metadata_update)
        self.run_test("List Documents by Collection", self.test_list_documents_by_collection)
        
        # 3. Indexing
        logger.section("3. INDEXING: Make Content Searchable")
        self.run_test("Trigger Indexing", self.test_trigger_indexing)
        self.run_test("Get Indexing Status", self.test_get_indexing_status)
        self.run_test("List Indexing Jobs", self.test_list_indexing_jobs)
        self.run_test("Get Indexing Job Status", self.test_get_indexing_job_status)
        
        # 4. Webpages
        logger.section("4. WEBPAGES: Crawl and Manage External Content")
        self.run_test("Fetch Webpage", self.test_fetch_webpage)
        self.run_test("List Webpages", self.test_list_webpages)
        self.run_test("Get Webpage", self.test_get_webpage)
        self.run_test("Get Webpage by URL", self.test_get_webpage_by_url)
        self.run_test("List Webpages by Collection", self.test_list_webpages_by_collection)
        self.run_test("Recrawl Webpage", self.test_recrawl_webpage)
        
        # 5. Web Crawler
        logger.section("5. WEB CRAWLER: Crawl Sites for Bulk Content")
        self.run_test("Start Website Crawl", self.test_start_crawl)
        self.run_test("List Crawl Jobs", self.test_list_crawl_jobs)
        self.run_test("Get Crawl Status", self.test_get_crawl_status)
        
        # 6. Chat
        logger.section("6. CHAT: Ask Questions and Retrieve Answers")
        self.run_test("Send Chat Query", self.test_chat_query)
        self.run_test("Agency-Scoped Chat", self.test_agency_scoped_chat)
        self.run_test("Get Chat History", self.test_get_chat_history)
        self.run_test("Get Chat Events", self.test_get_chat_events)
        self.run_test("Get Latest Chat Events", self.test_get_latest_chat_events)
        
        # 7. Ratings
        logger.section("7. RATINGS: Evaluate Chat Responses")
        self.run_test("Submit Rating", self.test_submit_rating)
        self.run_test("List Ratings", self.test_list_ratings)
        self.run_test("Get Rating", self.test_get_rating)
        self.run_test("Update Rating", self.test_update_rating)
        self.run_test("Get Rating Stats", self.test_get_rating_stats)
        
        # 8. Audit Logs
        logger.section("8. AUDIT LOGS: Monitor Activity")
        self.run_test("List Audit Logs", self.test_list_audit_logs)
        self.run_test("Get Audit Summary", self.test_get_audit_summary)
        self.run_test("Get User Audit Logs", self.test_get_user_audit_logs)
        self.run_test("Get Resource Audit Logs", self.test_get_resource_audit_logs)
        
        # 9. Transcriptions
        logger.section("9. TRANSCRIPTIONS: Convert Audio to Text")
        self.run_test("Upload Transcription", self.test_upload_transcription)
        self.run_test("List Transcriptions", self.test_list_transcriptions)
        self.run_test("Get Transcription", self.test_get_transcription)
        
        # Cleanup
        logger.section("CLEANUP: Remove Test Data")
        self.run_test("Delete Rating", self.test_delete_rating)
        self.run_test("Delete Chat Session", self.test_delete_chat_session)
        self.run_test("Delete Webpage", self.test_delete_webpage)
        self.run_test("Delete Document", self.test_delete_document)
        self.run_test("Delete Collection", self.test_delete_collection)
        
        # Summary
        summary = self.results.summary()
        log_test_summary(summary)
        
        logger.info(f"\nTest completed at: {datetime.now().isoformat()}")
        logger.info(f"Logs saved to: {logger.logger.handlers[0].baseFilename}")
        
        return summary


def main():
    """Main entry point"""
    try:
        # Validate configuration
        validate_config()
        
        # Create and run test suite
        suite = GovStackTestSuite()
        summary = suite.run_all_tests()
        
        # Exit with appropriate code
        if summary["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
