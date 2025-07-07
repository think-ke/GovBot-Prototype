"""
Analytics API main application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routers import user_analytics, usage_analytics, conversation_analytics, business_analytics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GovStack Analytics API",
    description="Analytics microservice for GovStack chatbot metrics and insights",
    version="1.0.0",
    docs_url="/analytics/docs",
    redoc_url="/analytics/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_analytics.router, prefix="/analytics/user", tags=["User Analytics"])
app.include_router(usage_analytics.router, prefix="/analytics/usage", tags=["Usage Analytics"])
app.include_router(conversation_analytics.router, prefix="/analytics/conversation", tags=["Conversation Analytics"])
app.include_router(business_analytics.router, prefix="/analytics/business", tags=["Business Analytics"])

@app.get("/analytics/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "analytics"}

@app.get("/analytics")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GovStack Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "user": "/analytics/user",
            "usage": "/analytics/usage", 
            "conversation": "/analytics/conversation",
            "business": "/analytics/business"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
