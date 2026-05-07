# Changelog

## [2.0.0] - 2025-05-07

### Breaking Changes
- Development status upgraded to Production/Stable
- Bumped `httpx` minimum to >=0.27
- Bumped `pydantic` minimum to >=2.5
- Added `tenacity` as core dependency for retry logic

### Added
- Retry logic with exponential backoff for upstream failures
- `Typing :: Typed` classifier — fully typed package
- `routing` keyword for discoverability
- `mypy` in dev dependencies
- `fastapi` bumped to >=0.115, `uvicorn` to >=0.30

### Improved
- Better error messages for misconfigured routes
- Improved A2A protocol compliance (streaming support)
- Config validation on load (fail-fast on invalid YAML)
- `pytest-asyncio` bumped to >=0.24

### Fixed
- Race condition in concurrent request translation
- Environment variable expansion for nested YAML values
- OpenAI translator now handles streaming responses correctly

---

## [1.0.0] - 2025-03-10

### Added
- Full protocol translation matrix: A2A ↔ MCP ↔ OpenAI ↔ REST
- YAML configuration with `${ENV_VAR}` expansion
- Health check endpoint
- Hot config reload with `--watch`
- CLI: `serve`, `validate`, `routes`, `health`

### Improved
- Connection pooling for upstream HTTP clients
- Request/response logging middleware

---

## [0.1.0] - 2025-01-25

### Added
- Initial release
- Gateway core with protocol translators
- A2A, MCP, OpenAI, REST translators
- YAML-based route configuration
- FastAPI server with ingress endpoints
