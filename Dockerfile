FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home mcp
USER mcp
ENV AIVIKINGS_MCP_HOST=0.0.0.0 AIVIKINGS_MCP_PORT=8081
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/healthz', timeout=3)"]
CMD ["aivikings-mcp"]
