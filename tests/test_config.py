import json
import os
import tempfile

import pytest

from config import load_config


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file and return its path."""
    def _factory(data: dict) -> str:
        path = tmp_path / "config.json"
        path.write_text(json.dumps(data))
        return str(path)
    return _factory


class TestLoadConfig:
    def test_loads_json_file(self, tmp_config, monkeypatch):
        data = {"llm": {"model": "gpt-4o"}, "auth": {"jwt_secret": "s3cret"}}
        path = tmp_config(data)
        monkeypatch.setenv("TARGET_CONFIG_PATH", path)
        config = load_config()
        assert config == data

    def test_env_var_override_string(self, tmp_config, monkeypatch):
        data = {"llm": {"model": "gpt-4o"}}
        path = tmp_config(data)
        monkeypatch.setenv("TARGET_CONFIG_PATH", path)
        monkeypatch.setenv("TARGET_CONFIG__LLM__MODEL", "deepseek-chat")
        config = load_config()
        assert config["llm"]["model"] == "deepseek-chat"

    def test_env_var_override_boolean(self, tmp_config, monkeypatch):
        data = {"llm": {"mock": False}}
        path = tmp_config(data)
        monkeypatch.setenv("TARGET_CONFIG_PATH", path)
        monkeypatch.setenv("TARGET_CONFIG__LLM__MOCK", "true")
        config = load_config()
        assert config["llm"]["mock"] is True

    def test_env_var_override_creates_nested_key(self, tmp_config, monkeypatch):
        data = {"llm": {"model": "gpt-4o"}}
        path = tmp_config(data)
        monkeypatch.setenv("TARGET_CONFIG_PATH", path)
        monkeypatch.setenv("TARGET_CONFIG__NEW__NESTED__KEY", "hello")
        config = load_config()
        assert config["new"]["nested"]["key"] == "hello"

    def test_missing_config_file_raises(self, monkeypatch):
        monkeypatch.setenv("TARGET_CONFIG_PATH", "/nonexistent/path/config.json")
        with pytest.raises(FileNotFoundError):
            load_config()

    def test_env_var_override_json_list(self, tmp_config, monkeypatch):
        data = {"verifiers": ["a", "b"]}
        path = tmp_config(data)
        monkeypatch.setenv("TARGET_CONFIG_PATH", path)
        monkeypatch.setenv("TARGET_CONFIG__VERIFIERS", '["x", "y", "z"]')
        config = load_config()
        assert config["verifiers"] == ["x", "y", "z"]
