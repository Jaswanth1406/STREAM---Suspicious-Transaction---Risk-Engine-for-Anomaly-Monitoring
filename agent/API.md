# Agent API Endpoints

## `POST /agent/chat`

**Request:**

```json
{
  "messages": [
    { "role": "user", "content": "Show me the top 5 riskiest tenders" }
  ],
  "session_id": "optional-session-id"
}
```

**Response:**

```json
{
  "response": "Here are the top 5 riskiest tenders...",
  "tool_calls": [
    {
      "tool": "query_database",
      "args": { "question": "top 5 highest risk tenders" }
    }
  ],
  "session_id": "optional-session-id"
}
```

---

## `POST /agent/chat/stream`

**Request:** Same as `/agent/chat`

```json
{
  "messages": [
    { "role": "user", "content": "Investigate vendor XYZ" }
  ],
  "session_id": "optional-session-id"
}
```

**Response:** `text/event-stream` (Server-Sent Events)

```
data: {"type": "tool_start", "tool": "investigate_vendor", "input": "XYZ"}

data: {"type": "tool_end", "tool": "investigate_vendor", "output_preview": "=== VENDOR PROFILE: XYZ ===..."}

data: {"type": "token", "content": "Based"}

data: {"type": "token", "content": " on"}

data: {"type": "token", "content": " the"}

...

data: {"type": "done"}
```

### SSE Event Types

| Type | Description |
|------|-------------|
| `token` | Partial response text (streamed token-by-token) |
| `tool_start` | Agent is invoking a tool (includes tool name + input) |
| `tool_end` | Tool returned result (includes truncated preview) |
| `done` | Stream complete |
