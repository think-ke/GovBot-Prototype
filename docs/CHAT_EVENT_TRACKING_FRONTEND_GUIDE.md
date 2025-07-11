# Chat Event Tracking - Frontend Integration Guide

## Overview

The GovStack chat system now includes real-time event tracking that provides visibility into backend processing stages. Frontend applications can integrate with this system to show users what's happening behind the scenes when they send chat messages.

## Available Integration Methods

### 1. WebSocket Real-time Updates (Best for Real-time UX)

Connect to the WebSocket endpoint for instant event streaming:

**Pros:** Instant updates, efficient, great user experience  
**Cons:** More complex connection management, firewall issues  
**Best for:** Interactive dashboards, real-time monitoring

```javascript
const sessionId = 'your-chat-session-id';
const ws = new WebSocket(`ws://localhost:5000/chat/ws/events/${sessionId}`);

ws.onopen = function(event) {
    console.log('Connected to event stream');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'event') {
        // Handle chat processing event
        displayEventToUser(data.event);
    } else if (data.type === 'keepalive') {
        // Handle keepalive message
        console.log('Keepalive received');
    }
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed');
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

// Send ping for keepalive
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);
```

### 2. Polling-based Updates (Best for Simplicity)

For simpler implementations and better reliability, use the REST API to poll for events:

**Pros:** Simple, reliable, works everywhere, easier debugging  
**Cons:** Small delay (1-2 seconds), slightly higher bandwidth  
**Best for:** Most applications, corporate environments, mobile apps

```javascript
let lastEventTimestamp = null;

async function pollForEvents(sessionId) {
    try {
        const url = lastEventTimestamp 
            ? `/chat/events/${sessionId}?since=${lastEventTimestamp}`
            : `/chat/events/${sessionId}/latest?count=10`;
            
        const response = await fetch(url, {
            headers: {
                'X-API-Key': 'your-api-key'
            }
        });
        
        const data = await response.json();
        
        // Process new events
        data.events.forEach(event => {
            displayEventToUser(event);
            lastEventTimestamp = event.timestamp;
        });
        
    } catch (error) {
        console.error('Error polling for events:', error);
    }
}

// Poll every 1 second while chat is active
const pollInterval = setInterval(() => {
    pollForEvents(sessionId);
}, 1000);
```

## Event Types and User Messages

Events include user-friendly messages that can be displayed directly to users:

### Core Processing Events

| Event Type | Status | User Message | Description |
|------------|--------|--------------|-------------|
| `message_received` | `started` | 📩 Processing your message... | Message validation |
| `message_received` | `completed` | ✅ Message received and validated | Message ready for processing |
| `agent_thinking` | `started` | 🤔 AI is analyzing your question... | Agent analysis phase |
| `agent_thinking` | `completed` | ✅ Analysis complete | Agent finished thinking |
| `response_generation` | `started` | ✍️ Generating response... | Creating final response |
| `response_generation` | `completed` | ✅ Response ready | Response generation done |

### Tool Execution Events

| Event Type | Status | User Message | Description |
|------------|--------|--------------|-------------|
| `tool_search_documents` | `started` | 📄 Searching relevant documents... | Document search initiated |
| `tool_search_documents` | `progress` | 🔍 Found {count} potential matches... | Progress update |
| `tool_search_documents` | `completed` | ✅ Document search complete | Search finished |

### Database Operations

| Event Type | Status | User Message | Description |
|------------|--------|--------------|-------------|
| `loading_history` | `started` | 📚 Loading conversation history... | Loading past messages |
| `loading_history` | `completed` | ✅ History loaded | History loading done |
| `saving_message` | `started` | 💾 Saving conversation... | Saving chat data |
| `saving_message` | `completed` | ✅ Conversation saved | Save operation done |

### Error Events

| Event Type | Status | User Message | Description |
|------------|--------|--------------|-------------|
| `error` | `failed` | ❌ {error_message} | Any error that occurs |

## Frontend Implementation Examples

### React Component Example

```jsx
import React, { useState, useEffect, useRef } from 'react';

const ChatEventDisplay = ({ sessionId }) => {
    const [events, setEvents] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef(null);

    useEffect(() => {
        if (!sessionId) return;

        // Connect to WebSocket
        const ws = new WebSocket(`ws://localhost:5000/chat/ws/events/${sessionId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            console.log('Connected to event stream');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'event') {
                setEvents(prev => [...prev, data.event]);
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            console.log('Disconnected from event stream');
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        // Cleanup on unmount
        return () => {
            ws.close();
        };
    }, [sessionId]);

    return (
        <div className="chat-events">
            <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
                {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
            
            <div className="events-list">
                {events.slice(-5).map((event, index) => (
                    <div key={`${event.id}-${index}`} className={`event event-${event.event_status}`}>
                        <span className="event-message">{event.user_message}</span>
                        <span className="event-time">
                            {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ChatEventDisplay;
```

### Vue.js Component Example

```vue
<template>
  <div class="chat-events">
    <div :class="`connection-status ${isConnected ? 'connected' : 'disconnected'}`">
      {{ isConnected ? '🟢 Connected' : '🔴 Disconnected' }}
    </div>
    
    <div class="events-list">
      <div 
        v-for="(event, index) in recentEvents" 
        :key="`${event.id}-${index}`"
        :class="`event event-${event.event_status}`"
      >
        <span class="event-message">{{ event.user_message }}</span>
        <span class="event-time">{{ formatTime(event.timestamp) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatEventDisplay',
  props: {
    sessionId: String
  },
  data() {
    return {
      events: [],
      isConnected: false,
      ws: null
    };
  },
  computed: {
    recentEvents() {
      return this.events.slice(-5);
    }
  },
  watch: {
    sessionId(newSessionId) {
      if (newSessionId) {
        this.connectWebSocket(newSessionId);
      }
    }
  },
  mounted() {
    if (this.sessionId) {
      this.connectWebSocket(this.sessionId);
    }
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  },
  methods: {
    connectWebSocket(sessionId) {
      if (this.ws) {
        this.ws.close();
      }

      this.ws = new WebSocket(`ws://localhost:5000/chat/ws/events/${sessionId}`);

      this.ws.onopen = () => {
        this.isConnected = true;
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'event') {
          this.events.push(data.event);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
      };
    },
    
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString();
    }
  }
};
</script>
```

## CSS Styling Examples

```css
.chat-events {
  max-width: 400px;
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.connection-status {
  font-size: 12px;
  margin-bottom: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.connection-status.connected {
  background: #d4edda;
  color: #155724;
}

.connection-status.disconnected {
  background: #f8d7da;
  color: #721c24;
}

.events-list {
  max-height: 200px;
  overflow-y: auto;
}

.event {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: 14px;
}

.event.event-started {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
}

.event.event-progress {
  background: #d1ecf1;
  border-left: 4px solid #17a2b8;
}

.event.event-completed {
  background: #d4edda;
  border-left: 4px solid #28a745;
}

.event.event-failed {
  background: #f8d7da;
  border-left: 4px solid #dc3545;
}

.event-message {
  flex: 1;
}

.event-time {
  font-size: 12px;
  color: #666;
}
```

## API Reference

### WebSocket Endpoint

- **URL**: `ws://your-api-host/chat/ws/events/{session_id}`
- **Authentication**: None required for WebSocket
- **Messages**: JSON format with `type` field

### REST Endpoints

#### Get Events for Session
- **URL**: `GET /chat/events/{session_id}`
- **Query Parameters**:
  - `since`: ISO timestamp to get events after
  - `limit`: Maximum events to return (1-200, default 50)
- **Authentication**: X-API-Key header required

#### Get Latest Events
- **URL**: `GET /chat/events/{session_id}/latest`
- **Query Parameters**:
  - `count`: Number of latest events (1-50, default 10)
- **Authentication**: X-API-Key header required

## Best Practices

1. **Connection Management**: Always handle WebSocket reconnection for reliability
2. **Event Filtering**: Show only relevant events to avoid overwhelming users
3. **Performance**: Limit the number of displayed events and clean up old ones
4. **Error Handling**: Gracefully handle connection failures and API errors
5. **User Experience**: Use smooth animations and clear visual indicators
6. **Accessibility**: Ensure events are readable by screen readers
7. **Mobile**: Optimize event display for smaller screens

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check if the API server is running
   - Verify the WebSocket URL and session ID
   - Check browser console for CORS issues

2. **No Events Received**
   - Ensure session ID is correct and active
   - Verify the chat session exists
   - Check API key permissions for REST endpoints

3. **Events Not Updating**
   - Check WebSocket connection status
   - Verify event handlers are properly bound
   - Look for JavaScript errors in console

### Debug Mode

Enable debug logging to troubleshoot issues:

```javascript
const DEBUG = true;

if (DEBUG) {
  ws.onmessage = function(event) {
    console.log('Received event:', event.data);
    // Your normal event handling...
  };
}
```
