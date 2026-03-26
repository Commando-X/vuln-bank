from __future__ import annotations

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
_DEFAULT_INITIAL_DELAY = 1.0
_DEFAULT_MAX_DELAY = 8.0
_DEFAULT_TOTAL_BUDGET = 30.0


class ObjectiveReporter:
    def __init__(
        self,
        api_url: str,
        experiment_id: str,
        run_id: str,
        transport: httpx.BaseTransport | None = None,
        total_budget: float = _DEFAULT_TOTAL_BUDGET,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._experiment_id = experiment_id
        self._run_id = run_id
        self._total_budget = total_budget
        client_kwargs: dict = {"timeout": httpx.Timeout(10.0)}
        if transport is not None:
            client_kwargs["transport"] = transport
        self._client = httpx.AsyncClient(**client_kwargs)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> ObjectiveReporter:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _post_with_retry(
        self, url: str, *, json: dict | None = None, label: str = "request"
    ) -> None:
        delay = _DEFAULT_INITIAL_DELAY
        start = time.monotonic()

        while True:
            try:
                response = await self._client.post(url, json=json)
                if response.status_code not in _RETRYABLE_STATUS_CODES:
                    if response.status_code >= 400:
                        logger.error(
                            "Failed %s: HTTP %d",
                            label,
                            response.status_code,
                        )
                    return
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                pass

            elapsed = time.monotonic() - start
            if elapsed + delay > self._total_budget:
                logger.error(
                    "Failed %s after %.1fs",
                    label,
                    elapsed,
                )
                return

            await asyncio.sleep(delay)

            # Sawtooth backoff: double until max, then reset
            delay *= 2
            if delay > _DEFAULT_MAX_DELAY:
                delay = _DEFAULT_INITIAL_DELAY

    async def report_objective_complete(self, objective_name: str) -> None:
        url = (
            f"{self._api_url}/api/experiments/runs/{self._experiment_id}/"
            f"target-runs/{self._run_id}/objectives/{objective_name}/complete"
        )
        await self._post_with_retry(
            url, label=f"reporting objective '{objective_name}' complete"
        )

    async def report_objective_score(self, objective_name: str, score: float) -> None:
        url = (
            f"{self._api_url}/api/experiments/runs/{self._experiment_id}/"
            f"target-runs/{self._run_id}/objectives/{objective_name}/score"
        )
        await self._post_with_retry(
            url, json={"score": score}, label=f"reporting objective '{objective_name}' score"
        )
