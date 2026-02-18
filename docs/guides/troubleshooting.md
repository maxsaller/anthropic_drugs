# Troubleshooting Guide

> **Applies to:** Claude Sonnet 4.5 | `src/steroid_v4-5.py` (v4.1.0)

## Common Issues and Solutions

### Installation & Setup

#### Issue: "ANTHROPIC_API_KEY is not configured"

**Symptoms:**
- Error message on first use
- Function refuses to run

**Solution:**
1. Navigate to **Workspace → Functions**
2. Find "Claude Sonnet 4.5 (Complete)"
3. Click the gear icon (settings)
4. Go to **Valves** tab
5. Enter your API key in `ANTHROPIC_API_KEY`
6. Click **Save**

**Verification:**
- Send a test message
- Should see "Connecting to Claude..." status

---

#### Issue: Function not appearing in model dropdown

**Symptoms:**
- Can't select the model
- Not listed in available models

**Solution:**
1. Check function is saved and enabled
2. Refresh browser (hard refresh: Cmd/Ctrl + Shift + R)
3. Check browser console for JavaScript errors
4. Verify function has `self.type = "manifold"`

---

### Extended Thinking

#### Issue: Thinking shown as raw text instead of collapsible

**Symptoms:**
```
The user is asking about...
My knowledge cutoff is...
Let me search for information...
```

**Root Cause:**
`<think>` tags not being output correctly

**Solution v4:**
This was fixed in v4! The issue was:
- Setting `thinking_state = IN_PROGRESS` in `content_block_start`
- Then checking `if state == NOT_STARTED` in `thinking_delta`
- Result: Never output opening tag!

**Fix:** Don't change state in `content_block_start`, let first `thinking_delta` handle it.

**Verification in logs:**
```
Thinking content block started
input_json_delta received, fragment: {"
✅ Successfully parsed accumulated JSON
```

---

#### Issue: Thinking takes too long / too expensive

**Symptoms:**
- Responses very slow
- High token costs
- Long thinking sections

**Solution:**
Reduce thinking budget:
```python
THINKING_BUDGET_TOKENS: 2000  # Instead of 10000
```

**Trade-offs:**
- Lower budget = faster, cheaper, potentially lower quality
- Higher budget = slower, expensive, better reasoning

**Recommended budgets:**
- Simple queries: 2000-5000
- Complex reasoning: 5000-10000
- Maximum quality: 10000-16000

---

### Web Search

#### Issue: Web search queries not captured

**Symptoms:**
- Web Searches section shows: `Search 1: (query not captured)`
- Logs show empty queries

**Root Cause:**
Query comes in streaming `input_json_delta` events as **character fragments**:
```
Fragment 1: "{"
Fragment 2: "query": "go"
Fragment 3: "vernment shu"
Fragment 4: "tdown 202"
Fragment 5: "5"}"
```

**Solution v4:**
Accumulate fragments in buffer until valid JSON:

```python
state.current_search.partial_json_buffer += partial_json
parsed = json.loads(state.current_search.partial_json_buffer)
query = parsed["query"]
```

**Verification in logs:**
```
input_json_delta received, fragment: {"
input_json_delta received, fragment: query": "go"
✅ Successfully parsed accumulated JSON: {'query': 'government shutdown 2025'}
✅ Extracted search query: 'government shutdown 2025'
```

---

#### Issue: Web search disabled/not working

**Symptoms:**
- No web searches happening
- "Search failed" messages

**Solutions:**

**1. Check admin valve:**
```python
ENABLE_WEB_SEARCH: true
```

**2. Check user valve:**
```python
ENABLE_MY_WEB_SEARCH: true
```

**3. Check domain filters:**
- Can't use BOTH allowlist AND blocklist
- Remove one or both

**4. Check beta headers:**
Logs should show:
```
Beta headers (Sonnet 4.5): ...,web-search-2025-03-05,...
```

---

#### Issue: "Error: Cannot use both allowed_domains and blocked_domains"

**Symptoms:**
- Error on first message
- Web search fails

**Solution:**
Clear one of these valves:
```python
WEB_SEARCH_DOMAIN_ALLOWLIST: ""  # Empty
WEB_SEARCH_DOMAIN_BLOCKLIST: ""  # Empty
```

Use only ONE:
- Allowlist: "wikipedia.org,github.com"
- OR Blocklist: "spam.com,ads.com"

---

### Citations

#### Issue: No citations appearing

**Symptoms:**
- No citation chips at bottom
- Web search results visible but not cited

**Understanding Citation Types:**

**1. Formal API Citations** (documents only)
- Requires uploaded files
- `citations.enabled=true` on documents
- Includes `start_char_index`, `end_char_index`
- NOT supported for web search currently

**2. Web Search Citations** (fallback)
- From web search results
- No character positions
- Shows as clickable chips
- Uses `title`, `url`, `page_age`

**Solution:**

**For web search:**
Logs should show:
```
No formal citations, emitting web search results as citation chips
Emitted X citation events
```

**For documents:**
- Upload PDF/text files
- Enable citations in request
- Check logs for "Found X citations"

---

#### Issue: Citations show but no inline `[1]` markers

**Status:**
This is **expected behavior** for web search!

**Why:**
- Web search citations don't include character positions
- Can't insert markers without positions
- Document citations (coming soon) will support this

**Current behavior:**
- Citation chips at bottom
- Clickable sources
- No inline markers (by design)

---

### Prompt Caching

#### Issue: High costs despite caching enabled

**Symptoms:**
- Cache hit rate low
- `cache_read_input_tokens: 0`

**Common causes:**

**1. Cache misses**
- Changing system prompts
- Different user messages
- Cache expired (5min/1hour TTL)

**2. New conversations**
- First message never cached
- Need 2+ messages for user message cache

**3. Cache disabled**
```python
ENABLE_PROMPT_CACHING: false  # Check this!
```

**Verification in logs:**
```
Applied 2 cache breakpoints
```

**In response:**
```
Token Usage
- 💾 Cache Hit: 5,000 tokens (83% saved)
```

---

#### Issue: Cache not working with tools

**Symptoms:**
- Tools enabled
- No cache hits

**Root cause:**
Cache breakpoints must be carefully placed around tool definitions.

**Solution:**
The function handles this automatically! If still issues:
1. Check logs for "Applied X cache breakpoints"
2. Verify beta headers include "prompt-caching-2024-07-31"
3. Try disabling tools to isolate issue

---

### Code Execution & Skills

#### Issue: Skills not working

**Symptoms:**
- Code execution requested but doesn't run
- Skills not available

**Solutions:**

**1. Check admin valve:**
```python
ENABLE_CODE_EXECUTION: true
```

**2. Check user valve:**
```python
ENABLE_MY_CODE_EXECUTION: true
```

**3. Check skill enables:**
```python
ENABLE_SKILL_XLSX: true
ENABLE_SKILL_PPTX: true
ENABLE_SKILL_DOCX: true
ENABLE_SKILL_PDF: true
```

**4. Check beta headers:**
Logs should show:
```
Beta headers (Sonnet 4.5): ...,code-execution-2025-08-25,skills-2025-10-02,files-api-2025-04-14,...
```

---

#### Issue: Custom skills not loading

**Symptoms:**
- Organization skills not available
- Custom skill IDs ignored

**Solution:**
Format custom skills correctly:
```python
CUSTOM_SKILL_IDS: "my-skill-1,data-analysis,report-gen"
```

**Requirements:**
- Comma-separated
- No spaces
- Valid skill IDs from your org

**Verification in logs:**
```
Skills configured: ['xlsx', 'pptx', 'my-skill-1', 'data-analysis']
```

---

### Performance

#### Issue: Slow responses

**Symptoms:**
- Long wait times
- Timeouts

**Common causes & solutions:**

**1. High thinking budget**
```python
THINKING_BUDGET_TOKENS: 5000  # Reduce from 10000
```

**2. Multiple web searches**
```python
WEB_SEARCH_MAX_USES: 3  # Reduce from 5
```

**3. Long context**
- Shorter system prompts
- Fewer messages in conversation
- Enable prompt caching

**4. Request timeout**
```python
REQUEST_TIMEOUT: 600  # Increase from 300
```

---

#### Issue: "Request timed out"

**Symptoms:**
```
⏱️ Request timed out. Partial response may be shown above.
```

**Solutions:**

**1. Increase timeout:**
```python
REQUEST_TIMEOUT: 600  # 10 minutes
```

**2. Reduce complexity:**
- Lower thinking budget
- Fewer web searches
- Shorter prompts

**3. Check internet connection:**
- Docker container networking
- Firewall settings
- Anthropic API status

---

### Logging & Debugging

#### Issue: Can't find logs

**Docker Desktop:**
1. Open Docker Desktop app
2. Containers tab (left sidebar)
3. Click on `open-webui` container
4. Click **Logs** tab at top
5. Logs stream in real-time!

**Command line:**
```bash
# Show last 100 lines
docker logs --tail 100 open-webui

# Follow logs in real-time
docker logs -f open-webui

# Search for specific function
docker logs open-webui | grep "function_steroid_4_5"
```

---

#### Issue: Too much logging / not enough

**Too much:**
```python
LOG_LEVEL: "WARNING"  # Or "ERROR"
```

**Too little:**
```python
LOG_LEVEL: "DEBUG"  # Or "INFO"
```

**Recommended:**
- Development: `DEBUG`
- Production: `INFO` or `WARNING`

---

### API Errors

#### Issue: "Authentication failed"

**Symptoms:**
```
❌ Authentication failed. Check your API key.
```

**Solutions:**
1. Verify API key is correct (no extra spaces)
2. Check key hasn't been revoked
3. Visit https://console.anthropic.com/
4. Generate new key if needed

---

#### Issue: "Rate limit exceeded"

**Symptoms:**
```
⚠️ Rate limit exceeded. Please wait and try again.
```

**Solutions:**
1. Wait a few minutes
2. Check your Anthropic tier limits
3. Reduce concurrent requests
4. Consider upgrading API tier

---

#### Issue: "Bad request" with error details

**Symptoms:**
```
❌ Bad request: [detailed error message]
```

**Common causes:**

**1. Invalid beta headers:**
- Check enabled features
- Verify beta header combinations

**2. Invalid parameters:**
- Check thinking budget (1024-16000)
- Verify temperature (0.0-1.0)
- Check max_tokens (≤8192)

**3. Conflicting settings:**
- Both domain allowlist AND blocklist
- Invalid skill IDs
- Malformed requests

**Solution:**
Read error message carefully, it usually indicates the exact issue!

---

## 🔍 Debug Checklist

When something doesn't work:

**1. Check valves:**
- [ ] ANTHROPIC_API_KEY is set
- [ ] Feature is enabled (admin valve)
- [ ] Feature is enabled (user valve)
- [ ] No conflicting settings

**2. Check logs:**
- [ ] Found relevant log lines
- [ ] No error messages
- [ ] Beta headers correct
- [ ] Events processing correctly

**3. Check OpenWebUI:**
- [ ] Function saved and enabled
- [ ] Model selected in dropdown
- [ ] Browser cache cleared
- [ ] No JavaScript errors

**4. Test isolation:**
- [ ] Disable all features
- [ ] Enable one at a time
- [ ] Identify which feature fails

---

## 📞 Getting Help

**Still stuck?**

1. **Gather information:**
   - OpenWebUI version
   - Docker setup (Docker Desktop/CLI)
   - Function version (v3/v4)
   - Relevant log excerpts (sanitized!)
   - Steps to reproduce

2. **Check existing issues:**
   - Search GitHub issues
   - Look for similar problems
   - Check if already reported

3. **Create detailed issue:**
   - Clear title
   - Step-by-step reproduction
   - Expected vs actual behavior
   - Logs and screenshots
   - Configuration (remove API key!)

4. **Community resources:**
   - OpenWebUI Discord
   - Anthropic Discord
   - GitHub Discussions

---

**Remember:** Most issues are configuration-related! Double-check valves and logs before diving deeper.
