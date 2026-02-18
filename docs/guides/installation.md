# Installation Guide

> **Applies to:** Claude Sonnet 4.5 | `src/steroid_v4-5.py` (v4.1.0)

Step-by-step instructions for installing Claude Sonnet 4.5 Complete in OpenWebUI.

## Prerequisites

Before you begin, ensure you have:

- ✅ **OpenWebUI Instance** - Running via Docker or locally
  - Docker Desktop: [Download here](https://www.docker.com/products/docker-desktop/)
  - OpenWebUI: [Installation guide](https://docs.openwebui.com/)
- ✅ **Anthropic API Key** - From [console.anthropic.com](https://console.anthropic.com/)
- ✅ **Python 3.8+** - Required for OpenWebUI functions

## Step 1: Get Your Anthropic API Key

1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-...`)

⚠️ **Important:** Save this key securely. You won't be able to see it again!

## Step 2: Access OpenWebUI Functions

1. Open your OpenWebUI instance (typically `http://localhost:3000`)
2. Sign in to your account
3. Click your profile icon (top-right)
4. Select **Workspace** from the dropdown
5. Click **Functions** in the left sidebar

You should see the Functions management page.

## Step 3: Add the Function

### Option A: Copy-Paste (Recommended)

1. Click **+ Add Function** button (top-right)
2. Open [`src/steroid_v4-5.py`](../../src/steroid_v4-5.py) from this repository
3. Copy the entire contents (Cmd/Ctrl + A, then Cmd/Ctrl + C)
4. Paste into the OpenWebUI editor
5. Click **Save** (bottom-right)

### Option B: Import from URL

1. Click **+ Add Function** → **Import**
2. Enter the raw GitHub URL:
   ```
   https://raw.githubusercontent.com/[your-username]/steroid_sonnet/main/src/steroid_v4-5.py
   ```
3. Click **Import**
4. Click **Save**

## Step 4: Configure the Function

### 4.1 Set API Key

1. In the function editor, click the **⚙️ Settings** icon (top-right)
2. Click the **Valves** tab
3. Find `ANTHROPIC_API_KEY` field
4. Paste your API key from Step 1
5. Click **Save**

### 4.2 Optional: Adjust Settings

You can customize the function behavior now or later. Key settings:

| Setting | Default | When to Change |
|---------|---------|----------------|
| `ENABLE_EXTENDED_THINKING` | `true` | Disable if you don't want to see reasoning |
| `THINKING_BUDGET_TOKENS` | `10000` | Reduce for faster/cheaper responses |
| `ENABLE_WEB_SEARCH` | `true` | Disable for offline use |
| `ENABLE_PROMPT_CACHING` | `true` | Keep enabled for cost savings |

See [Configuration Guide](configuration.md) for all settings.

### 4.3 Enable the Function

1. Ensure the toggle at the top is **ON** (green)
2. Click **Save** one final time

## Step 5: Verify Installation

### 5.1 Select the Model

1. Go back to the main chat interface
2. Click the model selector dropdown (top-center)
3. Find **"Claude Sonnet 4.5 (Complete)"** in the list
4. Select it

### 5.2 Test with a Simple Query

Send a test message:
```
Hello! Can you verify that extended thinking is working?
```

**Expected result:**
- You should see a `Thinking...` section (clickable/collapsible)
- Followed by a response
- Token usage displayed at the bottom

### 5.3 Test Web Search

Send a query requiring current information:
```
What are the latest developments in AI this week?
```

**Expected result:**
- `Web Searches` section appears (collapsible)
- Citation chips at the bottom
- Response includes current information

## Troubleshooting Installation

### Function Not Appearing in Model Dropdown

**Possible causes:**
1. Function not saved properly
2. Function disabled (toggle is OFF)
3. Browser cache issue

**Solutions:**
1. Verify function is saved and enabled
2. Refresh browser (hard refresh: Cmd/Ctrl + Shift + R)
3. Check browser console for errors (F12 → Console tab)
4. Restart OpenWebUI container:
   ```bash
   docker restart open-webui
   ```

### "ANTHROPIC_API_KEY is not configured" Error

**Solution:**
1. Go to function settings → Valves
2. Verify API key is correctly pasted (no extra spaces)
3. Click Save
4. Refresh the chat page

### Function Crashes on First Message

**Check logs:**

**Docker Desktop:**
1. Open Docker Desktop app
2. Containers → `open-webui` → Logs tab

**Command line:**
```bash
docker logs --tail 100 open-webui
```

**Common issues:**
- Invalid API key → Check for typos
- Network issues → Verify internet connection
- Beta features not available → Check Anthropic account tier

### Web Search Not Working

**Symptoms:** No web searches happening, or errors

**Solutions:**
1. Check `ENABLE_WEB_SEARCH` valve is `true`
2. Check `ENABLE_MY_WEB_SEARCH` user valve is `true`
3. Clear domain filters if both allowlist AND blocklist are set
4. Check logs for API errors

See [Troubleshooting Guide](troubleshooting.md) for more issues.

## Next Steps

- **[Configuration Guide](configuration.md)** - Customize all settings
- **[Usage Examples](examples.md)** - Learn best practices
- **[Troubleshooting](troubleshooting.md)** - Fix common issues

## Updating to New Versions

When a new version is released:

1. Navigate to **Workspace → Functions**
2. Find "Claude Sonnet 4.5 (Complete)"
3. Click **Edit**
4. Copy new `src/steroid_v4-5.py` contents
5. Paste over existing code
6. Click **Save**

⚠️ **Note:** Your valve settings will be preserved!

## Uninstalling

To remove the function:

1. Navigate to **Workspace → Functions**
2. Find "Claude Sonnet 4.5 (Complete)"
3. Click the **Delete** icon (trash can)
4. Confirm deletion

---

**Need help?** Open an [issue](https://github.com/[your-repo]/issues) with:
- OpenWebUI version
- Docker setup details
- Error logs (sanitized - remove API keys!)
