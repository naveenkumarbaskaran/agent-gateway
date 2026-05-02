# Contributing to agent-gateway

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/naveenkumarbaskaran/agent-gateway.git
cd agent-gateway
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check .
ruff format .
```

## Making Changes

1. Fork the repo and create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Add or update tests for any new functionality
4. Ensure all tests pass and linting is clean
5. Open a pull request against `main`

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add LangChain protocol translator`
- `fix: handle timeout in upstream forwarding`
- `test: add config validation edge cases`
- `docs: add deployment guide`

## Adding a New Protocol Translator

1. Create a new class inheriting from `BaseTranslator` in `translator.py`
2. Implement `to_canonical()` and `from_canonical()` methods
3. Register it with `@TranslatorRegistry.register("protocol_name")`
4. Add an endpoint in `server.py` if needed
5. Add tests and update the README

## Architecture Overview

```
Inbound Request → Translator.to_canonical() → AgentRequest
                                                    ↓
                                              Gateway.forward()
                                                    ↓
AgentResponse ← Translator.from_canonical() ← Upstream Response
```

## Reporting Issues

- Use GitHub Issues with a clear title and reproduction steps
- Include your Python version, gateway config (redact secrets), and error output
- For protocol-specific issues, include the raw request/response if possible

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
