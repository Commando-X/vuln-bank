from __future__ import annotations

import asyncio


class HealthChecker:
    def __init__(self, port: int, path: str, health_type: str) -> None:
        self.port = port
        self.path = path
        self.health_type = health_type

    async def check(self) -> bool:
        if self.health_type == "http":
            return await self._check_http()
        return await self._check_tcp()

    async def _check_http(self) -> bool:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", self.port),
                timeout=5.0,
            )
        except (OSError, asyncio.TimeoutError):
            return False

        try:
            request = (
                f"GET {self.path} HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{self.port}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )
            writer.write(request.encode())
            await writer.drain()

            status_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            parts = status_line.decode().split(" ", 2)
            if len(parts) >= 2:
                return parts[1] == "200"
            return False
        except (OSError, asyncio.TimeoutError):
            return False
        finally:
            writer.close()
            await writer.wait_closed()

    async def _check_tcp(self) -> bool:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", self.port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (OSError, asyncio.TimeoutError):
            return False
