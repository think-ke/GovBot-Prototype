# GovStack Chat API Examples

This document provides examples of how to use the GovStack Chat API endpoints.

## Chat API Endpoint

The Chat API endpoint is available at:
- `/chat`

This endpoint provides all chat functionality including creating new conversations, continuing existing conversations, and handling message history automatically.

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
      "message_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
      "message_type": "user",
      "message_object": {
        "query": "What documents are available about agriculture policies?"
      },
      "timestamp": "2023-05-15T10:30:00Z"
    },
    {
      "id": 2,
      "message_id": "f6e5d4c3-b2a1-0987-f6e5-d4c3b2a10987",
      "message_type": "assistant",
      "message_object": {
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
      },
      "timestamp": "2023-05-15T10:30:05Z"
    },
    {
      "id": 3,
      "message_id": "1a2b3c4d-5e6f-7890-1a2b-3c4d5e6f7890",
      "message_type": "user",
      "message_object": {
        "query": "Can you summarize the key points?"
      },
      "timestamp": "2023-05-15T10:31:00Z"
    },
    {
      "id": 4,
      "message_id": "7e8f9a0b-1c2d-3e4f-7e8f-9a0b1c2d3e4f",
      "message_type": "assistant",
      "message_object": {
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
      },
      "timestamp": "2023-05-15T10:31:05Z"
    }
  ],
  "user_id": "user123",
  "created_at": "2023-05-15T10:30:00Z",
  "updated_at": "2023-05-15T10:31:05Z",
  "message_count": 4,
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

You can include additional metadata with your chat requests to provide more context. This metadata is stored with the chat session and can be used for tracking, analytics, or other purposes.

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

## Example: Kenya Film Classification Board Queries

Here are examples of conversations related to the Kenya Film Classification Board (KFCB) and film industry in Kenya.

### Request: Film Licensing Information

```http
POST /chat
Content-Type: application/json

{
  "message": "What licenses do I need to film in Kenya?",
  "user_id": "filmmaker123"
}
```

### Response

```json
{
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "answer": "To film in Kenya, you need to obtain a filming license from the Kenya Film Classification Board (KFCB). This is mandated by the Films and Stage Plays Act Cap 222 of the Laws of Kenya. KFCB issues licenses to both local and international filmmakers. You can apply for a filming license through the E-Services page on the KFCB website (www.kfcb.go.ke) or through their eCitizen portal. Depending on your filming activity, you might also need additional permits from other authorities.",
  "sources": [
    {
      "document_id": "kfcb-001",
      "title": "KFCB Regulatory Mandate and Services",
      "url": "https://kfcb.go.ke/our-regulatory-mandate-and-services"
    }
  ],
  "confidence": 0.95,
  "retriever_type": "semantic",
  "trace_id": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d"
}
```

### Follow-up Request: Film Classification

```http
POST /chat
Content-Type: application/json

{
  "message": "What is the Watershed Period mentioned in film regulations?",
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "user_id": "filmmaker123"
}
```

### Response

```json
{
  "session_id": "5f9b5b7e-8f0c-4a3c-9d8f-5f9b5b7e8f0c",
  "answer": "The Watershed Period in Kenya's broadcasting regulations refers to the time between 5:00 am and 10:00 pm. During this period, content that is rated for adults or contains language intended for adult audiences should not be aired. This regulation is enforced by the Kenya Film Classification Board (KFCB) under the authority of the Kenya Information and Communications Act (KICA). The purpose is to protect children from exposure to inappropriate content during times when they are likely to be watching television.",
  "sources": [
    {
      "document_id": "kfcb-002",
      "title": "KFCB FAQs",
      "url": "https://kfcb.go.ke/faqs"
    }
  ],
  "confidence": 0.92,
  "retriever_type": "hybrid",
  "trace_id": "3c4d5e6f-7g8h-9i0j-1k2l-3m4n5o6p7q8r"
}
```

### Request: Film Exhibition License

```http
POST /chat
Content-Type: application/json

{
  "message": "How do I get a license to operate a cinema in Kenya?",
  "user_id": "theatre_owner456"
}
```

### Response

```json
{
  "session_id": "6a0c6c8f-9d1e-5b4f-0e3a-6a0c6c8f9d1e",
  "answer": "To operate a cinema in Kenya, you need to obtain an exhibition license from the Kenya Film Classification Board (KFCB). The Board issues exhibition licenses to cinema theaters under the Films and Stage Plays Act Cap 222. You can apply for this license through the KFCB E-Services portal on their website (www.kfcb.go.ke) or through their eCitizen platform. The application process requires submitting necessary documentation and paying the applicable fees. For specific requirements and current fee structures, you can also contact KFCB directly at info@kfcb.go.ke or call 0711 222204.",
  "sources": [
    {
      "document_id": "kfcb-003",
      "title": "Film Distribution and Exhibition Licenses",
      "url": "https://kfcb.go.ke/licenses"
    }
  ],
  "confidence": 0.94,
  "retriever_type": "semantic",
  "trace_id": "9s8r7q6p-5o4n-3m2l-1k0j-9i8h7g6f5e4d"
}
```

### Request: Nairobi Film Centre Information

```http
POST /chat
Content-Type: application/json

{
  "message": "What is the Nairobi Film Centre and what services does it offer?",
  "user_id": "film_student789"
}
```

### Response

```json
{
  "session_id": "7b1d7d9a-0e2f-6c5g-1f4h-7b1d7d9a0e2f",
  "answer": "The Nairobi Film Centre (NFC) is a facility operated by the Kenya Film Classification Board (KFCB) that serves as a hub for film industry activities in Kenya. The centre offers various services including film screening facilities, training spaces for filmmakers, networking opportunities, and hosts events like the 'Filmmakers Hangout' that bring together creative professionals. The NFC aims to promote local film production, provide resources for emerging filmmakers, and create opportunities for collaboration within the industry. For partnerships or to utilize the facilities, you can apply through KFCB's website or contact them directly.",
  "sources": [
    {
      "document_id": "nfc-001",
      "title": "Nairobi Film Centre",
      "url": "https://www.kfcb.go.ke/nairobi-film-centre-nfc"
    },
    {
      "document_id": "kfcb-news-001",
      "title": "Creatives Throng KFCB's Nairobi Film Centre For The 4th Edition Of 'Filmmakers Hangout'",
      "url": "https://www.kfcb.go.ke/creatives-throng-kfcbs-nairobi-film-centre-4th-edition-filmmakers-hangout"
    }
  ],
  "confidence": 0.91,
  "retriever_type": "semantic",
  "trace_id": "5e6f7g8h-9i0j-1k2l-3m4n-5o6p7q8r9s0t"
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
- The system maintains the conversation context between messages when using the same session ID.
- User messages are stored with a simple structure `{"query": "message text"}`.
- Assistant messages contain the full response including sources, confidence score, and retriever type.
- The chat endpoint also supports metadata for additional context that can be useful for tracking or analytics.
- For Kenya Film Classification Board specific queries, the system searches through relevant government documents and regulations to provide accurate information.