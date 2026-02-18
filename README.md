# Claude Sonnet 4.5 Complete for OpenWebUI

> **Production-ready Claude integration with extended thinking, web search, citations, skills, and prompt caching**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenWebUI](https://img.shields.io/badge/OpenWebUI-Compatible-green.svg)](https://github.com/open-webui/open-webui)

## ✨ Features

- **🧠 Extended Thinking** - Real-time reasoning with collapsible `<think>` tags, configurable budget (1K-16K tokens)
- **🔍 Web Search** - Powered by Anthropic's API with domain filtering and automatic query capture
- **💾 Prompt Caching** - Up to 90% cost savings with automatic cache breakpoints
- **📚 Citations** - Clickable citation chips from web search results
- **🛠️ Skills & Code** - Pre-built skills (Excel, PowerPoint, Word, PDF) + custom skill support
- **🖼️ Image Support** - Paste images directly into chat for multimodal interactions
- **🎨 Clean UX** - Collapsible sections, streaming responses, minimal design

## 🚀 Quick Start

### 1. Get API Key

Visit [console.anthropic.com](https://console.anthropic.com/) and generate an API key.

### 2. Install Function

1. Navigate to **Workspace → Functions** in OpenWebUI
2. Click **+ Add Function**
3. Copy the contents of [`src/steroid_v4-5.py`](src/steroid_v4-5.py)
4. Paste into the editor and click **Save**

### 3. Configure

1. Open function settings → **Valves** tab
2. Set `ANTHROPIC_API_KEY` to your API key
3. Click **Save**

### 4. Start Chatting

Select "Claude Sonnet 4.5 (Complete)" from the model dropdown. Extended thinking and web search are enabled by default!

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
| `ENABLE_EXTENDED_THINKING` | `true` | Enable reasoning display |
| `THINKING_BUDGET_TOKENS` | `10000` | Thinking token budget |
| `ENABLE_WEB_SEARCH` | `true` | Enable web search |
| `ENABLE_PROMPT_CACHING` | `true` | Enable caching (90% savings) |

See [Configuration Guide](docs/guides/configuration.md) for all valves.

## 🐛 Common Issues

**"ANTHROPIC_API_KEY is not configured"**
→ Set your API key in function settings → Valves tab

**Web search queries not showing**
→ Check Docker logs: `docker logs -f open-webui`

**Thinking not collapsing**
→ Ensure OpenWebUI is updated (requires `<think>` tag support)

See [Troubleshooting Guide](docs/guides/troubleshooting.md) for more.

## 📊 Cost Optimization

- **Prompt caching**: Up to 90% savings on multi-turn conversations
- **Thinking budget**: Reduce from 10K to 2K-5K for cost-sensitive apps
- **Cache TTL**: Use `1hour` for longer sessions

See [Examples Guide](docs/guides/examples.md) for detailed optimization strategies.

## 🔄 Version History

**v4.1.0** (Current) - Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) - [`src/steroid_v4-5.py`](src/steroid_v4-5.py)
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
