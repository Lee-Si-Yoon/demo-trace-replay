from __future__ import annotations

import time

import openai

from trace_replay.api.base import APIResponse, BaseAPIAdapter
from trace_replay.models import TraceRequest


class OpenAIAdapter(BaseAPIAdapter):
    def __init__(self, base_url: str, api_key: str | None = None):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key or "sk-placeholder")

    def send(self, request: TraceRequest) -> APIResponse:
        start = time.monotonic()
        try:
            response = self.client.chat.completions.create(
                model=request.model,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=request.stream,
            )

            if request.stream:
                response_length = 0
                for _ in response:
                    response_length += 1
            else:
                response_length = len(response.choices[0].message.content or "") if response.choices else 0

            latency_ms = (time.monotonic() - start) * 1000
            return APIResponse(status_code=200, latency_ms=latency_ms, response_length=response_length)

        except openai.APIStatusError as e:
            latency_ms = (time.monotonic() - start) * 1000
            return APIResponse(status_code=e.status_code, latency_ms=latency_ms, response_length=0)

        except openai.APIConnectionError:
            latency_ms = (time.monotonic() - start) * 1000
            return APIResponse(status_code=0, latency_ms=latency_ms, response_length=0)
