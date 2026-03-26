from __future__ import annotations

import asyncio


class ProcessManager:
    def __init__(self, command: str) -> None:
        self.command = command
        self._process: asyncio.subprocess.Process | None = None
        self._output_tasks: list[asyncio.Task[None]] = []
        self._monitor_task: asyncio.Task[None] | None = None
        self._stopping = False

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def start(self) -> None:
        self._process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if self._process.stdout is not None:
            self._output_tasks.append(
                asyncio.create_task(self._stream_output(self._process.stdout))
            )
        if self._process.stderr is not None:
            self._output_tasks.append(
                asyncio.create_task(self._stream_output(self._process.stderr))
            )

        self._monitor_task = asyncio.create_task(self._monitor())

    async def stop(self) -> None:
        self._stopping = True
        if self._process is not None and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()

        for task in self._output_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self._monitor_task is not None:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _stream_output(self, stream: asyncio.StreamReader) -> None:
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode().rstrip("\n")
            print(f"[upstream] {text}", flush=True)

    async def _monitor(self) -> None:
        if self._process is None:
            return

        returncode = await self._process.wait()
        if returncode != 0 and not self._stopping:
            print(
                f"[upstream] process exited unexpectedly with code {returncode}",
                flush=True,
            )
