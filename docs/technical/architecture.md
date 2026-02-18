# Architecture Documentation

> **Applies to:** Claude Sonnet 4.5 | `src/steroid_v4-5.py` (v4.1.0)

## Overview

Claude Sonnet 4.5 Complete is a production-ready OpenWebUI pipe function that provides full access to Anthropic's latest Claude features including extended thinking, web search, prompt caching, and code execution.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         OpenWebUI                           │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   User     │→ │  Functions   │→ │  Event Emitter   │   │
│  │ Interface  │  │   Manager    │  │   (Citations)    │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│              Claude Sonnet Complete (Pipe)                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  1. Request Preprocessing                           │  │
│  │     • Extract system message                         │  │
│  │     • Process messages (text/images)                 │  │
│  │     • Validate configuration                         │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  2. Dynamic Configuration                           │  │
│  │     • Compose beta headers                          │  │
│  │     • Configure tools (web search, code exec)       │  │
│  │     • Set up thinking parameters                    │  │
│  │     • Apply prompt caching                          │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  3. API Request                                     │  │
│  │     • Build payload                                  │  │
│  │     • Add headers                                    │  │
│  │     • Make streaming request                        │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ SSE Stream
┌─────────────────────────────────────────────────────────────┐
│                    Anthropic API                            │
│                                                             │
│  • Claude Sonnet 4.5 Model (claude-sonnet-4-5-20250929)      │
│  • Extended Thinking Engine                                 │
│  • Web Search Service                                       │
│  • Code Execution Sandbox                                   │
│  • Prompt Cache                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ SSE Events
┌─────────────────────────────────────────────────────────────┐
│              Event Processing Pipeline                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  4. Event Stream Processing                         │  │
│  │     • Parse SSE events                               │  │
│  │     • Update streaming state                         │  │
│  │     • Handle <think> tags                            │  │
│  │     • Accumulate JSON fragments                      │  │
│  │     • Extract citations                              │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  5. Output Formatting                               │  │
│  │     • Format thinking with tags                      │  │
│  │     • Stream response text                          │  │
│  │     • Build collapsible sections                     │  │
│  │     • Emit citation events                          │  │
│  │     • Format token usage                            │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓ Formatted Output
┌─────────────────────────────────────────────────────────────┐
│                    OpenWebUI Display                        │
│                                                             │
│  • Collapsible <think> sections                             │
│  • Markdown-formatted response                              │
│  • Citation chips                                           │
│  • Collapsible Web Searches                                 │
│  • Collapsible Token Usage                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Configuration Management

#### Valves System
```python
class Valves(BaseModel):
    # Admin settings (global)
    ANTHROPIC_API_KEY: str
    ENABLE_EXTENDED_THINKING: bool = True
    ENABLE_WEB_SEARCH: bool = True
    # ... more settings

class UserValves(BaseModel):
    # Per-user settings
    ENABLE_MY_WEB_SEARCH: bool = True
    ENABLE_MY_CODE_EXECUTION: bool = False
```

**Design rationale:**
- Admin controls global capabilities
- Users control their personal preferences
- Two-level permission system

#### Dynamic Beta Headers
```python
def _get_headers(self, user_valves) -> Dict[str, str]:
    betas = []
    if self.valves.ENABLE_PROMPT_CACHING:
        betas.append("prompt-caching-2024-07-31")
    if self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH:
        betas.append("web-search-2025-03-05")
    # ... more features

    headers = {"anthropic-beta": ",".join(betas)}
    return headers
```

**Key features:**
- Only includes needed beta headers
- Prevents header conflicts
- Enables interleaved thinking when appropriate

---

### 2. Streaming State Management

#### StreamingState Dataclass
```python
@dataclass
class StreamingState:
    thinking_state: ThinkingState = NOT_STARTED
    thinking_buffer: str = ""
    response_buffer: str = ""
    web_searches: List[WebSearchResult] = field(default_factory=list)
    citations: List[CitationData] = field(default_factory=list)
    current_search: Optional[WebSearchResult] = None
    all_events: List[Dict[str, Any]] = field(default_factory=list)
```

**Purpose:**
- Track state across streaming events
- Manage concurrent operations (thinking + search + response)
- Store data for post-processing

#### State Transitions

**Thinking State Machine:**
```
NOT_STARTED → IN_PROGRESS → COMPLETED
     │             │              │
     │             │              │
  First         Stream        Close
thinking_delta  thinking     </think>
  opens tag     content        tag
```

**Web Search Flow:**
```
server_tool_use → input_json_delta → web_search_tool_result → content_block_stop
      ↓                  ↓                    ↓                      ↓
Create search      Accumulate          Capture results        Finalize search
   object         query fragments       in object             append to list
```

---

### 3. Event Processing Pipeline

#### Event Types

**1. message_start**
```json
{
  "type": "message_start",
  "message": {
    "usage": {
      "input_tokens": 100,
      "cache_read_input_tokens": 5000
    }
  }
}
```
**Action:** Capture initial usage stats

**2. content_block_start**
```json
{
  "type": "content_block_start",
  "index": 0,
  "content_block": {
    "type": "thinking"  // or "text", "server_tool_use", etc.
  }
}
```
**Action:** Initialize state for block type

**3. content_block_delta**
```json
{
  "type": "content_block_delta",
  "delta": {
    "type": "thinking_delta",
    "thinking": "Let me analyze..."
  }
}
```
**Action:** Stream content, update buffers

**4. content_block_stop**
```json
{
  "type": "content_block_stop",
  "index": 0
}
```
**Action:** Finalize block processing

**5. message_delta**
```json
{
  "type": "message_delta",
  "usage": {
    "output_tokens": 500,
    "thinking_tokens": 2000
  }
}
```
**Action:** Update final usage stats

**6. message_stop**
```json
{
  "type": "message_stop"
}
```
**Action:** Complete response, clean up

---

### 4. Critical Subsystems

#### A. JSON Fragment Accumulation

**Problem:**
Query comes as streaming fragments:
```
"{"
"query\": \"go"
"vernment shu"
"tdown 202"
"5\"}"
```

**Solution:**
```python
@dataclass
class WebSearchResult:
    query: str
    results: List[Dict] = field(default_factory=list)
    partial_json_buffer: str = ""  # Accumulator!

# In event handler:
state.current_search.partial_json_buffer += partial_json
try:
    parsed = json.loads(state.current_search.partial_json_buffer)
    state.current_search.query = parsed["query"]
except JSONDecodeError:
    # Keep accumulating...
```

**Why it works:**
- Buffer grows: `""` → `"{"` → `"{\"query\": \"go"` → ... → `"{\"query\": \"government shutdown\"}"`
- JSON parse fails until complete
- Extract query once valid

---

#### B. Think Tag Management

**Challenge:** OpenWebUI expects `<think>` tags around reasoning

**State machine:**
```python
# 1. First thinking_delta arrives
if state.thinking_state == NOT_STARTED:
    yield "\n<think>\n"
    state.thinking_state = IN_PROGRESS

# 2. Stream thinking content
yield thinking_text

# 3. Text response starts OR message ends
if state.thinking_state == IN_PROGRESS:
    yield "\n</think>\n\n"
    state.thinking_state = COMPLETED
```

**Critical bug (v3):**
Setting `state = IN_PROGRESS` in `content_block_start` meant first delta check failed!

**Fix (v4):**
Only change state when outputting tag.

---

#### C. Citation Extraction

**Multi-source approach:**

```python
# Try all event types
for event in state.all_events:
    if event.get("type") == "content_block_start":
        # Check content_block.citations
    elif event.get("type") == "message_start":
        # Check message.content[].citations
    elif event.get("type") == "message_delta":
        # Check delta.content[].citations
```

**Fallback chain:**
1. Formal API citations (documents)
2. Web search results as citations
3. Empty (no sources)

**Event emission:**
```python
await __event_emitter__({
    "type": "citation",
    "data": {
        "document": [title],
        "metadata": [{"source": url}],
        "source": {
            "name": "[1]",
            "type": "web_search_results",
            "urls": [url]
        }
    }
})
```

---

#### D. Prompt Caching

**Strategy:**
```
System Prompt [CACHE]
├─ User Message 1
├─ Assistant Response 1
├─ User Message 2 [CACHE]  ← 2nd-to-last
├─ Assistant Response 2
└─ User Message 3 (current)
```

**Implementation:**
```python
def _apply_caching(self, payload):
    # 1. Cache last item in system array
    payload["system"][-1]["cache_control"] = {"type": "ephemeral"}

    # 2. Cache 2nd-to-last user message
    user_indices = [i for i, m in enumerate(messages) if m["role"] == "user"]
    if len(user_indices) >= 2:
        idx = user_indices[-2]
        messages[idx]["content"][-1]["cache_control"] = {"type": "ephemeral"}
```

**Why 2nd-to-last?**
- Current message can't be cached (not sent yet)
- Previous assistant response changes frequently
- 2nd-to-last user creates stable cache point

---

### 5. Output Formatting

#### Collapsible Sections

**Thinking:**
```markdown
<think>
Reasoning content streams here in real-time...
</think>
```
OpenWebUI recognizes this and makes it collapsible automatically!

**Web Searches:**
```html
<details>
<summary>Web Searches</summary>

**Search 1:** government shutdown 2025
- Found 10 results
  1. CNN Article
  2. Wikipedia
  ...
</details>
```

**Token Usage:**
```html
<details>
<summary>Token Usage</summary>

- 💾 Cache Hit: 5,000 tokens (83% saved)
- 🧠 Thinking: 2,345 tokens
- 📥 Input: 150 tokens
- 📤 Output: 900 tokens
- 🔍 Web Searches: 1
</details>
```

**Design choice:** Collapsed by default for clean UX

---

## Data Flow Examples

### Example 1: Simple Query (No Tools)

```
User: "Explain quantum entanglement"
  ↓
[Request Processing]
  • No tools configured
  • Thinking enabled
  • Prompt caching applied
  ↓
[API Request]
  • Beta: prompt-caching-2024-07-31
  • Thinking budget: 10000
  • No tools array
  ↓
[Event Stream]
  1. content_block_start: thinking
  2. content_block_delta: thinking_delta (×N)
     → Output: "<think>\nLet me explain...\n"
  3. content_block_start: text
     → Output: "</think>\n\n"
  4. content_block_delta: text_delta (×N)
     → Output: "Quantum entanglement is..."
  5. message_stop
  ↓
[Post-Processing]
  • Format token usage
  • No citations
  ↓
[Output]
<think>
Extended reasoning about quantum mechanics...
</think>

Quantum entanglement is a phenomenon...

<details>
<summary>Token Usage</summary>
...
</details>
```

---

### Example 2: Web Search Query

```
User: "Recent government shutdown info"
  ↓
[Request Processing]
  • Web search enabled
  • Thinking enabled (interleaved)
  • Prompt caching applied
  ↓
[API Request]
  • Beta: prompt-caching,web-search,interleaved-thinking
  • Thinking budget: 10000
  • Tools: [web_search]
  ↓
[Event Stream]
  1. content_block_start: thinking
  2. content_block_delta: thinking_delta
     → Output: "<think>\nUser wants recent info...\n"
  3. content_block_start: server_tool_use (web_search)
     → Create search object, query=""
  4. content_block_delta: input_json_delta
     → Buffer: "{\"query\": \"government shutdown 2025\"}"
     → Extract: query = "government shutdown 2025"
  5. content_block_start: web_search_tool_result
     → Capture 10 results
  6. content_block_stop
     → Finalize search, append to list
  7. content_block_delta: thinking_delta
     → Output: "Based on search results...\n"
  8. content_block_start: text
     → Output: "</think>\n\n"
  9. content_block_delta: text_delta
     → Output: "Here's a summary..."
  10. message_stop
  ↓
[Post-Processing]
  • Format Web Searches section
  • Emit citation events for each result
  • Format token usage
  ↓
[Output]
<think>
User wants recent info...
[Search happening]
Based on search results...
</think>

Here's a summary of the recent government shutdown...

<details>
<summary>Web Searches</summary>
**Search 1:** government shutdown 2025
- Found 10 results
  1. CNN Article
  ...
</details>

[Citation chips at bottom]
[1] CNN [2] Wikipedia [3] ...

<details>
<summary>Token Usage</summary>
...
</details>
```

---

## Performance Considerations

### Token Efficiency

**Prompt Caching Impact:**
```
Without caching:
Request: 10,000 tokens @ $3/MTok = $0.03

With caching (90% hit):
Cached: 9,000 tokens @ $0.30/MTok = $0.0027
Fresh:  1,000 tokens @ $3/MTok = $0.003
Total: $0.0057 (81% savings!)
```

**Thinking Token Impact:**
```
Response without thinking:
Output: 500 tokens @ $15/MTok = $0.0075

Response with thinking:
Thinking: 2,000 tokens @ $15/MTok = $0.03
Output: 500 tokens @ $15/MTok = $0.0075
Total: $0.0375 (5× cost but better quality!)
```

### Latency Optimization

**Streaming advantages:**
- First token: ~1-2 seconds
- Thinking visible immediately
- Response appears progressively
- User sees work happening

**vs Non-streaming:**
- Wait for complete response
- 10-30+ seconds of silence
- Poor user experience

### Memory Management

**State object size:**
- Thinking buffer: ~10-50KB
- Web searches: ~5-20KB
- All events: ~100-500KB
- Total: <1MB per request

**Cleanup:**
- State GC'd after request
- No persistent storage
- Stateless design

---

## Security Considerations

### API Key Protection
- Never logged
- Never sent to client
- Stored in valve settings
- Environment variable fallback

### Input Validation
- Request structure validated
- Message format checked
- Configuration conflicts detected
- Malformed requests rejected

### Rate Limiting
- Anthropic API handles this
- 429 errors caught and reported
- User-friendly error messages

### Content Safety
- Anthropic's safety filters apply
- No client-side filtering needed
- Code execution sandboxed (Anthropic)

---

## Extensibility

### Adding New Features

**1. New tool type:**
```python
# In _configure_tools():
if self.valves.ENABLE_NEW_TOOL:
    tools.append({
        "type": "new_tool_type",
        "name": "new_tool",
        # ... config
    })
```

**2. New event type:**
```python
# In stream_response():
elif event_type == "new_event_type":
    # Handle new event
    pass
```

**3. New output section:**
```python
# After response:
if self.valves.SHOW_NEW_SECTION:
    yield "\n\n<details>\n"
    yield "<summary>New Section</summary>\n\n"
    # ... content
    yield "</details>\n\n"
```

### Plugin Architecture

Current design supports:
- Multiple valve levels (admin/user/context)
- Feature flags for all capabilities
- Dynamic header composition
- Modular output formatting

Future possibilities:
- Custom formatters
- Additional citation sources
- Alternative thinking displays
- Integration with other services

---

## Testing Strategy

### Unit Testing Targets
- JSON fragment accumulation
- Think tag state machine
- Cache breakpoint placement
- Beta header composition

### Integration Testing
- Full request/response cycle
- Event stream processing
- Citation extraction
- Output formatting

### Manual Testing Checklist
- [ ] Thinking displays correctly
- [ ] Web search queries captured
- [ ] Citations appear as chips
- [ ] Caching reduces costs
- [ ] All collapsible sections work
- [ ] Token usage accurate

---

## Monitoring & Observability

### Key Metrics
- Cache hit rate (from usage stats)
- Thinking token usage
- Web search frequency
- Response latency
- Error rates

### Logging Strategy
- DEBUG: All events and state changes
- INFO: Key operations (search, citations)
- WARNING: Recoverable issues
- ERROR: Failures

### Log Analysis
```bash
# Count web searches
docker logs open-webui | grep "Extracted search query" | wc -l

# Check cache hit rate
docker logs open-webui | grep "Cache Hit"

# Find errors
docker logs open-webui | grep "ERROR"
```

---

## Future Enhancements

### Planned Features
1. **Document citations with inline markers**
   - Waiting for API support
   - Would enable `[1]` markers in text

2. **Custom citation formatters**
   - APA, MLA, Chicago styles
   - Academic use cases

3. **Advanced caching strategies**
   - Conversation summarization
   - Smart breakpoint selection

4. **Performance monitoring dashboard**
   - Cost tracking
   - Usage analytics
   - Quality metrics

### API Evolution
- Track Anthropic beta releases
- Adapt to new event types
- Leverage new features
- Maintain backward compatibility

---

**Questions about the architecture? Check the troubleshooting guide or open an issue!**
