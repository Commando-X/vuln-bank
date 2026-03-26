from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from swigdojo_target.scoring import ScoringContext


class TestHttpClient:
    def test_http_client_configured_with_upstream_url(self) -> None:
        ctx = ScoringContext(health_port=8080)
        assert ctx.http.base_url == "http://localhost:8080"


class TestReadFile:
    @pytest.mark.asyncio
    async def test_read_file_returns_contents(self) -> None:
        ctx = ScoringContext(health_port=8080)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            f.flush()
            result = await ctx.read_file(f.name)
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_read_file_raises_on_missing_file(self) -> None:
        ctx = ScoringContext(health_port=8080)
        with pytest.raises(FileNotFoundError):
            await ctx.read_file("/nonexistent/path/file.txt")

    @pytest.mark.asyncio
    async def test_read_file_rejects_path_outside_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as base:
            ctx = ScoringContext(health_port=8080, base_dir=Path(base))
            with pytest.raises(ValueError, match="outside allowed directory"):
                await ctx.read_file("/etc/passwd")

    @pytest.mark.asyncio
    async def test_read_file_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as base:
            ctx = ScoringContext(health_port=8080, base_dir=Path(base))
            with pytest.raises(ValueError, match="outside allowed directory"):
                await ctx.read_file(f"{base}/../../../etc/passwd")

    @pytest.mark.asyncio
    async def test_read_file_allows_path_inside_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as base:
            file_path = Path(base) / "test.txt"
            file_path.write_text("sandboxed content")
            ctx = ScoringContext(health_port=8080, base_dir=Path(base))
            result = await ctx.read_file(str(file_path))
        assert result == "sandboxed content"

    @pytest.mark.asyncio
    async def test_read_file_allows_any_path_without_base_dir(self) -> None:
        ctx = ScoringContext(health_port=8080)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("no sandbox")
            f.flush()
            result = await ctx.read_file(f.name)
        assert result == "no sandbox"


class TestExec:
    @pytest.mark.asyncio
    async def test_exec_returns_stdout(self) -> None:
        ctx = ScoringContext(health_port=8080)
        result = await ctx.exec("echo", "hello")
        assert result.strip() == "hello"

    @pytest.mark.asyncio
    async def test_exec_raises_on_nonzero_exit(self) -> None:
        ctx = ScoringContext(health_port=8080)
        with pytest.raises(RuntimeError):
            await ctx.exec("false")


class TestGetStored:
    def test_scoring_context_get_stored(self) -> None:
        storage = {"actor_trajectory": [1, 2, 3]}
        ctx = ScoringContext(health_port=8080, storage_getter=storage.get)
        assert ctx.get_stored("actor_trajectory") == [1, 2, 3]

    def test_scoring_context_get_stored_default(self) -> None:
        storage: dict = {}
        ctx = ScoringContext(health_port=8080, storage_getter=storage.get)
        assert ctx.get_stored("missing", default="fallback") == "fallback"

    def test_scoring_context_get_stored_none_without_storage(self) -> None:
        ctx = ScoringContext(health_port=8080)
        assert ctx.get_stored("anything") is None


class TestGetRequestLog:
    def test_get_request_log_raises_without_proxy(self) -> None:
        ctx = ScoringContext(health_port=8080)
        with pytest.raises(RuntimeError, match="Proxy mode is not enabled"):
            ctx.get_request_log()


class TestGetTraces:
    def test_get_traces_returns_collected_spans(self) -> None:
        from swigdojo_target.otel import OtelCollector

        collector = OtelCollector()
        collector.ingest_traces(
            {
                "resourceSpans": [
                    {
                        "resource": {"attributes": []},
                        "scopeSpans": [
                            {"spans": [{"traceId": "t1", "spanId": "s1", "name": "op1"}]}
                        ],
                    }
                ]
            }
        )
        ctx = ScoringContext(health_port=8080, otel_collector=collector)
        traces = ctx.get_traces()
        assert len(traces) == 1
        assert traces[0]["name"] == "op1"

    def test_get_traces_raises_without_otel(self) -> None:
        ctx = ScoringContext(health_port=8080)
        with pytest.raises(RuntimeError, match="OTEL collection is not enabled"):
            ctx.get_traces()
