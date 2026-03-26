from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from swigdojo_target.reporter import ObjectiveReporter


class TestReportsObjectiveComplete:
    @pytest.mark.asyncio
    async def test_reports_objective_complete(self) -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(204)
        )
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
        )
        await reporter.report_objective_complete("my-objective")
        # No exception means success


class TestRetryBehavior:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [500, 502, 503, 504])
    async def test_retries_on_retryable_status(self, status_code: int) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(status_code)
            return httpx.Response(204)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
        )
        await reporter.report_objective_complete("obj-1")
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_connection_error(self) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("Connection refused")
            return httpx.Response(204)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
        )
        await reporter.report_objective_complete("obj-1")
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_timeout(self) -> None:
        call_count = 0
        fake_time = 0.0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(503)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
            total_budget=30.0,
        )

        advances = iter([0.0, 1.0, 3.0, 7.0, 15.0, 16.0, 24.0, 25.0, 31.0])

        async def fake_sleep(duration: float) -> None:
            nonlocal fake_time
            fake_time = next(advances, fake_time + duration)

        def fake_monotonic() -> float:
            return fake_time

        with (
            patch("swigdojo_target.reporter.asyncio.sleep", side_effect=fake_sleep),
            patch("swigdojo_target.reporter.time.monotonic", side_effect=fake_monotonic),
        ):
            await reporter.report_objective_complete("obj-1")

        # Should have attempted multiple times but eventually gave up
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_sawtooth_backoff_resets(self) -> None:
        delays: list[float] = []
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(503)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
            total_budget=60.0,
        )

        fake_time = 0.0

        async def fake_sleep(duration: float) -> None:
            nonlocal fake_time
            delays.append(duration)
            fake_time += duration

        def fake_monotonic() -> float:
            return fake_time

        with (
            patch("swigdojo_target.reporter.asyncio.sleep", side_effect=fake_sleep),
            patch("swigdojo_target.reporter.time.monotonic", side_effect=fake_monotonic),
        ):
            await reporter.report_objective_complete("obj-1")

        # Sawtooth: 1 -> 2 -> 4 -> 8 -> reset to 1 -> 2 -> 4 -> 8 -> reset ...
        # Verify the pattern resets after reaching max delay
        assert len(delays) >= 5
        assert delays[0] == pytest.approx(1.0)
        assert delays[1] == pytest.approx(2.0)
        assert delays[2] == pytest.approx(4.0)
        assert delays[3] == pytest.approx(8.0)
        assert delays[4] == pytest.approx(1.0)  # reset!


class TestReportsObjectiveScore:
    @pytest.mark.asyncio
    async def test_reports_objective_score(self) -> None:
        captured_body = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_body
            captured_body = request.content
            return httpx.Response(204)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
        )
        await reporter.report_objective_score("my-objective", 0.75)

        import json
        body = json.loads(captured_body)
        assert body == {"score": 0.75}

    @pytest.mark.asyncio
    async def test_score_url_construction(self) -> None:
        captured_url = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_url
            captured_url = str(request.url)
            return httpx.Response(204)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-123",
            run_id="run-456",
            transport=transport,
        )
        await reporter.report_objective_score("check-auth", 0.5)
        assert captured_url == (
            "http://swigdojo.test/api/experiments/runs/exp-123/"
            "target-runs/run-456/objectives/check-auth/score"
        )

    @pytest.mark.asyncio
    async def test_score_retries_on_server_error(self) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(503)
            return httpx.Response(204)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            transport=transport,
        )
        await reporter.report_objective_score("obj-1", 0.9)
        assert call_count == 2


class TestUrlConstruction:
    @pytest.mark.asyncio
    async def test_posts_to_correct_url(self) -> None:
        captured_url = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_url
            captured_url = str(request.url)
            return httpx.Response(204)

        transport = httpx.MockTransport(handler)
        reporter = ObjectiveReporter(
            api_url="http://swigdojo.test",
            experiment_id="exp-123",
            run_id="run-456",
            transport=transport,
        )
        await reporter.report_objective_complete("check-auth")
        assert captured_url == (
            "http://swigdojo.test/api/experiments/runs/exp-123/"
            "target-runs/run-456/objectives/check-auth/complete"
        )
