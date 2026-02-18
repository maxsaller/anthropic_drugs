# Claude Opus 4.6 Research Notes

> Compiled: 2026-02-17 | For upgrading sonnet-steroid repo

---

## 1. Model Identity

| Property | Value |
|---|---|
| **Model ID** | `claude-opus-4-6` |
| **Release Date** | February 5, 2026 |
| **Context Window** | 200K standard, 1M beta (`context-1m-2025-08-07`) |
| **Max Output Tokens** | **128K** (doubled from 64K on Opus 4.5) |
| **Knowledge Cutoff** | May 2025 (reliable), August 2025 (training) |
| **API Version** | `2023-06-01` (unchanged) |

### Pricing

| Category | Price |
|---|---|
| Input tokens | $5 / MTok |
| Output tokens | $25 / MTok |
| 5-min cache writes | $6.25 / MTok |
| 1-hour cache writes | $10 / MTok |
| Cache reads | $0.50 / MTok |

---

## 2. Breaking Changes for Opus 4.6

### Prefill Removal
- Prefilling assistant messages returns **400 error**
- Use system prompt instructions or `output_config.format` instead
- For continuations: use a user message ("Your previous response was interrupted...")

### Streaming Error Recovery Changed
- Claude 4.5: Resume by replaying partial assistant message
- Claude 4.6: Add a user message instructing continuation

### Deprecated Features
1. **`thinking: {type: "enabled", budget_tokens: N}`** -- Use `thinking: {type: "adaptive"}` instead
2. **`interleaved-thinking-2025-05-14` beta header** -- Deprecated on Opus 4.6 (adaptive auto-enables it)
3. **`output_format`** parameter -- Use `output_config.format` instead

---

## 3. Adaptive Thinking (NEW - Recommended for Opus 4.6)

Replaces manual `budget_tokens` approach. Claude dynamically decides when and how much to think.

```json
{
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "high"}
}
```

### Three Thinking Modes

| Mode | Config | When to Use |
|---|---|---|
| **Adaptive** (NEW) | `thinking: {type: "adaptive"}` | Opus 4.6 / Sonnet 4.6 -- recommended |
| **Manual** (deprecated) | `thinking: {type: "enabled", budget_tokens: N}` | Older models, legacy support |
| **Disabled** | Omit `thinking` | No thinking needed |

### Key Characteristics
- Claude evaluates complexity and decides whether/how much to think
- Automatically enables interleaved thinking (no beta header needed)
- At `high`/`max` effort, Claude almost always thinks
- At lower effort, may skip thinking for simple problems
- `max_tokens` acts as hard limit on total output (thinking + response)
- Promptable -- system prompt can guide when Claude thinks

---

## 4. Effort Parameter (GA - No Beta Header Required)

Controls inference effort level. Works independently from thinking.

```json
{
    "output_config": {
        "effort": "medium"
    }
}
```

### Values

| Level | Description | Availability |
|---|---|---|
| `max` | Maximum capability, no constraints | **Opus 4.6 only** |
| `high` | Default behavior | Opus 4.6, Sonnet 4.6, Opus 4.5 |
| `medium` | Balanced, moderate token savings | Opus 4.6, Sonnet 4.6, Opus 4.5 |
| `low` | Most efficient, significant savings | Opus 4.6, Sonnet 4.6, Opus 4.5 |

### Relationship to budget_tokens
- **Opus 4.6 / Sonnet 4.6**: `effort` replaces `budget_tokens` (deprecated)
- **Older models**: `effort` works alongside `budget_tokens`
- Effort is a behavioral signal, not a strict token budget
- Affects ALL tokens: text, tool calls, AND thinking

---

## 5. Beta Headers Reference

### Still Required

| Feature | Beta Header |
|---|---|
| 1M context window | `context-1m-2025-08-07` |
| Extended cache TTL (1hr) | `extended-cache-ttl-2025-04-11` |
| Fast mode | `fast-mode-2026-02-01` |
| Agent Skills | `skills-2025-10-02` |
| Dynamic web filtering | `code-execution-web-tools-2026-02-09` |
| Interleaved thinking (Sonnet 4.6 only) | `interleaved-thinking-2025-05-14` |

### No Longer Required (GA)

| Feature | Old Header | Status |
|---|---|---|
| Prompt caching | `prompt-caching-2024-07-31` | GA |
| Effort parameter | `effort-2025-11-24` | GA |
| Web search (basic) | -- | GA |
| Web fetch (basic) | -- | GA |
| Code execution | `code-execution-2025-08-25` | GA (free with web tools) |
| 128K output | `output-128k-2025-02-19` | Built-in on Opus 4.6 |
| Interleaved thinking | `interleaved-thinking-2025-05-14` | Deprecated on Opus 4.6 |

---

## 6. Tool Versions

### Current Versions

| Tool | Current Type | Newer Version Available |
|---|---|---|
| Web Search | `web_search_20250305` (GA) | `web_search_20260209` (beta, dynamic filtering) |
| Web Fetch | `web_fetch_20250910` (GA) | `web_fetch_20260209` (beta, dynamic filtering) |
| Code Execution | `code_execution_20250825` | `code_execution_20260120` |
| Text Editor | `text_editor_20250124` | `text_editor_20250728` |

---

## 7. Streaming Events (Complete)

### Event Types
1. `message_start` -- stream init, contains `Message` with empty content
2. `content_block_start` -- new block with `index` and `content_block`
3. `content_block_delta` -- incremental update with `delta`
4. `content_block_stop` -- block complete
5. `message_delta` -- top-level changes (stop_reason, cumulative usage)
6. `message_stop` -- stream complete
7. `ping` -- keepalive
8. `error` -- in-stream error

### Delta Types
| Delta | `delta.type` | Key Field | Block Type |
|---|---|---|---|
| Text | `text_delta` | `delta.text` | `text` |
| Input JSON | `input_json_delta` | `delta.partial_json` | `tool_use`, `server_tool_use` |
| Thinking | `thinking_delta` | `delta.thinking` | `thinking` |
| Signature | `signature_delta` | `delta.signature` | `thinking` |
| Citations | `citations_delta` | `delta.citation` | `text` |

### Content Block Types
| Type | Description |
|---|---|
| `text` | Text output, may include citations |
| `thinking` | Reasoning with `thinking` + `signature` fields |
| `redacted_thinking` | Encrypted thinking (safety) |
| `tool_use` | Client-side tool call |
| `server_tool_use` | Server-side tool call |
| `web_search_tool_result` | Web search results |

### Stop Reasons
| Reason | Description |
|---|---|
| `end_turn` | Natural completion |
| `max_tokens` | Hit limit |
| `stop_sequence` | Custom stop |
| `tool_use` | Tool invocation |
| `refusal` | Model refused (Claude 4+) |
| `pause_turn` | Server tool loop limit reached |

---

## 8. Request Parameters (Messages API)

### New Parameters for Opus 4.6

```json
{
    "model": "claude-opus-4-6",
    "max_tokens": 16000,
    "stream": true,
    "thinking": {"type": "adaptive"},
    "output_config": {
        "effort": "high",
        "format": {"type": "json_schema", "schema": {}}
    },
    "speed": "standard",
    "service_tier": "auto",
    "inference_geo": "global",
    "metadata": {"user_id": "uuid-hash"},
    "messages": [...],
    "system": [...],
    "tools": [...]
}
```

### Temperature Constraints
- **Cannot set `temperature` when thinking is enabled**
- Cannot set `top_k` when thinking is enabled
- `top_p` can be 0.95-1.0 with thinking

---

## 9. Prompt Caching Updates

- GA -- `prompt-caching-2024-07-31` header no longer needed
- 1-hour TTL still requires `extended-cache-ttl-2025-04-11`
- Cache control syntax: `"cache_control": {"type": "ephemeral"}` (5min) or `{"type": "ephemeral", "ttl": "1h"}`
- Up to 4 breakpoints per request
- Min cacheable: 4096 tokens for Opus 4.6
- Switching between adaptive/enabled/disabled thinking breaks message cache
- Tool definition changes invalidate ALL caches

---

## 10. Gaps in Current Codebase

| Gap | Current State | Required Change |
|---|---|---|
| Model ID | `claude-sonnet-4-5-20250929` | `claude-opus-4-6` |
| Max tokens cap | Hardcoded 8192 | Support up to 128K |
| Thinking budget cap | Hardcoded 16000 | Remove (use adaptive) |
| Thinking mode | `{type: "enabled", budget_tokens: N}` | `{type: "adaptive"}` |
| Effort parameter | Not implemented | Add `output_config.effort` |
| Beta headers | Includes deprecated headers | Update header list |
| Temperature validation | Not validated with thinking | Block when thinking enabled |
| Interleaved thinking header | Always added | Remove for Opus 4.6 |
| Prompt caching header | Always added | Remove (GA) |
| `speed` parameter | Not implemented | Optional: add fast mode |
| `service_tier` | Not implemented | Optional |
| `metadata.user_id` | Not implemented | Optional |
| Streaming error recovery | Not implemented | User-message continuation |
| New tool versions | Old versions | Update to latest |
