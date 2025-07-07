"""
Locust-based load testing for GovStack API
"""
import time
import random
import logging
from uuid import uuid4
from typing import Dict, Any, List
from locust import HttpUser, task, between, events
from locust.env import Environment

from ..config import config
from ..utils.monitoring import PerformanceMonitor
from ..utils.token_tracker import TokenTracker

logger = logging.getLogger(__name__)

class GovStackUser(HttpUser):
    """Simulates a user interacting with the GovStack API"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Initialize user session"""
        self.session_id = str(uuid4())
        self.user_id = f"load_test_user_{uuid4()}"
        self.query_count = 0
        self.token_tracker = TokenTracker()
        
        # Test connectivity to external server
        try:
            response = self.client.get("/health", timeout=10)
            if response.status_code != 200:
                logger.warning(f"External server health check failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to external server: {e}")
        
    @task(3)
    def chat_with_api(self):
        """Simulate chat interaction - most common task"""
        query = random.choice(config.sample_queries)
        
        payload = {
            "message": query,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "metadata": {
                "test_type": "load_test",
                "query_count": self.query_count
            }
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/api/v1/chat",  # Updated endpoint path
            json=payload,
            timeout=config.network_timeout,
            catch_response=True
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Track token usage if available
                    if "usage" in data:
                        self.token_tracker.track_usage_from_response(data)
                    response.success()
                except Exception as e:
                    logger.error(f"Failed to parse response: {e}")
                    response.failure(f"Invalid JSON response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:100]}")
        
        self.query_count += 1
    
    @task(1)
    def get_chat_history(self):
        """Get chat history - less frequent task"""
        with self.client.get(
            f"/api/v1/chat/{self.session_id}",
            timeout=config.network_timeout,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Session not found is expected for new sessions
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def get_health_check(self):
        """Health check endpoint"""
        with self.client.get("/health", catch_response=True, timeout=10) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: HTTP {response.status_code}")

class ConcurrentChatUser(HttpUser):
    """Simulates users having longer conversations"""
    
    wait_time = between(2, 8)
    
    def on_start(self):
        self.session_id = str(uuid4())
        self.user_id = f"concurrent_user_{uuid4()}"
        self.conversation_count = 0
        
        # Test connectivity
        try:
            self.client.get("/health", timeout=10)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
        
    @task
    def have_conversation(self):
        """Simulate a multi-turn conversation"""
        queries = [
            "What services are available for business registration?",
            "What are the required documents?",
            "How long does the process take?",
            "What are the fees involved?",
            "Can I track my application status?"
        ]
        
        for i, query in enumerate(queries):
            payload = {
                "message": query,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "metadata": {
                    "test_type": "conversation",
                    "turn": i + 1,
                    "conversation_id": self.conversation_count
                }
            }
            
            with self.client.post(
                "/api/v1/chat",
                json=payload,
                timeout=config.network_timeout,
                catch_response=True
            ) as response:
                if response.status_code != 200:
                    response.failure(f"HTTP {response.status_code}")
                    break  # Exit conversation on error
                else:
                    response.success()
                    
                # Add delay between conversation turns
                time.sleep(random.uniform(1, 3))
        
        self.conversation_count += 1


# Event listeners for monitoring
@events.request.add_listener
def request_handler(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Log request details for analysis"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    
    # Log slow requests
    if response_time > config.max_response_time_ms:
        logger.warning(f"Slow request: {name} took {response_time:.2f}ms")

@events.test_start.add_listener
def test_start_handler(environment, **kwargs):
    """Initialize monitoring when test starts"""
    print(f"🚀 Load test starting with {environment.parsed_options.num_users} users")
    print(f"🎯 Target URL: {environment.host}")
    print(f"📊 Expected response time threshold: {config.max_response_time_ms}ms")
    print(f"🔄 Network timeout: {config.network_timeout}s")

@events.test_stop.add_listener  
def test_stop_handler(environment, **kwargs):
    """Clean up when test stops"""
    print("✅ Load test completed")
    
    # Print summary statistics
    if hasattr(environment, 'stats'):
        stats = environment.stats
        print(f"\n📈 Test Summary:")
        print(f"Total requests: {stats.total.num_requests}")
        print(f"Total failures: {stats.total.num_failures}")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
        print(f"Max response time: {stats.total.max_response_time:.2f}ms")
        print(f"Requests per second: {stats.total.current_rps:.2f}")
        
        failure_rate = (stats.total.num_failures / max(1, stats.total.num_requests)) * 100
        print(f"Failure rate: {failure_rate:.2f}%")
        
        # Check against thresholds
        if failure_rate > config.max_error_rate * 100:
            print(f"⚠️  High failure rate detected: {failure_rate:.2f}% > {config.max_error_rate * 100}%")
        
        if stats.total.avg_response_time > config.max_response_time_ms:
            print(f"⚠️  High average response time: {stats.total.avg_response_time:.2f}ms > {config.max_response_time_ms}ms")


class StressTestUser(HttpUser):
    """High-intensity user for stress testing"""
    
    wait_time = between(0.1, 0.5)  # Very short wait times
    
    def on_start(self):
        self.session_id = str(uuid4())
        self.user_id = f"stress_user_{uuid4()}"
        
    @task
    def rapid_fire_requests(self):
        """Send rapid requests to stress test the external server"""
        query = random.choice(config.sample_queries[:3])  # Use shorter queries
        
        payload = {
            "message": query,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "metadata": {"test_type": "stress"}
        }
        
        with self.client.post(
            "/api/v1/chat",
            json=payload,
            timeout=config.network_timeout,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


if __name__ == "__main__":
    # Run the load test directly
    from locust import run_single_user
    run_single_user(GovStackUser)
