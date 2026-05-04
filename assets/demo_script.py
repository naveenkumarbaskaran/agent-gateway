#!/usr/bin/env python3
"""Simulated agent-gateway demo for terminal recording."""
import time, sys, os

os.environ["TERM"] = "xterm-256color"

def c(code, text):
    return f"\033[{code}m{text}\033[0m"

def slow(text, delay=0.012):
    for ch in text:
        sys.stdout.write(ch); sys.stdout.flush(); time.sleep(delay)
    print()

def section(text):
    print(c("1;36", f"\n  {text}"))
    print(c("36", f"  {'─'*56}"))

print(c("1;32", """
   █████╗  ██████╗ ███████╗███╗   ██╗████████╗
  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
   ██████╗  █████╗ ████████╗███████╗██╗    ██╗ █████╗ ██╗   ██╗
  ██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝██║    ██║██╔══██╗╚██╗ ██╔╝
  ██║  ███╗███████║   ██║   █████╗  ██║ █╗ ██║███████║ ╚████╔╝
  ██║   ██║██╔══██║   ██║   ██╔══╝  ██║███╗██║██╔══██║  ╚██╔╝
  ╚██████╔╝██║  ██║   ██║   ███████╗╚███╔███╔╝██║  ██║   ██║
   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝"""))

time.sleep(0.2)
print(c("2", "  v0.1.0 • Universal agent protocol gateway — A2A, MCP, OpenAI, REST"))
time.sleep(0.4)

# Show config
section("gateway.yaml")
time.sleep(0.2)

cfg_lines = [
    "  gateway:",
    "    port: 9000",
    "    routes:",
    "      - name: weather-agent",
    "        protocol: a2a",
    "        upstream: http://localhost:8001",
    "      - name: code-tools",
    "        protocol: mcp",
    "        upstream: http://localhost:8002",
    "      - name: assistant",
    "        protocol: openai",
    "        upstream: https://api.openai.com/v1",
    "      - name: legacy-api",
    "        protocol: rest",
    "        upstream: http://internal:3000/api",
]
for line in cfg_lines:
    col = "36" if ":" in line[:25] else "37"
    if "protocol:" in line: col = "33"
    if "name:" in line: col = "1;37"
    print(c(col, line))
    time.sleep(0.04)

time.sleep(0.4)

# Start gateway
section("$ agent-gateway start --config gateway.yaml")
time.sleep(0.3)

print(c("2", "  Loading gateway configuration..."))
time.sleep(0.3)

routes = [
    ("weather-agent", "A2A",    "http://localhost:8001", "32"),
    ("code-tools",    "MCP",    "http://localhost:8002", "33"),
    ("assistant",     "OpenAI", "https://api.openai.com/v1", "35"),
    ("legacy-api",    "REST",   "http://internal:3000/api", "36"),
]
print(f"\n  {c('1','Route'):18s} {c('1','Protocol'):10s} {c('1','Upstream'):>32s}")
print(f"  {'─'*18} {'─'*10} {'─'*32}")
for name, proto, upstream, clr in routes:
    print(f"  {c('1',name):26s} {c(clr,proto):18s} {c('2',upstream):>32s}")
    time.sleep(0.15)

time.sleep(0.3)
print(f"\n  {c('1;32','✓')} Gateway listening on {c('1','http://localhost:9000')}")
print(c("2", "    All protocols unified under one endpoint"))
time.sleep(0.4)

# Show translation
section("Protocol Translation in Action")
time.sleep(0.2)

print(f"\n  {c('1','Request')}: POST /weather-agent (A2A format)")
print(c("2", '  {"task": {"message": "Weather in Berlin?"}}'))
time.sleep(0.3)

print(f"\n  {c('33','▸')} Gateway translates A2A → upstream A2A agent")
print(f"  {c('33','▸')} Response: {c('32','200 OK')} in {c('1','0.8s')}")
time.sleep(0.3)

print(f"\n  {c('1','Request')}: POST /code-tools (MCP format)")
print(c("2", '  {"method": "tools/call", "params": {"name": "lint"}}'))
time.sleep(0.3)

print(f"\n  {c('33','▸')} Gateway routes to MCP server")
print(f"  {c('33','▸')} Response: {c('32','200 OK')} in {c('1','0.3s')}")
time.sleep(0.3)

print(f"\n  {c('1','Cross-protocol')}: A2A client → REST backend")
print(c("2", "  Client sends A2A → Gateway translates → REST call → A2A response"))
time.sleep(0.2)
print(f"  {c('33','▸')} A2A task → {c('36','GET /api/data?q=...')} → {c('32','A2A result')}")
time.sleep(0.4)

# Metrics
section("Gateway Metrics")
time.sleep(0.2)

print(f"\n  {c('1','Route'):18s} {c('1','Requests'):>10s} {c('1','Avg Latency'):>12s} {c('1','Errors'):>8s}")
print(f"  {'─'*18} {'─'*10} {'─'*12} {'─'*8}")
stats = [
    ("weather-agent", "1,247",  "0.82s",  "0.1%"),
    ("code-tools",    "3,891",  "0.31s",  "0.0%"),
    ("assistant",     "892",    "1.24s",  "0.3%"),
    ("legacy-api",    "5,102",  "0.08s",  "0.0%"),
]
for name, reqs, lat, err in stats:
    ecol = "32" if err == "0.0%" else "33"
    print(f"  {c('37',name):26s} {c('1',reqs):>18s} {c('36',lat):>20s} {c(ecol,err):>16s}")
    time.sleep(0.1)

print(f"\n  {c('1','Total')}: {c('1;33','11,132 requests')} | {c('1;32','99.9% success')} | {c('2','4 protocols unified')}")

time.sleep(0.4)
print(c("1;36", f"\n  {'─'*56}"))
print(c("1;32", "  ✓ One gateway • Four protocols • Zero translation code"))
print(c("2",    "    pip install agentic-gateway"))
print(c("1;36", f"  {'─'*56}\n"))
time.sleep(1.0)
