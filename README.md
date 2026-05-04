# agent-gateway

[![PyPI version](https://img.shields.io/pypi/v/agent-gateway.svg)](https://pypi.org/project/agent-gateway/)
[![Python](https://img.shields.io/pypi/pyversions/agent-gateway.svg)](https://pypi.org/project/agent-gateway/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/naveenkumarbaskaran/agent-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/naveenkumarbaskaran/agent-gateway/actions)

**One gateway. Every agent protocol.** Route requests between A2A, MCP, OpenAI Assistants, and plain REST — with a single YAML config.

```
pip install agent-gateway
```

## 🎬 Demo

<p align="center">
  <img src="assets/demo.gif" alt="agent-gateway demo — unified protocol routing for A2A, MCP, OpenAI, REST" width="700">
  <br>
  <em>Starting the gateway, routing requests across 4 protocols, and viewing live metrics</em>
</p>

---

## The Problem

The AI agent ecosystem is fragmented:

```
Your App ──→ Agent A (A2A protocol)
         ──→ Agent B (MCP tools)
         ──→ Agent C (OpenAI Assistants API)
         ──→ Agent D (plain REST)
```

Each speaks a different language. You write adapters for each. Then a new protocol drops and you rewrite everything.

## The Solution

```
                  ┌────────────────────┐
Your App ────────→│   agent-gateway    │────→ Agent A (A2A)
                  │                    │────→ Agent B (MCP)
                  │   One protocol     │────→ Agent C (OpenAI)
                  │   in, any out      │────→ Agent D (REST)
                  └────────────────────┘
```

Talk to the gateway in **any** protocol. It translates to **any** other.

## Quick Start

### 1. Define your gateway

```yaml
# gateway.yaml
gateway:
  name: my-gateway
  port: 8080

routes:
  - name: search-agent
    upstream:
      protocol: a2a
      url: http://localhost:9000
    expose_as:
      - mcp      # Expose A2A agent as MCP tool
      - rest     # And as REST endpoint

  - name: code-helper
    upstream:
      protocol: mcp
      command: python -m code_helper_mcp
      transport: stdio
    expose_as:
      - a2a      # Expose MCP server as A2A agent
      - openai   # And as OpenAI Assistants-compatible

  - name: legacy-api
    upstream:
      protocol: rest
      url: https://api.example.com/analyze
      method: POST
      headers:
        Authorization: "Bearer ${API_KEY}"
    expose_as:
      - a2a
      - mcp
```

### 2. Start the gateway

```bash
agent-gateway serve gateway.yaml
```

### 3. Connect from any protocol

```python
# As A2A client:
response = a2a_client.send_task("search-agent", "Find recent papers on RLHF")

# As MCP client (from Claude Desktop):
# Just add to claude_desktop_config.json:
#   {"mcpServers": {"gateway": {"url": "http://localhost:8080/mcp"}}}

# As OpenAI-compatible:
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/openai/v1")
response = client.chat.completions.create(
    model="code-helper",
    messages=[{"role": "user", "content": "Fix this bug"}],
)

# As REST:
import httpx
response = httpx.post("http://localhost:8080/rest/search-agent", json={"query": "RLHF papers"})
```

## Protocol Support Matrix

| From ↓ / To → | A2A | MCP | OpenAI | REST |
|:---------------|:---:|:---:|:------:|:----:|
| **A2A**        | —   | ✅  | ✅     | ✅   |
| **MCP**        | ✅  | —   | ✅     | ✅   |
| **OpenAI**     | ✅  | ✅  | —      | ✅   |
| **REST**       | ✅  | ✅  | ✅     | —    |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        agent-gateway                             │
│                                                                  │
│  ┌──────────┐    ┌────────────┐    ┌──────────┐    ┌─────────┐ │
│  │ Ingress  │───→│  Router    │───→│Translator│───→│  Egress │ │
│  │          │    │            │    │          │    │         │ │
│  │ • A2A    │    │ • Match    │    │ • A2A↔X  │    │ • HTTP  │ │
│  │ • MCP    │    │   route    │    │ • MCP↔X  │    │ • stdio │ │
│  │ • OpenAI │    │ • Auth     │    │ • OAI↔X  │    │ • SSE   │ │
│  │ • REST   │    │ • Rate     │    │ • REST↔X │    │         │ │
│  └──────────┘    └────────────┘    └──────────┘    └─────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Protocol translation** — Seamless conversion between A2A, MCP, OpenAI, REST
- **YAML configuration** — No code required, just declare routes
- **Environment variables** — `${VAR}` expansion in config
- **Auth passthrough** — Forward headers, tokens, API keys
- **Health checks** — Built-in `/health` endpoint with upstream status
- **Hot reload** — Change config without restart (`--watch`)
- **Middleware** — Rate limiting, logging, request/response transforms
- **Discovery** — Auto-generates agent cards, tool lists, OpenAPI specs

## CLI

```bash
# Start gateway
agent-gateway serve gateway.yaml

# Validate config
agent-gateway validate gateway.yaml

# List routes
agent-gateway routes gateway.yaml

# Health check
agent-gateway health http://localhost:8080
```

## Programmatic Usage

```python
from agent_gateway import Gateway

gateway = Gateway.from_yaml("gateway.yaml")

# Translate a single request
result = await gateway.translate(
    source_protocol="rest",
    target_route="search-agent",
    payload={"query": "test"},
)
```

## Why Not Just Use X?

| Solution | Limitation |
|----------|-----------|
| mcp-a2a-bridge | Only 2 protocols (MCP ↔ A2A) |
| LangServe | LangChain-only, single protocol |
| Custom adapters | One-off, unmaintainable |
| API Gateway (Kong, etc.) | No protocol awareness, just HTTP routing |

agent-gateway understands the **semantics** of each protocol — agent cards, tool schemas, function calling, streaming — and translates them correctly.

## Contributing

```bash
git clone https://github.com/naveenkumarbaskaran/agent-gateway.git
cd agent-gateway
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT
