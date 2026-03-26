from __future__ import annotations

import asyncio
import inspect
import logging
import traceback
from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from swigdojo_target.health import HealthChecker
from swigdojo_target.reporter import ObjectiveReporter
from swigdojo_target.scoring import ScoringContext
from swigdojo_target.wrapper import TargetWrapper

if TYPE_CHECKING:
    from swigdojo_target.otel import OtelCollector

logger = logging.getLogger(__name__)


def create_app(
    wrapper: TargetWrapper,
    health_checker: HealthChecker,
    reporter: ObjectiveReporter,
    otel_collector: "OtelCollector | None" = None,
) -> Starlette:
    async def health(request: Request) -> Response:
        healthy = await health_checker.check()
        if healthy:
            return Response(status_code=200)
        return Response(status_code=503)

    async def objectives(request: Request) -> JSONResponse:
        result = [
            {
                "name": obj.name,
                "description": obj.description,
                "isPublic": obj.public,
                "passThreshold": obj.pass_threshold,
            }
            for obj in wrapper.objectives.values()
        ]
        return JSONResponse(result)

    async def settle(request: Request) -> Response:
        async def _run_scoring(name: str, func, ctx: ScoringContext) -> tuple[str, float]:
            try:
                if inspect.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(ctx), timeout=wrapper.settle_timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(func, ctx), timeout=wrapper.settle_timeout
                    )
                return (name, max(0.0, min(1.0, float(result))))
            except asyncio.TimeoutError:
                logger.warning("Scoring function '%s' cancelled after timeout", name)
                return (name, 0.0)
            except Exception:
                logger.error(
                    "Scoring function '%s' raised an exception:\n%s",
                    name,
                    traceback.format_exc(),
                )
                return (name, 0.0)

        async with ScoringContext(
            health_port=wrapper.health_port,
            proxy=wrapper._proxy_recorder,
            otel_collector=otel_collector,
            storage_getter=wrapper.get_stored,
        ) as ctx:
            tasks = [
                _run_scoring(obj.name, obj.func, ctx)
                for obj in wrapper.objectives.values()
            ]
            results = await asyncio.gather(*tasks)

        for name, score in results:
            await reporter.report_objective_score(name, score)

        if wrapper._proxy_recorder is not None:
            await wrapper._proxy_recorder.reset()

        return Response(status_code=200)

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/objectives", objectives, methods=["GET"]),
        Route("/settle", settle, methods=["POST"]),
    ]

    if otel_collector is not None:
        async def otel_traces(request: Request) -> Response:
            data = await request.json()
            otel_collector.ingest_traces(data)
            return Response(status_code=200)

        routes.append(Route("/otel/v1/traces", otel_traces, methods=["POST"]))

    for registered_route in wrapper.routes:
        routes.append(
            Route(
                registered_route.path,
                registered_route.handler,
                methods=registered_route.methods,
            )
        )

    if wrapper.proxy:
        from swigdojo_target.proxy import create_proxy_app

        proxy_app = create_proxy_app(wrapper)
        routes.append(Mount("/", app=proxy_app))

    return Starlette(routes=routes)
