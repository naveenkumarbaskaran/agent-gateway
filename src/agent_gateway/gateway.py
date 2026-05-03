"""Gateway core — routes requests through protocol translators to upstreams."""

from __future__ import annotations

from typing import Any

import httpx

from agent_gateway.config import GatewayConfig, RouteConfig
from agent_gateway.models import AgentRequest, AgentResponse
from agent_gateway.translator import get_translator


class Gateway:
    """Core gateway that routes and translates between protocols."""

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(timeout=30.0)

    @classmethod
    def from_yaml(cls, path: str) -> Gateway:
        """Create gateway from YAML config file."""
        config = GatewayConfig.from_yaml(path)
        return cls(config)

    async def translate(
        self,
        source_protocol: str,
        target_route: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Translate a request from source protocol, route to target, return in source format.

        This is the main entry point for all translations.
        """
        # 1. Find route
        route = self.config.get_route(target_route)
        if not route:
            return get_translator(source_protocol).format_response(
                AgentResponse(content="", error=f"Route '{target_route}' not found", status="failed")
            )

        # 2. Parse incoming request using source protocol translator
        source_translator = get_translator(source_protocol)
        request = source_translator.parse_request(payload)
        request.route = target_route

        # 3. Forward to upstream
        response = await self._forward_to_upstream(route, request)

        # 4. Format response in source protocol
        return source_translator.format_response(response)

    async def _forward_to_upstream(
        self, route: RouteConfig, request: AgentRequest
    ) -> AgentResponse:
        """Forward request to the upstream agent in its native protocol."""
        upstream = route.upstream

        if upstream.protocol == "rest":
            return await self._forward_rest(route, request)
        elif upstream.protocol == "a2a":
            return await self._forward_a2a(route, request)
        elif upstream.protocol == "openai":
            return await self._forward_openai(route, request)
        else:
            return AgentResponse(
                error=f"Upstream protocol '{upstream.protocol}' forwarding not implemented",
                status="failed",
            )

    async def _forward_rest(self, route: RouteConfig, request: AgentRequest) -> AgentResponse:
        """Forward to a REST upstream."""
        upstream = route.upstream
        if not upstream.url:
            return AgentResponse(error="No URL configured for REST upstream", status="failed")

        try:
            resp = await self._client.request(
                method=upstream.method,
                url=upstream.url,
                json={"query": request.message, "context": request.context},
                headers=upstream.headers,
                timeout=upstream.timeout_s,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("result", data.get("content", data.get("response", str(data))))
            return AgentResponse(content=str(content), status="completed")
        except httpx.HTTPError as e:
            return AgentResponse(error=f"REST upstream error: {e}", status="failed")

    async def _forward_a2a(self, route: RouteConfig, request: AgentRequest) -> AgentResponse:
        """Forward to an A2A upstream."""
        upstream = route.upstream
        if not upstream.url:
            return AgentResponse(error="No URL configured for A2A upstream", status="failed")

        a2a_payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "id": request.route,
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": request.message}],
                },
            },
        }

        try:
            resp = await self._client.post(
                upstream.url,
                json=a2a_payload,
                headers=upstream.headers,
                timeout=upstream.timeout_s,
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract content from A2A response
            result = data.get("result", {})
            status = result.get("status", {})
            msg = status.get("message", {})
            parts = msg.get("parts", [])
            content = " ".join(p.get("text", "") for p in parts if "text" in p)

            return AgentResponse(content=content, status="completed")
        except httpx.HTTPError as e:
            return AgentResponse(error=f"A2A upstream error: {e}", status="failed")

    async def _forward_openai(self, route: RouteConfig, request: AgentRequest) -> AgentResponse:
        """Forward to OpenAI-compatible upstream."""
        upstream = route.upstream
        if not upstream.url:
            return AgentResponse(error="No URL configured for OpenAI upstream", status="failed")

        openai_payload = {
            "model": route.name,
            "messages": [
                *[{"role": m["role"], "content": m["content"]} for m in request.context],
                {"role": "user", "content": request.message},
            ],
        }

        try:
            url = upstream.url.rstrip("/") + "/chat/completions"
            resp = await self._client.post(
                url,
                json=openai_payload,
                headers=upstream.headers,
                timeout=upstream.timeout_s,
            )
            resp.raise_for_status()
            data = resp.json()

            choices = data.get("choices", [])
            content = choices[0]["message"]["content"] if choices else ""
            return AgentResponse(content=content, status="completed")
        except httpx.HTTPError as e:
            return AgentResponse(error=f"OpenAI upstream error: {e}", status="failed")

    @property
    def routes(self) -> list[RouteConfig]:
        return self.config.routes

    async def health(self) -> dict[str, Any]:
        """Check gateway and upstream health."""
        return {
            "status": "healthy",
            "gateway": self.config.name,
            "routes": len(self.config.routes),
            "route_names": [r.name for r in self.config.routes],
        }

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
