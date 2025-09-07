# GovStack Documentation Index

Start here to navigate project documentation. The sections below link to design, security, analytics, integration, and testing resources.

## Architecture and Security
- Technical Design: ./technical_design.md
- Security Guidelines: ./SECURITY.md
- Privacy & PII (Presidio): ./PII_PRESIDIO_SETUP.md
- Risk Mitigation (overview): ./RISK_MITIGATION_OVERVIEW_PUBLIC.md
- Risk Mitigation (plan): ./RISK_MITIGATION_PLAN.md
- Data Quality Framework: ./dqf.md
- Data Provenance: ./DATA_PROVENANCE_ANALYSIS.md
 - Deployment: ./DEPLOYMENT.md
 - Operations: ./OPERATIONS.md

## AI Orchestration and RAG
- LlamaIndex Orchestrator: ./LLAMAINDEX_ORCHESTRATOR.md
- LlamaIndex Usage Tracking Requirements: ./LLAMAINDEX_USAGE_TRACKING_REQUIREMENTS.md
- GovBot Overview: ./govbot.md
 - RAG Indexing Component: ../app/core/rag/README.md
 - Crawling Guide: ./CRAWLING_GUIDE.md

## Chat Events and Ratings
- Chat Event Tracking (backend): ./CHAT_EVENT_TRACKING_SYSTEM.md
- Chat Event Tracking (frontend): ./CHAT_EVENT_TRACKING_FRONTEND_GUIDE.md
- Message Rating System: ./MESSAGE_RATING_SYSTEM.md
- Fallback & Escalation: ./FALLBACK_AND_ESCALATION.md
 - Chat Persistence Module: ../app/utils/README_chat_persistence.md

## Analytics
- Analytics Service Overview & Endpoints: ../analytics/README.md
- Analytics Module Technical Documentation: ./ANALYTICS_MODULE_DOCUMENTATION.md
- Analytics Dashboard Specification: ./ANALYTICS_DASHBOARD_SPECIFICATION.md
- Analytics Integration (admin dashboard): ./ANALYTICS_INTEGRATION.md
- Composite Sentiment API details: ../analytics/COMPOSITE_METRICS_API.md
- Sentiment Analysis (VADER): ../analytics/SENTIMENT_ANALYSIS.md

## Business Intelligence
- Metabase Setup: ./METABASE_SETUP.md
 - Storage Guide (MinIO & ChromaDB): ./STORAGE.md

## Operations
- Database Backups: ../README_DATABASE_BACKUPS.md

## API Reference
- Main API Reference: ./API_REFERENCE.md
- Analytics OpenAPI (runtime): http://localhost:8005/analytics/docs

## Testing
- Test Plan: ./TEST_PLAN.md
- Testing Protocols: ./TESTING_PROTOCOLS.md
- Test Suite README: ../tests/README.md

## Status and Presentations
- Implementation Status: ./implementation_status.md
- Technical Architecture Presentation: ./GovStack_Technical_Architecture_Presentation.md
- Detailed Slides: ./GovStack_Detailed_Presentation_Slides.md
