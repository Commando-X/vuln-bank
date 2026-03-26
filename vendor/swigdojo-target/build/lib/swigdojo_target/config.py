from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TargetConfig:
    api_url: str
    experiment_id: str
    run_id: str
    wrapper_port: int


def load_config() -> TargetConfig:
    required_vars = {
        "SWIGDOJO_API_URL": "api_url",
        "SWIGDOJO_EXPERIMENT_ID": "experiment_id",
        "SWIGDOJO_RUN_ID": "run_id",
    }

    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    wrapper_port = int(os.environ.get("SWIGDOJO_WRAPPER_PORT", "8787"))

    return TargetConfig(
        api_url=os.environ["SWIGDOJO_API_URL"],
        experiment_id=os.environ["SWIGDOJO_EXPERIMENT_ID"],
        run_id=os.environ["SWIGDOJO_RUN_ID"],
        wrapper_port=wrapper_port,
    )
