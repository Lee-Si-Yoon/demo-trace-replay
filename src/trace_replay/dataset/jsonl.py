from __future__ import annotations

import json

from trace_replay.dataset.base import BaseDatasetLoader
from trace_replay.models import TraceRequest


class JSONLLoader(BaseDatasetLoader):
    def __init__(self, path: str, schema: str):
        self.path = path
        self.schema = schema

    def load(self, max_samples: int) -> list[TraceRequest]:
        requests: list[TraceRequest] = []

        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                req = self._parse_row(row)
                if req:
                    requests.append(req)
                if len(requests) >= max_samples:
                    break

        if not requests:
            raise ValueError(f"No valid traces found in {self.path} (schema={self.schema})")

        return requests

    def _parse_row(self, row: dict) -> TraceRequest | None:
        if self.schema == "openai_messages":
            return self._parse_openai_messages(row)
        elif self.schema == "sharegpt":
            return self._parse_sharegpt(row)
        elif self.schema == "arena":
            return self._parse_arena(row)
        return None

    def _parse_openai_messages(self, row: dict) -> TraceRequest | None:
        messages = row.get("messages")
        if not messages or not isinstance(messages, list):
            return None
        if not any(m.get("role") == "user" for m in messages):
            return None
        return TraceRequest(
            messages=messages,
            model=row.get("model", "gpt-3.5-turbo"),
            max_tokens=row.get("max_tokens", 256),
            temperature=row.get("temperature", 0.7),
        )

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

    def _parse_arena(self, row: dict) -> TraceRequest | None:
        conversation = row.get("conversation_a") or row.get("conversation_b")
        if not conversation or not isinstance(conversation, list):
            return None
        if not any(m.get("role") == "user" for m in conversation):
            return None
        return TraceRequest(messages=conversation)
