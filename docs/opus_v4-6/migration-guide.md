# Migration Guide: Opus 4.5 / Sonnet 4.5 to Opus 4.6

> For upgrading the `sonnet-steroid` codebase from the current v4.1.0
> (targeting Claude Sonnet 4.5 / Opus 4.5) to Claude Opus 4.6.

---

## Table of Contents

1. [Breaking Changes Summary](#1-breaking-changes-summary)
2. [Thinking System Migration](#2-thinking-system-migration)
3. [Beta Header Cleanup](#3-beta-header-cleanup)
4. [Temperature and Sampling Constraints](#4-temperature-and-sampling-constraints)
5. [Max Token Changes](#5-max-token-changes)
6. [Prefill Removal](#6-prefill-removal)
7. [Streaming Error Recovery](#7-streaming-error-recovery)
8. [Tool Version Updates](#8-tool-version-updates)
9. [New Parameters](#9-new-parameters)
10. [Prompt Caching Changes](#10-prompt-caching-changes)
11. [Codebase Change Checklist](#11-codebase-change-checklist)

---

## 1. Breaking Changes Summary

| Change | Impact | Severity |
|---|---|---|
| Prefill removal | Assistant message prefill returns 400 | **Breaking** |
| Thinking mode deprecated | `budget_tokens` deprecated in favor of adaptive | **Deprecation** |
| Interleaved thinking header deprecated | No longer needed on Opus 4.6 | **Deprecation** |
| Prompt caching header removed | `prompt-caching-2024-07-31` is GA | **Cleanup** |
| Max output tokens doubled | 8192 cap is artificially low; 128K now supported | **Enhancement** |
| Temperature blocked with thinking | Cannot set temperature when thinking is enabled | **Constraint** |
| Streaming error recovery changed | Cannot replay partial assistant messages | **Behavioral** |
| `output_format` deprecated | Use `output_config.format` instead | **Deprecation** |

---

## 2. Thinking System Migration

### What Changed

The manual `budget_tokens` approach is deprecated on Opus 4.6. The new **adaptive thinking** mode lets Claude decide when and how much to think based on problem complexity.

### Before (Current Code)

Both `steroid_v4-5.py` and `opioid_v4-5.py` use this pattern:

```python
# In Valves:
THINKING_BUDGET_TOKENS: int = Field(
    default=10000,
    description="Thinking budget in tokens (1024-16000 recommended)"
)

# In _configure_thinking():
def _configure_thinking(self) -> Optional[Dict[str, Any]]:
    if not self.valves.ENABLE_EXTENDED_THINKING:
        return None
    budget = max(1024, min(self.valves.THINKING_BUDGET_TOKENS, 16000))
    return {
        "type": "enabled",
        "budget_tokens": budget
    }
```

### After (Opus 4.6)

```python
# In Valves -- replace THINKING_BUDGET_TOKENS with EFFORT_LEVEL:
EFFORT_LEVEL: Literal["low", "medium", "high", "max"] = Field(
    default="high",
    description="Inference effort level: low (fastest), medium, high (default), max (Opus 4.6 only)"
)

# In _configure_thinking():
def _configure_thinking(self) -> Optional[Dict[str, Any]]:
    if not self.valves.ENABLE_EXTENDED_THINKING:
        return None
    return {"type": "adaptive"}
```

The effort level is controlled separately via `output_config.effort` in the payload:

```python
# In _prepare_payload():
if self.valves.EFFORT_LEVEL:
    payload["output_config"] = {
        "effort": self.valves.EFFORT_LEVEL
    }
```

### Key Differences

| Aspect | budget_tokens (old) | adaptive + effort (new) |
|---|---|---|
| Who decides thinking depth | Developer sets fixed budget | Claude decides dynamically |
| Configuration | `thinking.budget_tokens: 10000` | `thinking.type: "adaptive"` + `output_config.effort: "high"` |
| Interleaved thinking | Requires separate beta header | Automatic (no header needed on Opus 4.6) |
| Token accounting | `budget_tokens < max_tokens` | `max_tokens` is hard cap on total output |
| Effort scope | Thinking only | All tokens: text, tool calls, AND thinking |

### Valve Migration

| Old Valve | New Valve | Notes |
|---|---|---|
| `THINKING_BUDGET_TOKENS` | `EFFORT_LEVEL` | Replace integer budget with effort enum |
| `ENABLE_EXTENDED_THINKING` | `ENABLE_EXTENDED_THINKING` | Keep -- still controls whether thinking is used at all |

---

## 3. Beta Header Cleanup

### What Changed

Several features graduated to GA. The interleaved thinking header is deprecated on Opus 4.6 because adaptive thinking auto-enables it.

### Before (Current Code)

In `_get_headers()` (both files):

```python
betas = []

# Prompt caching
if self.valves.ENABLE_PROMPT_CACHING:
    betas.append("prompt-caching-2024-07-31")          # <-- REMOVE (GA)
    if self.valves.CACHE_TTL == "1hour":
        betas.append("extended-cache-ttl-2025-04-11")  # <-- KEEP

# Web search
if self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH:
    betas.append("web-search-2025-03-05")              # <-- REMOVE (GA)

# Code execution + skills + files
if self._should_enable_code_execution(user_valves):
    betas.append("code-execution-2025-08-25")          # <-- REMOVE (GA)
    betas.append("skills-2025-10-02")                  # <-- KEEP
    betas.append("files-api-2025-04-14")               # <-- KEEP (review if GA)

# Interleaved thinking
if self.valves.ENABLE_EXTENDED_THINKING and self._has_tools(user_valves):
    betas.append("interleaved-thinking-2025-05-14")    # <-- REMOVE (deprecated on Opus 4.6)
```

### After (Opus 4.6)

```python
betas = []

# Extended cache TTL (still beta)
if self.valves.ENABLE_PROMPT_CACHING and self.valves.CACHE_TTL == "1hour":
    betas.append("extended-cache-ttl-2025-04-11")

# Skills (still beta)
if self._should_enable_code_execution(user_valves):
    betas.append("skills-2025-10-02")

# Fast mode (new, optional)
if self.valves.ENABLE_FAST_MODE:
    betas.append("fast-mode-2026-02-01")
```

### Summary Table

| Header | Action | Reason |
|---|---|---|
| `prompt-caching-2024-07-31` | **Remove** | GA on Opus 4.6 |
| `web-search-2025-03-05` | **Remove** | GA |
| `code-execution-2025-08-25` | **Remove** | GA |
| `interleaved-thinking-2025-05-14` | **Remove** | Deprecated; adaptive auto-enables it |
| `extended-cache-ttl-2025-04-11` | **Keep** | Still beta |
| `skills-2025-10-02` | **Keep** | Still beta |
| `files-api-2025-04-14` | **Keep** | Still beta (review) |
| `fast-mode-2026-02-01` | **Add** (optional) | New fast inference mode |
| `context-1m-2025-08-07` | **Add** (optional) | 1M context window |

---

## 4. Temperature and Sampling Constraints

### What Changed

When thinking is enabled (adaptive or manual), Opus 4.6 enforces strict constraints on sampling parameters. The current codebase does **not** validate these.

### New Constraints

| Parameter | Constraint When Thinking Is Enabled |
|---|---|
| `temperature` | **Must not be set** (returns 400 error) |
| `top_k` | **Must not be set** (returns 400 error) |
| `top_p` | Must be 0.95--1.0 |

### Required Code Change

Add validation in `_prepare_payload()`:

```python
# Temperature -- block when thinking is enabled
thinking_config = self._configure_thinking()
if thinking_config:
    payload["thinking"] = thinking_config
    # CRITICAL: Remove temperature/top_k when thinking is enabled
    payload.pop("temperature", None)
    payload.pop("top_k", None)
    # Clamp top_p if present
    if "top_p" in payload:
        payload["top_p"] = max(0.95, min(payload["top_p"], 1.0))
else:
    # Only set temperature when thinking is disabled
    if "temperature" in body:
        payload["temperature"] = body["temperature"]
    elif self.valves.DEFAULT_TEMPERATURE != 1.0:
        payload["temperature"] = self.valves.DEFAULT_TEMPERATURE
```

---

## 5. Max Token Changes

### What Changed

Opus 4.6 supports up to **128,000** output tokens (doubled from 64K on Opus 4.5). The current codebase hardcodes an 8,192 cap.

### Before (Current Code)

```python
DEFAULT_MAX_TOKENS: int = Field(
    default=8192,
    description="Default maximum tokens for responses (max 8192)"
)

def _calculate_max_tokens(self, requested_max: int) -> int:
    if not self.valves.ENABLE_EXTENDED_THINKING:
        return min(requested_max, 8192)
    # ...
    result = min(calculated, 8192)
    return result
```

### After (Opus 4.6)

```python
DEFAULT_MAX_TOKENS: int = Field(
    default=16000,
    description="Default maximum tokens for responses (up to 128000 on Opus 4.6)"
)

def _calculate_max_tokens(self, requested_max: int) -> int:
    # With adaptive thinking, max_tokens is a hard cap on total output
    # (thinking + response combined). No need to manually reserve thinking budget.
    cap = 128000  # Opus 4.6 max
    return min(max(requested_max, self.valves.DEFAULT_MAX_TOKENS), cap)
```

The `_calculate_max_tokens` method becomes much simpler because:
- Adaptive thinking does not require separate budget reservation.
- `max_tokens` is just a hard cap on total output.
- The `thinking_budget + 2000` arithmetic is no longer needed.

---

## 6. Prefill Removal

### What Changed

On Opus 4.6, if the last message in the `messages` array has `role: "assistant"` (a "prefill"), the API returns a **400 error**. Previous models allowed prefilling to steer output format.

### Impact on Current Codebase

The current code does not use prefill directly (it does not inject assistant messages), so this is a **low-risk** change. However, validation should be added to catch cases where OpenWebUI passes through an assistant prefill from a custom pipeline.

### Recommended Guard

```python
# In _prepare_payload() or pipe():
if processed_messages and processed_messages[-1]["role"] == "assistant":
    logger.warning("Removing assistant prefill -- not supported on Opus 4.6")
    processed_messages = processed_messages[:-1]
```

---

## 7. Streaming Error Recovery

### What Changed

| Scenario | Before (4.5) | After (4.6) |
|---|---|---|
| Stream interrupted mid-response | Replay the partial assistant message in a new request | Add a **user message** instructing continuation |

### Before

```python
# Could replay partial assistant message to resume
messages.append({"role": "assistant", "content": partial_text})
# Then continue the conversation
```

### After

```python
# Must use a user message to request continuation
messages.append({
    "role": "user",
    "content": "Your previous response was interrupted. Please continue from where you left off."
})
```

### Impact

The current codebase does not implement error recovery (no retry-on-stream-failure logic). If this feature is added in the future, it must use the user-message approach, not assistant-message replay.

---

## 8. Tool Version Updates

### Current Versions in Codebase

Both files currently use:

| Tool | Current Type in Code |
|---|---|
| Web Search | `web_search_20250305` |
| Code Execution | `code_execution_20250825` |

### Available Updates

| Tool | GA Version | Newer Beta Version | Change Required? |
|---|---|---|---|
| Web Search | `web_search_20250305` | `web_search_20260209` (dynamic filtering) | Optional upgrade |
| Web Fetch | `web_fetch_20250910` | `web_fetch_20260209` (dynamic filtering) | Not currently used |
| Code Execution | `code_execution_20250825` | `code_execution_20260120` | Optional upgrade |
| Text Editor | `text_editor_20250124` | `text_editor_20250728` | Not currently used |

The GA versions work fine. Upgrading to the newer beta versions requires the `code-execution-web-tools-2026-02-09` beta header and provides dynamic web filtering capabilities.

---

## 9. New Parameters

### Effort Parameter (GA)

Already covered in [Section 2](#2-thinking-system-migration). Add to payload:

```python
payload["output_config"] = {"effort": self.valves.EFFORT_LEVEL}
```

### Speed Parameter (Optional)

```python
# New valve:
ENABLE_FAST_MODE: bool = Field(
    default=False,
    description="Use fast inference mode (requires beta header)"
)

# In _prepare_payload():
if self.valves.ENABLE_FAST_MODE:
    payload["speed"] = "fast"
```

Requires `fast-mode-2026-02-01` beta header.

### Service Tier (Optional)

```python
SERVICE_TIER: Literal["auto", "standard"] = Field(
    default="auto",
    description="Routing tier: auto may use higher-capacity infrastructure"
)

# In _prepare_payload():
payload["service_tier"] = self.valves.SERVICE_TIER
```

### Metadata (Optional)

```python
# In _prepare_payload():
if __user__ and "id" in __user__:
    payload["metadata"] = {"user_id": __user__["id"]}
```

---

## 10. Prompt Caching Changes

### What Changed

- Prompt caching is now **GA** -- the `prompt-caching-2024-07-31` beta header should be removed.
- Extended 1-hour TTL still requires `extended-cache-ttl-2025-04-11`.
- Minimum cacheable size for Opus 4.6 is **4,096 tokens** (was 2,048 for some older models).
- Switching between `adaptive` / `enabled` / `disabled` thinking modes across turns **breaks the message cache**.
- Tool definition changes invalidate **all** caches.

### Code Impact

1. Remove `prompt-caching-2024-07-31` from `_get_headers()` (already covered in [Section 3](#3-beta-header-cleanup)).
2. No changes needed to `_apply_caching()` logic -- cache breakpoint placement remains the same.
3. Consider adding a note in the valve description that switching thinking modes mid-conversation will invalidate cache.

---

## 11. Codebase Change Checklist

This checklist covers every change needed across both `src/steroid_v4-5.py` and `src/opioid_v4-5.py`. Changes are grouped by area and ordered by priority.

### Model Identity and Metadata

- [ ] Update `MODEL_ID` class constant
  - `steroid_v4-5.py`: Change `"claude-sonnet-4-5-20250929"` to `"claude-opus-4-6"`
  - `opioid_v4-5.py`: Change `"claude-opus-4-5-20251101"` to `"claude-opus-4-6"`
- [ ] Update `pipes()` return value
  - `steroid_v4-5.py`: Change id/name from Sonnet 4.5 to Opus 4.6
  - `opioid_v4-5.py`: Change id/name from Opus 4.5 to Opus 4.6
- [ ] Update module docstring (title, description, version)
- [ ] Update logger init message from `"v4.0.0"` to new version
- [ ] Update class docstring from `"Claude Sonnet 4.5 Complete"` / `"Claude Opus 4.5 Complete"` to `"Claude Opus 4.6"`

### Thinking System (Both Files)

- [ ] Replace `THINKING_BUDGET_TOKENS` valve with `EFFORT_LEVEL` valve (enum: `low`, `medium`, `high`, `max`)
- [ ] Rewrite `_configure_thinking()` to return `{"type": "adaptive"}` instead of `{"type": "enabled", "budget_tokens": N}`
- [ ] Add `output_config.effort` to `_prepare_payload()`
- [ ] Simplify `_calculate_max_tokens()` -- remove thinking budget arithmetic, raise cap from 8192 to 128000

### Beta Header Cleanup (Both Files -- `_get_headers()`)

- [ ] Remove `prompt-caching-2024-07-31` from beta headers
- [ ] Remove `web-search-2025-03-05` from beta headers
- [ ] Remove `code-execution-2025-08-25` from beta headers
- [ ] Remove `interleaved-thinking-2025-05-14` from beta headers
- [ ] Keep `extended-cache-ttl-2025-04-11`
- [ ] Keep `skills-2025-10-02`
- [ ] Keep `files-api-2025-04-14`
- [ ] Optionally add `fast-mode-2026-02-01` behind a new valve

### Temperature / Sampling Validation (Both Files -- `_prepare_payload()`)

- [ ] When thinking is enabled, remove `temperature` from payload
- [ ] When thinking is enabled, remove `top_k` from payload
- [ ] When thinking is enabled, clamp `top_p` to 0.95--1.0

### Max Token Cap (Both Files)

- [ ] Update `DEFAULT_MAX_TOKENS` valve default and description (8192 -> 16000, cap to 128000)
- [ ] Update `_calculate_max_tokens()` to remove 8192 hard cap, use 128000

### Prefill Guard (Both Files -- `pipe()` or `_prepare_payload()`)

- [ ] Add guard to strip trailing assistant messages from processed messages

### New Valves (Both Files)

- [ ] Add `EFFORT_LEVEL` valve (replaces `THINKING_BUDGET_TOKENS`)
- [ ] Optionally add `ENABLE_FAST_MODE` valve
- [ ] Optionally add `SERVICE_TIER` valve

### New Payload Parameters (Both Files -- `_prepare_payload()`)

- [ ] Add `output_config.effort` based on `EFFORT_LEVEL` valve
- [ ] Optionally add `speed` parameter
- [ ] Optionally add `service_tier` parameter
- [ ] Optionally add `metadata.user_id` from `__user__`

### File Renaming (Recommended)

- [ ] Rename `src/steroid_v4-5.py` to `src/steroid_v4-6.py`
- [ ] Rename `src/opioid_v4-5.py` to `src/opioid_v4-6.py`

### Bump Version

- [ ] Update version in module docstring to `5.0.0` (breaking change warrants major version bump)

---

## Quick Reference: Minimal Viable Migration

If you want the fastest path to a working Opus 4.6 integration, these are the **minimum required changes**:

1. Change `MODEL_ID` to `"claude-opus-4-6"`.
2. Change `_configure_thinking()` to return `{"type": "adaptive"}`.
3. Add `output_config.effort` to the payload in `_prepare_payload()`.
4. Remove `prompt-caching-2024-07-31` and `interleaved-thinking-2025-05-14` from `_get_headers()`.
5. Remove `temperature` and `top_k` from the payload when thinking is enabled.
6. Raise or remove the 8192 `max_tokens` cap.

Everything else (new valves, file renames, optional parameters) is quality-of-life polish.
