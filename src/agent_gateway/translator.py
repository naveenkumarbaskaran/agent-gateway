"""Protocol translators — convert between protocol-specific and canonical formats."""

from __future__ import annotations

from typing import Any

from agent_gateway.models import AgentRequest, AgentResponse


class ProtocolTranslator:
    """Base class for protocol translators."""

    protocol: str = "base"

    def parse_request(self, raw: dict[str, Any]) -> AgentRequest:
        """Parse a protocol-specific request into canonical form."""
        raise NotImplementedError

    def format_response(self, response: AgentResponse) -> dict[str, Any]:
        """Format a canonical response into protocol-specific format."""
        raise NotImplementedError


class A2ATranslator(ProtocolTranslator):
    """Translator for the A2A (Agent-to-Agent) protocol."""

    protocol = "a2a"

    def parse_request(self, raw: dict[str, Any]) -> AgentRequest:
        """Parse A2A task/send request."""
        # A2A sends tasks with messages containing text parts
        message = ""
        params = raw.get("params", {})
        msg = params.get("message", {})
        parts = msg.get("parts", [])
        for part in parts:
            if part.get("type") == "text" or "text" in part:
                message += part.get("text", "")

        return AgentRequest(
            route=params.get("id", ""),
            message=message,
            source_protocol="a2a",
            metadata={"task_id": params.get("id", "")},
        )

    def format_response(self, response: AgentResponse) -> dict[str, Any]:
        """Format as A2A task result."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "status": {
                    "state": "completed" if response.is_success else "failed",
                    "message": {
                        "role": "agent",
                        "parts": [{"type": "text", "text": response.content}],
                    },
                },
            },
        }


class MCPTranslator(ProtocolTranslator):
    """Translator for the MCP (Model Context Protocol)."""

    protocol = "mcp"

    def parse_request(self, raw: dict[str, Any]) -> AgentRequest:
        """Parse MCP tool call request."""
        method = raw.get("method", "")
        params = raw.get("params", {})

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            # Convert tool call to a natural language message
            message = f"Call tool '{tool_name}' with: {arguments}"
            return AgentRequest(
                route=tool_name,
                message=message,
                source_protocol="mcp",
                metadata={"tool_name": tool_name, "arguments": arguments},
            )

        return AgentRequest(route="", message=str(params), source_protocol="mcp")

    def format_response(self, response: AgentResponse) -> dict[str, Any]:
        """Format as MCP tool result."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{"type": "text", "text": response.content}],
                "isError": not response.is_success,
            },
        }


class OpenAITranslator(ProtocolTranslator):
    """Translator for OpenAI Chat Completions API format."""

    protocol = "openai"

    def parse_request(self, raw: dict[str, Any]) -> AgentRequest:
        """Parse OpenAI-style chat completion request."""
        messages = raw.get("messages", [])
        last_message = messages[-1]["content"] if messages else ""
        model = raw.get("model", "")

        context = [
            {"role": m["role"], "content": m["content"]}
            for m in messages[:-1]
        ] if len(messages) > 1 else []

        return AgentRequest(
            route=model,
            message=last_message,
            context=context,
            source_protocol="openai",
        )

    def format_response(self, response: AgentResponse) -> dict[str, Any]:
        """Format as OpenAI chat completion response."""
        return {
            "id": "chatcmpl-gateway",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.content,
                },
                "finish_reason": "stop" if response.is_success else "error",
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }


class RESTTranslator(ProtocolTranslator):
    """Translator for plain REST/JSON APIs."""

    protocol = "rest"

    def parse_request(self, raw: dict[str, Any]) -> AgentRequest:
        """Parse plain JSON request."""
        # Look for common field names
        message = (
            raw.get("message")
            or raw.get("query")
            or raw.get("input")
            or raw.get("text")
            or raw.get("prompt")
            or str(raw)
        )
        return AgentRequest(
            route=raw.get("route", raw.get("agent", "")),
            message=str(message),
            source_protocol="rest",
            metadata=raw,
        )

    def format_response(self, response: AgentResponse) -> dict[str, Any]:
        """Format as plain JSON."""
        return {
            "status": response.status,
            "content": response.content,
            "error": response.error,
            "metadata": response.metadata,
        }


# Registry
TRANSLATORS: dict[str, ProtocolTranslator] = {
    "a2a": A2ATranslator(),
    "mcp": MCPTranslator(),
    "openai": OpenAITranslator(),
    "rest": RESTTranslator(),
}


def get_translator(protocol: str) -> ProtocolTranslator:
    """Get translator for a protocol."""
    if protocol not in TRANSLATORS:
        raise ValueError(f"Unknown protocol: '{protocol}'. Supported: {list(TRANSLATORS.keys())}")
    return TRANSLATORS[protocol]
