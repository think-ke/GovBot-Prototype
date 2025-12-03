# Fallback and Escalation Policy

This policy defines standardized responses and user flows when the system cannot confidently answer a query.

## When to Trigger
- No results or low-confidence retrieval.
- Ambiguous/underspecified queries.
- Out-of-scope topics (non-government).

## Standard Messages
- Implemented in `app/utils/fallbacks.py` with English, Kiswahili, and Sheng variants.
- Out-of-scope message ensures clear domain boundaries.
- “Agent” keyword can trigger human escalation in the UI.

## Event Logging
- `knowledge_gap` events emitted from `/chat` endpoints when sources are empty and confidence low.
- Use analytics to prioritize content updates and indexing.

## Human Escalation (Planned)
- UI: Show “Contact eCitizen support” option on repeated failures.
- Backend: Create `/chat/escalate` ticket endpoint (TBD) and route to helpdesk.

## Review
- Weekly review of knowledge gaps and ratings to reduce fallback frequency over time.
