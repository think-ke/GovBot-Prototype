# Chat Event Tracking System

## Overview

The GovStack chat system now includes comprehensive real-time event tracking that provides frontend users with visibility into backend processing stages. This system tracks every step of chat message processing, from initial receipt through final response generation.

## Features

- **Real-time Event Streaming**: WebSocket-based live updates
- **Polling Support**: REST API for simpler implementations
- **User-friendly Messages**: Emoji-enhanced status messages
- **Performance Tracking**: Processing time measurement
- **Error Handling**: Comprehensive error event tracking
- **Tool Integration**: Track RAG tool executions
- **Optional Cleanup**: Configurable event retention (not required for most use cases)

## Quick Start

### 1. Database Setup

Run the migration script to create the event tracking tables:

```bash
python scripts/add_event_tracking.py
```

### 2. Frontend Integration

#### WebSocket (Recommended)

```javascript
const ws = new WebSocket(`ws://localhost:5000/chat/ws/events/${sessionId}`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'event') {
        console.log(data.event.user_message); // e.g., "🤔 AI is analyzing your question..."
    }
};
```

#### REST API Polling

```javascript
const response = await fetch(`/chat/events/${sessionId}/latest?count=10`, {
    headers: { 'X-API-Key': 'your-api-key' }
});
const data = await response.json();
```

### 3. Event Types

The system tracks these event types:

- **message_received**: Message validation and processing start
- **agent_thinking**: AI analysis and decision making
- **tool_search_documents**: Document search operations
- **response_generation**: Final response creation
- **saving_message**: Database persistence
- **loading_history**: Conversation history retrieval
- **error**: Any errors that occur

## API Endpoints

### WebSocket
- `ws://host/chat/ws/events/{session_id}` - Real-time event stream

### REST API
- `GET /chat/events/{session_id}` - Get events with optional filtering
- `GET /chat/events/{session_id}/latest` - Get latest events

## Event Structure

```json
{
  "id": 123,
  "session_id": "session-uuid",
  "message_id": "message-uuid",
  "event_type": "agent_thinking",
  "event_status": "started",
  "event_data": {"context": "additional data"},
  "user_message": "🤔 AI is analyzing your question...",
  "timestamp": "2023-10-20T14:30:15.123456Z",
  "processing_time_ms": 150
}
```

## Architecture

### Database Schema

```sql
CREATE TABLE chat_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    message_id VARCHAR(64),
    event_type VARCHAR(50) NOT NULL,
    event_status VARCHAR(20) NOT NULL,
    event_data JSON,
    user_message VARCHAR(500),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time_ms INTEGER
);
```

### Component Overview

1. **ChatEvent Model** (`app/db/models/chat_event.py`)
   - Database model for storing events
   - Includes indexes for efficient querying

2. **ChatEventService** (`app/utils/chat_event_service.py`)
   - Core service for creating and managing events
   - User-friendly message generation
   - Cleanup operations

3. **Event Endpoints** (`app/api/endpoints/chat_event_endpoints.py`)
   - WebSocket and REST API endpoints
   - Connection management
   - Real-time broadcasting

4. **Enhanced Orchestrator** (`app/core/event_orchestrator.py`)
   - Event-aware agent with context tracking
   - Tool execution monitoring
   - Context variable management

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `CHROMA_HOST`: ChromaDB host for vector store
- `CHROMA_PORT`: ChromaDB port
- `LOG_LEVEL`: Logging level for event system

### Event Retention

Events are automatically cleaned up based on age. Configure retention:

```python
# Clean up events older than 24 hours (default)
await ChatEventService.cleanup_old_events(db, hours_old=24)
```

## Maintenance

### Manual Cleanup

```bash
# View statistics
python scripts/event_cleanup.py stats

# Dry run cleanup (see what would be deleted)
python scripts/event_cleanup.py cleanup --hours 48 --dry-run

# Actually cleanup events older than 48 hours
python scripts/event_cleanup.py cleanup --hours 48
```

### Monitoring

Monitor event system health by checking:

1. **Event Volume**: Normal chat sessions generate 8-12 events
2. **Error Rate**: Monitor `error` events for system issues
3. **Performance**: Check `processing_time_ms` for bottlenecks
4. **Connection Health**: WebSocket connection stability

## Performance Considerations

### Database

- Events table includes optimized indexes
- Automatic cleanup prevents unbounded growth
- Batch operations for high-volume scenarios

### WebSocket Connections

- Connection pooling for multiple sessions
- Automatic reconnection handling
- Graceful degradation if events fail

### Memory Usage

- Context variables for thread-safe event tracking
- Limited event history to prevent memory leaks
- Efficient JSON serialization

## Security

- **Authentication**: REST endpoints require API key
- **WebSocket**: No authentication required (session-scoped)
- **Data Privacy**: Events contain no sensitive user data
- **Rate Limiting**: Built-in protection against event spam

## Error Handling

The system includes comprehensive error handling:

1. **Graceful Degradation**: Chat continues if events fail
2. **Error Events**: All errors generate trackable events
3. **Logging**: Detailed logs for debugging
4. **Retry Logic**: Automatic retry for transient failures

## Testing

### Unit Tests

```bash
# Test event service
python -m pytest tests/unit/test_chat_event_service.py

# Test event endpoints
python -m pytest tests/unit/test_chat_event_endpoints.py
```

### Integration Tests

```bash
# Test complete chat flow with events
python -m pytest tests/integration/test_chat_with_events.py

# Test WebSocket functionality
python -m pytest tests/integration/test_websocket_events.py
```

### Load Testing

```bash
# Test event system under load
python -m pytest tests/load/test_event_performance.py
```

## Troubleshooting

### Common Issues

1. **Events Not Appearing**
   - Check database connection
   - Verify session ID is correct
   - Ensure migration was run

2. **WebSocket Connection Fails**
   - Check firewall settings
   - Verify WebSocket support in proxy
   - Check CORS configuration

3. **High Database Usage**
   - Run cleanup script more frequently
   - Reduce event retention period
   - Check for query performance issues

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.utils.chat_event_service').setLevel(logging.DEBUG)
```

## Migration Guide

### From No Events to Event Tracking

1. Run database migration:
   ```bash
   python scripts/add_event_tracking.py
   ```

2. Update chat endpoint imports:
   ```python
   from app.utils.chat_event_service import ChatEventService
   ```

3. Add event tracking to chat flow:
   ```python
   await ChatEventService.create_event(db, session_id, "message_received", "started")
   ```

4. Update frontend to consume events

### Configuration Changes

Update your application configuration to include:

```python
# In FastAPI app startup
from app.db.models.chat_event import Base as ChatEventBase
await conn.run_sync(ChatEventBase.metadata.create_all)
```

## Future Enhancements

### Planned Features

1. **Analytics Dashboard**: Real-time event analytics
2. **Custom Events**: User-defined event types
3. **Event Aggregation**: Summary statistics
4. **Alerting**: Automated alerts for error patterns
5. **Export**: Event data export functionality

### API Extensions

1. **Event Filtering**: Advanced filtering options
2. **Bulk Operations**: Batch event management
3. **Event Subscriptions**: Subscribe to specific event types
4. **Historical Analysis**: Time-series event analysis

## Contributing

When adding new event types:

1. Update `EVENT_MESSAGES` in `ChatEventService`
2. Add appropriate event emissions in code
3. Update frontend documentation
4. Add tests for new events
5. Update this documentation

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs with debug level enabled
3. Test with minimal reproduction case
4. File issue with detailed description

## License

This event tracking system is part of the GovStack project and follows the same license terms.
