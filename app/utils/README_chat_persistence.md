# Chat Persistence in GovStack

This module provides functionality to store and retrieve chat history in the GovStack application using PydanticAI's message persistence capabilities.

## Overview

The chat persistence system allows:

- Storing complete conversation history between users and the AI assistant
- Continuing conversations with full context from previous interactions
- Retrieving chat history for analysis or audit purposes
- Serializing and deserializing message history to JSON for API responses

## Core Components

1. **Database Models:**
   - `Chat`: Stores metadata about a conversation session
   - `ChatMessage`: Stores individual messages, including request, response, and tool interactions

2. **Service Layer:**
   - `ChatPersistenceService`: Provides methods to create, retrieve, and manage chat sessions

3. **API Endpoints:**
   - Create new chat sessions
   - Continue existing conversations with context
   - Retrieve chat history
   - Delete chat sessions

## How It Works

The system uses PydanticAI's built-in message handling to:

1. Extract messages from agent runs using `result.all_messages()` and `result.new_messages()`
2. Serialize messages to a database-friendly format using `to_jsonable_python`
3. Reconstruct messages using `ModelMessagesTypeAdapter.validate_python`
4. Pass message history to new agent instances to maintain conversation context

## Usage Examples

### Creating a New Chat

```python
# Create a new chat session
session_id = await ChatPersistenceService.create_chat_session(db, user_id="user123")

# Run the agent and get a response
agent = generate_agent()
result = agent.run_sync("What information do you have about Kenya Film Commission?")

# Save the messages to the database
await ChatPersistenceService.save_messages(db, session_id, result.all_messages())
```

### Continuing a Conversation

```python
# Load the previous messages
message_history = await ChatPersistenceService.load_messages(db, session_id)

# Create an agent with the message history
agent = generate_agent(message_history=message_history)

# Continue the conversation
result = agent.run_sync("Tell me more about their film industry support")

# Save only the new messages
await ChatPersistenceService.save_messages(db, session_id, result.new_messages())
```

## API Endpoints

The system exposes the following REST API endpoints:

- `POST /v2/chat/` - Create a new chat session and process the initial message
- `POST /v2/chat/{session_id}` - Continue an existing chat session
- `GET /v2/chat/{session_id}` - Retrieve the chat history
- `DELETE /v2/chat/{session_id}` - Delete a chat session

## Setup

To set up the chat persistence system:

1. Run the migration script to create the required database tables:
   ```bash
   python scripts/add_chat_tables.py
   ```

2. Ensure the chat persistence service is properly initialized in your application

## References

- [PydanticAI Message History Documentation](https://ai.pydantic.dev/message-history/)
- [Chat App Example with FastAPI](https://ai.pydantic.dev/examples/chat-app/)
- [Messages API Reference](https://ai.pydantic.dev/api/messages/)
