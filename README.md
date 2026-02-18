# Claude Opus 4.6 / Sonnet 4.6 Complete for OpenWebUI

> **Production-ready Claude integration with adaptive thinking, web search, web fetch, citations, skills, prompt caching, and fast mode (Opus)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenWebUI](https://img.shields.io/badge/OpenWebUI-Compatible-green.svg)](https://github.com/open-webui/open-webui)

## ✨ Features

- **🧠 Adaptive Thinking** - Always-on reasoning with collapsible `<think>` tags, effort-based depth control
- **🔍 Web Search** - Powered by Anthropic's API with domain filtering and automatic query capture
- **🌐 Web Fetch** - Full page reading for deep content analysis
- **⚡ Fast Mode** - 2.5x faster inference at 6x cost (Opus only)
- **💾 Prompt Caching** - Up to 90% cost savings with automatic cache breakpoints
- **📚 Citations** - Clickable citation chips from web search results
- **🗜️ Conversation Compaction** - Automatic context compression for long conversations
- **📦 Container Persistence** - Code execution containers persist across turns within a chat
- **💰 Cost Estimation** - Per-message cost estimates in token usage display
- **🛠️ Skills & Code** - Pre-built skills (Excel, PowerPoint, Word, PDF) + custom skill support
- **🖼️ Image Support** - Paste images directly into chat for multimodal interactions
- **🎨 Clean UX** - Collapsible sections, streaming responses, minimal design

## 🚀 Quick Start

### 1. Get API Key

Visit [console.anthropic.com](https://console.anthropic.com/) and generate an API key.

### 2. Install Function

1. Navigate to **Workspace → Functions** in OpenWebUI
2. Click **+ Add Function**
3. Copy the contents of [`src/opioid_v4-6.py`](src/opioid_v4-6.py) (Opus 4.6) or [`src/steroid_v4-6.py`](src/steroid_v4-6.py) (Sonnet 4.6) -- or [`src/steroid_v4-5.py`](src/steroid_v4-5.py) for Sonnet/Opus 4.5
4. Paste into the editor and click **Save**

### 3. Configure

1. Open function settings → **Valves** tab
2. Set `ANTHROPIC_API_KEY` to your API key
3. Click **Save**

### 4. Start Chatting

Select "Opioid - Opus 4.6 (Complete)" or "Steroid - Sonnet 4.6 (Complete)" from the model dropdown. Adaptive thinking and web search are enabled by default!

## 📖 Documentation

- **[Installation Guide](docs/guides/installation.md)** - Detailed setup instructions
- **[Configuration](docs/guides/configuration.md)** - All valves explained with examples
- **[Usage Examples](docs/guides/examples.md)** - Domain filtering, custom skills, cost optimization
- **[Troubleshooting](docs/guides/troubleshooting.md)** - Common issues and solutions
- **[Architecture](docs/technical/architecture.md)** - Technical deep-dive
- **[API Reference](docs/technical/api-reference.md)** - Quick valve lookup

## ⚙️ Configuration Quick Reference

### Essential Valves

| Valve | Default | Description |
|-------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Your API key |
| `EFFORT_LEVEL` | `high` (Opus) / `medium` (Sonnet) | Controls inference depth (`max` Opus only) |
| `ENABLE_FAST_MODE` | `false` | 2.5x faster inference at 6x cost (Opus only) |
| `ENABLE_WEB_SEARCH` | `true` | Enable web search |
| `ENABLE_PROMPT_CACHING` | `true` | Enable caching (90% savings) |

See [Configuration Guide](docs/guides/configuration.md) for all valves.

## 🐛 Common Issues

**"ANTHROPIC_API_KEY is not configured"**
→ Set your API key in function settings → Valves tab

**Web search queries not showing**
→ Check Docker logs: `docker logs -f open-webui`

**Thinking not collapsing**
→ Ensure OpenWebUI is updated (requires `<think>` tag support). Thinking is always-on in v5.0.0 (adaptive mode).

See [Troubleshooting Guide](docs/guides/troubleshooting.md) for more.

## 📊 Cost Optimization

- **Prompt caching**: Up to 90% savings on multi-turn conversations
- **Effort level**: Use `low` or `medium` for cost-sensitive apps (replaces thinking budget)
- **Fast mode** (Opus only): 2.5x faster but 6x cost -- use selectively for latency-critical tasks
- **Cache TTL**: Use `1hour` for longer sessions

See [Examples Guide](docs/guides/examples.md) for detailed optimization strategies.

## 🔄 Version History

**v5.0.0** (Current) - [`src/opioid_v4-6.py`](src/opioid_v4-6.py) (Opus 4.6) · [`src/steroid_v4-6.py`](src/steroid_v4-6.py) (Sonnet 4.6)
- ✅ Adaptive thinking (always-on, effort-based depth control)
- ✅ Web fetch (full page reading)
- ✅ Fast mode (Opus only, 2.5x faster inference)
- ✅ Conversation compaction for long contexts
- ✅ Container persistence across turns
- ✅ Cost estimation in token usage
- ✅ Async HTTP with aiohttp

**v4.1.0** - Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) - [`src/steroid_v4-5.py`](src/steroid_v4-5.py)
- ✅ `<think>` tags for collapsible reasoning
- ✅ Web search query accumulation fixed
- ✅ Clean UI without icons
- ✅ Citation chips working
- ✅ Image support (base64 and URL)

**v3.0.0** - [`archive/v3.0.0/function.py`](archive/v3.0.0/function.py)
- ❌ Deprecated (HTML rendering issues, query capture broken)

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## 🤝 Contributing

Found a bug? Want to add a feature?

1. Check [Issues](../../issues) for existing reports
2. Create detailed bug report with logs
3. Include OpenWebUI version and Docker setup
4. Share sanitized configuration (remove API keys!)

## 📚 Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [OpenWebUI Documentation](https://docs.openwebui.com/)
- [Prompt Caching Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Extended Thinking Overview](https://www.anthropic.com/news/extended-thinking)

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

**Questions?** Open an [issue](../../issues) or [discussion](../../discussions)!
