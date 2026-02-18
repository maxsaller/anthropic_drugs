"""
title: Claude Sonnet 4.5 Complete v4.1
author: Enhanced by AI
version: 4.1.0
license: MIT
description: Production-ready Claude Sonnet 4.5 with <think> tags for reasoning, web search, skills, and clean UX
requirements: requests, pydantic
"""

import os
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Literal
import requests
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
    current_block_index: int = 0
    current_block_type: Optional[str] = None
    current_search: Optional[WebSearchResult] = None
    current_search_results: List[Dict[str, Any]] = field(default_factory=list)
    all_events: List[Dict[str, Any]] = field(default_factory=list)  # Store all events for citation extraction


# ==================== MAIN PIPE CLASS ====================


class Pipe:
    """Claude Sonnet 4.5 Complete Integration for OpenWebUI"""

    class Valves(BaseModel):
        """Admin-configurable settings"""

        # API & Core Settings
        ANTHROPIC_API_KEY: str = Field(
            default="",
            description="Your Anthropic API key"
        )
        DEFAULT_MAX_TOKENS: int = Field(
            default=8192,
            description="Default maximum tokens for responses (max 8192)"
        )
        DEFAULT_TEMPERATURE: float = Field(
            default=1.0,
            description="Default temperature (0.0-1.0)"
        )
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="API request timeout in seconds"
        )

        # Extended Thinking
        ENABLE_EXTENDED_THINKING: bool = Field(
            default=True,
            description="Enable extended thinking for complex reasoning"
        )
        THINKING_BUDGET_TOKENS: int = Field(
            default=10000,
            description="Thinking budget in tokens (1024-16000 recommended)"
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

    API_VERSION = "2023-06-01"
    API_BASE_URL = "https://api.anthropic.com/v1"
    MODEL_ID = "claude-sonnet-4-5-20250929"

    def __init__(self):
        self.type = "manifold"
        self.id = "claude_complete_v4"
        self.name = "claude/"
        self.citation = False  # CRITICAL: Disable OpenWebUI auto-citations

        self.valves = self.Valves(
            ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", "")
        )
        self.user_valves = self.UserValves()

        # Set logging level
        log_level = getattr(logging, self.valves.LOG_LEVEL)
        logger.setLevel(log_level)

        logger.info("Claude Sonnet 4.5 Complete v4.0.0 initialized")

    def pipes(self) -> List[Dict[str, str]]:
        """Return available model configurations"""
        return [
            {
                "id": "claude-sonnet-4.5-complete",
                "name": "Claude Sonnet 4.5 (Complete)"
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

    def _has_tools(self, user_valves) -> bool:
        """Check if any tools are enabled"""
        return (
            (self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH) or
            self._should_enable_code_execution(user_valves)
        )

    def _get_headers(self, user_valves) -> Dict[str, str]:
        """Dynamically compose beta headers based on enabled features"""
        betas = []

        # Prompt caching
        if self.valves.ENABLE_PROMPT_CACHING:
            betas.append("prompt-caching-2024-07-31")
            if self.valves.CACHE_TTL == "1hour":
                betas.append("extended-cache-ttl-2025-04-11")

        # Web search
        if self.valves.ENABLE_WEB_SEARCH and user_valves.ENABLE_MY_WEB_SEARCH:
            betas.append("web-search-2025-03-05")

        # Code execution + skills + files
        if self._should_enable_code_execution(user_valves):
            betas.append("code-execution-2025-08-25")
            betas.append("skills-2025-10-02")
            betas.append("files-api-2025-04-14")

        # Interleaved thinking (only when thinking + tools both enabled)
        if self.valves.ENABLE_EXTENDED_THINKING and self._has_tools(user_valves):
            betas.append("interleaved-thinking-2025-05-14")

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
                "type": "web_search_20250305",
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

    def _configure_thinking(self) -> Optional[Dict[str, Any]]:
        """Configure extended thinking if enabled"""
        if not self.valves.ENABLE_EXTENDED_THINKING:
            return None

        # Clamp budget to recommended range
        budget = max(1024, min(self.valves.THINKING_BUDGET_TOKENS, 16000))

        logger.debug(f"Extended thinking enabled with budget: {budget} tokens")
        return {
            "type": "enabled",
            "budget_tokens": budget
        }

    def _calculate_max_tokens(self, requested_max: int) -> int:
        """
        Calculate appropriate max_tokens accounting for thinking budget.

        With extended thinking: max_tokens must accommodate both thinking and response.
        Without thinking: just use the requested amount (capped at 8192).
        """
        if not self.valves.ENABLE_EXTENDED_THINKING:
            return min(requested_max, 8192)

        thinking_budget = max(1024, min(self.valves.THINKING_BUDGET_TOKENS, 16000))

        # Reserve at least 2000 tokens for the actual response
        min_required = thinking_budget + 2000

        # Use the larger of requested or minimum required, cap at 8192
        calculated = max(requested_max, min_required)
        result = min(calculated, 8192)

        logger.debug(
            f"Max tokens calculation: requested={requested_max}, "
            f"thinking_budget={thinking_budget}, result={result}"
        )
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
        user_valves
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

        # Temperature
        if "temperature" in body:
            payload["temperature"] = body["temperature"]
        elif self.valves.DEFAULT_TEMPERATURE != 1.0:
            payload["temperature"] = self.valves.DEFAULT_TEMPERATURE

        # Other sampling parameters
        if "top_k" in body:
            payload["top_k"] = body["top_k"]
        if "top_p" in body:
            payload["top_p"] = body["top_p"]
        if "stop_sequences" in body or "stop" in body:
            payload["stop_sequences"] = body.get(
                "stop_sequences", body.get("stop", [])
            )

        # System message
        if system_message:
            payload["system"] = system_message

        # Extended thinking
        thinking_config = self._configure_thinking()
        if thinking_config:
            payload["thinking"] = thinking_config

        # Tools
        tools = self._configure_tools(user_valves)
        if tools:
            payload["tools"] = tools

        # Apply caching last (after all content is in place)
        payload = self._apply_caching(payload)

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

    def _format_token_usage(self, usage: Dict[str, Any]) -> str:
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

        output += "\n</details>\n"
        return output

    # ==================== STREAMING IMPLEMENTATION ====================

    async def stream_response(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        user_valves,
        __event_emitter__=None
    ) -> Generator[str, None, None]:
        """Stream response with <think> tags for reasoning"""

        state = StreamingState()
        final_usage = {}

        try:
            with requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=(30, self.valves.REQUEST_TIMEOUT)
            ) as response:

                if response.status_code != 200:
                    error_detail = response.text
                    if response.status_code == 429:
                        msg = "⚠️ **Rate limit exceeded**. Please wait and try again."
                    elif response.status_code == 401:
                        msg = "❌ **Authentication failed**. Check your API key."
                    elif response.status_code == 400:
                        msg = f"❌ **Bad request**: {error_detail}"
                    else:
                        msg = f"❌ **API Error ({response.status_code})**: {error_detail}"

                    yield msg
                    return

                for line in response.iter_lines():
                    if not line:
                        continue

                    decoded = line.decode("utf-8")
                    if not decoded.startswith("data: "):
                        continue

                    raw_json = decoded[6:]
                    if raw_json.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(raw_json)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON: {raw_json[:100]}")
                        continue

                    # Store all events for later citation extraction
                    state.all_events.append(data)
                    event_type = data.get("type")

                    # Message start - capture initial usage
                    if event_type == "message_start":
                        message_data = data.get("message", {})
                        if "usage" in message_data:
                            final_usage = message_data["usage"]

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
                            # Check for citations in this text block
                            if "citations" in content_block:
                                logger.info(f"Found {len(content_block['citations'])} citations in content_block_start")
                                for cit in content_block["citations"]:
                                    state.citations.append(CitationData(
                                        url=cit.get("url", ""),
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
                            if tool_name == "web_search":
                                # Safely extract query - input might be a string or dict
                                input_data = content_block.get("input", {})
                                logger.info(f"Input data type: {type(input_data)}, value: {input_data}")
                                if isinstance(input_data, dict):
                                    query = input_data.get("query", "")
                                    logger.info(f"Query from input dict: '{query}'")
                                else:
                                    query = ""  # Will be populated by input_json_delta
                                    logger.info(f"Input is not dict, query will come from input_json_delta")
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
                                            # Note: encrypted_content is for Claude's use, not display
                                        })
                                state.current_search.results = results
                                logger.info(f"Captured {len(results)} search results. Current query: '{state.current_search.query}'")

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
                            # Web search query streaming - accumulate partial JSON fragments!
                            partial_json = delta.get("partial_json", "")
                            logger.info(f"input_json_delta received, fragment: {partial_json[:50]}")
                            if state.current_search:
                                # Accumulate the fragment
                                state.current_search.partial_json_buffer += partial_json
                                logger.debug(f"Buffer now: {state.current_search.partial_json_buffer[:100]}")

                                # Try to parse the accumulated buffer
                                try:
                                    parsed = json.loads(state.current_search.partial_json_buffer)
                                    logger.info(f"✅ Successfully parsed accumulated JSON: {parsed}")
                                    if "query" in parsed:
                                        state.current_search.query = parsed["query"]
                                        logger.info(f"✅ Extracted search query: '{parsed['query']}'")
                                    else:
                                        logger.warning(f"No 'query' field in parsed JSON: {parsed}")
                                except json.JSONDecodeError as e:
                                    # Still incomplete - keep accumulating
                                    logger.debug(f"Buffer not yet complete JSON, continuing to accumulate...")
                            else:
                                logger.warning(f"⚠️ input_json_delta received but state.current_search is None!")

                        elif delta_type == "text_delta":
                            text = delta.get("text", "")
                            state.response_buffer += text
                            # Close thinking tag if still open
                            if state.thinking_state == ThinkingState.IN_PROGRESS:
                                yield "\n</think>\n\n"
                                state.thinking_state = ThinkingState.COMPLETED
                            # Stream response text
                            yield text

                    # Content block stop
                    elif event_type == "content_block_stop":
                        stop_index = data.get("index", -1)
                        logger.info(f"content_block_stop for block_index={stop_index}, block_type={state.current_block_type}")
                        if state.current_block_type == "web_search_tool_result":
                            # Finalize current search (display at end instead of inline)
                            if state.current_search:
                                logger.info(f"🔚 Finalizing search with query='{state.current_search.query}' and {len(state.current_search.results)} results")
                                state.web_searches.append(state.current_search)

                                # Just log, don't display inline
                                if state.current_search.results:
                                    logger.info(f"Search '{state.current_search.query}' found {len(state.current_search.results)} results")

                                logger.info(f"Setting state.current_search = None")
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
                                        state.citations.append(CitationData(
                                            url=cit.get("url", ""),
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

                # Extract citations from all events
                logger.info(f"Processing {len(state.all_events)} events for citations")

                for event in state.all_events:
                    event_type = event.get("type")

                    # Check message_start for complete message structure
                    if event_type == "message_start":
                        message = event.get("message", {})
                        content = message.get("content", [])
                        for block in content:
                            if block.get("type") == "text" and "citations" in block:
                                logger.info(f"Found {len(block['citations'])} citations in message_start")
                                for cit in block["citations"]:
                                    state.citations.append(CitationData(
                                        url=cit.get("url", ""),
                                        title=cit.get("title", ""),
                                        cited_text=cit.get("cited_text", ""),
                                        encrypted_index=cit.get("encrypted_index", "")
                                    ))

                    # Check content_block_stop for complete blocks
                    elif event_type == "content_block_stop":
                        # Some streaming implementations include the complete block here
                        if "content_block" in event:
                            block = event["content_block"]
                            if block.get("type") == "text" and "citations" in block:
                                logger.info(f"Found {len(block['citations'])} citations in content_block_stop")
                                for cit in block["citations"]:
                                    state.citations.append(CitationData(
                                        url=cit.get("url", ""),
                                        title=cit.get("title", ""),
                                        cited_text=cit.get("cited_text", ""),
                                        encrypted_index=cit.get("encrypted_index", "")
                                    ))

                # Show web searches in collapsible section (no icon)
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
                if state.citations:
                    logger.info(f"Emitting {len(state.citations)} formal citations as citation chips")
                    for i, citation in enumerate(state.citations, 1):
                        # Build document text with cited text if available
                        document_text = citation.title
                        if citation.cited_text:
                            excerpt = citation.cited_text[:150]
                            if len(citation.cited_text) > 150:
                                excerpt += "..."
                            document_text += f' - "{excerpt}"'

                        # Emit citation event - creates clickable citation chip in UI!
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
                elif state.web_searches and any(s.results for s in state.web_searches):
                    logger.info("No formal citations, emitting web search results as citation chips")

                    ref_num = 1
                    for search in state.web_searches:
                        for result in search.results:
                            title = result.get('title', 'Source')
                            url = result.get('url', '')
                            page_age = result.get('page_age', '')

                            # Build document text with page age if available
                            document_text = title
                            if page_age:
                                document_text += f" (Last updated: {page_age})"

                            # Emit citation event - creates clickable citation chip in UI!
                            if __event_emitter__:
                                await __event_emitter__({
                                    "type": "citation",
                                    "data": {
                                        "document": [document_text],
                                        "metadata": [{"source": url}],
                                        "source": {
                                            "name": f"[{ref_num}]",
                                            "type": "web_search_results",
                                            "urls": [url]
                                        }
                                    }
                                })
                            ref_num += 1

                    logger.info(f"Emitted {ref_num - 1} citation events")

                # Show token usage (no icon)
                if final_usage:
                    usage_formatted = self._format_token_usage(final_usage)
                    if usage_formatted:
                        yield usage_formatted

        except requests.exceptions.Timeout:
            error_msg = "\n\n⏱️ **Request timed out**. Partial response may be shown above."
            logger.error("Request timeout")
            yield error_msg

        except requests.exceptions.ConnectionError:
            error_msg = "\n\n🔌 **Connection error**. Please check your internet connection."
            logger.error("Connection error")
            yield error_msg

        except Exception as e:
            error_msg = f"\n\n❌ **Unexpected error**: {str(e)}"
            logger.error(f"Unexpected error in stream_response: {e}", exc_info=True)
            yield error_msg

    # ==================== NON-STREAMING IMPLEMENTATION ====================

    def non_stream_response(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        user_valves
    ) -> str:
        """Handle non-streaming requests"""
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=(30, self.valves.REQUEST_TIMEOUT)
            )

            if response.status_code != 200:
                return f"Error: API Error ({response.status_code}): {response.text}"

            data = response.json()
            content_parts = []
            thinking_parts = []
            citations = []

            for block in data.get("content", []):
                block_type = block.get("type")

                if block_type == "text":
                    content_parts.append(block.get("text", ""))
                    # Extract citations
                    if "citations" in block:
                        for cit in block["citations"]:
                            citations.append(CitationData(
                                url=cit.get("url", ""),
                                title=cit.get("title", ""),
                                cited_text=cit.get("cited_text", "")
                            ))

                elif block_type == "thinking":
                    thinking_parts.append(block.get("thinking", ""))

            # Assemble response
            result = ""

            if thinking_parts:
                result += f"\n<think>\n{''.join(thinking_parts)}\n</think>\n\n"

            if content_parts:
                result += "".join(content_parts)

            if "usage" in data:
                result += self._format_token_usage(data["usage"])

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
            # Get user valves
            user_valves = self.user_valves
            if __user__ and hasattr(__user__, "valves"):
                user_valves = __user__.valves

            # Extract and process messages
            system_message, messages = pop_system_message(body.get("messages", []))
            if not messages:
                return "Error: No user messages provided"

            processed_messages = self._process_messages(messages)

            # Prepare request
            headers = self._get_headers(user_valves)
            payload = self._prepare_payload(
                body, processed_messages, system_message, user_valves
            )
            url = f"{self.API_BASE_URL}/messages"

            logger.info(
                f"Request: model={payload['model']}, stream={payload['stream']}, "
                f"max_tokens={payload['max_tokens']}, thinking={bool(payload.get('thinking'))}, "
                f"tools={len(payload.get('tools', []))}"
            )

            # Execute request
            if payload.get("stream", True):
                return self.stream_response(
                    url, headers, payload, user_valves, __event_emitter__
                )
            else:
                return self.non_stream_response(url, headers, payload, user_valves)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
