"""
Analytics API main application.

This module initializes the FastAPI app, registers analytics routers, and
defines a couple of top-level utility endpoints. It also enriches the
OpenAPI schema with detailed tags, examples, and helpful tooltips so the
admin dashboard can surface better in-UI help.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from time import perf_counter

from analytics.routers import user_analytics, usage_analytics, conversation_analytics, business_analytics
from analytics.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAPI tags metadata used by routers for grouping
tags_metadata = [
    {
        "name": "User Analytics",
        "description": (
            "Metrics about users of the chatbot (demographics, sentiment, sessions, retention).\n\n"
            "Note: Some sub-endpoints may return placeholder/demo values in dev."
        ),
        "x-tooltips": {
            "retention": "Retention percentages are illustrative by default in dev.",
            "geographic": "Requires location collection; disabled in most dev setups.",
        },
        "externalDocs": {
            "description": "Analytics module docs",
            "url": "https://github.com/think-ke/govstack/tree/pydantic-llamaindex/docs",
        },
    },
    {
        "name": "Usage Analytics",
        "description": (
            "System usage, performance and reliability insights (traffic, errors, response times).\n\n"
            "Note: Hourly traffic and response-time trends may be generated as demo shapes in dev."
        ),
        "x-tooltips": {
            "hourly-traffic": "24 buckets, UTC hours, demo shape unless data available.",
            "response-times": "Daily series with P50/P95/P99; demo jitter in dev mode.",
        },
    },
    {
        "name": "Conversation Analytics",
        "description": (
            "Insights derived from conversations (flows, intents, retrieval, sentiment, knowledge gaps).\n\n"
            "Note: Intents and document retrieval examples are illustrative unless NLP pipelines are enabled."
        ),
        "x-tooltips": {
            "intents": "Static examples in dev until intent classification is wired.",
            "document-retrieval": "Shows common types with example collection_ids in dev.",
        },
    },
    {
        "name": "Business Analytics",
        "description": (
            "Executive and operational KPIs (ROI, containment, costs, dashboards)."
        ),
    },
]

# Create FastAPI app
app = FastAPI(
    title="GovStack Analytics API",
    description=(
        "Analytics microservice for GovStack chatbot metrics and insights.\n\n"
        "This service powers the admin dashboard analytics tabs. Some endpoints return"
        " demo or placeholder values when historical data is not available in dev."
    ),
    version="1.0.0",
    docs_url="/analytics/docs",
    redoc_url="/analytics/redoc",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "docExpansion": "list",
        "defaultModelsExpandDepth": 1,
        "tryItOutEnabled": True,
        "filter": True,
    },
    contact={
        "name": "GovStack Team",
        "url": "https://github.com/think-ke/govstack",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
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

class HealthResponse(BaseModel):
    """Schema for service health response."""

    model_config = ConfigDict(
        title="HealthResponse",
        json_schema_extra={
            "examples": [{"status": "healthy", "service": "analytics"}],
            "x-tooltip": "Simple liveness probe for the analytics service.",
        },
    )

    status: str = Field(..., description="Service health status, e.g., 'healthy'")
    service: str = Field(..., description="Service name identifier")


@app.get(
    "/analytics/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns liveness information for the analytics service. Useful for k8s"
        " probes and uptime checks."
    ),
    responses={
        200: {
            "description": "Service is up and responding",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "service": "analytics"}
                }
            },
        }
    },
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="analytics")

class EndpointsInfo(BaseModel):
    """Top-level endpoint paths."""

    model_config = ConfigDict(
        title="EndpointPaths",
        json_schema_extra={
            "x-tooltip": "Base paths for each analytics area.",
        },
    )

    user: str = Field(..., examples=["/analytics/user"])
    usage: str = Field(..., examples=["/analytics/usage"])
    conversation: str = Field(..., examples=["/analytics/conversation"])
    business: str = Field(..., examples=["/analytics/business"])


class RootResponse(BaseModel):
    """Schema for the root analytics info endpoint."""

    model_config = ConfigDict(
        title="RootResponse",
        json_schema_extra={
            "examples": [
                {
                    "message": "GovStack Analytics API",
                    "version": "1.0.0",
                    "endpoints": {
                        "user": "/analytics/user",
                        "usage": "/analytics/usage",
                        "conversation": "/analytics/conversation",
                        "business": "/analytics/business",
                    },
                }
            ],
            "x-notes": [
                "In development mode, some routes surface demo/placeholder numbers.",
                "Look for 'x-tooltips' on tag groups in the docs for more context.",
            ],
        },
    )

    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Service version")
    endpoints: EndpointsInfo


@app.get(
    "/analytics",
    response_model=RootResponse,
    summary="Service root",
    description="Provides base paths and version information for the analytics API.",
)
async def root() -> RootResponse:
    return RootResponse(
        message="GovStack Analytics API",
        version="1.0.0",
        endpoints=EndpointsInfo(
            user="/analytics/user",
            usage="/analytics/usage",
            conversation="/analytics/conversation",
            business="/analytics/business",
        ),
    )

class DBHealthResponse(BaseModel):
    """Schema for database connectivity health."""

    model_config = ConfigDict(
        title="DBHealthResponse",
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "latency_ms": 2.3,
                }
            ]
        },
    )

    status: str = Field(..., description="'ok' when DB ping succeeds, else 'error'")
    latency_ms: float = Field(..., description="Round-trip time for SELECT 1 in milliseconds")


@app.get(
    "/analytics/health/db",
    response_model=DBHealthResponse,
    summary="Database connectivity health",
    description="Executes SELECT 1 to verify DB connectivity and reports latency (ms).",
)
async def db_health(db: AsyncSession = Depends(get_db)) -> DBHealthResponse:
    start = perf_counter()
    await db.execute(text("SELECT 1"))
    latency = (perf_counter() - start) * 1000.0
    return DBHealthResponse(status="ok", latency_ms=round(latency, 3))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
