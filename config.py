import json
import os


def load_config() -> dict:
    config_path = os.environ.get("TARGET_CONFIG_PATH", "configs/default.json")
    with open(config_path) as f:
        config = json.load(f)
    prefix = "TARGET_CONFIG__"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            path = key[len(prefix):].lower().split("__")
            try:
                parsed = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                parsed = value
            target = config
            for part in path[:-1]:
                target = target.setdefault(part, {})
            target[path[-1]] = parsed
    return config
