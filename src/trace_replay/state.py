from __future__ import annotations

from trace_replay.api.anthropic import AnthropicAdapter
from trace_replay.api.base import BaseAPIAdapter
from trace_replay.api.openai import OpenAIAdapter
from trace_replay.config import AppConfig
from trace_replay.models import TraceRequest

traces: list[TraceRequest] = []
adapter: BaseAPIAdapter | None = None
config: AppConfig | None = None


def configure_user(app_config: AppConfig, loaded_traces: list[TraceRequest]) -> None:
    global traces, adapter, config
    traces = loaded_traces
    config = app_config

    api_key = app_config.endpoint.api_key or None

    if app_config.endpoint.api_format == "openai":
        adapter = OpenAIAdapter(base_url=app_config.endpoint.url, api_key=api_key)
    elif app_config.endpoint.api_format == "anthropic":
        adapter = AnthropicAdapter(base_url=app_config.endpoint.url, api_key=api_key)
    else:
        raise ValueError(f"Unsupported api_format: {app_config.endpoint.api_format}")
