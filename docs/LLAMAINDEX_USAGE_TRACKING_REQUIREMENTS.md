# LlamaIndex Usage Tracking — Requirements

## Overview
Record agent invocations and tool calls from the LlamaIndex-based chatbot into the existing ChatEvent table so we can aggregate usage by collection/agency and by session.

## Scope
- LlamaIndex FunctionAgent path only (pydantic agent remains unchanged for now).
- Event types:
  - agent_invocation: started/completed/failed
  - tool_search_documents: started/completed/failed

## Data model
- Reuse `chat_events` table via `ChatEventService.create_event`.
- Required fields:
  - session_id: string (provided by API)
  - event_type: string (see above)
  - event_status: started|completed|failed
  - event_data: JSON — for tools include { collection, count? }, for errors include { error }
- PII: service sanitizes payloads and messages via `redact_pii`.

## Emission strategy
- Orchestrator sets context vars (session_id, db) when db + session_id provided.
- Tools (static and dynamic) emit:
  - started with { collection }
  - completed with { collection, count }
  - failed with { collection, error }
- Agent wrapper emits agent_invocation at start/completion/failure.
- If context is missing, events are silently skipped (no-op).

## API integration
- Agency-scoped endpoint (`POST /chat/{agency}`) passes the DB session into `run_llamaindex_agent`.
- Default endpoint still uses compatibility agent (follow-up can wire DB similarly).

## Aggregation examples
- Tool calls by collection:
  - SELECT event_data->>'collection', count(*) FROM chat_events WHERE event_type='tool_search_documents' AND event_status='completed' GROUP BY 1;
- Chats per collection (assistant messages with retriever_type): existing ChatMessage persistence supports this.

## Non-goals
- New tables or migrations.
- Full analytics endpoints UI; can be added later.

## Acceptance criteria
- When calling `/chat/{agency}`, events appear for agent and tool usage with proper collection.
- No crashes when DB/session is absent.
- Code duplication reduced; orchestrator_clean is removed/deprecated.

## Risks
- Double emission if both compatibility/event orchestrators are used; mitigate by using one path at a time.
- Inconsistent collection keys from dynamic aliasing; we emit the handle used by the tool.
