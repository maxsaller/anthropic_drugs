# API Reference

> **Applies to:** Claude Sonnet 4.5 | `src/steroid_v4-5.py` (v4.1.0)

Quick reference for all configuration valves.

## Admin Valves

### API & Core

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `ANTHROPIC_API_KEY` | string | `""` | - | **Required.** Your Anthropic API key |
| `DEFAULT_MAX_TOKENS` | int | `8192` | 1-8192 | Maximum response tokens |
| `DEFAULT_TEMPERATURE` | float | `1.0` | 0.0-1.0 | Response randomness (0=deterministic, 1=creative) |
| `REQUEST_TIMEOUT` | int | `300` | 60-600 | API request timeout (seconds) |

### Extended Thinking

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `ENABLE_EXTENDED_THINKING` | bool | `true` | true/false | Enable reasoning display |
| `THINKING_BUDGET_TOKENS` | int | `10000` | 1024-16000 | Max thinking tokens (higher=better quality) |

### Prompt Caching

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `ENABLE_PROMPT_CACHING` | bool | `true` | true/false | Enable caching (up to 90% savings) |
| `CACHE_TTL` | string | `"5min"` | `"5min"`, `"1hour"` | Cache duration |
| `CACHE_SYSTEM_PROMPT` | bool | `true` | true/false | Cache system prompt |
| `CACHE_USER_MESSAGES` | bool | `true` | true/false | Cache 2nd-to-last user message |

### Web Search

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `ENABLE_WEB_SEARCH` | bool | `true` | true/false | Enable web search capability |
| `WEB_SEARCH_MAX_USES` | int | `5` | 0-10 | Max searches per request |
| `WEB_SEARCH_DOMAIN_ALLOWLIST` | string | `""` | comma-separated | Only search these domains |
| `WEB_SEARCH_DOMAIN_BLOCKLIST` | string | `""` | comma-separated | Never search these domains |

⚠️ **Note:** Cannot use both allowlist and blocklist simultaneously!

### Skills & Code Execution

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `ENABLE_CODE_EXECUTION` | bool | `false` | true/false | Enable Python code execution |
| `ENABLE_SKILL_XLSX` | bool | `true` | true/false | Enable Excel processing |
| `ENABLE_SKILL_PPTX` | bool | `true` | true/false | Enable PowerPoint generation |
| `ENABLE_SKILL_DOCX` | bool | `true` | true/false | Enable Word processing |
| `ENABLE_SKILL_PDF` | bool | `true` | true/false | Enable PDF generation |
| `CUSTOM_SKILL_IDS` | string | `""` | comma-separated | Organization custom skill IDs |

### UX Settings

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `SHOW_WEB_SEARCH_DETAILS` | bool | `true` | true/false | Show collapsible search results section |
| `SHOW_CITATIONS` | bool | `true` | true/false | Show citation chips at bottom |
| `SHOW_TOKEN_USAGE` | bool | `true` | true/false | Show token usage statistics |

### Logging

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `LOG_LEVEL` | string | `"DEBUG"` | DEBUG, INFO, WARNING, ERROR | Logging verbosity in Docker logs |

---

## User Valves

| Valve | Type | Default | Range/Options | Description |
|-------|------|---------|---------------|-------------|
| `ENABLE_MY_WEB_SEARCH` | bool | `true` | true/false | Enable web search for my queries |
| `ENABLE_MY_CODE_EXECUTION` | bool | `false` | true/false | Enable code execution for my queries |

---

## Quick Configuration Recipes

### Cost-Optimized
```yaml
THINKING_BUDGET_TOKENS: 2000
ENABLE_PROMPT_CACHING: true
CACHE_TTL: "1hour"
WEB_SEARCH_MAX_USES: 2
DEFAULT_MAX_TOKENS: 4096
```

### Maximum Quality
```yaml
THINKING_BUDGET_TOKENS: 16000
ENABLE_EXTENDED_THINKING: true
WEB_SEARCH_MAX_USES: 10
DEFAULT_MAX_TOKENS: 8192
DEFAULT_TEMPERATURE: 1.0
```

### Fast Response
```yaml
THINKING_BUDGET_TOKENS: 2000
ENABLE_EXTENDED_THINKING: false
ENABLE_WEB_SEARCH: false
DEFAULT_MAX_TOKENS: 2048
```

### Academic Research
```yaml
WEB_SEARCH_DOMAIN_ALLOWLIST: "arxiv.org,scholar.google.com,jstor.org"
WEB_SEARCH_MAX_USES: 10
THINKING_BUDGET_TOKENS: 10000
SHOW_CITATIONS: true
```

---

## Model

This function targets **Claude Sonnet 4.5** with model ID `claude-sonnet-4-5-20250929` (defined in `src/steroid_v4-5.py`).

---

## Feature Dependencies

### Extended Thinking
**Requires:**
- `ENABLE_EXTENDED_THINKING: true`

**Affected by:**
- `THINKING_BUDGET_TOKENS` (quality/cost)

**Beta header (Sonnet 4.5):** `interleaved-thinking-2025-05-14`

---

### Web Search
**Requires:**
- `ENABLE_WEB_SEARCH: true` (admin)
- `ENABLE_MY_WEB_SEARCH: true` (user)

**Optional:**
- `WEB_SEARCH_DOMAIN_ALLOWLIST` OR `WEB_SEARCH_DOMAIN_BLOCKLIST` (not both)
- `WEB_SEARCH_MAX_USES`

**Beta header (Sonnet 4.5):** `web-search-2025-03-05`

---

### Prompt Caching
**Requires:**
- `ENABLE_PROMPT_CACHING: true`

**Affected by:**
- `CACHE_TTL` (duration)
- `CACHE_SYSTEM_PROMPT` (cache system prompt)
- `CACHE_USER_MESSAGES` (cache previous messages)

**Beta header (Sonnet 4.5):** `prompt-caching-2024-07-31`

---

### Code Execution & Skills
**Requires:**
- `ENABLE_CODE_EXECUTION: true` (admin)
- `ENABLE_MY_CODE_EXECUTION: true` (user)

**Individual skills:**
- `ENABLE_SKILL_XLSX` (Excel)
- `ENABLE_SKILL_PPTX` (PowerPoint)
- `ENABLE_SKILL_DOCX` (Word)
- `ENABLE_SKILL_PDF` (PDF)
- `CUSTOM_SKILL_IDS` (custom skills)

**Beta headers (Sonnet 4.5):**
- `code-execution-2025-08-25`
- `skills-2025-10-02`
- `files-api-2025-04-14`

---

## Token Budget Guidelines

| Budget | Use Case | Quality | Cost/Request | Speed |
|--------|----------|---------|--------------|-------|
| 1024-2000 | Simple Q&A | ⭐⭐ | $0.02-0.03 | Fast |
| 2000-5000 | Standard queries | ⭐⭐⭐ | $0.03-0.08 | Medium |
| 5000-10000 | Complex reasoning | ⭐⭐⭐⭐ | $0.08-0.15 | Slow |
| 10000-16000 | Maximum quality | ⭐⭐⭐⭐⭐ | $0.15-0.24 | Very slow |

**Note:** Costs assume 50% actual thinking usage. Actual costs may vary.

---

## Cost Estimates (per 1000 queries)

### Scenario 1: Basic Q&A
```yaml
THINKING_BUDGET_TOKENS: 2000
ENABLE_WEB_SEARCH: false
Avg thinking used: 1000 tokens
Avg output: 500 tokens
Cost per query: ~$0.025
Cost per 1000 queries: ~$25
```

### Scenario 2: Web Search
```yaml
THINKING_BUDGET_TOKENS: 5000
ENABLE_WEB_SEARCH: true
WEB_SEARCH_MAX_USES: 3
Avg thinking: 3000 tokens
Avg output: 1000 tokens
Cost per query: ~$0.065
Cost per 1000 queries: ~$65
```

### Scenario 3: Deep Reasoning
```yaml
THINKING_BUDGET_TOKENS: 16000
ENABLE_WEB_SEARCH: false
Avg thinking: 12000 tokens
Avg output: 2000 tokens
Cost per query: ~$0.21
Cost per 1000 queries: ~$210
```

### Scenario 4: With Caching (90% hit rate)
```yaml
Same as Scenario 2, but:
ENABLE_PROMPT_CACHING: true
CACHE_TTL: "1hour"
Cost per query: ~$0.025 (62% savings)
Cost per 1000 queries: ~$25
```

---

## Related Documentation

- **[Configuration Guide](../guides/configuration.md)** - Detailed valve explanations
- **[Usage Examples](../guides/examples.md)** - Configuration recipes in action
- **[Architecture](architecture.md)** - How features work internally

---

**Questions?** See [Troubleshooting](../guides/troubleshooting.md) or open an [issue](https://github.com/[your-repo]/issues).
