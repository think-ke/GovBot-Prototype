"""
Unit tests for the GovStack API
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient
import json
from uuid import uuid4

from app.api.fast_api_app import app
from app.utils.chat_persistence import ChatPersistenceService
from app.core.orchestrator import generate_agent, Output, Source, Usage, UsageDetails


class TestChatEndpoints:
    """Test chat-related endpoints"""
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_success(self):
        """Test successful chat request"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "message": "What is the Kenya Film Commission?",
                "session_id": str(uuid4()),
                "user_id": "test_user"
            }
            
            headers = {"X-API-Key": "gs-dev-master-key-12345"}
            response = await client.post("/chat/", json=payload, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "session_id" in data
            assert "confidence" in data
            assert "sources" in data
            assert "usage" in data
            assert len(data["answer"]) > 0
            
            # Validate usage structure
            usage = data["usage"]
            if usage:  # usage can be None
                assert "requests" in usage
                assert "request_tokens" in usage
                assert "response_tokens" in usage
                assert "total_tokens" in usage
                assert "details" in usage
                assert isinstance(usage["details"], dict)
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_missing_api_key(self):
        """Test chat request without API key"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "message": "What is the Kenya Film Commission?",
                "session_id": str(uuid4()),
                "user_id": "test_user"
            }
            
            response = await client.post("/chat/", json=payload)
            assert response.status_code == 401
            assert "API key required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_invalid_api_key(self):
        """Test chat request with invalid API key"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "message": "What is the Kenya Film Commission?",
                "session_id": str(uuid4()),
                "user_id": "test_user"
            }
            
            headers = {"X-API-Key": "invalid-key"}
            response = await client.post("/chat/", json=payload, headers=headers)
            assert response.status_code == 401
            assert "Invalid API key" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_missing_message(self):
        """Test chat request with missing message"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "session_id": str(uuid4()),
                "user_id": "test_user"
            }
            
            headers = {"X-API-Key": "gs-dev-master-key-12345"}
            response = await client.post("/chat/", json=payload, headers=headers)
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_empty_message(self):
        """Test chat request with empty message"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "message": "",
                "session_id": str(uuid4()),
                "user_id": "test_user"
            }
            
            response = await client.post("/chat/", json=payload)
            assert response.status_code == 422  # Should fail validation
    
    @pytest.mark.asyncio
    async def test_get_chat_history_nonexistent(self):
        """Test getting history for non-existent session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            fake_session_id = str(uuid4())
            headers = {"X-API-Key": "gs-dev-master-key-12345"}
            response = await client.get(f"/chat/{fake_session_id}", headers=headers)
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_chat_session(self):
        """Test deleting a chat session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"X-API-Key": "gs-dev-master-key-12345"}
            
            # First create a chat session
            payload = {
                "message": "Test message",
                "session_id": str(uuid4()),
                "user_id": "test_user"
            }
            
            create_response = await client.post("/chat/", json=payload, headers=headers)
            assert create_response.status_code == 200
            
            session_id = create_response.json()["session_id"]
            
            # Delete the session
            delete_response = await client.delete(f"/chat/{session_id}", headers=headers)
            assert delete_response.status_code == 200
            
            # Verify it's deleted
            get_response = await client.get(f"/chat/{session_id}", headers=headers)
            assert get_response.status_code == 404


class TestChatPersistence:
    """Test chat persistence service"""
    
    @pytest.mark.asyncio
    async def test_create_chat_session(self):
        """Test creating a new chat session"""
        # Mock database session
        mock_db = AsyncMock()
        
        with patch('app.utils.chat_persistence.Chat') as mock_chat:
            session_id = await ChatPersistenceService.create_chat_session(mock_db, "test_user")
            
            assert session_id is not None
            assert len(session_id) > 0
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_message(self):
        """Test saving a message"""
        mock_db = AsyncMock()
        session_id = str(uuid4())
        
        with patch('app.utils.chat_persistence.ChatMessage') as mock_message:
            result = await ChatPersistenceService.save_message(
                mock_db,
                session_id,
                "user",
                {"query": "test message"}
            )
            
            assert result is True
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()


class TestOrchestrator:
    """Test the orchestrator and agent functionality"""
    
    def test_generate_agent(self):
        """Test agent generation"""
        agent = generate_agent()
        assert agent is not None
        assert hasattr(agent, 'run_sync')
    
    @pytest.mark.asyncio
    async def test_agent_response_structure(self):
        """Test that agent returns proper response structure"""
        agent = generate_agent()
        
        # Mock the agent to avoid actual API calls in tests
        with patch.object(agent, 'run_sync') as mock_run:
            mock_output = Mock()
            mock_output.answer = "Test answer"
            mock_output.sources = []
            mock_output.confidence = 0.9
            mock_output.retriever_type = "test"
            mock_output.recommended_follow_up_questions = []
            
            mock_result = Mock()
            mock_result.output = mock_output
            mock_run.return_value = mock_result
            
            result = agent.run_sync("test query")
            
            assert result.output.answer == "Test answer"
            assert result.output.confidence == 0.9
            assert isinstance(result.output.sources, list)


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint - should work without API key"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint - should work without API key"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200


class TestAPIKeySecurity:
    """Test API key security functionality"""
    
    @pytest.mark.asyncio
    async def test_api_info_endpoint(self):
        """Test API info endpoint with valid key"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"X-API-Key": "gs-dev-master-key-12345"}
            response = await client.get("/api-info", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["api_key_name"] == "master"
            assert "read" in data["permissions"]
            assert "write" in data["permissions"]
    
    @pytest.mark.asyncio
    async def test_admin_key_permissions(self):
        """Test admin key has correct permissions"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"X-API-Key": "gs-dev-admin-key-67890"}
            response = await client.get("/api-info", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["api_key_name"] == "admin"
            assert "admin" in data["permissions"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_key(self):
        """Test that protected endpoints require API key"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/documents/")
            assert response.status_code == 401


class TestValidation:
    """Test request validation"""
    
    @pytest.mark.asyncio
    async def test_chat_request_validation(self):
        """Test chat request validation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test invalid JSON
            response = await client.post("/chat/", data="invalid json")
            assert response.status_code == 422
            
            # Test missing required fields
            response = await client.post("/chat/", json={})
            assert response.status_code == 422
            
            # Test invalid field types
            response = await client.post("/chat/", json={
                "message": 123,  # Should be string
                "session_id": "valid_id"
            })
            assert response.status_code == 422


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors"""
        # This would require mocking the database connection
        # to simulate failures
        pass
    
    @pytest.mark.asyncio
    async def test_llm_api_error(self):
        """Test handling of LLM API errors"""
        # This would require mocking the LLM API calls
        # to simulate failures
        pass


# Fixtures for common test data
@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {
        "message": "What services are available for business registration?",
        "session_id": str(uuid4()),
        "user_id": "test_user_123",
        "metadata": {"test": True}
    }

@pytest.fixture
def sample_chat_response():
    """Sample chat response data"""
    return {
        "session_id": str(uuid4()),
        "answer": "To register a business, you need to...",
        "sources": [
            {
                "title": "Business Registration Guide",
                "url": "https://example.gov/business-reg",
                "snippet": "The Business Registration Service..."
            }
        ],
        "confidence": 0.95,
        "retriever_type": "brs",
        "recommended_follow_up_questions": [
            "What are the fees for business registration?",
            "How long does the process take?"
        ],
        "usage": {
            "requests": 1,
            "request_tokens": 150,
            "response_tokens": 300,
            "total_tokens": 450,
            "details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0,
                "cached_tokens": 0
            }
        }
    }

@pytest.fixture
async def test_client():
    """Test client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
