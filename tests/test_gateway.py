"""Tests for agent-gateway."""

import pytest
from agent_gateway.config import GatewayConfig, RouteConfig, UpstreamConfig
from agent_gateway.translator import (
    A2ATranslator, MCPTranslator, OpenAITranslator, RESTTranslator, get_translator,
)
from agent_gateway.models import AgentResponse
from agent_gateway.gateway import Gateway


# ─── Config Tests ───────────────────────────────────────────────

def test_config_from_dict():
    config = GatewayConfig(
        name="test",
        routes=[
            RouteConfig(
                name="agent-1",
                upstream=UpstreamConfig(protocol="a2a", url="http://localhost:9000"),
                expose_as=["mcp", "rest"],
            )
        ],
    )
    assert config.name == "test"
    assert len(config.routes) == 1
    assert config.routes[0].name == "agent-1"


def test_config_get_route():
    config = GatewayConfig(routes=[
        RouteConfig(name="search", upstream=UpstreamConfig(protocol="rest", url="http://x")),
        RouteConfig(name="chat", upstream=UpstreamConfig(protocol="a2a", url="http://y")),
    ])
    assert config.get_route("search") is not None
    assert config.get_route("chat") is not None
    assert config.get_route("nonexistent") is None


def test_config_from_yaml(tmp_path):
    yaml_content = """
gateway:
  name: test-gw
  port: 9090

routes:
  - name: my-agent
    upstream:
      protocol: a2a
      url: http://localhost:8000
    expose_as:
      - mcp
      - rest
"""
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(yaml_content)
    config = GatewayConfig.from_yaml(config_file)
    assert config.name == "test-gw"
    assert config.port == 9090
    assert len(config.routes) == 1


# ─── Translator Tests ───────────────────────────────────────────

def test_a2a_translator_parse():
    translator = A2ATranslator()
    raw = {
        "params": {
            "id": "task-1",
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello agent"}],
            },
        },
    }
    request = translator.parse_request(raw)
    assert request.message == "Hello agent"
    assert request.source_protocol == "a2a"


def test_a2a_translator_format():
    translator = A2ATranslator()
    response = AgentResponse(content="Hi there!", status="completed")
    formatted = translator.format_response(response)
    assert formatted["result"]["status"]["state"] == "completed"
    assert "Hi there!" in formatted["result"]["status"]["message"]["parts"][0]["text"]


def test_mcp_translator_parse():
    translator = MCPTranslator()
    raw = {
        "method": "tools/call",
        "params": {"name": "search", "arguments": {"query": "test"}},
    }
    request = translator.parse_request(raw)
    assert "search" in request.message
    assert request.metadata["tool_name"] == "search"


def test_mcp_translator_format():
    translator = MCPTranslator()
    response = AgentResponse(content="Found 5 results")
    formatted = translator.format_response(response)
    assert formatted["result"]["content"][0]["text"] == "Found 5 results"
    assert formatted["result"]["isError"] is False


def test_openai_translator_parse():
    translator = OpenAITranslator()
    raw = {
        "model": "my-agent",
        "messages": [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "What is 2+2?"},
        ],
    }
    request = translator.parse_request(raw)
    assert request.message == "What is 2+2?"
    assert request.route == "my-agent"
    assert len(request.context) == 1


def test_openai_translator_format():
    translator = OpenAITranslator()
    response = AgentResponse(content="4")
    formatted = translator.format_response(response)
    assert formatted["choices"][0]["message"]["content"] == "4"
    assert formatted["object"] == "chat.completion"


def test_rest_translator_parse():
    translator = RESTTranslator()
    raw = {"query": "find papers on RLHF", "route": "search"}
    request = translator.parse_request(raw)
    assert request.message == "find papers on RLHF"


def test_rest_translator_format():
    translator = RESTTranslator()
    response = AgentResponse(content="Here are the results", status="completed")
    formatted = translator.format_response(response)
    assert formatted["content"] == "Here are the results"
    assert formatted["status"] == "completed"


def test_get_translator_valid():
    assert get_translator("a2a").protocol == "a2a"
    assert get_translator("mcp").protocol == "mcp"
    assert get_translator("openai").protocol == "openai"
    assert get_translator("rest").protocol == "rest"


def test_get_translator_invalid():
    with pytest.raises(ValueError, match="Unknown protocol"):
        get_translator("graphql")


# ─── Model Tests ────────────────────────────────────────────────

def test_agent_response_success():
    resp = AgentResponse(content="ok", status="completed")
    assert resp.is_success is True


def test_agent_response_failure():
    resp = AgentResponse(content="", error="timeout", status="failed")
    assert resp.is_success is False


# ─── Gateway Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gateway_unknown_route():
    config = GatewayConfig(routes=[])
    gw = Gateway(config)
    result = await gw.translate("rest", "nonexistent", {"query": "test"})
    assert result["error"] is not None or "not found" in str(result)
    await gw.close()


@pytest.mark.asyncio
async def test_gateway_health():
    config = GatewayConfig(name="test-gw", routes=[
        RouteConfig(name="r1", upstream=UpstreamConfig(protocol="rest", url="http://x")),
    ])
    gw = Gateway(config)
    health = await gw.health()
    assert health["status"] == "healthy"
    assert health["routes"] == 1
    await gw.close()
