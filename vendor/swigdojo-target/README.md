# swigdojo-target

Python SDK for wrapping existing applications as SwigDojo targets. Turn any Docker image into a benchmarkable target by adding a scoring script — no modifications to the original application required.

## Installation

```bash
pip install swigdojo-target
```

Requires Python 3.11+.

## Quick Start

Create a file called `wrapper.py`:

```python
from swigdojo_target import TargetWrapper

wrapper = TargetWrapper(
    command="./start-my-app.sh",
    health_port=3000,
    health_path="/health",
)

@wrapper.objective(
    name="form-submitted",
    description="Agent successfully submitted the contact form",
    public=True,
)
async def check_form_submitted(ctx):
    response = await ctx.http.get("/api/submissions")
    return len(response.json()) > 0

if __name__ == "__main__":
    wrapper.run()
```

When `wrapper.run()` is called, the SDK:

1. Starts your application as a subprocess via the `command` parameter
2. Waits for the application to become healthy (with progress logging)
3. Serves the SwigDojo protocol endpoints on port 8787 (configurable via `SWIGDOJO_WRAPPER_PORT`)
4. Proxies all non-protocol HTTP requests to the upstream app (actors see a single endpoint)
5. During settle, runs all scoring functions and reports results to the platform

## API Reference

### `TargetWrapper`

Main entry point. Configures the upstream application and registers scoring objectives.

```python
TargetWrapper(
    command: str | list[str],
    health_port: int,
    health_path: str = "/health",
    health_type: str = "http",
    proxy: bool = True,
    settle_timeout: int = 60,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `command` | `str \| list[str]` | *required* | Shell command to start the upstream application. Accepts a string or a list of arguments (joined with spaces). |
| `health_port` | `int` | *required* | Port where the upstream app accepts health checks |
| `health_path` | `str` | `"/health"` | HTTP endpoint path for health checks |
| `health_type` | `str` | `"http"` | Health check type: `"http"` or `"tcp"` |
| `proxy` | `bool` | `True` | Proxy non-protocol requests to upstream app. Set `False` to only serve protocol endpoints. |
| `settle_timeout` | `int` | `60` | Timeout in seconds for each scoring function during settle |

### `@wrapper.objective`

Decorator that registers a scoring function as an objective.

```python
@wrapper.objective(
    name: str,
    description: str,
    public: bool,
)
async def my_objective(ctx):
    ...
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Objective identifier. Must match `[a-z0-9-]+` (lowercase alphanumerics and hyphens). Must be unique. |
| `description` | `str` | Human-readable description of the objective |
| `public` | `bool` | Whether the actor can see this objective. Set to `False` for secret objectives (e.g. security checks). |

The decorated function receives a `ScoringContext` as its only argument. Return a truthy value to mark the objective as passed. Scoring functions can be `async` or synchronous.

### `ScoringContext`

Passed to every scoring function. Provides methods to inspect the target application's state.

#### `ctx.http`

Pre-configured `httpx.AsyncClient` pointed at the upstream application (`http://localhost:{health_port}`). Use it to make HTTP requests to the target.

```python
response = await ctx.http.get("/api/data")
data = response.json()
```

#### `ctx.read_file(path: str) -> str`

Read a file from the container filesystem. Useful for inspecting logs, data files, or configuration.

```python
logs = await ctx.read_file("/var/log/app/queries.log")
```

Raises `FileNotFoundError` if the file does not exist.

#### `ctx.exec(*args: str) -> str`

Run a command and return its stdout. Arguments are passed as separate strings to prevent shell injection — shell features like pipes and redirects are not supported.

```python
result = await ctx.exec("psql", "-U", "app", "-d", "mydb", "-t", "-c", "SELECT count(*) FROM users")
```

Raises `RuntimeError` if the command exits with a non-zero code.

#### `ctx.get_request_log()`

Returns a list of `RequestRecord` objects representing all HTTP requests the actor made to the target. Raises `RuntimeError` if proxy mode is disabled.

```python
requests = ctx.get_request_log()
api_calls = [r for r in requests if "/api/chat" in r.path]
```

Each `RequestRecord` has the following fields:

| Field | Type | Description |
|---|---|---|
| `method` | `str` | HTTP method (e.g. `"GET"`, `"POST"`) |
| `path` | `str` | Request path including query string (e.g. `"/api/chat?id=1"`) |
| `headers` | `dict[str, str]` | Request headers |
| `body` | `bytes` | Request body |
| `response_status` | `int` | Response status code |
| `response_headers` | `dict[str, str]` | Response headers |
| `response_body` | `bytes` | Response body |

## Proxy Mode

By default, the wrapper acts as a reverse proxy between the actor and the upstream application. All non-protocol HTTP requests are forwarded transparently to the upstream app and recorded. During settle, scoring functions can inspect the recorded traffic via `ctx.get_request_log()`.

The proxy rewrites `Location` headers on redirects so they route back through the wrapper rather than exposing the upstream's internal port.

Set `proxy=False` if you only need the protocol endpoints and don't want the actor to reach the app through the wrapper.

## Dockerfile Pattern

The recommended way to wrap an existing Docker image is with a multi-stage build:

```dockerfile
# Stage 1: build wheels
FROM python:3.12-slim AS wrapper-deps
RUN pip wheel --no-cache-dir --wheel-dir /wheels swigdojo-target

# Stage 2: add wrapper to the upstream image
FROM my-web-app:latest

# Install Python from the base image's package manager (NOT from the builder stage)
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install pre-built wheels
COPY --from=wrapper-deps /wheels /tmp/wheels
RUN pip install --no-cache-dir --break-system-packages /tmp/wheels/*.whl && \
    rm -rf /tmp/wheels

COPY wrapper.py /swigdojo/wrapper.py

RUN adduser --disabled-password --gecos "" --uid 1001 wrapper || true
USER 1001

# Clear base image entrypoint so CMD takes effect
ENTRYPOINT []
CMD ["python3", "/swigdojo/wrapper.py"]
```

**Important:** Install Python from the upstream image's package manager, not by copying binaries from the builder stage. Different base images ship different OpenSSL versions — copying Python from `python:3.12-slim` into a different base will cause `libcrypto.so: version not found` errors.

Replace `my-web-app:latest` with your upstream application image. The wrapper starts the original app via the `command` parameter and serves the SwigDojo protocol endpoints alongside it.

See `examples/Dockerfile.template` for a commented version with package manager variants.

## Port Configuration

The wrapper serves protocol endpoints on port **8787** by default (configurable via `SWIGDOJO_WRAPPER_PORT`). This avoids conflicts with common application ports (8080, 3000, etc.).

Your upstream application should bind to a different port (specified by `health_port`). The wrapper proxies requests from 8787 to the upstream port transparently.

## Environment Variables

SwigDojo injects these environment variables into every target container:

| Variable | Required | Description |
|---|---|---|
| `SWIGDOJO_API_URL` | Yes | SwigDojo platform API base URL |
| `SWIGDOJO_EXPERIMENT_ID` | Yes | Current experiment ID |
| `SWIGDOJO_RUN_ID` | Yes | Current target run ID |
| `SWIGDOJO_WRAPPER_PORT` | No | Port for the wrapper server (default: `8787`) |

The wrapper reads these automatically. If any required variable is missing, the wrapper fails fast at startup with a clear error listing which variables are missing.

You do not need to set these variables yourself — they are provided by the SwigDojo platform when it deploys your target container.

## Error Handling

**Scoring function raises an exception:** The objective stays incomplete (not passed). The exception is logged with a full traceback. Other scoring functions still run — one failure does not block the others.

**Scoring function exceeds `settle_timeout`:** The function is cancelled and the objective stays incomplete. A warning is logged.

**Upstream application fails to start:** The `command` process exits with a non-zero code. The wrapper logs the error and the health endpoint continues returning 503. SwigDojo eventually marks the target run as failed.

**Upstream application crashes mid-run:** Scoring functions that use `ctx.http` will fail, but `ctx.read_file()` and `ctx.exec()` still work if the container filesystem is intact.

**SwigDojo API unreachable during settle:** The wrapper retries objective completion reports with sawtooth backoff (up to 30 seconds total). After exhausting retries, the error is logged and the objective stays incomplete.

## Examples

See the `examples/` directory for complete working examples:

- `web_app_wrapper.py` — Wrapping a web application with HTTP and file-based scoring
- `postgres_wrapper.py` — Wrapping a Postgres database with SQL-based scoring
- `proxy_mode_wrapper.py` — Using proxy mode with LLM-as-judge scoring
- `Dockerfile.template` — Multi-stage Dockerfile pattern for wrapping any image
