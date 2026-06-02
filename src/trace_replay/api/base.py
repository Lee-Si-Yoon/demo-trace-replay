from __future__ import annotations

from abc import ABC, abstractmethod

from trace_replay.models import TraceRequest


class APIResponse:
    __slots__ = ("status_code", "latency_ms", "response_length")

    def __init__(self, status_code: int, latency_ms: float, response_length: int | None = None):
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.response_length = response_length


class BaseAPIAdapter(ABC):
    @abstractmethod
    def send(self, request: TraceRequest) -> APIResponse:
        ...
