from __future__ import annotations

import asyncio
import socket

import pytest

from swigdojo_target.health import HealthChecker


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_http_health_check_success(self) -> None:
        port = _find_free_port()

        async def _handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            await reader.readuntil(b"\r\n\r\n")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(_handler, "127.0.0.1", port)
        try:
            checker = HealthChecker(port=port, path="/health", health_type="http")
            result = await checker.check()
            assert result is True
        finally:
            server.close()
            await server.wait_closed()

    @pytest.mark.asyncio
    async def test_http_health_check_non_200(self) -> None:
        port = _find_free_port()

        async def _handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            await reader.readuntil(b"\r\n\r\n")
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(_handler, "127.0.0.1", port)
        try:
            checker = HealthChecker(port=port, path="/health", health_type="http")
            result = await checker.check()
            assert result is False
        finally:
            server.close()
            await server.wait_closed()

    @pytest.mark.asyncio
    async def test_tcp_health_check_success(self) -> None:
        port = _find_free_port()

        async def _handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writer.close()

        server = await asyncio.start_server(_handler, "127.0.0.1", port)
        try:
            checker = HealthChecker(port=port, path="/health", health_type="tcp")
            result = await checker.check()
            assert result is True
        finally:
            server.close()
            await server.wait_closed()

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_unreachable(self) -> None:
        port = _find_free_port()
        checker = HealthChecker(port=port, path="/health", health_type="tcp")
        result = await checker.check()
        assert result is False

    @pytest.mark.asyncio
    async def test_http_health_check_custom_path(self) -> None:
        port = _find_free_port()
        received_path = ""

        async def _handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            nonlocal received_path
            request_line = await reader.readline()
            received_path = request_line.decode().split(" ")[1]
            await reader.readuntil(b"\r\n\r\n")
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(_handler, "127.0.0.1", port)
        try:
            checker = HealthChecker(port=port, path="/custom/ready", health_type="http")
            await checker.check()
            assert received_path == "/custom/ready"
        finally:
            server.close()
            await server.wait_closed()

    @pytest.mark.asyncio
    async def test_tcp_health_check_port(self) -> None:
        port = _find_free_port()

        async def _handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writer.close()

        server = await asyncio.start_server(_handler, "127.0.0.1", port)
        try:
            checker = HealthChecker(port=port, path="/health", health_type="tcp")
            result = await checker.check()
            assert result is True
        finally:
            server.close()
            await server.wait_closed()

        # After server closes, same port should be unreachable
        result = await checker.check()
        assert result is False
