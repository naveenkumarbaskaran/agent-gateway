"""FastAPI server for the gateway (optional: pip install agent-gateway[server])."""

from __future__ import annotations

from typing import Any

from agent_gateway.config import GatewayConfig
from agent_gateway.gateway import Gateway


def create_app(config: GatewayConfig) -> Any:
    """Create FastAPI app for the gateway."""
    from fastapi import FastAPI, Request  # type: ignore[import-untyped]
    from fastapi.responses import JSONResponse  # type: ignore[import-untyped]

    app = FastAPI(title=config.name, version="0.1.0")
    gateway = Gateway(config)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return await gateway.health()

    @app.post("/a2a")
    async def a2a_endpoint(request: Request) -> JSONResponse:
        """A2A protocol endpoint."""
        body = await request.json()
        result = await gateway.translate("a2a", _extract_route(body, "a2a"), body)
        return JSONResponse(result)

    @app.post("/mcp")
    async def mcp_endpoint(request: Request) -> JSONResponse:
        """MCP protocol endpoint."""
        body = await request.json()
        route = body.get("params", {}).get("name", "")
        result = await gateway.translate("mcp", route, body)
        return JSONResponse(result)

    @app.post("/openai/v1/chat/completions")
    async def openai_endpoint(request: Request) -> JSONResponse:
        """OpenAI-compatible endpoint."""
        body = await request.json()
        model = body.get("model", "")
        result = await gateway.translate("openai", model, body)
        return JSONResponse(result)

    @app.post("/rest/{route_name}")
    async def rest_endpoint(route_name: str, request: Request) -> JSONResponse:
        """REST pass-through endpoint."""
        body = await request.json()
        body["route"] = route_name
        result = await gateway.translate("rest", route_name, body)
        return JSONResponse(result)

    @app.get("/routes")
    async def list_routes() -> list[dict[str, Any]]:
        """List all configured routes."""
        return [
            {
                "name": r.name,
                "upstream_protocol": r.upstream.protocol,
                "expose_as": r.expose_as,
                "description": r.description,
            }
            for r in config.routes
        ]

    return app


def _extract_route(body: dict[str, Any], protocol: str) -> str:
    """Extract route name from protocol-specific request body."""
    if protocol == "a2a":
        return body.get("params", {}).get("id", "")
    return ""
