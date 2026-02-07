"""Configuration models for gateway."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class UpstreamConfig(BaseModel):
    """Configuration for an upstream agent/service."""

    protocol: str  # "a2a", "mcp", "openai", "rest"
    url: str | None = None
    command: str | None = None  # For stdio-based MCP
    args: list[str] = Field(default_factory=list)
    transport: str = "http"  # "http", "stdio", "sse"
    method: str = "POST"  # For REST
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_s: float = 30.0


class RouteConfig(BaseModel):
    """A single route: upstream + exposure config."""

    name: str
    upstream: UpstreamConfig
    expose_as: list[str] = Field(default_factory=lambda: ["a2a", "mcp", "rest"])
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class GatewayConfig(BaseModel):
    """Top-level gateway configuration."""

    name: str = "agent-gateway"
    host: str = "0.0.0.0"
    port: int = 8080
    routes: list[RouteConfig] = Field(default_factory=list)
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @classmethod
    def from_yaml(cls, path: str | Path) -> GatewayConfig:
        """Load config from YAML file with env var expansion."""
        content = Path(path).read_text()
        # Expand ${VAR} → os.environ[VAR]
        content = _expand_env_vars(content)
        data = yaml.safe_load(content)

        gateway_data = data.get("gateway", {})
        routes_data = data.get("routes", [])

        routes = [RouteConfig(**r) for r in routes_data]
        return cls(
            name=gateway_data.get("name", "agent-gateway"),
            host=gateway_data.get("host", "0.0.0.0"),
            port=gateway_data.get("port", 8080),
            routes=routes,
            log_level=gateway_data.get("log_level", "INFO"),
        )

    def get_route(self, name: str) -> RouteConfig | None:
        """Find a route by name."""
        for route in self.routes:
            if route.name == name:
                return route
        return None


def _expand_env_vars(text: str) -> str:
    """Replace ${VAR} or $VAR with environment variable values."""
    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, match.group(0))

    return re.sub(r'\$\{(\w+)\}|\$(\w+)', replacer, text)
