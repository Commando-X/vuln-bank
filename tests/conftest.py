import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pytest

from config import load_config


@dataclass
class MockRequestRecord:
    method: str = "GET"
    path: str = "/"
    headers: dict = field(default_factory=dict)
    body: Optional[str] = None
    response_status: int = 200
    response_headers: dict = field(default_factory=dict)
    response_body: str = ""


class MockScoringContext:
    def __init__(
        self,
        request_log: list[MockRequestRecord] | None = None,
        stored: dict[str, Any] | None = None,
        files: dict[str, str] | None = None,
    ):
        self._request_log = request_log or []
        self._stored = stored or {}
        self._files = files or {}
        self._exec_results: dict[str, Any] = {}

    def get_request_log(self) -> list[MockRequestRecord]:
        return self._request_log

    def get_stored(self, key: str, default: Any = None) -> Any:
        return self._stored.get(key, default)

    def read_file(self, path: str) -> str:
        if path not in self._files:
            raise FileNotFoundError(path)
        return self._files[path]

    async def exec(self, *args) -> Any:
        key = " ".join(args)
        return self._exec_results.get(key, "")


@pytest.fixture
def mock_ctx():
    def _factory(**kwargs):
        return MockScoringContext(**kwargs)
    return _factory


@pytest.fixture
def make_request():
    def _factory(**kwargs):
        return MockRequestRecord(**kwargs)
    return _factory


@pytest.fixture
def default_config():
    config_path = Path(__file__).parent.parent / "configs" / "default.json"
    with open(config_path) as f:
        return json.load(f)
