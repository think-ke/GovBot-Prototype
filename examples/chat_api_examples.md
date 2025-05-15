# GovStack Chat API Examples

This document provides examples of how to use the GovStack Chat API endpoints.

## Chat API Endpoint

The Chat API endpoint is available at:
- `/chat`

## Starting a New Conversation

To start a new conversation, send a POST request to the chat endpoint without providing a `session_id`. The API will create a new session and return the session ID in the response.

### Request

```http
POST /chat
Content-Type: application/json

{
  "message": "What documents are available about agriculture policies?",
  "user_id": "user123"
}
```

### Response

```json
{
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "answer": "There are several documents about agriculture policies available...",
  "sources": [
    {
      "document_id": "123",
      "title": "Agriculture Policy 2023",
      "url": "https://example.com/docs/agriculture-policy-2023"
    }
  ],
  "confidence": 0.92,
  "retriever_type": "semantic",
  "trace_id": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d"
}
```

## Continuing a Conversation

To continue an existing conversation, include the `session_id` from the previous response.

### Request

```http
POST /chat
Content-Type: application/json

{
  "message": "Can you summarize the key points?",
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "user_id": "user123"
}
```

### Response

```json
{
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "answer": "The key points of the agriculture policies are...",
  "sources": [
    {
      "document_id": "123",
      "title": "Agriculture Policy 2023",
      "url": "https://example.com/docs/agriculture-policy-2023"
    }
  ],
  "confidence": 0.89,
  "retriever_type": "hybrid",
  "trace_id": "3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r"
}
```

## Retrieving Chat History

You can retrieve the history of a chat session by making a GET request with the session ID.

### Request

```http
GET /chat/5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c
```

### Response

```json
{
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "messages": [
    {
      "id": 1,
      "message_type": "request-text",
      "content": {
        "text": "What documents are available about agriculture policies?"
      },
      "timestamp": "2023-05-15T10:30:00Z",
      "metadata": null,
      "message_idx": 0
    },
    {
      "id": 2,
      "message_type": "response-text",
      "content": {
        "text": "There are several documents about agriculture policies available..."
      },
      "timestamp": "2023-05-15T10:30:05Z",
      "metadata": {
        "usage": {
          "prompt_tokens": 45,
          "completion_tokens": 120,
          "total_tokens": 165
        }
      },
      "message_idx": 1
    },
    {
      "id": 3,
      "message_type": "request-text",
      "content": {
        "text": "Can you summarize the key points?"
      },
      "timestamp": "2023-05-15T10:31:00Z",
      "metadata": null,
      "message_idx": 2
    },
    {
      "id": 4,
      "message_type": "response-text",
      "content": {
        "text": "The key points of the agriculture policies are..."
      },
      "timestamp": "2023-05-15T10:31:05Z",
      "metadata": {
        "usage": {
          "prompt_tokens": 210,
          "completion_tokens": 85,
          "total_tokens": 295
        }
      },
      "message_idx": 3
    }
  ],
  "user_id": "user123",
  "created_at": "2023-05-15T10:30:00Z",
  "updated_at": "2023-05-15T10:31:05Z",
  "num_messages": 4
}
```

## Deleting a Chat Session

To delete a chat session and all its messages, send a DELETE request with the session ID.

### Request

```http
DELETE /chat/5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c
```

### Response

```json
{
  "message": "Chat session 5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c deleted successfully"
}
```

## Including Optional Metadata

You can include additional metadata with your chat requests to provide more context.

### Request

```http
POST /chat
Content-Type: application/json

{
  "message": "Tell me about sustainable farming practices",
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "user_id": "user123",
  "metadata": {
    "source": "mobile-app",
    "location": "rural-region",
    "language_preference": "en"
  }
}
```

## Error Handling

### Session Not Found

```json
{
  "detail": "Chat session 5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c not found"
}
```

### Internal Server Error

```json
{
  "detail": "Internal server error: Error processing chat"
}
```

## Notes

- If you provide a `session_id` that doesn't exist, the system will create a new session with that ID instead of returning an error.
- Chat history is saved automatically for all conversations.
- The system truncates message history if it gets too long to avoid token limits.