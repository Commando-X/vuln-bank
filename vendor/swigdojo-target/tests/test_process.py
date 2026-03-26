from __future__ import annotations

import asyncio

import pytest

from swigdojo_target.process import ProcessManager


@pytest.fixture
def manager() -> ProcessManager:
    return ProcessManager("echo hello")


class TestProcessManager:
    @pytest.mark.asyncio
    async def test_starts_subprocess_with_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        manager = ProcessManager("echo started")
        await manager.start()
        await asyncio.sleep(0.2)

        assert manager._process is not None
        assert manager._process.returncode == 0
        captured = capsys.readouterr()
        assert "[upstream] started" in captured.out

    @pytest.mark.asyncio
    async def test_captures_stdout_with_prefix(self, capsys: pytest.CaptureFixture[str]) -> None:
        manager = ProcessManager("echo hello-stdout")
        await manager.start()
        await asyncio.sleep(0.2)

        captured = capsys.readouterr()
        assert "[upstream] hello-stdout" in captured.out

    @pytest.mark.asyncio
    async def test_captures_stderr_with_prefix(self, capsys: pytest.CaptureFixture[str]) -> None:
        manager = ProcessManager("echo hello-stderr >&2")
        await manager.start()
        await asyncio.sleep(0.2)

        captured = capsys.readouterr()
        assert "[upstream] hello-stderr" in captured.out

    @pytest.mark.asyncio
    async def test_detects_unexpected_exit(self, capsys: pytest.CaptureFixture[str]) -> None:
        manager = ProcessManager("exit 42")
        await manager.start()
        await asyncio.sleep(0.2)

        captured = capsys.readouterr()
        assert "42" in captured.out
        assert manager.is_running is False

    @pytest.mark.asyncio
    async def test_is_running_true_while_process_alive(self) -> None:
        manager = ProcessManager("sleep 10")
        await manager.start()

        try:
            assert manager.is_running is True
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_is_running_false_after_exit(self) -> None:
        manager = ProcessManager("echo done")
        await manager.start()
        await asyncio.sleep(0.2)

        assert manager.is_running is False

    @pytest.mark.asyncio
    async def test_graceful_shutdown_on_sigterm(self) -> None:
        manager = ProcessManager("sleep 60")
        await manager.start()

        assert manager.is_running is True
        await manager.stop()

        assert manager.is_running is False
        assert manager._process is not None
        assert manager._process.returncode is not None
