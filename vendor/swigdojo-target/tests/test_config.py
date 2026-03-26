import os

import pytest

from swigdojo_target.config import load_config


class TestLoadConfig:
    def test_reads_all_env_vars(self, monkeypatch):
        monkeypatch.setenv("SWIGDOJO_API_URL", "http://localhost:5000")
        monkeypatch.setenv("SWIGDOJO_EXPERIMENT_ID", "exp-123")
        monkeypatch.setenv("SWIGDOJO_RUN_ID", "run-456")

        config = load_config()

        assert config.api_url == "http://localhost:5000"
        assert config.experiment_id == "exp-123"
        assert config.run_id == "run-456"

    def test_fails_fast_when_api_url_missing(self, monkeypatch):
        monkeypatch.setenv("SWIGDOJO_EXPERIMENT_ID", "exp-123")
        monkeypatch.setenv("SWIGDOJO_RUN_ID", "run-456")
        monkeypatch.delenv("SWIGDOJO_API_URL", raising=False)

        with pytest.raises(ValueError, match="SWIGDOJO_API_URL"):
            load_config()

    def test_fails_fast_when_experiment_id_missing(self, monkeypatch):
        monkeypatch.setenv("SWIGDOJO_API_URL", "http://localhost:5000")
        monkeypatch.setenv("SWIGDOJO_RUN_ID", "run-456")
        monkeypatch.delenv("SWIGDOJO_EXPERIMENT_ID", raising=False)

        with pytest.raises(ValueError, match="SWIGDOJO_EXPERIMENT_ID"):
            load_config()

    def test_fails_fast_when_run_id_missing(self, monkeypatch):
        monkeypatch.setenv("SWIGDOJO_API_URL", "http://localhost:5000")
        monkeypatch.setenv("SWIGDOJO_EXPERIMENT_ID", "exp-123")
        monkeypatch.delenv("SWIGDOJO_RUN_ID", raising=False)

        with pytest.raises(ValueError, match="SWIGDOJO_RUN_ID"):
            load_config()

    def test_lists_all_missing_vars_in_error(self, monkeypatch):
        monkeypatch.delenv("SWIGDOJO_API_URL", raising=False)
        monkeypatch.delenv("SWIGDOJO_EXPERIMENT_ID", raising=False)
        monkeypatch.delenv("SWIGDOJO_RUN_ID", raising=False)

        with pytest.raises(ValueError) as exc_info:
            load_config()

        message = str(exc_info.value)
        assert "SWIGDOJO_API_URL" in message
        assert "SWIGDOJO_EXPERIMENT_ID" in message
        assert "SWIGDOJO_RUN_ID" in message

    def test_default_wrapper_port(self, monkeypatch):
        monkeypatch.setenv("SWIGDOJO_API_URL", "http://localhost:5000")
        monkeypatch.setenv("SWIGDOJO_EXPERIMENT_ID", "exp-123")
        monkeypatch.setenv("SWIGDOJO_RUN_ID", "run-456")
        monkeypatch.delenv("SWIGDOJO_WRAPPER_PORT", raising=False)

        config = load_config()

        assert config.wrapper_port == 8787

    def test_custom_wrapper_port(self, monkeypatch):
        monkeypatch.setenv("SWIGDOJO_API_URL", "http://localhost:5000")
        monkeypatch.setenv("SWIGDOJO_EXPERIMENT_ID", "exp-123")
        monkeypatch.setenv("SWIGDOJO_RUN_ID", "run-456")
        monkeypatch.setenv("SWIGDOJO_WRAPPER_PORT", "9090")

        config = load_config()

        assert config.wrapper_port == 9090
