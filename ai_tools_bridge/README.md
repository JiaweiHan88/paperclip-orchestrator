# AI Tools Bridge

FastAPI server that exposes all `ai_tools_*` tool functions over HTTP for
Paperclip plugin workers.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check + loaded tool count |
| `GET` | `/tools/manifest` | All tools across all packages |
| `GET` | `/tools/manifest/{package}` | Tools for one package (`github`, `jira`, `confluence`, `gerrit`) |
| `POST` | `/tools/{package}/{tool_name}` | Execute a tool |

## Request format

```json
POST /tools/jira/get_jira_issue
{
  "params": { "key": "PROJ-123" },
  "credentials": {
    "jira_client": "<resolved at runtime by plugin worker>"
  }
}
```

The `credentials` object is forwarded to the tool function via parameter
name matching. Any key in `credentials` whose name matches a function
parameter that is **not** in the Pydantic schema is injected at call time.

## Running locally

```sh
cd ai_tools_bridge
uv sync
uv run python -m ai_tools_bridge
```

Or via Docker Compose:

```sh
docker compose up ai-tools-bridge
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRIDGE_HOST` | `0.0.0.0` | Listen host |
| `BRIDGE_PORT` | `8000` | Listen port |
| `BRIDGE_LOG_LEVEL` | `info` | Uvicorn log level |
