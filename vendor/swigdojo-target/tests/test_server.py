from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swigdojo_target.wrapper import TargetWrapper


def _make_wrapper(**kwargs) -> TargetWrapper:
    defaults = dict(command="echo hello", health_port=3000)
    defaults.update(kwargs)
    return TargetWrapper(**defaults)


class TestServe:
    def test_serve_validates_config(self) -> None:
        with patch("swigdojo_target.server.load_config") as mock_load_config:
            mock_load_config.side_effect = ValueError(
                "Missing required environment variables"
            )

            from swigdojo_target.server import serve

            with pytest.raises(ValueError, match="Missing required"):
                serve(_make_wrapper())

            mock_load_config.assert_called_once()

    @patch("swigdojo_target.server.uvicorn.Server")
    @patch("swigdojo_target.server.ObjectiveReporter")
    @patch("swigdojo_target.server.ProcessManager")
    @patch("swigdojo_target.server.load_config")
    def test_serve_starts_subprocess(
        self,
        mock_load_config: MagicMock,
        mock_process_cls: MagicMock,
        mock_reporter_cls: MagicMock,
        mock_server_cls: MagicMock,
    ) -> None:
        from swigdojo_target.config import TargetConfig
        from swigdojo_target.server import serve

        mock_load_config.return_value = TargetConfig(
            api_url="http://swigdojo.test",
            experiment_id="exp-1",
            run_id="run-1",
            wrapper_port=8080,
        )

        mock_process = MagicMock()
        mock_process.start = AsyncMock()
        mock_process.stop = AsyncMock()
        mock_process_cls.return_value = mock_process

        mock_reporter = MagicMock()
        mock_reporter.close = AsyncMock()
        mock_reporter_cls.return_value = mock_reporter

        mock_server = MagicMock()
        mock_server.serve = AsyncMock()
        mock_server_cls.return_value = mock_server

        serve(_make_wrapper())

        mock_process_cls.assert_called_once_with("echo hello")
        mock_process.start.assert_awaited_once()
