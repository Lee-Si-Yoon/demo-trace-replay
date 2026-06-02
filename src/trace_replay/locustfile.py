from __future__ import annotations

import random
import time

from locust import User, between, events, task

from trace_replay.session import load_session
from trace_replay.state import configure_user

try:
    _config, _traces = load_session()
    configure_user(_config, _traces)
except RuntimeError:
    _config = None
    _traces = []


from trace_replay import state


class TraceReplayUser(User):
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        if not state.traces:
            raise RuntimeError("No traces loaded. Call configure_user() before starting Locust.")

    @task
    def send_trace_request(self) -> None:
        trace = random.choice(state.traces)
        adapter = state.adapter

        request_overrides = {}
        if state.config and state.config.request.model_override:
            request_overrides["model"] = state.config.request.model_override
        if state.config:
            request_overrides["max_tokens"] = state.config.request.max_tokens
            request_overrides["temperature"] = state.config.request.temperature
            request_overrides["stream"] = state.config.request.stream

        effective = trace.model_copy(update=request_overrides)

        start = time.monotonic()
        try:
            response = adapter.send(effective)
        except Exception as e:
            total_ms = (time.monotonic() - start) * 1000
            events.request.fire(
                request_type="LLM",
                name=state.config.endpoint.url if state.config else "unknown",
                response_time=total_ms,
                response_length=0,
                exception=e,
            )
            return

        exception = None
        if response.status_code >= 400 or response.status_code == 0:
            exception = Exception(f"HTTP {response.status_code}")

        events.request.fire(
            request_type="LLM",
            name=state.config.endpoint.url if state.config else "unknown",
            response_time=response.latency_ms,
            response_length=response.response_length or 0,
            exception=exception,
        )
