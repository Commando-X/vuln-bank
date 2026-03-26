from __future__ import annotations

import threading


class OtelCollector:
    def __init__(self) -> None:
        self._spans: list[dict] = []
        self._lock = threading.Lock()

    def ingest_traces(self, data: dict) -> None:
        spans: list[dict] = []
        for resource_span in data.get("resourceSpans", []):
            resource = resource_span.get("resource", {})
            resource_attrs = {}
            for attr in resource.get("attributes", []):
                key = attr.get("key", "")
                value = attr.get("value", {})
                for type_key, type_val in value.items():
                    resource_attrs[f"resource.{key}"] = type_val
                    break

            for scope_span in resource_span.get("scopeSpans", []):
                for span in scope_span.get("spans", []):
                    flat = dict(span)
                    flat.update(resource_attrs)
                    spans.append(flat)

        with self._lock:
            self._spans.extend(spans)

    def get_traces(self) -> list[dict]:
        with self._lock:
            return list(self._spans)
