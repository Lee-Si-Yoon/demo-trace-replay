from __future__ import annotations

import random

from datasets import load_dataset

from trace_replay.dataset.base import BaseDatasetLoader
from trace_replay.models import TraceRequest


class HuggingFaceLoader(BaseDatasetLoader):
    def __init__(self, repo_id: str, split: str, schema: str):
        self.repo_id = repo_id
        self.split = split
        self.schema = schema

    def load(self, max_samples: int) -> list[TraceRequest]:
        ds = load_dataset(self.repo_id, split=self.split, streaming=True)
        requests: list[TraceRequest] = []

        for row in ds:
            req = self._parse_row(row)
            if req:
                requests.append(req)
            if len(requests) >= max_samples:
                break

        if not requests:
            raise ValueError(f"No valid traces found in {self.repo_id} (split={self.split}, schema={self.schema})")

        return requests

    def _parse_row(self, row: dict) -> TraceRequest | None:
        if self.schema == "openai_messages":
            return self._parse_openai_messages(row)
        elif self.schema == "arena":
            return self._parse_arena(row)
        elif self.schema == "sharegpt":
            return self._parse_sharegpt(row)
        return None

    def _parse_openai_messages(self, row: dict) -> TraceRequest | None:
        messages = row.get("messages")
        if not messages or not isinstance(messages, list):
            return None
        if not any(m.get("role") == "user" for m in messages):
            return None
        return TraceRequest(messages=messages)

    def _parse_arena(self, row: dict) -> TraceRequest | None:
        conversation = row.get("conversation_a") or row.get("conversation_b")
        if not conversation or not isinstance(conversation, list):
            return None
        if not any(m.get("role") == "user" for m in conversation):
            return None
        return TraceRequest(messages=conversation)

    def _parse_sharegpt(self, row: dict) -> TraceRequest | None:
        conversations = row.get("conversations")
        if not conversations or not isinstance(conversations, list):
            return None

        from_map = {"human": "user", "gpt": "assistant", "user": "user", "assistant": "assistant"}
        messages = []
        for turn in conversations:
            role = from_map.get(turn.get("from", ""), turn.get("from", ""))
            content = turn.get("value", "")
            if role and content:
                messages.append({"role": role, "content": content})

        if not any(m["role"] == "user" for m in messages):
            return None
        return TraceRequest(messages=messages)
