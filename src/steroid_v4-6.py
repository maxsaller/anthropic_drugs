"""
title: Claude Opus 4.6 Complete v5.0
author: Enhanced by AI
version: 5.0.0
license: MIT
description: Production-ready Claude Opus 4.6 with adaptive thinking, web search, web fetch, code execution, skills, compaction, fast mode, and clean UX
requirements: aiohttp, pydantic
"""

import os
import json
import logging
import asyncio
import aiohttp
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Set
from pydantic import BaseModel, Field
from open_webui.utils.misc import pop_system_message

# Configure logging
logger = logging.getLogger(__name__)


# ==================== ENUMS & DATA CLASSES ====================


class ThinkingState(Enum):
    """Thinking process states"""
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2


@dataclass
class CitationData:
    """Structured citation information"""
    url: str
    title: str
    cited_text: str = ""
    encrypted_index: str = ""


@dataclass
class WebSearchResult:
    """Web search result data"""
    query: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    partial_json_buffer: str = ""  # Accumulate partial JSON fragments


@dataclass
class StreamingState:
    """State management for streaming responses"""
    thinking_state: ThinkingState = ThinkingState.NOT_STARTED
    thinking_buffer: str = ""
    response_buffer: str = ""
    web_searches: List[WebSearchResult] = field(default_factory=list)
    citations: List[CitationData] = field(default_factory=list)
    seen_citation_urls: Set[str] = field(default_factory=set)
    current_block_index: int = 0
    current_block_type: Optional[str] = None
    current_search: Optional[WebSearchResult] = None
    current_search_results: List[Dict[str, Any]] = field(default_factory=list)
    container_id: Optional[str] = None


# ==================== MAIN PIPE CLASS ====================


class Pipe:
    """Claude Opus 4.6 Complete Integration for OpenWebUI"""

    class Valves(BaseModel):
        """Admin-configurable settings"""

        # API & Core Settings
        ANTHROPIC_API_KEY: str = Field(
            default="",
            description="Your Anthropic API key"
        )
        DEFAULT_MAX_TOKENS: int = Field(
            default=16384,
            description="Default maximum tokens for responses (max 128000)"
        )
        DEFAULT_TEMPERATURE: float = Field(
            default=1.0,
            description="Default temperature (0.0-1.0)"
        )
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="API request timeout in seconds"
        )

        # Prompt Caching
        ENABLE_PROMPT_CACHING: bool = Field(
            default=True,
            description="Enable prompt caching (reduces cost up to 90%)"
        )
        CACHE_TTL: Literal["5min", "1hour"] = Field(
            default="5min",
            description="Cache duration: 5min (cheaper) or 1hour (longer sessions)"
        )
        CACHE_SYSTEM_PROMPT: bool = Field(
            default=True,
            description="Automatically cache system prompts"
        )
        CACHE_USER_MESSAGES: bool = Field(
            default=True,
            description="Cache recent user messages for stable cache points"
        )

        # Web Search
        ENABLE_WEB_SEARCH: bool = Field(
            default=True,
            description="Enable web search capability"
        )
        WEB_SEARCH_MAX_USES: int = Field(
            default=5,
            description="Maximum web searches per request (1-20)"
        )
        WEB_SEARCH_DOMAIN_ALLOWLIST: str = Field(
            default="",
            description="Allowed domains (comma-separated, e.g., 'wikipedia.org,github.com')"
        )
        WEB_SEARCH_DOMAIN_BLOCKLIST: str = Field(
            default="",
            description="Blocked domains (comma-separated)"
        )

        # Code Execution & Skills
        ENABLE_CODE_EXECUTION: bool = Field(
            default=False,
            description="Enable Python code execution (required for skills)"
        )
        ENABLE_SKILL_XLSX: bool = Field(
            default=True,
            description="Enable Excel spreadsheet support"
        )
        ENABLE_SKILL_PPTX: bool = Field(
            default=True,
            description="Enable PowerPoint support"
        )
        ENABLE_SKILL_DOCX: bool = Field(
            default=True,
            description="Enable Word document support"
        )
        ENABLE_SKILL_PDF: bool = Field(
            default=True,
            description="Enable PDF generation support"
        )
        CUSTOM_SKILL_IDS: str = Field(
            default="",
            description="Comma-separated custom skill IDs from your organization"
        )

        # Opus 4.6 Features
        EFFORT_LEVEL: Literal["low", "medium", "high", "max"] = Field(
            default="high",
            description="Inference effort level: low (fast/cheap), medium, high (default), max (Opus 4.6 only, most capable)"
        )
        ENABLE_WEB_FETCH: bool = Field(
            default=True,
            description="Enable web fetch for reading full page content"
        )
        WEB_FETCH_MAX_USES: int = Field(
            default=10,
            description="Maximum web page fetches per request (1-50)"
        )
        ENABLE_FAST_MODE: bool = Field(
            default=False,
            description="Enable fast mode: 2.5x faster inference at 6x cost"
        )
        ENABLE_COMPACTION: bool = Field(
            default=True,
            description="Enable automatic conversation compaction for long contexts"
        )
        COMPACTION_TRIGGER_TOKENS: int = Field(
            default=100000,
            description="Token threshold to trigger conversation compaction (min 50000)"
        )
        SHOW_COST_ESTIMATE: bool = Field(
            default=True,
            description="Show estimated cost in token usage section"
        )

        # UX Settings
        SHOW_WEB_SEARCH_DETAILS: bool = Field(
            default=True,
            description="Show web search results in collapsible section"
        )
        SHOW_CITATIONS: bool = Field(
            default=True,
            description="Show citation chips"
        )
        SHOW_TOKEN_USAGE: bool = Field(
            default=True,
            description="Display token usage statistics"
        )

        # Logging
        LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
            default="DEBUG",
            description="Logging verbosity level"
        )

    class UserValves(BaseModel):
        """Per-user configurable settings"""

        ENABLE_MY_WEB_SEARCH: bool = Field(
            default=True,
            description="Enable web search for my queries"
        )
        ENABLE_MY_CODE_EXECUTION: bool = Field(
            default=False,
            description="Enable code execution for my queries"
        )
        MY_EFFORT_LEVEL: Optional[Literal["low", "medium", "high", "max"]] = Field(
            default=None,
            description="Override effort level (None = use admin default)"
        )
        ENABLE_MY_FAST_MODE: Optional[bool] = Field(
            default=None,
            description="Override fast mode (None = use admin default)"
        )

    API_VERSION = "2023-06-01"
    API_BASE_URL = "https://api.anthropic.com/v1"
    MODEL_ID = "claude-opus-4-6"
    MAX_OUTPUT_TOKENS = 128_000

    def __init__(self):
        self.type = "manifold"
        self.id = "claude_complete_v5"
        self.name = "claude/"
        self.citation = False  # CRITICAL: Disable OpenWebUI auto-citations

        self.valves = self.Valves(
            ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", "")
        )
        self.user_valves = self.UserValves()
        self._containers = {}  # chat_id -> container_id for code execution persistence

        # Set logging level
        log_level = getattr(logging, self.valves.LOG_LEVEL)
        logger.setLevel(log_level)

        logger.info("Claude Opus 4.6 Complete v5.0.0 initialized")

    def pipes(self) -> List[Dict[str, str]]:
        """Return available model configurations"""
        return [
            {
                "id": "claude-opus-4.6-complete",
                "name": "Claude Opus 4.6 (Complete)"
            }
        ]

    # ==================== HELPER METHODS ====================

    def _should_enable_code_execution(self, user_valves) -> bool:
        """Check if code execution should be enabled"""
        if not user_valves.ENABLE_MY_CODE_EXECUTION:
            return False

        if not self.valves.ENABLE_CODE_EXECUTION:
            return False

        # Check if any skills are enabled
        has_skills = (
            self.valves.ENABLE_SKILL_XLSX or
            self.valves.ENABLE_SKILL_PPTX or
            self.valves.ENABLE_SKILL_DOCX or
            self.valves.ENABLE_SKILL_PDF or
            bool(self.valves.CUSTOM_SKILL_IDS.strip())
        )

        return has_skills or self.valves.ENABLE_CODE_EXECUTION

    def _resolve_effort(self, user_valves) -> str:
        """Resolve effort level: user override > admin default"""
        if user_valves and hasattr(user_valves, 'MY_EFFORT_LEVEL') and user_valves.MY_EFFORT_LEVEL:
            return user_valves.MY_EFFORT_LEVEL
        return self.valves.EFFORT_LEVEL

    def _resolve_fast_mode(self, user_valves) -> bool:
        """Resolve fast mode: user override > admin default"""
        if user_valves and hasattr(user_valves, 'ENABLE_MY_FAST_MODE') and user_valves.ENABLE_MY_FAST_MODE is not None:
            return user_valves.ENABLE_MY_FAST_MODE
        return self.valves.ENABLE_FAST_MODE

    def _get_headers(self, user_valves) -> Dict[str, str]:
        """Dynamically compose beta headers based on enabled features"""
        betas = []

        # Extended cache TTL (1-hour) -- prompt caching itself is GA, no header needed
        if self.valves.ENABLE_PROMPT_CACHING and self.valves.CACHE_TTL == "1hour":
            betas.append("extended-cache-ttl-2025-04-11")

        # Dynamic web filtering + free code execution (covers web search, web fetch, code exec)
        web_search_enabled = self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH
        web_fetch_enabled = self.valves.ENABLE_WEB_FETCH and web_search_enabled
        if web_search_enabled or web_fetch_enabled:
            betas.append("code-execution-web-tools-2026-02-09")

        # Skills + Files API
        code_exec_enabled = self._should_enable_code_execution(user_valves)
        any_skills_enabled = (
            self.valves.ENABLE_SKILL_XLSX or self.valves.ENABLE_SKILL_PPTX or
            self.valves.ENABLE_SKILL_DOCX or self.valves.ENABLE_SKILL_PDF or
            bool(self.valves.CUSTOM_SKILL_IDS.strip())
        )
        if code_exec_enabled and any_skills_enabled:
            betas.append("skills-2025-10-02")
            betas.append("files-api-2025-04-14")

        # Compaction
        if self.valves.ENABLE_COMPACTION:
            betas.append("compact-2026-01-12")

        # Fast mode
        if self._resolve_fast_mode(user_valves):
            betas.append("fast-mode-2026-02-01")

        headers = {
            "x-api-key": self.valves.ANTHROPIC_API_KEY,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }

        if betas:
            headers["anthropic-beta"] = ",".join(betas)
            logger.debug(f"Beta headers: {headers['anthropic-beta']}")

        return headers

    def _configure_tools(self, user_valves) -> List[Dict[str, Any]]:
        """Build the tools array for the API request"""
        tools = []

        # Web search tool
        if self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH:
            tool = {
                "type": "web_search_20260209",
                "name": "web_search",
                "max_uses": min(max(1, self.valves.WEB_SEARCH_MAX_USES), 20)
            }

            # Domain filtering (cannot use both allow and block lists)
            if self.valves.WEB_SEARCH_DOMAIN_ALLOWLIST:
                domains = [
                    d.strip()
                    for d in self.valves.WEB_SEARCH_DOMAIN_ALLOWLIST.split(",")
                    if d.strip()
                ]
                if domains:
                    tool["allowed_domains"] = domains
            elif self.valves.WEB_SEARCH_DOMAIN_BLOCKLIST:
                domains = [
                    d.strip()
                    for d in self.valves.WEB_SEARCH_DOMAIN_BLOCKLIST.split(",")
                    if d.strip()
                ]
                if domains:
                    tool["blocked_domains"] = domains

            tools.append(tool)
            logger.debug(f"Web search tool configured: max_uses={tool['max_uses']}")

        # Web fetch tool (requires web search to be enabled)
        web_fetch_enabled = self.valves.ENABLE_WEB_FETCH and (
            self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH
        )
        if web_fetch_enabled:
            tool = {
                "type": "web_fetch_20260209",
                "name": "web_fetch",
                "max_uses": min(max(1, self.valves.WEB_FETCH_MAX_USES), 50)
            }
            tools.append(tool)
            logger.debug(f"Web fetch tool configured: max_uses={tool['max_uses']}")

        # Code execution with skills
        if self._should_enable_code_execution(user_valves):
            skill_ids = []

            # Add pre-built skills
            if self.valves.ENABLE_SKILL_XLSX:
                skill_ids.append("xlsx")
            if self.valves.ENABLE_SKILL_PPTX:
                skill_ids.append("pptx")
            if self.valves.ENABLE_SKILL_DOCX:
                skill_ids.append("docx")
            if self.valves.ENABLE_SKILL_PDF:
                skill_ids.append("pdf")

            # Add custom skills
            if self.valves.CUSTOM_SKILL_IDS:
                custom = [
                    s.strip()
                    for s in self.valves.CUSTOM_SKILL_IDS.split(",")
                    if s.strip()
                ]
                skill_ids.extend(custom)

            tool = {
                "type": "code_execution_20250825",
                "name": "code_execution"
            }

            if skill_ids:
                tool["container"] = {"skill_ids": skill_ids}
                logger.debug(f"Skills configured: {skill_ids}")

            tools.append(tool)

        return tools

    def _configure_thinking(self) -> dict:
        """Configure adaptive thinking for Opus 4.6"""
        return {"type": "adaptive"}

    def _calculate_max_tokens(self, requested_max: int) -> int:
        """Calculate max_tokens for Opus 4.6 (supports up to 128K)"""
        result = min(max(1024, requested_max), self.MAX_OUTPUT_TOKENS)
        logger.debug(f"Max tokens: requested={requested_max}, result={result}")
        return result

    def _apply_caching(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply prompt caching breakpoints to system prompt and user messages.

        Caching strategy:
        1. Cache last item in system prompt array
        2. Cache 2nd-to-last user message (creates stable cache point)
        """
        if not self.valves.ENABLE_PROMPT_CACHING:
            return payload

        cache_control = {"type": "ephemeral"}
        cache_points = 0

        # Cache system prompt
        if self.valves.CACHE_SYSTEM_PROMPT and "system" in payload:
            system_content = payload["system"]

            if isinstance(system_content, str):
                # Convert string to array with cache control
                payload["system"] = [{
                    "type": "text",
                    "text": system_content,
                    "cache_control": cache_control
                }]
                cache_points += 1
            elif isinstance(system_content, list) and len(system_content) > 0:
                # Add cache control to last item
                payload["system"][-1]["cache_control"] = cache_control
                cache_points += 1

        # Cache user messages (2nd-to-last user message)
        if self.valves.CACHE_USER_MESSAGES:
            messages = payload.get("messages", [])
            user_message_indices = [
                i for i, m in enumerate(messages) if m["role"] == "user"
            ]

            # Need at least 2 user messages to cache the 2nd-to-last
            if len(user_message_indices) >= 2:
                idx = user_message_indices[-2]
                content = messages[idx]["content"]

                if isinstance(content, list) and len(content) > 0:
                    # Add cache control to last content block of this message
                    messages[idx]["content"][-1]["cache_control"] = cache_control
                    cache_points += 1

        logger.debug(f"Applied {cache_points} cache breakpoints")
        return payload

    def _prepare_payload(
        self,
        body: Dict[str, Any],
        processed_messages: List[Dict[str, Any]],
        system_message: Optional[str],
        user_valves,
        __user__: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Assemble the complete API request payload"""

        # Start with required fields
        payload = {
            "model": self.MODEL_ID,
            "messages": processed_messages,
            "max_tokens": self._calculate_max_tokens(
                body.get("max_tokens", self.valves.DEFAULT_MAX_TOKENS)
            ),
            "stream": body.get("stream", True)
        }

        # Adaptive thinking (always active on Opus 4.6)
        payload["thinking"] = self._configure_thinking()

        # Effort level
        effort = self._resolve_effort(user_valves)
        payload["output_config"] = {"effort": effort}

        # System message (normalized to array immediately)
        if system_message:
            payload["system"] = [{"type": "text", "text": str(system_message)}]

        # Sampling: temperature and top_k are incompatible with thinking (always active)
        # Only top_p is allowed (clamped to 0.95-1.0)
        if "top_p" in body:
            payload["top_p"] = max(0.95, min(1.0, body["top_p"]))

        # Stop sequences
        if "stop_sequences" in body or "stop" in body:
            payload["stop_sequences"] = body.get(
                "stop_sequences", body.get("stop", [])
            )

        # Tools
        tools = self._configure_tools(user_valves)
        if tools:
            payload["tools"] = tools

        # Fast mode
        if self._resolve_fast_mode(user_valves):
            payload["speed"] = "fast"

        # Compaction
        if self.valves.ENABLE_COMPACTION:
            payload["context_management"] = {
                "edits": [{
                    "type": "compact_20260112",
                    "trigger": {
                        "type": "input_tokens",
                        "value": max(50000, self.valves.COMPACTION_TRIGGER_TOKENS)
                    }
                }]
            }

        # Container persistence (reuse code execution containers across turns)
        chat_id = body.get("chat_id", "")
        if chat_id and chat_id in self._containers:
            payload["container"] = self._containers[chat_id]

        # User metadata for abuse detection
        if __user__ and "id" in __user__:
            payload["metadata"] = {"user_id": str(__user__["id"])}

        # Apply caching last (after all content is in place)
        payload = self._apply_caching(payload)

        # Prefill guard: strip trailing assistant message
        if payload["messages"] and payload["messages"][-1]["role"] == "assistant":
            payload["messages"] = payload["messages"][:-1]

        return payload

    def _transform_image_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform OpenAI image_url format to Anthropic image format.

        Handles:
        - Base64 data URLs (data:image/png;base64,...)
        - Regular HTTP/HTTPS URLs

        Args:
            item: Content item with type="image_url"

        Returns:
            Transformed content item with type="image"
        """
        # Extract URL from nested structure
        image_url_obj = item.get("image_url", {})
        url = image_url_obj.get("url", "")

        if not url:
            logger.warning("Image content missing URL, passing through as-is")
            return item

        # Check if it's a data URL (base64)
        if url.startswith("data:"):
            # Parse: data:image/png;base64,iVBORw0K...
            try:
                # Split into parts
                header, data = url.split(",", 1)
                # Extract media type (e.g., "image/png")
                media_type = header.split(";")[0].split(":")[1]

                logger.debug(f"Transformed base64 image with media_type={media_type}")
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data
                    }
                }
            except (ValueError, IndexError) as e:
                logger.warning(f"Malformed data URL: {e}, defaulting to image/jpeg")
                # Fallback: try to extract just the data part
                data = url.split(",", 1)[-1] if "," in url else ""
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": data
                    }
                }
        else:
            # Regular URL
            logger.debug(f"Transformed URL image: {url[:50]}...")
            return {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": url
                }
            }

    def _process_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process messages to handle different content types"""
        processed = []

        for message in messages:
            content = message.get("content")
            processed_content = []

            if isinstance(content, list):
                for item in content:
                    item_type = item.get("type")
                    if item_type == "text":
                        processed_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item_type == "image_url":
                        # Transform OpenAI format to Anthropic format
                        transformed = self._transform_image_content(item)
                        processed_content.append(transformed)
                        logger.debug("Transformed image_url to Anthropic image format")
                    else:
                        # Pass through other types as-is
                        processed_content.append(item)
            else:
                processed_content = [{"type": "text", "text": str(content)}]

            processed.append({
                "role": message["role"],
                "content": processed_content
            })

        return processed

    # ==================== FORMATTING FUNCTIONS ====================

    def _format_token_usage(self, usage: Dict[str, Any], is_fast_mode: bool = False) -> str:
        """Format token usage statistics in collapsible section"""
        if not self.valves.SHOW_TOKEN_USAGE or not usage:
            return ""

        output = "\n\n<details>\n"
        output += "<summary>Token Usage</summary>\n\n"

        # Cache statistics
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_created = usage.get("cache_creation_input_tokens", 0)

        if cache_read > 0:
            total_input = usage.get("input_tokens", 0) + cache_read
            savings_pct = (cache_read / total_input * 100) if total_input > 0 else 0
            output += f"- **Cache Hit:** {cache_read:,} tokens ({savings_pct:.0f}% saved)\n"

        if cache_created > 0:
            output += f"- **Cached:** {cache_created:,} tokens\n"

        # Token counts
        if "thinking_tokens" in usage:
            output += f"- **Thinking:** {usage['thinking_tokens']:,} tokens\n"

        output += f"- **Input:** {usage.get('input_tokens', 0):,} tokens\n"
        output += f"- **Output:** {usage.get('output_tokens', 0):,} tokens\n"

        # Tool usage
        server_tool_use = usage.get("server_tool_use", {})
        web_search_count = server_tool_use.get("web_search_requests", 0)
        if web_search_count > 0:
            output += f"- **Web Searches:** {web_search_count}\n"

        web_fetch_count = server_tool_use.get("web_fetch_requests", 0)
        if web_fetch_count > 0:
            output += f"- **Web Fetches:** {web_fetch_count}\n"

        # Cost estimation
        if self.valves.SHOW_COST_ESTIMATE:
            price_mult = 6.0 if is_fast_mode else 1.0
            input_cost = usage.get("input_tokens", 0) / 1_000_000 * 5 * price_mult
            output_cost = usage.get("output_tokens", 0) / 1_000_000 * 25 * price_mult
            cache_read_cost = usage.get("cache_read_input_tokens", 0) / 1_000_000 * 0.50
            cache_write_cost = usage.get("cache_creation_input_tokens", 0) / 1_000_000 * 6.25
            total = input_cost + output_cost + cache_read_cost + cache_write_cost
            output += f"- **Est. Cost:** ${total:.4f}\n"

        output += "\n</details>\n"
        return output

    # ==================== STREAMING IMPLEMENTATION ====================

    async def stream_response(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        user_valves,
        __event_emitter__=None,
        chat_id: str = ""
    ) -> AsyncGenerator[str, None]:
        """Stream response with <think> tags for reasoning"""

        state = StreamingState()
        final_usage = {}

        try:
            timeout = aiohttp.ClientTimeout(
                total=self.valves.REQUEST_TIMEOUT,
                connect=30
            )
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:

                    if response.status != 200:
                        error_detail = await response.text()
                        if response.status == 429:
                            msg = "**Rate limit exceeded**. Please wait and try again."
                        elif response.status == 401:
                            msg = "**Authentication failed**. Check your API key."
                        elif response.status == 400:
                            msg = f"**Bad request**: {error_detail}"
                        else:
                            msg = f"**API Error ({response.status})**: {error_detail}"

                        yield msg
                        return

                    # aiohttp StreamReader.__aiter__ uses readline(),
                    # giving us proper line-delimited SSE parsing
                    async for line_bytes in response.content:
                        line = line_bytes.decode("utf-8").strip()
                        if not line or not line.startswith("data: "):
                            continue

                        raw_json = line[6:]
                        if raw_json.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(raw_json)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON: {raw_json[:100]}")
                            continue

                        event_type = data.get("type")

                        # Message start - capture initial usage and container
                        if event_type == "message_start":
                            message_data = data.get("message", {})
                            if "usage" in message_data:
                                final_usage = message_data["usage"]
                            # Container persistence
                            container = message_data.get("container")
                            if container and container.get("id"):
                                state.container_id = container["id"]

                        # Content block start
                        elif event_type == "content_block_start":
                            content_block = data.get("content_block", {})
                            block_type = content_block.get("type")
                            state.current_block_type = block_type
                            state.current_block_index = data.get("index", 0)

                            if block_type == "thinking":
                                # DON'T set state here - let first thinking_delta open the tag
                                logger.debug("Thinking content block started")

                            elif block_type == "text":
                                # Clear status indicator (tool use is done)
                                if __event_emitter__:
                                    await __event_emitter__({"type": "status", "data": {"done": True}})

                                # Check for citations in this text block
                                if "citations" in content_block:
                                    logger.info(f"Found {len(content_block['citations'])} citations in content_block_start")
                                    for cit in content_block["citations"]:
                                        url_val = cit.get("url", "")
                                        if url_val and url_val not in state.seen_citation_urls:
                                            state.seen_citation_urls.add(url_val)
                                            state.citations.append(CitationData(
                                                url=url_val,
                                                title=cit.get("title", ""),
                                                cited_text=cit.get("cited_text", ""),
                                                encrypted_index=cit.get("encrypted_index", "")
                                            ))

                                # Response starting - close thinking tag if open
                                if state.thinking_state == ThinkingState.IN_PROGRESS:
                                    yield "\n</think>\n\n"
                                    state.thinking_state = ThinkingState.COMPLETED
                                    logger.debug("Thinking completed, response starting")

                            elif block_type == "server_tool_use":
                                tool_name = content_block.get("name")
                                logger.info(f"Server tool use: {tool_name}, block_index={state.current_block_index}")

                                # Emit status event for UI feedback
                                if __event_emitter__:
                                    status_msg = {
                                        "web_search": "Searching the web...",
                                        "web_fetch": "Reading web page...",
                                        "bash_code_execution": "Running code...",
                                        "code_execution": "Executing code...",
                                    }.get(tool_name, f"Using {tool_name}...")
                                    await __event_emitter__({"type": "status", "data": {"description": status_msg, "done": False}})

                                if tool_name == "web_search":
                                    # Safely extract query - input might be a string or dict
                                    input_data = content_block.get("input", {})
                                    logger.info(f"Input data type: {type(input_data)}, value: {input_data}")
                                    if isinstance(input_data, dict):
                                        query = input_data.get("query", "")
                                        logger.info(f"Query from input dict: '{query}'")
                                    else:
                                        query = ""  # Will be populated by input_json_delta
                                        logger.info("Input is not dict, query will come from input_json_delta")
                                    state.current_search = WebSearchResult(query=query)
                                    logger.info(f"Created search object with query='{query}', block_index={state.current_block_index}")

                            elif block_type == "web_search_tool_result":
                                # Capture search results - they're in a "content" array
                                logger.info(f"web_search_tool_result block, current_search={'exists' if state.current_search else 'None'}")
                                if state.current_search:
                                    content_array = content_block.get("content", [])
                                    logger.info(f"Result content_array has {len(content_array)} items")
                                    # Extract web_search_result items
                                    results = []
                                    for item in content_array:
                                        if item.get("type") == "web_search_result":
                                            results.append({
                                                "title": item.get("title", ""),
                                                "url": item.get("url", ""),
                                                "page_age": item.get("page_age", "")
                                            })
                                    state.current_search.results = results
                                    logger.info(f"Captured {len(results)} search results. Current query: '{state.current_search.query}'")

                            elif block_type == "redacted_thinking":
                                if state.thinking_state == ThinkingState.IN_PROGRESS:
                                    yield "\n</think>\n\n"
                                    state.thinking_state = ThinkingState.COMPLETED
                                yield "*[Some reasoning was redacted for safety]*\n\n"

                            elif block_type == "compaction":
                                logger.info("Conversation compacted by API")

                        # Content block delta
                        elif event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            delta_type = delta.get("type")

                            if delta_type == "thinking_delta":
                                thinking_text = delta.get("thinking", "")
                                state.thinking_buffer += thinking_text
                                # Start <think> tag on first thinking delta
                                if state.thinking_state == ThinkingState.NOT_STARTED:
                                    yield "\n<think>\n"
                                    state.thinking_state = ThinkingState.IN_PROGRESS
                                # Stream thinking text in real-time
                                yield thinking_text

                            elif delta_type == "input_json_delta":
                                # Web search query streaming - accumulate partial JSON fragments
                                partial_json = delta.get("partial_json", "")
                                logger.info(f"input_json_delta received, fragment: {partial_json[:50]}")
                                if state.current_search:
                                    # Accumulate the fragment
                                    state.current_search.partial_json_buffer += partial_json
                                    logger.debug(f"Buffer now: {state.current_search.partial_json_buffer[:100]}")

                                    # Try to parse the accumulated buffer
                                    try:
                                        parsed = json.loads(state.current_search.partial_json_buffer)
                                        logger.info(f"Successfully parsed accumulated JSON: {parsed}")
                                        if "query" in parsed:
                                            state.current_search.query = parsed["query"]
                                            logger.info(f"Extracted search query: '{parsed['query']}'")
                                        else:
                                            logger.warning(f"No 'query' field in parsed JSON: {parsed}")
                                    except json.JSONDecodeError:
                                        # Still incomplete - keep accumulating
                                        logger.debug("Buffer not yet complete JSON, continuing to accumulate...")
                                else:
                                    logger.warning("input_json_delta received but state.current_search is None!")

                            elif delta_type == "text_delta":
                                text = delta.get("text", "")
                                state.response_buffer += text
                                # Close thinking tag if still open
                                if state.thinking_state == ThinkingState.IN_PROGRESS:
                                    yield "\n</think>\n\n"
                                    state.thinking_state = ThinkingState.COMPLETED
                                # Stream response text
                                yield text

                            elif delta_type == "citations_delta":
                                citation = delta.get("citation", {})
                                url_val = citation.get("url", "")
                                if url_val and url_val not in state.seen_citation_urls:
                                    state.seen_citation_urls.add(url_val)
                                    state.citations.append(CitationData(
                                        url=url_val,
                                        title=citation.get("title", ""),
                                        cited_text=citation.get("cited_text", ""),
                                        encrypted_index=citation.get("encrypted_index", ""),
                                    ))

                            elif delta_type == "signature_delta":
                                logger.debug("Received thinking signature")

                        # Content block stop
                        elif event_type == "content_block_stop":
                            stop_index = data.get("index", -1)
                            logger.info(f"content_block_stop for block_index={stop_index}, block_type={state.current_block_type}")
                            if state.current_block_type == "web_search_tool_result":
                                # Finalize current search
                                if state.current_search:
                                    logger.info(f"Finalizing search with query='{state.current_search.query}' and {len(state.current_search.results)} results")
                                    state.web_searches.append(state.current_search)

                                    if state.current_search.results:
                                        logger.info(f"Search '{state.current_search.query}' found {len(state.current_search.results)} results")

                                    logger.info("Setting state.current_search = None")
                                    state.current_search = None
                                    state.current_search_results = []

                        # Message delta - update usage and check for citations
                        elif event_type == "message_delta":
                            if "usage" in data:
                                final_usage.update(data["usage"])
                            # Check if message delta contains complete content blocks with citations
                            if "delta" in data and "content" in data["delta"]:
                                content_blocks = data["delta"]["content"]
                                for block in content_blocks:
                                    if block.get("type") == "text" and "citations" in block:
                                        logger.info(f"Found {len(block['citations'])} citations in message_delta")
                                        for cit in block["citations"]:
                                            url_val = cit.get("url", "")
                                            if url_val and url_val not in state.seen_citation_urls:
                                                state.seen_citation_urls.add(url_val)
                                                state.citations.append(CitationData(
                                                    url=url_val,
                                                    title=cit.get("title", ""),
                                                    cited_text=cit.get("cited_text", ""),
                                                    encrypted_index=cit.get("encrypted_index", "")
                                                ))

                        # Message stop
                        elif event_type == "message_stop":
                            # Close thinking tag if still open
                            if state.thinking_state == ThinkingState.IN_PROGRESS:
                                yield "\n</think>\n"
                                state.thinking_state = ThinkingState.COMPLETED

                    # --- Post-stream output ---

                    # Store container for persistence
                    if state.container_id and chat_id:
                        self._containers[chat_id] = state.container_id

                    # Show web searches in collapsible section
                    if self.valves.SHOW_WEB_SEARCH_DETAILS and state.web_searches:
                        yield "\n\n<details>\n"
                        yield "<summary>Web Searches</summary>\n\n"
                        for i, search in enumerate(state.web_searches, 1):
                            query_display = search.query if search.query else "(query not captured)"
                            yield f"**Search {i}:** {query_display}\n"
                            if search.results:
                                yield f"- Found {len(search.results)} results\n"
                                for j, result in enumerate(search.results[:3], 1):  # Show top 3
                                    title = result.get('title', 'Untitled')
                                    yield f"  {j}. {title}\n"
                            yield "\n"
                        yield "</details>\n\n"
                        logger.info(f"Displayed {len(state.web_searches)} web searches in collapsible section")

                    # Emit citation events for clickable chips
                    if self.valves.SHOW_CITATIONS and state.citations:
                        logger.info(f"Emitting {len(state.citations)} formal citations as citation chips")
                        for i, citation in enumerate(state.citations, 1):
                            document_text = citation.title
                            if citation.cited_text:
                                excerpt = citation.cited_text[:150]
                                if len(citation.cited_text) > 150:
                                    excerpt += "..."
                                document_text += f' - "{excerpt}"'

                            if __event_emitter__:
                                await __event_emitter__({
                                    "type": "citation",
                                    "data": {
                                        "document": [document_text],
                                        "metadata": [{"source": citation.url}],
                                        "source": {
                                            "name": f"[{i}]",
                                            "type": "citation",
                                            "urls": [citation.url]
                                        }
                                    }
                                })
                        logger.info(f"Emitted {len(state.citations)} formal citation events")
                    # Fallback: If no formal citations but we have web searches, emit as citation events
                    elif self.valves.SHOW_CITATIONS and state.web_searches and any(s.results for s in state.web_searches):
                        logger.info("No formal citations, emitting web search results as citation chips")

                        ref_num = 1
                        for search in state.web_searches:
                            for result in search.results:
                                title = result.get('title', 'Source')
                                url_val = result.get('url', '')
                                page_age = result.get('page_age', '')

                                document_text = title
                                if page_age:
                                    document_text += f" (Last updated: {page_age})"

                                if __event_emitter__:
                                    await __event_emitter__({
                                        "type": "citation",
                                        "data": {
                                            "document": [document_text],
                                            "metadata": [{"source": url_val}],
                                            "source": {
                                                "name": f"[{ref_num}]",
                                                "type": "web_search_results",
                                                "urls": [url_val]
                                            }
                                        }
                                    })
                                ref_num += 1

                        logger.info(f"Emitted {ref_num - 1} citation events")

                    # Show token usage
                    is_fast_mode = self._resolve_fast_mode(user_valves)
                    if final_usage:
                        usage_formatted = self._format_token_usage(final_usage, is_fast_mode=is_fast_mode)
                        if usage_formatted:
                            yield usage_formatted

        except aiohttp.ClientError as e:
            yield f"\n\n**Connection error**: {str(e)}"
            logger.error(f"Connection error: {e}")

        except asyncio.TimeoutError:
            yield "\n\n**Request timed out**. Partial response may be shown above."
            logger.error("Request timeout")

        except Exception as e:
            yield f"\n\n**Unexpected error**: {str(e)}"
            logger.error(f"Unexpected error in stream_response: {e}", exc_info=True)

    # ==================== NON-STREAMING IMPLEMENTATION ====================

    async def non_stream_response(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        user_valves
    ) -> str:
        """Handle non-streaming requests"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.valves.REQUEST_TIMEOUT, connect=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        return f"Error: **API Error ({response.status})**: {error_text}"

                    data = await response.json()
                    content_parts = []
                    thinking_parts = []

                    for block in data.get("content", []):
                        block_type = block.get("type")

                        if block_type == "text":
                            content_parts.append(block.get("text", ""))

                        elif block_type == "thinking":
                            thinking_parts.append(block.get("thinking", ""))

                        elif block_type == "redacted_thinking":
                            content_parts.append("*[Some reasoning was redacted for safety]*")

                    # Assemble response
                    result = ""

                    if thinking_parts:
                        result += f"\n<think>\n{''.join(thinking_parts)}\n</think>\n\n"

                    if content_parts:
                        result += "".join(content_parts)

                    is_fast_mode = self._resolve_fast_mode(user_valves)
                    if "usage" in data:
                        result += self._format_token_usage(data["usage"], is_fast_mode=is_fast_mode)

                    return result if result else "No response generated"

        except Exception as e:
            logger.error(f"Error in non_stream_response: {e}", exc_info=True)
            return f"Error: {str(e)}"

    # ==================== MAIN ENTRY POINT ====================

    async def pipe(
        self,
        body: Dict[str, Any],
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__=None,
        __event_call__=None
    ):
        """Main entry point for request processing"""

        # Pre-request validation
        if not self.valves.ANTHROPIC_API_KEY:
            return "Error: ANTHROPIC_API_KEY is not configured. Please add your API key in the valve settings."

        if "messages" not in body or not body["messages"]:
            return "Error: No messages in request"

        # Check for conflicting domain filters
        if (self.valves.WEB_SEARCH_DOMAIN_ALLOWLIST and
            self.valves.WEB_SEARCH_DOMAIN_BLOCKLIST):
            return "Error: Cannot use both allowed_domains and blocked_domains. Please use only one."

        try:
            # Get user valves (handle dict and object formats)
            user_valves = self.UserValves()
            if __user__:
                user_valve_data = __user__.get("valves") if isinstance(__user__, dict) else getattr(__user__, "valves", None)
                if user_valve_data:
                    if isinstance(user_valve_data, self.UserValves):
                        user_valves = user_valve_data
                    elif isinstance(user_valve_data, dict):
                        user_valves = self.UserValves(**user_valve_data)

            # Extract and process messages
            system_message, messages = pop_system_message(body.get("messages", []))
            if not messages:
                return "Error: No user messages provided"

            processed_messages = self._process_messages(messages)

            # Prepare request
            headers = self._get_headers(user_valves)
            payload = self._prepare_payload(
                body, processed_messages, system_message, user_valves, __user__
            )
            url = f"{self.API_BASE_URL}/messages"

            effort = self._resolve_effort(user_valves)
            is_fast_mode = self._resolve_fast_mode(user_valves)
            logger.info(
                f"Request: model={payload['model']}, stream={payload['stream']}, "
                f"max_tokens={payload['max_tokens']}, effort={effort}, "
                f"fast_mode={is_fast_mode}, tools={len(payload.get('tools', []))}"
            )

            # Execute request
            chat_id = body.get("chat_id", "")
            if payload.get("stream", True):
                return self.stream_response(
                    url, headers, payload, user_valves, __event_emitter__, chat_id
                )
            else:
                return await self.non_stream_response(url, headers, payload, user_valves)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
