from __future__ import annotations

import time

import anthropic

from trace_replay.api.base import APIResponse, BaseAPIAdapter
from trace_replay.models import TraceRequest


class AnthropicAdapter(BaseAPIAdapter):
    def __init__(self, base_url: str, api_key: str | None = None):
        self.client = anthropic.Anthropic(base_url=base_url, api_key=api_key or "sk-placeholder")

    def send(self, request: TraceRequest) -> APIResponse:
        start = time.monotonic()
        try:
            user_messages = [m for m in request.messages if m["role"] != "system"]
            system_text = "\n".join(m["content"] for m in request.messages if m["role"] == "system") or None

            kwargs: dict = {
                "model": request.model,
                "messages": user_messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            if system_text:
                kwargs["system"] = system_text

            if request.stream:
                with self.client.messages.stream(**kwargs) as stream:
                    response_length = 0
                    for _ in stream:
                        response_length += 1
            else:
                response = self.client.messages.create(**kwargs)
                response_length = len(response.content[0].text) if response.content else 0

            latency_ms = (time.monotonic() - start) * 1000
            return APIResponse(status_code=200, latency_ms=latency_ms, response_length=response_length)

        except anthropic.APIStatusError as e:
            latency_ms = (time.monotonic() - start) * 1000
            return APIResponse(status_code=e.status_code, latency_ms=latency_ms, response_length=0)

        except anthropic.APIConnectionError:
            latency_ms = (time.monotonic() - start) * 1000
            return APIResponse(status_code=0, latency_ms=latency_ms, response_length=0)
