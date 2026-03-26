from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable

import httpx


class ScoringContext:
    def __init__(
        self,
        health_port: int,
        proxy: Any | None = None,
        base_dir: Path | None = None,
        otel_collector: Any | None = None,
        storage_getter: Callable[[str, Any], Any] | None = None,
    ) -> None:
        self.http = httpx.AsyncClient(
            base_url=f"http://localhost:{health_port}",
            timeout=httpx.Timeout(30.0),
        )
        self._proxy = proxy
        self._base_dir = base_dir.resolve() if base_dir is not None else None
        self._otel_collector = otel_collector
        self._storage_getter = storage_getter

    async def close(self) -> None:
        await self.http.aclose()

    async def __aenter__(self) -> ScoringContext:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def read_file(self, path: str) -> str:
        file_path = Path(path).resolve()
        if self._base_dir is not None and not file_path.is_relative_to(self._base_dir):
            raise ValueError(f"Path {path} is outside allowed directory")
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_text()

    async def exec(self, *args: str) -> str:
        """Run a command and return its stdout.

        Accepts command arguments as separate strings to prevent shell injection.
        Shell features (pipes, redirects, globbing) are not supported.

        Example::

            await ctx.exec("grep", "pattern", "/var/log/app.log")
        """
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            cmd_str = " ".join(args)
            raise RuntimeError(
                f"Command '{cmd_str}' exited with code {process.returncode}: "
                f"{stderr.decode()}"
            )
        return stdout.decode()

    def get_stored(self, key: str, default: Any = None) -> Any:
        if self._storage_getter is None:
            return default
        return self._storage_getter(key, default)

    def get_request_log(self) -> Any:
        if self._proxy is None:
            raise RuntimeError("Proxy mode is not enabled")
        return self._proxy.get_log()

    def get_traces(self) -> list[dict]:
        if self._otel_collector is None:
            raise RuntimeError("OTEL collection is not enabled")
        return self._otel_collector.get_traces()
