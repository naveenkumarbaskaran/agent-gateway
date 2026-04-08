"""CLI for agent-gateway."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_gateway.config import GatewayConfig


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(prog="agent-gateway", description="Universal agent protocol gateway")
    subparsers = parser.add_subparsers(dest="command")

    # Serve
    serve_parser = subparsers.add_parser("serve", help="Start the gateway server")
    serve_parser.add_argument("config", help="Path to gateway.yaml")
    serve_parser.add_argument("--host", default=None, help="Override host")
    serve_parser.add_argument("--port", type=int, default=None, help="Override port")
    serve_parser.add_argument("--watch", action="store_true", help="Hot-reload on config change")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate gateway config")
    validate_parser.add_argument("config", help="Path to gateway.yaml")

    # Routes
    routes_parser = subparsers.add_parser("routes", help="List configured routes")
    routes_parser.add_argument("config", help="Path to gateway.yaml")

    # Health
    health_parser = subparsers.add_parser("health", help="Check gateway health")
    health_parser.add_argument("url", help="Gateway URL")

    args = parser.parse_args()

    if args.command == "serve":
        _serve(args)
    elif args.command == "validate":
        _validate(args)
    elif args.command == "routes":
        _routes(args)
    elif args.command == "health":
        _health(args)
    else:
        parser.print_help()


def _serve(args: argparse.Namespace) -> None:
    """Start the gateway server."""
    config = GatewayConfig.from_yaml(args.config)
    host = args.host or config.host
    port = args.port or config.port

    print(f"Starting agent-gateway '{config.name}' on {host}:{port}")
    print(f"Routes: {len(config.routes)}")
    for route in config.routes:
        print(f"  • {route.name} ({route.upstream.protocol}) → expose as {route.expose_as}")

    try:
        import uvicorn  # type: ignore[import-untyped]
        from agent_gateway.server import create_app

        app = create_app(config)
        uvicorn.run(app, host=host, port=port, log_level=config.log_level.lower())
    except ImportError:
        print("Server requires uvicorn + fastapi. Install: pip install agent-gateway[server]")
        sys.exit(1)


def _validate(args: argparse.Namespace) -> None:
    """Validate config file."""
    path = Path(args.config)
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    try:
        config = GatewayConfig.from_yaml(path)
        print(f"✓ Valid config: {config.name}")
        print(f"  Routes: {len(config.routes)}")
        for r in config.routes:
            print(f"    • {r.name} ({r.upstream.protocol} → {r.expose_as})")
    except Exception as e:
        print(f"✗ Invalid config: {e}")
        sys.exit(1)


def _routes(args: argparse.Namespace) -> None:
    """List routes."""
    config = GatewayConfig.from_yaml(args.config)
    print(f"Gateway: {config.name}")
    print(f"{'Route':<20} {'Upstream':<10} {'Expose As':<30}")
    print("─" * 60)
    for r in config.routes:
        print(f"{r.name:<20} {r.upstream.protocol:<10} {', '.join(r.expose_as):<30}")


def _health(args: argparse.Namespace) -> None:
    """Check health."""
    import httpx

    try:
        resp = httpx.get(f"{args.url.rstrip('/')}/health", timeout=5.0)
        if resp.status_code == 200:
            print(f"✓ Healthy: {resp.json()}")
        else:
            print(f"✗ Unhealthy: HTTP {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Unreachable: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
