from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Any, Callable


_OBJECTIVE_NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")

_RESERVED_PATHS = frozenset({"/health", "/objectives", "/settle", "/otel/v1/traces"})


@dataclass
class RegisteredObjective:
    name: str
    description: str
    public: bool
    pass_threshold: float
    func: Callable[..., Any]


@dataclass
class RegisteredRoute:
    path: str
    methods: list[str]
    handler: Callable[..., Any]


class TargetWrapper:
    def __init__(
        self,
        command: str | list[str],
        health_port: int,
        health_path: str = "/health",
        health_type: str = "http",
        proxy: bool = True,
        settle_timeout: int = 60,
        otel: bool = False,
    ) -> None:
        self.command = command if isinstance(command, str) else " ".join(command)
        self.health_port = health_port
        self.health_path = health_path
        self.health_type = health_type
        self.proxy = proxy
        self.settle_timeout = settle_timeout
        self.otel = otel
        self.objectives: dict[str, RegisteredObjective] = {}
        self.routes: list[RegisteredRoute] = []
        self._storage: dict[str, Any] = {}
        self._storage_lock = threading.Lock()
        self._proxy_recorder: Any | None = None

    def objective(
        self, name: str, description: str, public: bool, pass_threshold: float = 1.0
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        if not _OBJECTIVE_NAME_PATTERN.match(name):
            raise ValueError(
                f"Invalid objective name '{name}': must match [a-z0-9-]+"
            )

        if name in self.objectives:
            raise ValueError(
                f"Duplicate objective name '{name}': already registered"
            )

        if not (0.0 <= pass_threshold <= 1.0):
            raise ValueError(
                f"pass_threshold must be between 0.0 and 1.0, got {pass_threshold}"
            )

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.objectives[name] = RegisteredObjective(
                name=name,
                description=description,
                public=public,
                pass_threshold=pass_threshold,
                func=func,
            )
            return func

        return decorator

    def route(
        self, path: str, methods: list[str] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        if path in _RESERVED_PATHS:
            raise ValueError(
                f"Path '{path}' conflicts with reserved protocol path"
            )

        if any(r.path == path for r in self.routes):
            raise ValueError(
                f"Duplicate route path '{path}': already registered"
            )

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(
                RegisteredRoute(
                    path=path,
                    methods=methods or ["GET"],
                    handler=func,
                )
            )
            return func

        return decorator

    def store(self, key: str, value: Any) -> None:
        with self._storage_lock:
            self._storage[key] = value

    def get_stored(self, key: str, default: Any = None) -> Any:
        with self._storage_lock:
            return self._storage.get(key, default)

    def run(self) -> None:
        from .config import load_config

        load_config()

        from .server import serve

        serve(self)
