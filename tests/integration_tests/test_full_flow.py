"""
Integration tests for the GovStack API
Tests the full flow from API to database to LLM
"""
import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.fast_api_app import app
from app.db.database import async_session, engine
from app.db.models.chat import Base as ChatBase
from app.utils.chat_persistence import ChatPersistenceService


class TestFullChatFlow:
    """Test complete chat flow including persistence"""
    
    @pytest.mark.asyncio
    async def test_complete_chat_conversation(self):
        """Test a complete multi-turn conversation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            session_id = str(uuid4())
            user_id = f"integration_test_user_{int(time.time())}"
            
            # First message
            first_payload = {
                "message": "What is the Kenya Film Commission?",
                "session_id": session_id,
                "user_id": user_id,
                "metadata": {"test_type": "integration"}
            }
            
            first_response = await client.post("/chat/", json=first_payload)
            assert first_response.status_code == 200
            
            first_data = first_response.json()
            assert first_data["session_id"] == session_id
            assert len(first_data["answer"]) > 0
            assert isinstance(first_data["sources"], list)
            assert 0 <= first_data["confidence"] <= 1
            
            # Validate usage information
            if first_data.get("usage"):
                usage = first_data["usage"]
                assert "requests" in usage
                assert "request_tokens" in usage
                assert "response_tokens" in usage
                assert "total_tokens" in usage
                assert usage["total_tokens"] > 0
            
            # Second message (follow-up)
            second_payload = {
                "message": "What support do they provide to filmmakers?",
                "session_id": session_id,
                "user_id": user_id,
                "metadata": {"test_type": "integration"}
            }
            
            second_response = await client.post("/chat/", json=second_payload)
            assert second_response.status_code == 200
            
            second_data = second_response.json()
            assert second_data["session_id"] == session_id
            assert len(second_data["answer"]) > 0
            
            # Validate usage information for second response
            if second_data.get("usage"):
                usage = second_data["usage"]
                assert "requests" in usage
                assert "request_tokens" in usage
                assert "response_tokens" in usage
                assert "total_tokens" in usage
                assert usage["total_tokens"] > 0
            
            # Get chat history
            history_response = await client.get(f"/chat/{session_id}")
            assert history_response.status_code == 200
            
            history_data = history_response.json()
            assert history_data["session_id"] == session_id
            assert history_data["user_id"] == user_id
            assert len(history_data["messages"]) >= 2  # At least 2 exchanges
            
            # Clean up
            delete_response = await client.delete(f"/chat/{session_id}")
            assert delete_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_sessions(self):
        """Test multiple concurrent chat sessions"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create multiple sessions concurrently
            session_ids = [str(uuid4()) for _ in range(5)]
            user_id = f"concurrent_test_user_{int(time.time())}"
            
            # Define test queries
            queries = [
                "What is the Kenya Film Commission?",
                "How do I register a business?",
                "What are the requirements for a driver's license?",
                "How can I apply for a passport?",
                "What tax benefits are available?"
            ]
            
            # Send requests concurrently
            tasks = []
            for i, session_id in enumerate(session_ids):
                payload = {
                    "message": queries[i],
                    "session_id": session_id,
                    "user_id": f"{user_id}_{i}",
                    "metadata": {"concurrent_test": True, "session_index": i}
                }
                task = client.post("/chat/", json=payload)
                tasks.append(task)
            
            # Wait for all responses
            responses = await asyncio.gather(*tasks)
            
            # Verify all responses
            for i, response in enumerate(responses):
                assert response.status_code == 200
                data = response.json()
                assert data["session_id"] == session_ids[i]
                assert len(data["answer"]) > 0
            
            # Clean up all sessions
            cleanup_tasks = [
                client.delete(f"/chat/{session_id}") 
                for session_id in session_ids
            ]
            await asyncio.gather(*cleanup_tasks)


class TestDatabaseIntegration:
    """Test database integration"""
    
    @pytest.mark.asyncio
    async def test_chat_persistence_integration(self):
        """Test chat persistence with real database"""
        async with async_session() as db:
            user_id = f"db_test_user_{int(time.time())}"
            
            # Create chat session
            session_id = await ChatPersistenceService.create_chat_session(db, user_id)
            assert session_id is not None
            
            # Save a user message
            user_message = {
                "query": "Integration test message",
                "timestamp": time.time()
            }
            
            success = await ChatPersistenceService.save_message(
                db, session_id, "user", user_message
            )
            assert success is True
            
            # Save an assistant message
            assistant_message = {
                "answer": "This is a test response",
                "confidence": 0.9,
                "sources": [],
                "retriever_type": "test"
            }
            
            success = await ChatPersistenceService.save_message(
                db, session_id, "assistant", assistant_message
            )
            assert success is True
            
            # Retrieve chat with messages
            chat_data = await ChatPersistenceService.get_chat_with_messages(db, session_id)
            assert chat_data is not None
            assert chat_data["session_id"] == session_id
            assert chat_data["user_id"] == user_id
            assert len(chat_data["messages"]) >= 2
            
            # Clean up
            deleted = await ChatPersistenceService.delete_chat_session(db, session_id)
            assert deleted is True


class TestPerformanceIntegration:
    """Test performance-related integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_response_time_under_load(self):
        """Test response times under moderate load"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send multiple requests and measure response times
            response_times = []
            session_id = str(uuid4())
            
            for i in range(10):
                start_time = time.time()
                
                payload = {
                    "message": f"Test query number {i}",
                    "session_id": session_id,
                    "user_id": f"perf_test_user_{i}",
                    "metadata": {"performance_test": True}
                }
                
                response = await client.post("/chat/", json=payload)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
                
                assert response.status_code == 200
                
                # Add small delay between requests
                await asyncio.sleep(0.1)
            
            # Verify response times are reasonable
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            print(f"Average response time: {avg_response_time:.2f}ms")
            print(f"Max response time: {max_response_time:.2f}ms")
            
            # Assert reasonable performance (adjust thresholds as needed)
            assert avg_response_time < 5000  # 5 seconds average
            assert max_response_time < 10000  # 10 seconds max
            
            # Clean up
            await client.delete(f"/chat/{session_id}")
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test that memory usage doesn't grow excessively"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send many requests to test memory stability
            for i in range(20):
                payload = {
                    "message": f"Memory test query {i}",
                    "session_id": str(uuid4()),
                    "user_id": f"memory_test_user_{i}",
                    "metadata": {"memory_test": True}
                }
                
                response = await client.post("/chat/", json=payload)
                assert response.status_code == 200
                
                # Check memory every 5 requests
                if i % 5 == 0:
                    current_memory = process.memory_info().rss / (1024 * 1024)
                    memory_growth = current_memory - initial_memory
                    
                    print(f"Memory after {i+1} requests: {current_memory:.2f}MB (growth: {memory_growth:.2f}MB)")
                    
                    # Assert memory growth is reasonable (adjust threshold as needed)
                    assert memory_growth < 500  # Max 500MB growth
        
        # Final memory check
        final_memory = process.memory_info().rss / (1024 * 1024)
        total_growth = final_memory - initial_memory
        print(f"Total memory growth: {total_growth:.2f}MB")
        
        # Allow some memory growth but not excessive
        assert total_growth < 200  # Max 200MB total growth


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_invalid_session_handling(self):
        """Test handling of invalid session IDs"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test with malformed session ID
            response = await client.get("/chat/invalid-session-id")
            assert response.status_code == 404
            
            # Test with non-existent but valid UUID
            fake_session = str(uuid4())
            response = await client.get(f"/chat/{fake_session}")
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_large_message_handling(self):
        """Test handling of very large messages"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a very long message
            large_message = "This is a very long message. " * 1000  # ~30KB
            
            payload = {
                "message": large_message,
                "session_id": str(uuid4()),
                "user_id": "large_message_test_user"
            }
            
            response = await client.post("/chat/", json=payload)
            
            # Should either handle it gracefully or return appropriate error
            assert response.status_code in [200, 413, 422]  # OK, Payload Too Large, or Validation Error
    
    @pytest.mark.asyncio
    async def test_rapid_requests_same_session(self):
        """Test rapid successive requests to the same session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            session_id = str(uuid4())
            user_id = "rapid_test_user"
            
            # Send multiple rapid requests
            tasks = []
            for i in range(5):
                payload = {
                    "message": f"Rapid message {i}",
                    "session_id": session_id,
                    "user_id": user_id,
                    "metadata": {"rapid_test": True}
                }
                task = client.post("/chat/", json=payload)
                tasks.append(task)
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that at least some succeeded
            successful_responses = [
                r for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            ]
            
            assert len(successful_responses) > 0
            
            # Clean up
            await client.delete(f"/chat/{session_id}")


# Fixtures for integration tests
@pytest.fixture(scope="session")
async def test_database():
    """Set up test database"""
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)
    
    yield
    
    # Cleanup if needed
    # Note: In production, you might want to use a separate test database


@pytest.fixture
async def clean_test_session():
    """Provide a clean test session and clean up after"""
    session_id = str(uuid4())
    
    yield session_id
    
    # Clean up after test
    async with AsyncClient(app=app, base_url="http://test") as client:
        try:
            await client.delete(f"/chat/{session_id}")
        except:
            pass  # Ignore cleanup errors
