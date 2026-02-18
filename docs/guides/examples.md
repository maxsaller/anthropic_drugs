# Usage Examples

> **Applies to:** Claude Sonnet 4.5 | `src/steroid_v4-5.py` (v4.1.0)

Real-world usage patterns, configuration examples, and cost optimization strategies.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Domain Filtering](#domain-filtering)
- [Custom Skills](#custom-skills)
- [Cost Optimization](#cost-optimization)
- [Advanced Patterns](#advanced-patterns)

---

## Basic Usage

### Simple Q&A (No Web Search)

**Configuration:**
```
ENABLE_EXTENDED_THINKING: true
ENABLE_WEB_SEARCH: false
THINKING_BUDGET_TOKENS: 2000
```

**Example query:**
```
Explain the difference between TCP and UDP protocols.
```

**Expected behavior:**
- Brief thinking section
- Direct, factual answer
- No web searches
- Fast response (~2-3 seconds)

**Cost estimate:** ~$0.01 per query

---

### Current Events Research

**Configuration:**
```
ENABLE_WEB_SEARCH: true
WEB_SEARCH_MAX_USES: 5
SHOW_WEB_SEARCH_DETAILS: true
SHOW_CITATIONS: true
```

**Example query:**
```
What are the latest developments in quantum computing this month?
```

**Expected behavior:**
- Multiple web searches
- Collapsible "Web Searches" section
- Citation chips at bottom
- Synthesized answer with sources

**Cost estimate:** ~$0.05-0.08 per query

---

### Deep Reasoning Task

**Configuration:**
```
ENABLE_EXTENDED_THINKING: true
THINKING_BUDGET_TOKENS: 16000
ENABLE_WEB_SEARCH: false
DEFAULT_MAX_TOKENS: 8192
```

**Example query:**
```
Analyze the ethical implications of AI in healthcare, considering
privacy, bias, and accessibility. Provide a nuanced perspective.
```

**Expected behavior:**
- Extensive thinking section (may use full 16K budget)
- Detailed, multi-perspective analysis
- Long-form response
- Slower response (~30-60 seconds)

**Cost estimate:** ~$0.30-0.40 per query

---

## Domain Filtering

### Academic Research

**Configuration:**
```
ENABLE_WEB_SEARCH: true
WEB_SEARCH_DOMAIN_ALLOWLIST: "arxiv.org,scholar.google.com,pubmed.ncbi.nlm.nih.gov,jstor.org"
WEB_SEARCH_MAX_USES: 10
SHOW_CITATIONS: true
```

**Use case:** Research assistant for academic papers

**Example query:**
```
Find recent papers on transformer architecture improvements
published in the last 6 months.
```

**Why it works:**
- Only searches academic sources
- Multiple searches for comprehensive coverage
- Citations link directly to papers

---

### Technical Documentation

**Configuration:**
```
WEB_SEARCH_DOMAIN_ALLOWLIST: "github.com,stackoverflow.com,docs.python.org,developer.mozilla.org"
WEB_SEARCH_MAX_USES: 5
```

**Use case:** Programming assistant

**Example query:**
```
How do I implement async/await in Python with error handling?
Show me examples from official docs.
```

**Why it works:**
- Searches official docs and trusted code sources
- Avoids low-quality tutorials
- Direct links to documentation

---

### News Aggregation

**Configuration:**
```
WEB_SEARCH_DOMAIN_ALLOWLIST: "reuters.com,apnews.com,bbc.com,nytimes.com"
WEB_SEARCH_MAX_USES: 7
```

**Use case:** News summary bot

**Example query:**
```
Summarize today's major technology news from trusted sources.
```

**Why it works:**
- Only searches reputable news outlets
- Multiple sources for balanced coverage
- Citations show which outlet reported what

---

### Blocking Domains

**Configuration:**
```
WEB_SEARCH_DOMAIN_BLOCKLIST: "pinterest.com,quora.com,medium.com"
WEB_SEARCH_MAX_USES: 5
```

**Use case:** Avoid low-quality or paywalled content

**Why blocklist:**
- Pinterest: Image aggregator, not original content
- Quora: Variable quality, often outdated
- Medium: Paywalled content, inconsistent quality

⚠️ **Note:** Cannot use both allowlist AND blocklist simultaneously!

---

## Custom Skills

### Excel Data Analysis

**Configuration:**
```
ENABLE_CODE_EXECUTION: true
ENABLE_SKILL_XLSX: true
```

**Example workflow:**
1. User uploads `sales_data.xlsx`
2. Query: "Analyze this sales data, calculate monthly trends, and create a summary chart"
3. Claude uses xlsx skill to:
   - Read spreadsheet
   - Perform calculations
   - Generate charts
   - Return insights

**Use case:** Automated reporting, data analysis

---

### Presentation Generation

**Configuration:**
```
ENABLE_CODE_EXECUTION: true
ENABLE_SKILL_PPTX: true
```

**Example query:**
```
Create a 10-slide presentation on "Introduction to Machine Learning"
with sections for supervised learning, unsupervised learning, and
real-world applications. Include charts where appropriate.
```

**Expected output:**
- PowerPoint file (.pptx)
- Structured content
- Visual elements

**Use case:** Quick presentation drafts, educational content

---

### Custom Organization Skills

**Configuration:**
```
ENABLE_CODE_EXECUTION: true
CUSTOM_SKILL_IDS: "company-data-analyzer,report-generator,chart-maker"
```

**Requirements:**
- Skills must be created in your Anthropic organization
- Valid skill IDs (comma-separated, no spaces)
- Proper permissions configured

**Example use case:**
```
Your company has a custom "quarterly-report-generator" skill that:
- Connects to internal databases
- Generates standardized reports
- Applies company branding
```

**Query:**
```
Generate Q4 2024 financial report using our template.
```

---

## Cost Optimization

### Understanding Claude Sonnet 4.5 Pricing

**Current rates for Claude Sonnet 4.5 (model ID: `claude-sonnet-4-5-20250929`)** (as of Nov 2024):
- Input: $3.00 per million tokens (MTok)
- Output: $15.00 per MTok
- Cache write: $3.75 per MTok
- Cache read: $0.30 per MTok (90% savings!)

---

### Strategy 1: Reduce Thinking Budget

**Scenario:** Processing 1000 queries/day

**Before:**
```
THINKING_BUDGET_TOKENS: 10000
Average thinking used: 8000 tokens
Cost per query: ~$0.12
Daily cost: $120
Monthly cost: $3,600
```

**After:**
```
THINKING_BUDGET_TOKENS: 5000
Average thinking used: 4000 tokens
Cost per query: ~$0.06
Daily cost: $60
Monthly cost: $1,800
```

**Savings: 50% ($1,800/month)**

**Trade-off:** Slightly less detailed reasoning, but often adequate for most queries.

---

### Strategy 2: Maximize Prompt Caching

**Scenario:** Customer support chatbot with stable system prompt

**Configuration:**
```
ENABLE_PROMPT_CACHING: true
CACHE_TTL: "1hour"
CACHE_SYSTEM_PROMPT: true
CACHE_USER_MESSAGES: true
```

**Typical conversation:**
```
System prompt: 2000 tokens (cached after first message)
Average query: 100 tokens
Average response: 500 tokens
```

**First message:**
- Input: 2000 (system) + 100 (user) = 2100 tokens × $3/MTok = $0.0063
- Output: 500 tokens × $15/MTok = $0.0075
- Total: $0.0138

**Subsequent messages (within 1 hour):**
- Cached: 2000 tokens × $0.30/MTok = $0.0006
- New input: 100 tokens × $3/MTok = $0.0003
- Output: 500 tokens × $15/MTok = $0.0075
- Total: $0.0084

**Savings per follow-up: 39%**

**10-turn conversation:**
- Without caching: $0.138
- With caching: $0.090
- **Savings: 35% ($0.048)**

---

### Strategy 3: Optimize Max Tokens

**Scenario:** Short-form Q&A application

**Before:**
```
DEFAULT_MAX_TOKENS: 8192
Average actual usage: 1200 tokens
Wasted budget: 6992 tokens
```

**After:**
```
DEFAULT_MAX_TOKENS: 2048
Average actual usage: 1200 tokens
Wasted budget: 848 tokens
```

**Benefits:**
- Faster responses (less generation time)
- Lower costs (don't pay for unused capacity)
- Prevents unexpectedly long responses

---

### Strategy 4: Selective Web Search

**Scenario:** Mixed workload (some queries need search, some don't)

**Poor approach:**
```
ENABLE_WEB_SEARCH: true (always on)
WEB_SEARCH_MAX_USES: 5
Result: Searches happen even when not needed
```

**Better approach:**

Use user valve for selective enablement:
```python
# User A (needs web search):
ENABLE_MY_WEB_SEARCH: true

# User B (doesn't need web search):
ENABLE_MY_WEB_SEARCH: false
```

Or disable globally and enable only when needed:
```
Admin: ENABLE_WEB_SEARCH: false
User (when needed): ENABLE_MY_WEB_SEARCH: true
```

**Savings:** ~20-30% on queries that don't need search

---

### Strategy 5: Batch Similar Queries

**Scenario:** Processing customer feedback

**Poor approach:**
```
Query 1: "Analyze feedback #1"
Query 2: "Analyze feedback #2"
...
Each query: Fresh system prompt (no caching benefit)
```

**Better approach:**
```
Single query: "Analyze these 10 customer feedback items:
1. [feedback 1]
2. [feedback 2]
...
10. [feedback 10]

Provide a structured analysis for each."
```

**Benefits:**
- 1 system prompt instead of 10
- Caching works across all items
- ~60-70% cost reduction

---

### Cost Optimization Summary

| Strategy | Effort | Savings | Trade-off |
|----------|--------|---------|-----------|
| Reduce thinking budget | Low | 30-50% | Slightly less detailed reasoning |
| Enable caching | Low | 35-90% | None (keep system prompt stable) |
| Optimize max tokens | Low | 10-20% | May truncate long responses |
| Selective web search | Medium | 20-30% | Need per-user config |
| Batch queries | High | 60-70% | Requires code changes |

**Best quick wins:**
1. Enable prompt caching (`ENABLE_PROMPT_CACHING: true`)
2. Set cache TTL to 1 hour (`CACHE_TTL: "1hour"`)
3. Reduce thinking budget to 5000 (`THINKING_BUDGET_TOKENS: 5000`)

**Expected combined savings: 50-70%**

---

## Advanced Patterns

### Multi-Turn Conversation Optimization

**Pattern:** Conversational AI with context

**Configuration:**
```
ENABLE_PROMPT_CACHING: true
CACHE_TTL: "1hour"
CACHE_USER_MESSAGES: true
THINKING_BUDGET_TOKENS: 5000
```

**Implementation:**
1. First message: Establish context (cached)
2. Follow-ups: Reference cached context
3. Stay within 1-hour window for max savings

**Example:**
```
Turn 1: "I'm working on a Python web app using Flask.
         I need help with authentication."

Turn 2: "How do I implement password hashing?"
         (references cached context about Flask)

Turn 3: "What about session management?"
         (continues to benefit from cache)
```

---

### Research Assistant Pattern

**Pattern:** Deep research with quality sources

**Configuration:**
```
WEB_SEARCH_DOMAIN_ALLOWLIST: "arxiv.org,scholar.google.com,pubmed.gov"
WEB_SEARCH_MAX_USES: 10
THINKING_BUDGET_TOKENS: 10000
SHOW_CITATIONS: true
DEFAULT_TEMPERATURE: 0.5
```

**Query structure:**
```
"Research [topic] published in the last [timeframe].
Focus on [specific aspect].
Provide a summary with key findings and cite sources."
```

---

### Code Assistant Pattern

**Pattern:** Programming help with official docs

**Configuration:**
```
WEB_SEARCH_DOMAIN_ALLOWLIST: "github.com,stackoverflow.com,docs.python.org"
WEB_SEARCH_MAX_USES: 3
THINKING_BUDGET_TOKENS: 5000
ENABLE_CODE_EXECUTION: false
DEFAULT_TEMPERATURE: 0.0
```

**Why these settings:**
- Low temperature for consistent code
- Limited searches (3 is usually enough)
- Moderate thinking budget
- Code execution disabled (security)

---

## Next Steps

- **[Configuration Guide](configuration.md)** - Detailed valve reference
- **[Troubleshooting](troubleshooting.md)** - Fix issues
- **[Architecture](../technical/architecture.md)** - Understand how it works

---

**Questions?** Share your use case in [Discussions](https://github.com/[your-repo]/discussions)!
