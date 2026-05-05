FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir ".[server]"

FROM python:3.12-slim

LABEL maintainer="Naveen Kumar Baskaran <naveenkb142@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/naveenkumarbaskaran/agent-gateway"
LABEL org.opencontainers.image.description="Universal agent protocol gateway — routes between A2A, MCP, OpenAI, and REST"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/agent-gateway /usr/local/bin/agent-gateway

EXPOSE 8000

ENTRYPOINT ["agent-gateway"]
CMD ["--help"]
