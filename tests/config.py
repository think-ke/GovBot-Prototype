"""
Scalability Testing Configuration
"""
import os
from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class TestConfig:
    """Configuration for scalability tests"""
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", os.getenv("EXTERNAL_API_URL", "http://localhost:5005"))
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    network_timeout: int = int(os.getenv("NETWORK_TIMEOUT", "60"))
    connection_retries: int = int(os.getenv("CONNECTION_RETRIES", "3"))
    
    # Load Testing Configuration
    max_users: int = int(os.getenv("MAX_USERS", "1000"))
    spawn_rate: int = int(os.getenv("SPAWN_RATE", "10"))  # users per second
    test_duration: int = int(os.getenv("TEST_DURATION", "300"))  # seconds
    
    # Daily Usage Simulation
    daily_users: int = int(os.getenv("DAILY_USERS", "40000"))
    peak_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 14, 15, 16])  # Peak usage hours
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/govstackdb")
    
    # Monitoring Configuration
    enable_prometheus: bool = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "8000"))
    
    # Test Data Configuration
    sample_queries: List[str] = field(default_factory=lambda: [
        "What services does the government provide for business registration?",
        "How do I apply for a passport?",
        "What are the requirements for obtaining a driver's license?",
        "How can I register to vote?",
        "What tax benefits are available for small businesses?",
        "How do I apply for unemployment benefits?",
        "What is the process for getting a building permit?",
        "How can I report a pothole or road issue?",
        "What healthcare services are available for seniors?",
        "How do I register my newborn child?"
    ])
    
    # Memory and Performance Thresholds
    max_memory_mb: int = int(os.getenv("MAX_MEMORY_MB", "2048"))
    max_response_time_ms: int = int(os.getenv("MAX_RESPONSE_TIME_MS", "3000"))  # Increased for network latency
    min_success_rate: float = float(os.getenv("MIN_SUCCESS_RATE", "0.95"))
    max_error_rate: float = float(os.getenv("MAX_ERROR_RATE", "0.05"))
    
    # Token Usage Monitoring
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    track_token_usage: bool = os.getenv("TRACK_TOKEN_USAGE", "true").lower() == "true"
    
    # Concurrency Testing
    concurrent_sessions: int = int(os.getenv("CONCURRENT_SESSIONS", "100"))
    messages_per_session: int = int(os.getenv("MESSAGES_PER_SESSION", "10"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'api_base_url': self.api_base_url,
            'max_users': self.max_users,
            'spawn_rate': self.spawn_rate,
            'test_duration': self.test_duration,
            'daily_users': self.daily_users,
            'max_memory_mb': self.max_memory_mb,
            'max_response_time_ms': self.max_response_time_ms,
            'min_success_rate': self.min_success_rate,
            'concurrent_sessions': self.concurrent_sessions,
            'messages_per_session': self.messages_per_session,
            'network_timeout': self.network_timeout,
            'connection_retries': self.connection_retries
        }

# Global configuration instance
config = TestConfig()
