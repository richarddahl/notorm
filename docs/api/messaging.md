# Messaging API Reference

This document provides a comprehensive reference for the Messaging API endpoints, following the domain-driven design approach. It includes detailed information about request and response formats, authentication requirements, and integration examples.

## Overview

The Messaging API provides functionality for an internal messaging system between users, with features like:

- Message threading
- Message importance levels
- Recipient tracking (TO/CC/BCC)
- Read receipts
- Draft messages

## Authentication

All endpoints require authentication. Include a valid JWT token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Base URL

All endpoints are prefixed with `/api/v1/messages`.

## Data Transfer Objects (DTOs)

### MessageBaseDto

Base DTO for message data.

```json
{
  "subject": "Meeting tomorrow",
  "body": "Let's discuss the project status.",
  "flag": "INFORMATION"
}
```

### MessageCreateDto

DTO for creating a new message.

```json
{
  "subject": "Meeting tomorrow",
  "body": "Let's discuss the project status.",
  "flag": "INFORMATION",
  "recipient_ids": ["user123", "user456"],
  "cc_ids": ["user789"],
  "bcc_ids": ["user321"],
  "is_draft": true,
  "parent_id": null,
  "meta_record_ids": [],
  "group_id": null
}
```

### MessageUpdateDto

DTO for updating an existing message.

```json
{
  "subject": "Updated: Meeting tomorrow",
  "body": "Let's discuss the project status and next steps.",
  "flag": "MEDIUM",
  "recipient_ids": ["user123", "user456", "user789"],
  "cc_ids": [],
  "bcc_ids": [],
  "meta_record_ids": ["meta123"]
}
```

### MessageViewDto

DTO for viewing a message.

```json
{
  "id": "msg123",
  "subject": "Meeting tomorrow",
  "body": "Let's discuss the project status.",
  "flag": "INFORMATION",
  "is_draft": false,
  "sent_at": "2023-06-15T15:00:00Z",
  "parent_id": null,
  "users": [
    {
      "id": "msg123_user123",
      "message_id": "msg123",
      "user_id": "user123",
      "is_sender": true,
      "is_addressee": false,
      "is_copied_on": false,
      "is_blind_copied_on": false,
      "is_read": true,
      "read_at": "2023-06-15T15:05:00Z"
    },
    {
      "id": "msg123_user456",
      "message_id": "msg123",
      "user_id": "user456",
      "is_sender": false,
      "is_addressee": true,
      "is_copied_on": false,
      "is_blind_copied_on": false,
      "is_read": false,
      "read_at": null
    }
  ],
  "meta_record_ids": ["meta123"],
  "group_id": null
}
```

### MessageListDto

DTO for a list of messages with pagination information.

```json
{
  "items": [
    {
      "id": "msg123",
      "subject": "Meeting tomorrow",
      "body": "Let's discuss the project status.",
      "flag": "INFORMATION",
      "is_draft": false,
      "sent_at": "2023-06-15T15:00:00Z",
      "parent_id": null,
      "users": [...],
      "meta_record_ids": ["meta123"],
      "group_id": null
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

## Endpoints

### Get Messages

Retrieves messages for a specific user.

```
GET /api/v1/messages?user_id={user_id}&only_unread={only_unread}&page={page}&page_size={page_size}
```

**Query Parameters:**

- `user_id` (required): ID of the user to get messages for
- `only_unread` (optional): Only include unread messages. Default: `false`
- `page` (optional): Page number. Default: `1`
- `page_size` (optional): Number of items per page. Default: `20`

**Response:** `MessageListDto`

### Get Draft Messages

Retrieves draft messages for a specific user.

```
GET /api/v1/messages/drafts?user_id={user_id}&page={page}&page_size={page_size}
```

**Query Parameters:**

- `user_id` (required): ID of the user to get draft messages for
- `page` (optional): Page number. Default: `1`
- `page_size` (optional): Number of items per page. Default: `20`

**Response:** `MessageListDto`

### Get Sent Messages

Retrieves sent messages for a specific user.

```
GET /api/v1/messages/sent?user_id={user_id}&page={page}&page_size={page_size}
```

**Query Parameters:**

- `user_id` (required): ID of the user to get sent messages for
- `page` (optional): Page number. Default: `1`
- `page_size` (optional): Number of items per page. Default: `20`

**Response:** `MessageListDto`

### Get Message Thread

Retrieves all messages in a thread.

```
GET /api/v1/messages/thread/{message_id}?page={page}&page_size={page_size}
```

**Path Parameters:**

- `message_id` (required): ID of the parent message

**Query Parameters:**

- `page` (optional): Page number. Default: `1`
- `page_size` (optional): Number of items per page. Default: `20`

**Response:** `MessageListDto`

### Get Message

Retrieves a specific message by ID.

```
GET /api/v1/messages/{message_id}
```

**Path Parameters:**

- `message_id` (required): ID of the message to retrieve

**Response:** `MessageViewDto`

### Create Message

Creates a new message.

```
POST /api/v1/messages?sender_id={sender_id}
```

**Query Parameters:**

- `sender_id` (required): ID of the sender

**Request Body:** `MessageCreateDto`

**Response:** `MessageViewDto`

### Update Message

Updates an existing message.

```
PUT /api/v1/messages/{message_id}
```

**Path Parameters:**

- `message_id` (required): ID of the message to update

**Request Body:** `MessageUpdateDto`

**Response:** `MessageViewDto`

### Send Message

Sends a draft message.

```
POST /api/v1/messages/{message_id}/send
```

**Path Parameters:**

- `message_id` (required): ID of the message to send

**Response:** `MessageViewDto`

### Mark as Read

Marks a message as read by a specific user.

```
POST /api/v1/messages/{message_id}/read?user_id={user_id}
```

**Path Parameters:**

- `message_id` (required): ID of the message to mark as read

**Query Parameters:**

- `user_id` (required): ID of the user who read the message

**Response:** `MessageViewDto`

### Delete Message

Deletes a message.

```
DELETE /api/v1/messages/{message_id}
```

**Path Parameters:**

- `message_id` (required): ID of the message to delete

**Response:** No content (204)

## Integration Examples

### Client-Side API Integration

Here's how to integrate with the Messaging API from a client application:

```typescript
// Example using fetch API in TypeScript
async function getMessages(userId: string, onlyUnread: boolean = false, page: number = 1): Promise<MessageListDto> {
  const response = await fetch(
    `/api/v1/messages?user_id=${userId}&only_unread=${onlyUnread}&page=${page}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get messages: ${response.statusText}`);
  }
  
  return await response.json();
}

async function createMessage(messageData: MessageCreateDto, senderId: string): Promise<MessageViewDto> {
  const response = await fetch(
    `/api/v1/messages?sender_id=${senderId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(messageData)
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to create message: ${response.statusText}`);
  }
  
  return await response.json();
}
```

### Server-Side API Integration

Here's how to register the Messaging API endpoints in your FastAPI application:

```python
from fastapi import FastAPI
from uno.messaging import register_messaging_endpoints

app = FastAPI()

# Register messaging endpoints
messaging_endpoints = register_messaging_endpoints(
    app,
    path_prefix="/api/v1",
    include_auth=True
)
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded with no content to return
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a detail message explaining the error:

```json
{
  "detail": "Message with ID msg123 not found"
}
```

## Message Importance Levels

The `flag` field in messages can have the following values:

- `INFORMATION`: Standard informational message
- `LOW`: Low importance message
- `MEDIUM`: Medium importance message
- `HIGH`: High importance message
- `CRITICAL`: Critical importance message

## Message Lifecycle

1. Create a draft message: `POST /api/v1/messages` with `is_draft=true`
2. Edit the draft: `PUT /api/v1/messages/{message_id}`
3. Send the message: `POST /api/v1/messages/{message_id}/send`
4. Recipient reads the message: `POST /api/v1/messages/{message_id}/read`
5. Reply to the message: `POST /api/v1/messages` with `parent_id={original_message_id}`

## UI Component Integration

Integrate with the Messaging UI components:

```html
<!-- Message List Component -->
<wa-message-list user-id="user123"></wa-message-list>

<!-- Message Composer Component -->
<wa-message-composer sender-id="user123"></wa-message-composer>

<!-- Message View Component -->
<wa-message-view message-id="msg123"></wa-message-view>
```