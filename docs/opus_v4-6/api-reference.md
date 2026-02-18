# Claude Opus 4.6 -- API Reference

> Derived from research notes compiled 2026-02-17.
> Covers every parameter, header, event, and content-block type needed to
> build against the Anthropic Messages API with Claude Opus 4.6.

---

## Table of Contents

1. [Endpoint and Authentication](#1-endpoint-and-authentication)
2. [Request Parameters](#2-request-parameters)
3. [Thinking Configuration](#3-thinking-configuration)
4. [Output Configuration](#4-output-configuration)
5. [Beta Headers](#5-beta-headers)
6. [Tool Definitions](#6-tool-definitions)
7. [Prompt Caching](#7-prompt-caching)
8. [Response Schema (Non-Streaming)](#8-response-schema-non-streaming)
9. [Streaming Events](#9-streaming-events)
10. [Content Block Types](#10-content-block-types)
11. [Delta Types](#11-delta-types)
12. [Stop Reasons](#12-stop-reasons)
13. [Pricing](#13-pricing)

---

## 1. Endpoint and Authentication

### Base URL

```
POST https://api.anthropic.com/v1/messages
```

### Required Headers

| Header | Value |
|---|---|
| `x-api-key` | Your Anthropic API key |
| `anthropic-version` | `2023-06-01` (unchanged from previous models) |
| `content-type` | `application/json` |

### Optional Headers

| Header | Value | Purpose |
|---|---|---|
| `anthropic-beta` | Comma-separated list | Enable beta features (see [Beta Headers](#5-beta-headers)) |

---

## 2. Request Parameters

### Complete Request Shape

```json
{
    "model": "claude-opus-4-6",
    "max_tokens": 16000,
    "stream": true,
    "messages": [
        {
            "role": "user",
            "content": "..."
        }
    ],
    "system": [
        {
            "type": "text",
            "text": "You are a helpful assistant.",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    "thinking": {"type": "adaptive"},
    "output_config": {
        "effort": "high",
        "format": {"type": "text"}
    },
    "speed": "standard",
    "service_tier": "auto",
    "inference_geo": "global",
    "metadata": {"user_id": "uuid-hash"},
    "tools": [],
    "temperature": 1.0,
    "top_p": 1.0,
    "stop_sequences": []
}
```

### Parameter Reference

#### Required Parameters

| Parameter | Type | Description |
|---|---|---|
| `model` | `string` | Model identifier. Use `claude-opus-4-6` for Opus 4.6. |
| `max_tokens` | `integer` | Hard cap on total output tokens (thinking + response). Opus 4.6 supports up to **128,000**. |
| `messages` | `array` | Array of message objects with `role` (`user` or `assistant`) and `content`. |

#### Common Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `stream` | `boolean` | `false` | Enable server-sent event streaming. |
| `system` | `string` or `array` | -- | System prompt. Can be a plain string or an array of content blocks (needed for caching). |
| `thinking` | `object` | -- | Thinking configuration. See [Thinking Configuration](#3-thinking-configuration). |
| `output_config` | `object` | -- | Controls effort level and structured output format. See [Output Configuration](#4-output-configuration). |
| `tools` | `array` | -- | Tool definitions. See [Tool Definitions](#6-tool-definitions). |
| `metadata` | `object` | -- | Request metadata. Currently supports `user_id` (string) for abuse tracking. |

#### Sampling Parameters

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `temperature` | `float` | `1.0` | **Cannot be set when thinking is enabled.** Range 0.0--1.0. |
| `top_p` | `float` | -- | When thinking is enabled: must be 0.95--1.0. |
| `top_k` | `integer` | -- | **Cannot be set when thinking is enabled.** |
| `stop_sequences` | `array` | -- | Custom stop strings (array of strings). |

#### New Parameters (Opus 4.6)

| Parameter | Type | Values | Description |
|---|---|---|---|
| `speed` | `string` | `"standard"`, `"fast"` | Inference speed mode. `"fast"` requires the `fast-mode-2026-02-01` beta header. |
| `service_tier` | `string` | `"auto"`, `"standard"` | Routing tier. `"auto"` may route to higher-capacity infrastructure. |
| `inference_geo` | `string` | `"global"`, region codes | Geographic preference for inference. |

### Prefill Removal (Breaking Change)

On Opus 4.6, prefilling assistant messages returns a **400 error**. This means you cannot start the assistant's response with pre-written text. Alternatives:

- Use system prompt instructions to guide output format.
- Use `output_config.format` for structured output (JSON schema).
- For continuations after interruption, add a user message like: "Your previous response was interrupted. Please continue from where you left off."

---

## 3. Thinking Configuration

Opus 4.6 introduces **adaptive thinking** as the recommended mode, replacing the manual `budget_tokens` approach.

### Three Modes

#### Adaptive (Recommended for Opus 4.6)

```json
{
    "thinking": {"type": "adaptive"}
}
```

Claude dynamically decides whether and how much to think based on problem complexity. Automatically enables interleaved thinking (no separate beta header needed on Opus 4.6).

#### Manual (Deprecated on Opus 4.6)

```json
{
    "thinking": {"type": "enabled", "budget_tokens": 10000}
}
```

Still functional but deprecated. Use adaptive mode instead for Opus 4.6.

#### Disabled

Omit the `thinking` parameter entirely.

### Adaptive Thinking Behavior

| Effort Level | Thinking Behavior |
|---|---|
| `max` | Almost always thinks, extensive reasoning |
| `high` (default) | Almost always thinks |
| `medium` | May skip thinking for simple tasks |
| `low` | Rarely thinks |

Key characteristics:

- Claude evaluates complexity and chooses thinking depth autonomously.
- `max_tokens` acts as a hard limit on **total** output (thinking + response combined).
- Thinking behavior is promptable -- system prompt instructions can guide when Claude engages deep reasoning.
- Switching between `adaptive` / `enabled` / `disabled` across turns **breaks message cache**.

---

## 4. Output Configuration

### Effort Parameter (GA -- No Beta Header)

Controls overall inference effort. Affects text generation, tool calls, **and** thinking depth.

```json
{
    "output_config": {
        "effort": "high"
    }
}
```

| Level | Description | Availability |
|---|---|---|
| `max` | Maximum capability, no constraints | Opus 4.6 only |
| `high` | Default behavior | Opus 4.6, Sonnet 4.6, Opus 4.5 |
| `medium` | Balanced, moderate token savings | Opus 4.6, Sonnet 4.6, Opus 4.5 |
| `low` | Most efficient, significant token savings | Opus 4.6, Sonnet 4.6, Opus 4.5 |

On Opus 4.6 / Sonnet 4.6, `effort` **replaces** `budget_tokens` as the primary way to control thinking depth. On older models, `effort` works alongside `budget_tokens`.

### Structured Output Format

```json
{
    "output_config": {
        "format": {"type": "json_schema", "schema": { ... }}
    }
}
```

Replaces the deprecated `output_format` top-level parameter.

---

## 5. Beta Headers

Set via the `anthropic-beta` header as a comma-separated string.

### Currently Required Beta Headers

| Feature | Header Value |
|---|---|
| 1M context window | `context-1m-2025-08-07` |
| Extended cache TTL (1 hour) | `extended-cache-ttl-2025-04-11` |
| Fast inference mode | `fast-mode-2026-02-01` |
| Agent Skills | `skills-2025-10-02` |
| Dynamic web filtering (new tool versions) | `code-execution-web-tools-2026-02-09` |
| Interleaved thinking (Sonnet 4.6 only) | `interleaved-thinking-2025-05-14` |

### No Longer Required (GA or Deprecated)

| Feature | Old Header | Status on Opus 4.6 |
|---|---|---|
| Prompt caching | `prompt-caching-2024-07-31` | GA -- remove header |
| Effort parameter | `effort-2025-11-24` | GA -- remove header |
| Web search (basic) | -- | GA |
| Web fetch (basic) | -- | GA |
| Code execution | `code-execution-2025-08-25` | GA (free with web tools) |
| 128K output | `output-128k-2025-02-19` | Built-in on Opus 4.6 -- remove header |
| Interleaved thinking | `interleaved-thinking-2025-05-14` | **Deprecated on Opus 4.6** (adaptive auto-enables it) |

### Example Header Construction

For a request using extended cache, web search, and skills:

```
anthropic-beta: extended-cache-ttl-2025-04-11,skills-2025-10-02
```

---

## 6. Tool Definitions

Tools are passed in the `tools` array. There are two categories: **server-side tools** (executed by Anthropic) and **client-side tools** (executed by your application).

### Web Search

```json
{
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
    "allowed_domains": ["wikipedia.org", "github.com"],
    "blocked_domains": []
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | GA version: `web_search_20250305`. Beta with dynamic filtering: `web_search_20260209`. |
| `name` | `string` | Must be `"web_search"`. |
| `max_uses` | `integer` | Max searches per request (1--20). |
| `allowed_domains` | `array` | Whitelist of domains. Cannot be used with `blocked_domains`. |
| `blocked_domains` | `array` | Blacklist of domains. Cannot be used with `allowed_domains`. |

### Web Fetch

```json
{
    "type": "web_fetch_20250910",
    "name": "web_fetch"
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | GA version: `web_fetch_20250910`. Beta: `web_fetch_20260209`. |
| `name` | `string` | Must be `"web_fetch"`. |

### Code Execution

```json
{
    "type": "code_execution_20250825",
    "name": "code_execution",
    "container": {
        "skill_ids": ["xlsx", "pptx", "docx", "pdf"]
    }
}
```

| Field | Type | Description |
|---|---|---|
| `type` | `string` | GA version: `code_execution_20250825`. Newer: `code_execution_20260120`. |
| `name` | `string` | Must be `"code_execution"`. |
| `container.skill_ids` | `array` | Optional. Built-in skills: `xlsx`, `pptx`, `docx`, `pdf`. Custom skill IDs also accepted. |

Skills require the `skills-2025-10-02` beta header.

### Tool Version Summary

| Tool | GA Version | Newer Beta Version |
|---|---|---|
| Web Search | `web_search_20250305` | `web_search_20260209` (dynamic filtering) |
| Web Fetch | `web_fetch_20250910` | `web_fetch_20260209` (dynamic filtering) |
| Code Execution | `code_execution_20250825` | `code_execution_20260120` |
| Text Editor | `text_editor_20250124` | `text_editor_20250728` |

---

## 7. Prompt Caching

Prompt caching is now **GA** on Opus 4.6 -- the `prompt-caching-2024-07-31` beta header is no longer needed. Extended 1-hour TTL still requires the `extended-cache-ttl-2025-04-11` beta header.

### Cache Control Syntax

#### 5-Minute TTL (Default)

```json
{
    "type": "text",
    "text": "System prompt content...",
    "cache_control": {"type": "ephemeral"}
}
```

#### 1-Hour TTL (Requires Beta Header)

```json
{
    "cache_control": {"type": "ephemeral", "ttl": "1h"}
}
```

### Configuration Rules

| Rule | Detail |
|---|---|
| Maximum breakpoints | 4 per request |
| Minimum cacheable size | 4,096 tokens for Opus 4.6 |
| Thinking mode changes | Switching between `adaptive` / `enabled` / `disabled` across turns **invalidates** the message cache |
| Tool definition changes | Modifying any tool definition invalidates **all** caches |

### Recommended Breakpoint Strategy

1. **System prompt** -- add `cache_control` to the last item in the system array.
2. **Conversation history** -- add `cache_control` to the 2nd-to-last user message for a stable cache point.

### Pricing

| Operation | Price |
|---|---|
| 5-minute cache write | $6.25 / MTok |
| 1-hour cache write | $10 / MTok |
| Cache read (hit) | $0.50 / MTok |
| Standard input (miss) | $5 / MTok |

---

## 8. Response Schema (Non-Streaming)

```json
{
    "id": "msg_01XYZ...",
    "type": "message",
    "role": "assistant",
    "model": "claude-opus-4-6",
    "content": [
        {
            "type": "thinking",
            "thinking": "Let me analyze this...",
            "signature": "..."
        },
        {
            "type": "text",
            "text": "Here is my response...",
            "citations": [
                {
                    "type": "web_search_result_location",
                    "url": "https://example.com",
                    "title": "Example Page",
                    "cited_text": "Relevant excerpt...",
                    "start_char_index": 0,
                    "end_char_index": 42
                }
            ]
        }
    ],
    "stop_reason": "end_turn",
    "usage": {
        "input_tokens": 1200,
        "output_tokens": 450,
        "cache_read_input_tokens": 800,
        "cache_creation_input_tokens": 400,
        "server_tool_use": {
            "web_search_requests": 2
        }
    }
}
```

---

## 9. Streaming Events

When `stream: true`, the API returns server-sent events (SSE). Each event is prefixed with `data: ` followed by a JSON object.

### Event Sequence

```
message_start          -- Stream initialization, contains Message shell
ping                   -- Keepalive (may appear at any time)
content_block_start    -- New content block begins
content_block_delta    -- Incremental content update
content_block_stop     -- Content block complete
  (repeat content_block_start/delta/stop for each block)
message_delta          -- Top-level changes (stop_reason, cumulative usage)
message_stop           -- Stream complete
error                  -- In-stream error (may appear at any point)
```

### Event Type Details

#### `message_start`

```json
{
    "type": "message_start",
    "message": {
        "id": "msg_01XYZ...",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-4-6",
        "content": [],
        "stop_reason": null,
        "usage": {"input_tokens": 1200, "output_tokens": 0}
    }
}
```

#### `content_block_start`

```json
{
    "type": "content_block_start",
    "index": 0,
    "content_block": {
        "type": "thinking",
        "thinking": ""
    }
}
```

The `content_block` field contains the initial (empty) block. The `index` field identifies which block subsequent deltas belong to.

#### `content_block_delta`

```json
{
    "type": "content_block_delta",
    "index": 0,
    "delta": {
        "type": "thinking_delta",
        "thinking": "Let me consider..."
    }
}
```

See [Delta Types](#11-delta-types) for all delta variants.

#### `content_block_stop`

```json
{
    "type": "content_block_stop",
    "index": 0
}
```

#### `message_delta`

```json
{
    "type": "message_delta",
    "delta": {
        "stop_reason": "end_turn"
    },
    "usage": {
        "output_tokens": 450
    }
}
```

Contains cumulative output usage and the final `stop_reason`.

#### `message_stop`

```json
{
    "type": "message_stop"
}
```

#### `error`

```json
{
    "type": "error",
    "error": {
        "type": "overloaded_error",
        "message": "Overloaded"
    }
}
```

---

## 10. Content Block Types

Content blocks appear in both streaming (`content_block_start`) and non-streaming (`content` array) responses.

| Type | Description | Key Fields |
|---|---|---|
| `text` | Text output | `text`, optionally `citations` (array) |
| `thinking` | Extended thinking / reasoning | `thinking` (text), `signature` (verification string) |
| `redacted_thinking` | Encrypted thinking (safety/compliance) | `data` (opaque encrypted payload) |
| `tool_use` | Client-side tool invocation | `id`, `name`, `input` (JSON object) |
| `server_tool_use` | Server-side tool invocation (web search, code exec) | `id`, `name`, `input` |
| `web_search_tool_result` | Results from a web search | `search_results` (array of result objects) |

### Citation Object (within `text` blocks)

```json
{
    "type": "web_search_result_location",
    "url": "https://example.com/page",
    "title": "Page Title",
    "cited_text": "The exact text that was cited...",
    "start_char_index": 0,
    "end_char_index": 42
}
```

---

## 11. Delta Types

Deltas are incremental updates delivered inside `content_block_delta` events.

| `delta.type` | Key Field | Appears In Block Type | Description |
|---|---|---|---|
| `text_delta` | `delta.text` | `text` | Incremental text output |
| `input_json_delta` | `delta.partial_json` | `tool_use`, `server_tool_use` | Incremental JSON for tool input |
| `thinking_delta` | `delta.thinking` | `thinking` | Incremental thinking text |
| `signature_delta` | `delta.signature` | `thinking` | Verification signature for thinking block |
| `citations_delta` | `delta.citation` | `text` | Incremental citation data |

---

## 12. Stop Reasons

The `stop_reason` field appears in `message_delta` (streaming) and the top-level response (non-streaming).

| Reason | Description |
|---|---|
| `end_turn` | Natural completion -- Claude finished its response. |
| `max_tokens` | Hit the `max_tokens` limit. |
| `stop_sequence` | A custom stop sequence was encountered. |
| `tool_use` | Claude invoked a client-side tool and is waiting for the result. |
| `refusal` | Model refused the request (Claude 4+ safety feature). |
| `pause_turn` | Server tool loop limit reached; the model paused execution. |

---

## 13. Pricing

### Token Pricing (Claude Opus 4.6)

| Category | Price |
|---|---|
| Input tokens | $5 / MTok |
| Output tokens | $25 / MTok |
| 5-minute cache writes | $6.25 / MTok |
| 1-hour cache writes | $10 / MTok |
| Cache reads | $0.50 / MTok |

### Model Limits

| Property | Value |
|---|---|
| Context window | 200K standard, 1M beta |
| Max output tokens | 128,000 |
| Knowledge cutoff | May 2025 (reliable), August 2025 (training) |
| Min cacheable tokens | 4,096 |

---

## Appendix: Quick Reference Links

- Extended Thinking: https://docs.claude.com/en/docs/build-with-claude/extended-thinking
- Prompt Caching: https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- Web Search Tool: https://docs.claude.com/en/docs/build-with-claude/tool-use/web-search-tool
- Agent Skills: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- Code Execution: https://docs.claude.com/en/docs/agents-and-tools/tool-use/code-execution
