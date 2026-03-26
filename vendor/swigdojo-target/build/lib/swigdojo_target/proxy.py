from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from swigdojo_target.wrapper import TargetWrapper


@dataclass
class RequestRecord:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes
    response_status: int
    response_headers: dict[str, str]
    response_body: bytes


class TrafficRecorder:
    def __init__(self) -> None:
        self._records: list[RequestRecord] = []
        self._lock = asyncio.Lock()

    async def record(self, record: RequestRecord) -> None:
        async with self._lock:
            self._records.append(record)

    def get_log(self) -> list[RequestRecord]:
        return list(self._records)


_REQUEST_SKIP = frozenset({"host", "transfer-encoding", "connection"})
_RESPONSE_SKIP = frozenset({"transfer-encoding", "connection", "content-length", "content-encoding"})


def _sanitize_path(path: str) -> str:
    """Collapse leading slashes to prevent SSRF via protocol-relative URLs."""
    return "/" + path.lstrip("/")


def create_proxy_app(wrapper: TargetWrapper) -> Starlette:
    recorder = TrafficRecorder()
    upstream_base = f"http://localhost:{wrapper.health_port}"
    wrapper._proxy_recorder = recorder
    client = httpx.AsyncClient(base_url=upstream_base)

    async def _forward(request: Request) -> Response:
        path = _sanitize_path(request.url.path)
        url = path
        if request.url.query:
            url = f"{path}?{request.url.query}"

        body = await request.body()
        forwarded_headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in _REQUEST_SKIP
        }

        upstream = await client.request(
            method=request.method,
            url=url,
            headers=forwarded_headers,
            content=body,
        )

        await recorder.record(
            RequestRecord(
                method=request.method,
                path=url,
                headers=dict(request.headers),
                body=body,
                response_status=upstream.status_code,
                response_headers=dict(upstream.headers),
                response_body=upstream.content,
            )
        )

        resp_headers = {
            k: v
            for k, v in upstream.headers.items()
            if k.lower() not in _RESPONSE_SKIP
        }

        if "location" in resp_headers:
            resp_headers["location"] = resp_headers["location"].replace(
                upstream_base, ""
            )

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=resp_headers,
        )

    @asynccontextmanager
    async def _lifespan(app: Starlette):
        yield
        await client.aclose()

    _all_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    return Starlette(
        routes=[Route("/{path:path}", _forward, methods=_all_methods)],
        lifespan=_lifespan,
    )
