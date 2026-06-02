from __future__ import annotations

from abc import ABC, abstractmethod

from trace_replay.models import TraceRequest


class BaseDatasetLoader(ABC):
    @abstractmethod
    def load(self, max_samples: int) -> list[TraceRequest]:
        ...
