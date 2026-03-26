from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from swigdojo_target.health import HealthChecker
from swigdojo_target.protocol import create_app
from swigdojo_target.reporter import ObjectiveReporter
from swigdojo_target.wrapper import TargetWrapper


def _make_wrapper(**kwargs) -> TargetWrapper:
    defaults = dict(command="echo hello", health_port=3000)
    defaults.update(kwargs)
    return TargetWrapper(**defaults)


def _make_app(
    wrapper: TargetWrapper,
    health_checker: HealthChecker | None = None,
    reporter: ObjectiveReporter | None = None,
) -> TestClient:
    hc = health_checker or MagicMock(spec=HealthChecker)
    rp = reporter or AsyncMock(spec=ObjectiveReporter)

    otel_collector = None
    if wrapper.otel:
        from swigdojo_target.otel import OtelCollector

        otel_collector = OtelCollector()

    app = create_app(wrapper, hc, rp, otel_collector=otel_collector)
    return TestClient(app)


class TestObjectivesEndpoint:
    def test_objectives_returns_json_array(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="check-login", description="Verify login works", public=True)
        def score_login(ctx):
            return True

        client = _make_app(wrapper)
        response = client.get("/objectives")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "check-login"
        assert data[0]["description"] == "Verify login works"
        assert data[0]["isPublic"] is True

    def test_objectives_includes_pass_threshold(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(
            name="check-login", description="Verify login works", public=True, pass_threshold=0.8
        )
        def score_login(ctx):
            return 0.9

        client = _make_app(wrapper)
        response = client.get("/objectives")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["passThreshold"] == 0.8

    def test_objectives_default_pass_threshold(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="check-login", description="Verify login works", public=True)
        def score_login(ctx):
            return 1.0

        client = _make_app(wrapper)
        response = client.get("/objectives")

        assert response.status_code == 200
        data = response.json()
        assert data[0]["passThreshold"] == 1.0

    def test_objectives_empty_when_none_registered(self) -> None:
        wrapper = _make_wrapper()
        client = _make_app(wrapper)
        response = client.get("/objectives")

        assert response.status_code == 200
        assert response.json() == []


class TestHealthEndpoint:
    def test_health_returns_503_when_upstream_not_ready(self) -> None:
        wrapper = _make_wrapper()
        hc = MagicMock(spec=HealthChecker)
        hc.check = AsyncMock(return_value=False)

        client = _make_app(wrapper, health_checker=hc)
        response = client.get("/health")

        assert response.status_code == 503

    def test_health_returns_200_when_upstream_ready(self) -> None:
        wrapper = _make_wrapper()
        hc = MagicMock(spec=HealthChecker)
        hc.check = AsyncMock(return_value=True)

        client = _make_app(wrapper, health_checker=hc)
        response = client.get("/health")

        assert response.status_code == 200


class TestSettleEndpoint:
    def test_settle_runs_all_scoring_functions(self) -> None:
        wrapper = _make_wrapper()
        called = []

        @wrapper.objective(name="obj-a", description="A", public=True)
        async def score_a(ctx):
            called.append("a")
            return True

        @wrapper.objective(name="obj-b", description="B", public=True)
        async def score_b(ctx):
            called.append("b")
            return True

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        response = client.post("/settle")

        assert response.status_code == 200
        assert "a" in called
        assert "b" in called

    def test_settle_reports_truthy_objectives_as_score(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-pass", description="Passes", public=True)
        async def score_pass(ctx):
            return True

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-pass", 1.0)

    def test_settle_reports_falsy_objectives_as_zero(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-fail", description="Fails", public=True)
        async def score_fail(ctx):
            return False

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-fail", 0.0)

    def test_settle_continues_after_scoring_exception(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-error", description="Errors", public=True)
        async def score_error(ctx):
            raise RuntimeError("boom")

        @wrapper.objective(name="obj-ok", description="OK", public=True)
        async def score_ok(ctx):
            return True

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        response = client.post("/settle")

        assert response.status_code == 200
        assert reporter.report_objective_score.await_count == 2

    def test_settle_cancels_on_timeout(self) -> None:
        wrapper = _make_wrapper(settle_timeout=1)

        @wrapper.objective(name="obj-slow", description="Slow", public=True)
        async def score_slow(ctx):
            await asyncio.sleep(999)
            return True

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        response = client.post("/settle")

        assert response.status_code == 200
        reporter.report_objective_score.assert_awaited_once_with("obj-slow", 0.0)

    def test_settle_handles_sync_scoring_functions(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-sync", description="Sync", public=True)
        def score_sync(ctx):
            return True

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-sync", 1.0)

    def test_settle_reports_float_score(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-score", description="Scores", public=True)
        async def score_it(ctx):
            return 0.75

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-score", 0.75)

    def test_settle_reports_zero_for_exception(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-error", description="Errors", public=True)
        async def score_error(ctx):
            raise RuntimeError("boom")

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-error", 0.0)

    def test_settle_reports_zero_for_timeout(self) -> None:
        wrapper = _make_wrapper(settle_timeout=1)

        @wrapper.objective(name="obj-slow", description="Slow", public=True)
        async def score_slow(ctx):
            await asyncio.sleep(999)
            return 1.0

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-slow", 0.0)

    def test_settle_clamps_score_above_one(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-high", description="High", public=True)
        async def score_high(ctx):
            return 1.5

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-high", 1.0)

    def test_settle_clamps_score_below_zero(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-low", description="Low", public=True)
        async def score_low(ctx):
            return -0.5

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        reporter.report_objective_score.assert_awaited_once_with("obj-low", 0.0)

    def test_settle_reports_all_objectives(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.objective(name="obj-a", description="A", public=True)
        async def score_a(ctx):
            return 0.5

        @wrapper.objective(name="obj-b", description="B", public=True)
        async def score_b(ctx):
            return 0.0

        reporter = AsyncMock(spec=ObjectiveReporter)
        reporter.report_objective_score = AsyncMock()
        client = _make_app(wrapper, reporter=reporter)
        client.post("/settle")

        assert reporter.report_objective_score.await_count == 2
        calls = reporter.report_objective_score.await_args_list
        call_dict = {c.args[0]: c.args[1] for c in calls}
        assert call_dict["obj-a"] == 0.5
        assert call_dict["obj-b"] == 0.0

    def test_settle_returns_200(self) -> None:
        wrapper = _make_wrapper()
        client = _make_app(wrapper)
        response = client.post("/settle")

        assert response.status_code == 200


class TestCustomRoutes:
    def test_custom_route_served(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.route("/telemetry", methods=["POST"])
        async def handle_telemetry(request):
            from starlette.responses import JSONResponse

            return JSONResponse({"status": "ok"})

        client = _make_app(wrapper)
        response = client.post("/telemetry", json={"data": 1})
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_custom_route_does_not_override_protocol(self) -> None:
        wrapper = _make_wrapper()

        @wrapper.route("/custom", methods=["GET"])
        async def handle_custom(request):
            from starlette.responses import JSONResponse

            return JSONResponse({"source": "custom"})

        hc = MagicMock(spec=HealthChecker)
        hc.check = AsyncMock(return_value=True)

        client = _make_app(wrapper, health_checker=hc)
        response = client.get("/health")
        assert response.status_code == 200

    def test_custom_route_before_proxy(self) -> None:
        wrapper = _make_wrapper(proxy=True)

        @wrapper.route("/custom", methods=["GET"])
        async def handle_custom(request):
            from starlette.responses import JSONResponse

            return JSONResponse({"source": "custom"})

        client = _make_app(wrapper)
        response = client.get("/custom")
        assert response.status_code == 200
        assert response.json() == {"source": "custom"}


class TestOtelEndpoint:
    def test_otel_endpoint_accepts_otlp_traces(self) -> None:
        wrapper = _make_wrapper(otel=True)
        client = _make_app(wrapper)
        data = {
            "resourceSpans": [
                {
                    "resource": {"attributes": []},
                    "scopeSpans": [
                        {"spans": [{"traceId": "t1", "spanId": "s1", "name": "op1"}]}
                    ],
                }
            ]
        }
        response = client.post("/otel/v1/traces", json=data)
        assert response.status_code == 200

    def test_otel_endpoint_not_mounted_when_disabled(self) -> None:
        wrapper = _make_wrapper(otel=False, proxy=False)
        client = _make_app(wrapper)
        response = client.post("/otel/v1/traces", json={"resourceSpans": []})
        assert response.status_code == 404 or response.status_code == 405

    def test_otel_endpoint_returns_200_on_valid_data(self) -> None:
        wrapper = _make_wrapper(otel=True)
        client = _make_app(wrapper)
        data = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "test"}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {"traceId": "abc", "spanId": "def", "name": "GET /"},
                                {"traceId": "abc", "spanId": "ghi", "name": "POST /api"},
                            ]
                        }
                    ],
                }
            ]
        }
        response = client.post("/otel/v1/traces", json=data)
        assert response.status_code == 200
