from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from trace_replay.config import AppConfig
from trace_replay.models import TraceRequest

SESSION_ENV_VAR = "TRACE_REPLAY_SESSION"


def write_session(config: AppConfig, traces: list[TraceRequest]) -> str:
    session = {
        "config": config.model_dump(by_alias=True),
        "traces": [t.model_dump() for t in traces],
    }

    fd, path = tempfile.mkstemp(suffix=".json", prefix="trace_replay_session_")
    with os.fdopen(fd, "w") as f:
        json.dump(session, f)

    return path


def load_session() -> tuple[AppConfig, list[TraceRequest]]:
    path = os.environ.get(SESSION_ENV_VAR)
    if not path or not Path(path).exists():
        raise RuntimeError(
            f"Session file not found. Ensure {SESSION_ENV_VAR} env var points to a valid session file. "
            "Run 'trace-replay replay ...' to create one."
        )

    with open(path) as f:
        session = json.load(f)

    config = AppConfig(**session["config"])
    traces = [TraceRequest(**t) for t in session["traces"]]
    return config, traces
