# Configuration Guide

> **Applies to:** Claude Sonnet 4.5 | `src/steroid_v4-5.py` (v4.1.0)

Complete reference for all configuration options (valves) in Claude Sonnet 4.5 Complete.

## Configuration Overview

The function uses **valves** for configuration - adjustable settings that control behavior. There are two types:

- **Admin Valves** - Global settings (affect all users)
- **User Valves** - Per-user settings (individual preferences)

## Accessing Valves

1. Navigate to **Workspace → Functions**
2. Find "Claude Sonnet 4.5 (Complete)"
3. Click **Edit** or the ⚙️ **Settings** icon
4. Click the **Valves** tab

---

## Admin Valves (Global Settings)

### API & Core Settings

#### `ANTHROPIC_API_KEY`
- **Type:** String (required)
- **Default:** `""` (empty)
- **Description:** Your Anthropic API key from [console.anthropic.com](https://console.anthropic.com/)

**Example:**
```
sk-ant-api03-aBcDeFgHiJkLmNoPqRsTuVwXyZ...
```

⚠️ **Security:** Never share your API key publicly!

---

#### `DEFAULT_MAX_TOKENS`
- **Type:** Integer
- **Default:** `8192`
- **Range:** 1 - 8192
- **Description:** Maximum tokens in response (includes thinking + output)

**When to adjust:**
- **Reduce (2048-4096):** Shorter responses, faster, cheaper
- **Keep high (8192):** Long-form content, detailed explanations

**Example use case:**
```
4096 - Quick Q&A, code snippets
8192 - Essays, detailed analyses, long documents
```

---

#### `DEFAULT_TEMPERATURE`
- **Type:** Float
- **Default:** `1.0`
- **Range:** 0.0 - 1.0
- **Description:** Response randomness/creativity

**Guidelines:**
- `0.0` - Deterministic, consistent, focused
- `0.5` - Balanced creativity and consistency
- `1.0` - Maximum creativity and variation

**Example use cases:**
```
0.0 - Code generation, factual answers, data extraction
0.5 - General conversation, balanced creativity
1.0 - Creative writing, brainstorming, diverse perspectives
```

---

#### `REQUEST_TIMEOUT`
- **Type:** Integer
- **Default:** `300` (5 minutes)
- **Range:** 60 - 600
- **Description:** API request timeout in seconds

**When to increase:**
- Complex queries with high thinking budget
- Multiple web searches
- Large document processing

**Example:**
```
300  - Normal queries (default)
600  - Complex reasoning, extensive web search
```

---

### Extended Thinking

#### `ENABLE_EXTENDED_THINKING`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable Claude's reasoning process display

**When to disable:**
- You want faster responses
- Don't need to see reasoning
- Cost-sensitive applications

**UI Impact:**
- ✅ Enabled: Shows `<think>` collapsible section
- ❌ Disabled: Direct answer only

---

#### `THINKING_BUDGET_TOKENS`
- **Type:** Integer
- **Default:** `10000`
- **Range:** 1024 - 16000
- **Description:** Maximum tokens Claude can use for thinking

**Budget Guidelines:**

| Budget | Use Case | Quality | Cost | Speed |
|--------|----------|---------|------|-------|
| 2000 | Simple queries | ⭐⭐ | 💰 | ⚡⚡⚡ |
| 5000 | Standard use | ⭐⭐⭐ | 💰💰 | ⚡⚡ |
| 10000 | Complex reasoning | ⭐⭐⭐⭐ | 💰💰💰 | ⚡ |
| 16000 | Maximum quality | ⭐⭐⭐⭐⭐ | 💰💰💰💰 | 🐌 |

**Cost calculation:**
```
Thinking tokens are output tokens: $15/MTok
- 2000 budget  = $0.03 per request
- 10000 budget = $0.15 per request
- 16000 budget = $0.24 per request
```

---

### Prompt Caching

#### `ENABLE_PROMPT_CACHING`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable prompt caching for cost savings

**Benefits:**
- Up to **90% cost reduction** on cached content
- Faster response times
- Efficient multi-turn conversations

**How it works:**
- System prompts cached automatically
- User messages cached after 2+ turns
- Cache valid for 5 minutes or 1 hour (see `CACHE_TTL`)

**When to disable:**
- Rapidly changing system prompts
- Single-shot queries (no caching benefit)
- Testing/debugging cache behavior

---

#### `CACHE_TTL`
- **Type:** String
- **Default:** `"5min"`
- **Options:** `"5min"` or `"1hour"`
- **Description:** Cache time-to-live duration

**Choosing TTL:**

**5 minutes** (`"5min"`):
- ✅ Quick conversations (< 5 min)
- ✅ Rapidly evolving context
- ✅ Lower risk of stale cache

**1 hour** (`"1hour"`):
- ✅ Extended sessions (> 5 min)
- ✅ Stable system prompts
- ✅ Maximum cost savings
- ⚠️ Higher cost to write cache initially

---

#### `CACHE_SYSTEM_PROMPT`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Cache system prompt for reuse

**Keep enabled unless:**
- System prompt changes frequently
- Testing different prompts

---

#### `CACHE_USER_MESSAGES`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Cache previous user messages (2nd-to-last message)

**Keep enabled for:**
- Multi-turn conversations
- Consistent context across turns

---

### Web Search

#### `ENABLE_WEB_SEARCH`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable Anthropic web search capability

**Features when enabled:**
- Real-time web search
- Automatic query generation
- Citation chips with sources
- Collapsible search results

**Disable when:**
- Offline use required
- Cost-sensitive (small additional cost)
- Don't need current information

---

#### `WEB_SEARCH_MAX_USES`
- **Type:** Integer
- **Default:** `5`
- **Range:** 0 - 10
- **Description:** Maximum web searches per request

**Guidelines:**
```
1-2  - Simple fact-checking
3-5  - Standard research queries (default)
7-10 - Deep research, multiple topics
```

⚠️ **Cost:** Each search adds ~100 output tokens

---

#### `WEB_SEARCH_DOMAIN_ALLOWLIST`
- **Type:** String (comma-separated)
- **Default:** `""` (empty - no filtering)
- **Description:** Only search these domains

**Example:**
```
wikipedia.org,github.com,arxiv.org,stackoverflow.com
```

**Use cases:**
- Academic research (arxiv.org, scholar.google.com)
- Technical docs (github.com, stackoverflow.com)
- Trusted news (nytimes.com, reuters.com)

⚠️ **Cannot use with BLOCKLIST simultaneously!**

---

#### `WEB_SEARCH_DOMAIN_BLOCKLIST`
- **Type:** String (comma-separated)
- **Default:** `""` (empty - no filtering)
- **Description:** Never search these domains

**Example:**
```
spam-site.com,low-quality-content.com,ads-domain.com
```

**Use cases:**
- Block known misinformation sites
- Exclude paywalled content
- Filter out ad-heavy domains

⚠️ **Cannot use with ALLOWLIST simultaneously!**

---

### Skills & Code Execution

#### `ENABLE_CODE_EXECUTION`
- **Type:** Boolean
- **Default:** `false`
- **Description:** Enable Python code execution in sandbox

**Security:**
- ✅ Runs in secure sandbox
- ✅ No access to your filesystem
- ✅ Network isolated

**Enable for:**
- Data analysis
- Mathematical computations
- Chart generation
- File processing

⚠️ **Note:** Beta feature - may have limitations

---

#### `ENABLE_SKILL_XLSX`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable Excel file processing

**Capabilities:**
- Read/write .xlsx files
- Data analysis
- Chart creation
- Formula evaluation

---

#### `ENABLE_SKILL_PPTX`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable PowerPoint file generation

**Capabilities:**
- Create presentations
- Add slides, images, charts
- Format text and layouts

---

#### `ENABLE_SKILL_DOCX`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable Word document processing

**Capabilities:**
- Read/write .docx files
- Format text, tables
- Add images and headers

---

#### `ENABLE_SKILL_PDF`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable PDF generation

**Capabilities:**
- Generate PDF documents
- Convert from other formats
- Extract text from PDFs

---

#### `CUSTOM_SKILL_IDS`
- **Type:** String (comma-separated)
- **Default:** `""` (empty)
- **Description:** Your organization's custom skill IDs

**Example:**
```
data-analysis-v2,report-generator,chart-maker
```

**Requirements:**
- Must be valid skill IDs from your Anthropic organization
- No spaces between IDs
- Comma-separated list

---

### UX Settings

#### `SHOW_WEB_SEARCH_DETAILS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Show collapsible "Web Searches" section

**Enabled:** Shows queries and result counts
**Disabled:** Search happens silently, only citations shown

---

#### `SHOW_CITATIONS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Show citation chips at response bottom

**Enabled:** Clickable source chips appear
**Disabled:** No citation chips (sources still used internally)

---

#### `SHOW_TOKEN_USAGE`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Show token usage statistics

**Example output:**
```
Token Usage
- Input: 1,234 tokens
- Output: 2,345 tokens
- 💾 Cache Hit: 900 tokens (73% saved)
- Total: 3,579 tokens
```

---

#### `LOG_LEVEL`
- **Type:** String
- **Default:** `"DEBUG"`
- **Options:** `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`
- **Description:** Logging verbosity in Docker logs

**Levels:**
- `DEBUG` - Everything (development, troubleshooting)
- `INFO` - Important events (normal production)
- `WARNING` - Issues that don't break functionality
- `ERROR` - Only errors (minimal logging)

**View logs:**
```bash
docker logs -f open-webui | grep function_steroid
```

---

## User Valves (Per-User Settings)

Users can override some admin settings for their own use.

### `ENABLE_MY_WEB_SEARCH`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable web search for my queries

**Use case:** User wants to disable web search for privacy or speed

---

### `ENABLE_MY_CODE_EXECUTION`
- **Type:** Boolean
- **Default:** `false`
- **Description:** Enable code execution for my queries

**Use case:** User needs code execution while admin has it globally disabled

---

## Configuration Recipes

### Cost-Optimized Setup
```
THINKING_BUDGET_TOKENS: 2000
ENABLE_PROMPT_CACHING: true
CACHE_TTL: "1hour"
WEB_SEARCH_MAX_USES: 2
DEFAULT_MAX_TOKENS: 4096
```

**Best for:** High-volume, cost-sensitive applications

---

### Maximum Quality Setup
```
THINKING_BUDGET_TOKENS: 16000
ENABLE_EXTENDED_THINKING: true
ENABLE_PROMPT_CACHING: true
WEB_SEARCH_MAX_USES: 10
DEFAULT_MAX_TOKENS: 8192
DEFAULT_TEMPERATURE: 1.0
```

**Best for:** Research, analysis, creative tasks

---

### Fast Response Setup
```
THINKING_BUDGET_TOKENS: 2000
ENABLE_EXTENDED_THINKING: false
ENABLE_WEB_SEARCH: false
DEFAULT_MAX_TOKENS: 2048
```

**Best for:** Quick Q&A, code assistance

---

### Academic Research Setup
```
WEB_SEARCH_DOMAIN_ALLOWLIST: "arxiv.org,scholar.google.com,jstor.org,pubmed.gov"
WEB_SEARCH_MAX_USES: 10
THINKING_BUDGET_TOKENS: 10000
SHOW_CITATIONS: true
```

**Best for:** Academic research, fact-checking

---

## Next Steps

- **[Usage Examples](examples.md)** - See configurations in action
- **[Troubleshooting](troubleshooting.md)** - Fix configuration issues
- **[API Reference](../technical/api-reference.md)** - Quick valve lookup table

---

**Questions?** Open an [issue](https://github.com/[your-repo]/issues) with your configuration details.
