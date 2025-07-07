"""
Security utilities for API authentication and authorization.
"""
import os
import secrets
from typing import Optional
from fastapi import HTTPException, Header, Depends
from fastapi.security import APIKeyHeader
import logging

logger = logging.getLogger(__name__)

# API Key configuration
API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get API keys from environment
MASTER_API_KEY = os.getenv("GOVSTACK_API_KEY")
ADMIN_API_KEY = os.getenv("GOVSTACK_ADMIN_API_KEY")

# Default API keys for development (should be overridden in production)
if not MASTER_API_KEY:
    MASTER_API_KEY = "gs-dev-master-key-12345"
    logger.warning("Using default master API key for development. Set GOVSTACK_API_KEY in production.")

if not ADMIN_API_KEY:
    ADMIN_API_KEY = "gs-dev-admin-key-67890"
    logger.warning("Using default admin API key for development. Set GOVSTACK_ADMIN_API_KEY in production.")

# Valid API keys with their permissions
VALID_API_KEYS = {
    MASTER_API_KEY: {
        "name": "master",
        "permissions": ["read", "write", "delete", "admin"],
        "description": "Master API key with full access"
    },
    ADMIN_API_KEY: {
        "name": "admin", 
        "permissions": ["read", "write", "admin"],
        "description": "Admin API key with management access"
    }
}

class APIKeyInfo:
    """Information about an API key."""
    def __init__(self, key: str, name: str, permissions: list, description: str):
        self.key = key
        self.name = name
        self.permissions = permissions
        self.description = description
    
    def has_permission(self, permission: str) -> bool:
        """Check if the API key has a specific permission."""
        return permission in self.permissions or "admin" in self.permissions

def generate_api_key(prefix: str = "gs") -> str:
    """Generate a secure API key."""
    return f"{prefix}-{secrets.token_urlsafe(32)}"

async def get_api_key_from_header(api_key: Optional[str] = Header(None, alias="X-API-Key")) -> Optional[str]:
    """Extract API key from header."""
    return api_key

async def validate_api_key(api_key: Optional[str] = Depends(get_api_key_from_header)) -> APIKeyInfo:
    """
    Validate API key and return key information.
    
    Args:
        api_key: API key from header
        
    Returns:
        APIKeyInfo object with key details
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key used: {api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    key_info = VALID_API_KEYS[api_key]
    logger.info(f"API request authenticated with key: {key_info['name']}")
    
    return APIKeyInfo(
        key=api_key,
        name=key_info["name"],
        permissions=key_info["permissions"],
        description=key_info["description"]
    )

async def require_permission(required_permission: str):
    """
    Create a dependency that requires a specific permission.
    
    Args:
        required_permission: The permission required to access the endpoint
        
    Returns:
        Dependency function
    """
    async def check_permission(api_key_info: APIKeyInfo = Depends(validate_api_key)) -> APIKeyInfo:
        if not api_key_info.has_permission(required_permission):
            logger.warning(f"API key {api_key_info.name} lacks permission: {required_permission}")
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permission}",
            )
        return api_key_info
    
    return check_permission

# Common permission dependencies
async def require_read_permission(api_key_info: APIKeyInfo = Depends(validate_api_key)) -> APIKeyInfo:
    """Require read permission."""
    if not api_key_info.has_permission("read"):
        raise HTTPException(
            status_code=403,
            detail="Read permission required",
        )
    return api_key_info

async def require_write_permission(api_key_info: APIKeyInfo = Depends(validate_api_key)) -> APIKeyInfo:
    """Require write permission."""
    if not api_key_info.has_permission("write"):
        raise HTTPException(
            status_code=403,
            detail="Write permission required",
        )
    return api_key_info

async def require_delete_permission(api_key_info: APIKeyInfo = Depends(validate_api_key)) -> APIKeyInfo:
    """Require delete permission."""
    if not api_key_info.has_permission("delete"):
        raise HTTPException(
            status_code=403,
            detail="Delete permission required",
        )
    return api_key_info

async def require_admin_permission(api_key_info: APIKeyInfo = Depends(validate_api_key)) -> APIKeyInfo:
    """Require admin permission."""
    if not api_key_info.has_permission("admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin permission required",
        )
    return api_key_info

def add_api_key_to_docs():
    """Add API key information to OpenAPI documentation."""
    return {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Use 'gs-dev-master-key-12345' for development."
        }
    }
