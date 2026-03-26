from __future__ import annotations

import pytest

from swigdojo_target.otel import OtelCollector


class TestOtelCollector:
    def test_get_traces_returns_empty_list_initially(self) -> None:
        collector = OtelCollector()
        assert collector.get_traces() == []

    def test_ingest_traces_stores_spans(self) -> None:
        collector = OtelCollector()
        data = {
            "resourceSpans": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "my-app"}}]},
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": "abc123",
                                    "spanId": "span1",
                                    "name": "GET /api",
                                    "kind": 2,
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        collector.ingest_traces(data)
        traces = collector.get_traces()
        assert len(traces) == 1
        assert traces[0]["name"] == "GET /api"
        assert traces[0]["traceId"] == "abc123"

    def test_ingest_traces_flattens_resource_spans(self) -> None:
        collector = OtelCollector()
        data = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "my-app"}},
                            {"key": "service.version", "value": {"stringValue": "1.0"}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {"traceId": "t1", "spanId": "s1", "name": "op1"},
                            ]
                        }
                    ],
                }
            ]
        }
        collector.ingest_traces(data)
        traces = collector.get_traces()
        assert len(traces) == 1
        assert traces[0]["resource.service.name"] == "my-app"
        assert traces[0]["resource.service.version"] == "1.0"

    def test_ingest_traces_handles_multiple_calls(self) -> None:
        collector = OtelCollector()
        data1 = {
            "resourceSpans": [
                {
                    "resource": {"attributes": []},
                    "scopeSpans": [
                        {"spans": [{"traceId": "t1", "spanId": "s1", "name": "op1"}]}
                    ],
                }
            ]
        }
        data2 = {
            "resourceSpans": [
                {
                    "resource": {"attributes": []},
                    "scopeSpans": [
                        {"spans": [{"traceId": "t2", "spanId": "s2", "name": "op2"}]}
                    ],
                }
            ]
        }
        collector.ingest_traces(data1)
        collector.ingest_traces(data2)
        traces = collector.get_traces()
        assert len(traces) == 2
        names = {t["name"] for t in traces}
        assert names == {"op1", "op2"}

    def test_ingest_traces_handles_empty_resource_spans(self) -> None:
        collector = OtelCollector()
        collector.ingest_traces({"resourceSpans": []})
        assert collector.get_traces() == []

    def test_ingest_traces_handles_multiple_scope_spans(self) -> None:
        collector = OtelCollector()
        data = {
            "resourceSpans": [
                {
                    "resource": {"attributes": []},
                    "scopeSpans": [
                        {"spans": [{"traceId": "t1", "spanId": "s1", "name": "op1"}]},
                        {"spans": [{"traceId": "t2", "spanId": "s2", "name": "op2"}]},
                    ],
                }
            ]
        }
        collector.ingest_traces(data)
        assert len(collector.get_traces()) == 2

    def test_ingest_traces_handles_missing_resource(self) -> None:
        collector = OtelCollector()
        data = {
            "resourceSpans": [
                {
                    "scopeSpans": [
                        {"spans": [{"traceId": "t1", "spanId": "s1", "name": "op1"}]}
                    ],
                }
            ]
        }
        collector.ingest_traces(data)
        traces = collector.get_traces()
        assert len(traces) == 1
        assert traces[0]["name"] == "op1"
