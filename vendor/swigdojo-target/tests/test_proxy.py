from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from starlette.testclient import TestClient

from swigdojo_target.proxy import create_proxy_app
from swigdojo_target.scoring import ScoringContext
from swigdojo_target.wrapper import TargetWrapper


def _make_wrapper(**kwargs) -> TargetWrapper:
    defaults = dict(command="echo hello", health_port=3000, proxy=True)
    defaults.update(kwargs)
    return TargetWrapper(**defaults)


def _mock_response(
    status: int = 200, content: bytes = b"ok", headers: dict | None = None
) -> httpx.Response:
    return httpx.Response(status_code=status, content=content, headers=headers or {})


def _patch_upstream(mock_cls, response: httpx.Response) -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.aclose = AsyncMock()
    mock_cls.return_value = mock_client
    return mock_client


class TestProxyForwarding:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_forwards_get_request_to_upstream(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        mock_client = _patch_upstream(mock_cls, _mock_response(200, b"get response"))

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        response = client.get("/api/data")

        assert response.status_code == 200
        assert response.content == b"get response"
        mock_client.request.assert_awaited_once()
        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "/api/data"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_forwards_post_request_to_upstream(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        mock_client = _patch_upstream(mock_cls, _mock_response(200, b"post response"))

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        response = client.post("/api/submit", content=b"request body")

        assert response.status_code == 200
        mock_client.request.assert_awaited_once()
        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["method"] == "POST"
        assert kwargs["content"] == b"request body"


class TestTrafficRecording:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_records_request_in_log(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.post("/api/action", content=b"payload")

        log = wrapper._proxy_recorder.get_log()
        assert len(log) == 1
        assert log[0].method == "POST"
        assert log[0].path == "/api/action"
        assert log[0].body == b"payload"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_records_response_in_log(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response(201, b"created"))

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.post("/api/items")

        log = wrapper._proxy_recorder.get_log()
        assert len(log) == 1
        assert log[0].response_status == 201
        assert log[0].response_body == b"created"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_multiple_requests_recorded_in_order(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/first")
        client.get("/second")
        client.get("/third")

        log = wrapper._proxy_recorder.get_log()
        assert len(log) == 3
        assert log[0].path == "/first"
        assert log[1].path == "/second"
        assert log[2].path == "/third"


class TestTrafficReset:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    @pytest.mark.anyio
    async def test_reset_clears_recorded_traffic(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/first")
        client.post("/second", content=b"data")

        assert len(wrapper._proxy_recorder.get_log()) == 2

        await wrapper._proxy_recorder.reset()

        assert wrapper._proxy_recorder.get_log() == []


class TestTransparency:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_does_not_modify_request_headers(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        mock_client = _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/test", headers={"X-Custom": "value123"})

        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["headers"]["x-custom"] == "value123"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_does_not_modify_response_body(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        body = b'{"key": "value", "nested": {"a": 1}}'
        _patch_upstream(mock_cls, _mock_response(200, body))

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        response = client.get("/data")

        assert response.content == body

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_does_not_modify_response_status(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response(418, b"teapot"))

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        response = client.get("/brew")

        assert response.status_code == 418


class TestLocationRewriting:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_rewrites_location_header_to_remove_upstream_base(self, mock_cls) -> None:
        wrapper = _make_wrapper(health_port=9998)
        _patch_upstream(
            mock_cls,
            _mock_response(302, b"", headers={"location": "http://localhost:9998/app/login"}),
        )

        app = create_proxy_app(wrapper)
        client = TestClient(app, follow_redirects=False)
        response = client.get("/app")

        assert response.status_code == 302
        assert response.headers["location"] == "/app/login"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_preserves_location_header_for_external_urls(self, mock_cls) -> None:
        wrapper = _make_wrapper(health_port=9998)
        _patch_upstream(
            mock_cls,
            _mock_response(302, b"", headers={"location": "https://example.com/login"}),
        )

        app = create_proxy_app(wrapper)
        client = TestClient(app, follow_redirects=False)
        response = client.get("/oauth")

        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/login"


class TestPathSanitization:
    def test_sanitize_collapses_double_slashes(self) -> None:
        from swigdojo_target.proxy import _sanitize_path

        assert _sanitize_path("//evil.com/foo") == "/evil.com/foo"

    def test_sanitize_preserves_normal_path(self) -> None:
        from swigdojo_target.proxy import _sanitize_path

        assert _sanitize_path("/api/data") == "/api/data"

    def test_sanitize_handles_empty_path(self) -> None:
        from swigdojo_target.proxy import _sanitize_path

        assert _sanitize_path("") == "/"


class TestQueryStringForwarding:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_forwards_query_string_to_upstream(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        mock_client = _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/api/data?page=1&limit=10")

        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["url"] == "/api/data?page=1&limit=10"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_records_query_string_in_log(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/api/data?key=value")

        log = wrapper._proxy_recorder.get_log()
        assert len(log) == 1
        assert log[0].path == "/api/data?key=value"

    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_no_query_string_omits_question_mark(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        mock_client = _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/api/data")

        kwargs = mock_client.request.call_args.kwargs
        assert kwargs["url"] == "/api/data"


class TestProtocolIntegration:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_protocol_endpoints_not_proxied(self, mock_cls) -> None:
        _patch_upstream(mock_cls, _mock_response())
        wrapper = _make_wrapper()

        @wrapper.objective(name="check", description="Check", public=True)
        async def check(ctx):
            return True

        from swigdojo_target.health import HealthChecker
        from swigdojo_target.protocol import create_app
        from swigdojo_target.reporter import ObjectiveReporter

        hc = MagicMock(spec=HealthChecker)
        hc.check = AsyncMock(return_value=True)
        rp = AsyncMock(spec=ObjectiveReporter)
        rp.report_objective_complete = AsyncMock()

        app = create_app(wrapper, hc, rp)
        client = TestClient(app)

        client.get("/health")
        client.get("/objectives")
        client.post("/settle")

        log = wrapper._proxy_recorder.get_log()
        assert len(log) == 0


class TestScoringIntegration:
    @patch("swigdojo_target.proxy.httpx.AsyncClient")
    def test_get_request_log_returns_records_in_proxy_mode(self, mock_cls) -> None:
        wrapper = _make_wrapper()
        _patch_upstream(mock_cls, _mock_response())

        app = create_proxy_app(wrapper)
        client = TestClient(app)
        client.get("/api/test")

        ctx = ScoringContext(
            health_port=wrapper.health_port, proxy=wrapper._proxy_recorder
        )
        log = ctx.get_request_log()

        assert len(log) == 1
        assert log[0].method == "GET"
        assert log[0].path == "/api/test"
