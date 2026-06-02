from __future__ import annotations

from pydantic import BaseModel, Field


class TraceRequest(BaseModel):
    messages: list[dict[str, str]] = Field(
        ...,
        description="Chat messages in OpenAI format: [{role, content}]",
    )
    model: str = Field(default="gpt-3.5-turbo", description="Model name to target")
    max_tokens: int = Field(default=256, description="Max tokens in response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: bool = Field(default=False, description="Enable streaming response")
