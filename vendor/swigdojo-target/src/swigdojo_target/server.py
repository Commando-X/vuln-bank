from __future__ import annotations

import asyncio
import logging
import signal

import uvicorn

from swigdojo_target.config import load_config
from swigdojo_target.health import HealthChecker
from swigdojo_target.process import ProcessManager
from swigdojo_target.protocol import create_app
from swigdojo_target.reporter import ObjectiveReporter
from swigdojo_target.wrapper import TargetWrapper

logger = logging.getLogger(__name__)


async def _wait_for_healthy(health_checker: HealthChecker, timeout: float = 120.0) -> None:
    start = asyncio.get_event_loop().time()
    attempt = 0
    while True:
        attempt += 1
        healthy = await health_checker.check()
        if healthy:
            elapsed = asyncio.get_event_loop().time() - start
            logger.info("Upstream healthy after %.1fs (%d checks)", elapsed, attempt)
            return
        elapsed = asyncio.get_event_loop().time() - start
        if elapsed >= timeout:
            logger.warning("Upstream not healthy after %.1fs — continuing anyway", elapsed)
            return
        if attempt == 1:
            logger.info("Waiting for upstream to become healthy on port %d...", health_checker.port)
        elif attempt % 10 == 0:
            logger.info("Still waiting for upstream... (%.0fs elapsed)", elapsed)
        await asyncio.sleep(1.0)


def serve(wrapper: TargetWrapper) -> None:
    config = load_config()

    process = ProcessManager(wrapper.command)

    health_checker = HealthChecker(
        port=wrapper.health_port,
        path=wrapper.health_path,
        health_type=wrapper.health_type,
    )

    reporter = ObjectiveReporter(
        api_url=config.api_url,
        experiment_id=config.experiment_id,
        run_id=config.run_id,
    )

    otel_collector = None
    if wrapper.otel:
        from swigdojo_target.otel import OtelCollector

        otel_collector = OtelCollector()

    app = create_app(wrapper, health_checker, reporter, otel_collector=otel_collector)

    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=config.wrapper_port, log_level="info")
    )

    async def _run() -> None:
        await process.start()
        await _wait_for_healthy(health_checker)

        original_handler = signal.getsignal(signal.SIGTERM)

        def _handle_sigterm(signum: int, frame: object) -> None:
            server.should_exit = True

        signal.signal(signal.SIGTERM, _handle_sigterm)

        try:
            await server.serve()
        finally:
            await reporter.close()
            await process.stop()
            if callable(original_handler):
                signal.signal(signal.SIGTERM, original_handler)

    asyncio.run(_run())
