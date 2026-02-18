# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2026-02-17

> **Source files:** `src/opioid_v4-6.py` (Opus 4.6) · `src/steroid_v4-6.py` (Sonnet 4.6) | **Models:** Claude Opus 4.6 (`claude-opus-4-6`) · Claude Sonnet 4.6 (`claude-sonnet-4-6`)

### Added
- Claude Opus 4.6 model support (`claude-opus-4-6`) with 128K max output tokens
- Claude Sonnet 4.6 model support (`claude-sonnet-4-6`) with 64K max output tokens
- Adaptive thinking (replaces manual budget_tokens, always-on)
- Effort parameter (`low`/`medium`/`high`/`max`) via `EFFORT_LEVEL` valve (`max` Opus only; Sonnet defaults to `medium`)
- Per-user effort override via `MY_EFFORT_LEVEL` user valve
- Web fetch tool (`web_fetch_20260209`) for reading full page content
- `ENABLE_WEB_FETCH` and `WEB_FETCH_MAX_USES` admin valves
- Fast mode (2.5x speed at 6x cost) via `ENABLE_FAST_MODE` valve (Opus only)
- Per-user fast mode override via `ENABLE_MY_FAST_MODE` user valve (Opus only)
- Conversation compaction for long contexts via `ENABLE_COMPACTION` valve
- `COMPACTION_TRIGGER_TOKENS` valve for trigger threshold
- Container persistence across conversation turns for code execution
- Cost estimation display in token usage (`SHOW_COST_ESTIMATE` valve)
- Status indicators during tool use ("Searching the web...", "Reading web page...", "Running code...")
- `citations_delta` streaming handler for inline citation extraction
- `redacted_thinking` handler with safety notice display
- `compaction` block handler
- Citation deduplication via URL tracking (eliminates duplicates)
- Prefill guard (strips trailing assistant messages to prevent API errors)

### Changed
- **BREAKING:** Migrated from `requests` (sync) to `aiohttp` (async) for non-blocking streaming
- **BREAKING:** Model upgraded from Sonnet 4.5 to Opus 4.6
- New beta headers: `code-execution-web-tools-2026-02-09`, `compact-2026-01-12`, `fast-mode-2026-02-01` (Opus only)
- Web search upgraded from `web_search_20250305` to `web_search_20260209`
- Max tokens cap increased from 8,192 to 128,000 (Opus) / 64,000 (Sonnet)
- Default max tokens increased from 8,192 to 16,384
- System message always normalized to array format immediately
- Citation extraction moved to inline (during stream) instead of post-stream rescan

### Removed
- `ENABLE_EXTENDED_THINKING` valve (adaptive thinking is always on)
- `THINKING_BUDGET_TOKENS` valve (replaced by effort parameter)
- `all_events` accumulation (eliminated memory leak from storing all streaming events)
- Deprecated beta headers: `prompt-caching-2024-07-31` (GA), `web-search-2025-03-05`, `code-execution-2025-08-25`
- `interleaved-thinking-2025-05-14` header removed from Opus (deprecated), retained for Sonnet 4.6
- Temperature and top_k parameters (incompatible with always-on thinking)
- Emoji from all log messages and error messages

### Fixed
- User valves access correctly handles dict-based `__user__` parameter from OpenWebUI
- `SHOW_CITATIONS` valve now actually controls citation emission
- Non-streaming response now properly async with `await`

### Migration from v4.1.0
- Replace `src/steroid_v4-5.py` with `src/opioid_v4-6.py` (Opus) or `src/steroid_v4-6.py` (Sonnet) in OpenWebUI Functions
- Remove `ENABLE_EXTENDED_THINKING` and `THINKING_BUDGET_TOKENS` from any saved config
- Set `EFFORT_LEVEL` to desired level (default: `high`)
- Ensure `aiohttp` is available in your Python environment

---

## [4.1.0] - 2025-11-17

> **Source file:** `src/steroid_v4-5.py` | **Model:** Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

### Fixed
- Image pasting now works correctly - transforms OpenAI `image_url` format to Anthropic `image` format
- Support for both base64-encoded images and external image URLs
- Graceful error handling for malformed image data

### Added
- `_transform_image_content` helper method for image format conversion
- Debug logging for image transformation details

## [4.0.0] - 2025-11-13

> **Source file:** `src/steroid_v4-5.py` (originally `function.py`) | **Model:** Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

### Added
- ✅ **`<think>` tag support** for collapsible, real-time thinking display
  - OpenWebUI-native collapsible thinking sections
  - Real-time streaming of reasoning as it happens
  - Clickable "Thinking..." notification
- ✅ **JSON fragment accumulation** for web search query capture
  - Accumulates partial JSON fragments across streaming events
  - Robust parsing of character-by-character query streaming
  - Fixes "query not captured" issue from v3
- ✅ **Clean UI design** without icons
  - Removed icons from collapsible sections
  - Professional, minimal appearance
  - Markdown-only formatting (no HTML/CSS)
- ✅ **Comprehensive logging** for debugging
  - Detailed event logging
  - Query accumulation trace logs
  - Token usage tracking

### Fixed
- 🐛 **Opening `<think>` tag not appearing** (critical bug)
  - Root cause: State set too early in `content_block_start`
  - Solution: Let first `thinking_delta` handle state and tag opening
  - Result: Thinking now displays correctly in collapsible section
- 🐛 **Web search queries showing as "(query not captured)"**
  - Root cause: Queries stream as character fragments, not complete JSON
  - Solution: Accumulate fragments in buffer until valid JSON
  - Result: All search queries now captured and displayed correctly
- 🐛 **Citation chips working correctly**
  - Fixed event emitter format for OpenWebUI
  - Web search results properly formatted as citations
  - Clickable citation chips at response bottom

### Changed
- 📝 **Switched from HTML/CSS to Markdown** for all formatting
  - OpenWebUI doesn't render inline HTML
  - All sections now use Markdown formatting
  - Collapsible sections use `<details>` tags
- 📝 **Removed reasoning section at bottom**
  - Redundant with `<think>` tags
  - Cleaner response format
  - Thinking integrated into response flow

### Technical Details
- **Think tag state machine:**
  ```python
  NOT_STARTED → first thinking_delta opens <think> → IN_PROGRESS
  → content_block_stop closes </think> → COMPLETED
  ```
- **Query accumulation algorithm:**
  ```python
  partial_json_buffer += fragment
  try: json.loads(buffer) → extract query
  except: continue accumulating
  ```

### Migration from v3
- Replace `claude_sonnet_complete_v3.py` with `src/steroid_v4-5.py` (previously `function.py`)
- All valve settings preserved
- Improved UX with no configuration changes needed

---

## [3.0.0] - 2025-11-12

### Added
- ✅ **Extended thinking** with configurable budget (1,024-16,000 tokens)
- ✅ **Web search** powered by Anthropic API
- ✅ **Prompt caching** with 5min/1hour TTL options
- ✅ **Citations** from web search results
- ✅ **Skills system** (xlsx, pptx, docx, pdf) with custom skill support
- ✅ **Code execution** in secure sandbox
- ✅ **Dynamic beta header composition**
- ✅ **Collapsible sections** for web searches and token usage
- ✅ **Comprehensive valve system** for admin and user settings

### Issues (Deprecated)
- ❌ **Thinking displayed as raw text** instead of collapsible
  - Attempted HTML/CSS formatting, but OpenWebUI doesn't render inline HTML
  - Progress bar notifications stacked incorrectly
  - No real-time streaming of thinking text
- ❌ **Web search query capture broken**
  - Queries streaming as character fragments not handled
  - All searches showed "(query not captured)"
  - No accumulation buffer implemented
- ❌ **HTML/CSS rendered as raw text**
  - Beautiful cards and formatting displayed as `<div style='...'>`
  - OpenWebUI treats output as Markdown, escapes HTML
- ❌ **Citations inconsistent**
  - Formal API citations often empty
  - Fallback citation implementation incomplete

### Deprecation Notice
**v3.0.0 is deprecated** and replaced by v4.0.0. See [`archive/v3.0.0/function.py`](archive/v3.0.0/function.py) for historical reference.

---

## Version Comparison

| Feature | v3.0.0 | v4.0.0 |
|---------|--------|--------|
| Extended thinking | ⚠️ Raw text | ✅ Collapsible `<think>` |
| Web search queries | ❌ Not captured | ✅ Captured correctly |
| UI formatting | ❌ HTML (broken) | ✅ Markdown |
| Citations | ⚠️ Inconsistent | ✅ Working |
| Thinking streaming | ❌ Progress bar | ✅ Real-time text |
| Clean UI | ❌ Icons, HTML | ✅ Minimal design |
| Debugging | ⚠️ Basic logs | ✅ Comprehensive |

---

## Future Roadmap

### Planned Features
- 📄 **Document citations with inline markers** - `[1]`, `[2]` in response text
  - Waiting for Anthropic to add character positions to web search citations
  - Currently possible with uploaded documents (PDF, text)
- 🔧 **Advanced caching strategies** - Per-conversation cache management
- 📊 **Usage analytics** - Built-in token/cost tracking dashboard
- 🎨 **Customizable UI themes** - User-selectable response formatting
- 🔌 **Webhook support** - External integrations and notifications

### Under Consideration
- 🌐 **Multi-model support** - Opus, Haiku alongside Sonnet
- 🔄 **Conversation branching** - Alternative response paths
- 📝 **Response templating** - Structured output formats
- 🛡️ **Enhanced security** - Additional sandboxing options

---

## Breaking Changes

### v3.0.0 → v4.0.0
- **No breaking changes to valves** - All settings preserved
- **UI changes only** - Better UX, same functionality
- **Drop-in replacement** - Copy new `src/steroid_v4-5.py` (previously `function.py`), done!
- **Source file moved** - `function.py` relocated to `src/steroid_v4-5.py`

---

## Known Issues

### Current Limitations
1. **Web search citations don't include inline markers** - By design (API limitation)
2. **Thinking budget is a maximum, not a guarantee** - Actual usage varies
3. **Cache TTL cannot be customized per-request** - Global setting only

See [Troubleshooting Guide](docs/guides/troubleshooting.md) for solutions to common issues.

---

## Development History

### Design Phase (2025-11-12)
- Created comprehensive design document
- Researched Claude API features
- Planned valve system architecture
- Defined event processing pipeline

### v3 Implementation (2025-11-12)
- Implemented core features
- Attempted HTML/CSS formatting
- Encountered OpenWebUI rendering limitations
- Identified critical bugs

### v4 Implementation (2025-11-13)
- Adopted `<think>` tags for thinking display
- Implemented JSON fragment accumulation
- Fixed all critical bugs from v3
- Cleaned up UI design
- Added comprehensive logging

### Documentation Overhaul (2025-11-13)
- Restructured repository
- Created comprehensive guides
- Added API reference
- Documented architecture
- Created this changelog

---

## Contributing

Found a bug? Want to add a feature? See our [Contributing Guidelines](README.md#-contributing).

---

## Acknowledgments

**Technologies:**
- Anthropic Claude API and extended thinking capabilities
- OpenWebUI platform and community

---

**Questions?** Open an [issue](../../issues) or [discussion](../../discussions)!
