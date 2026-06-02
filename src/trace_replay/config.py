from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field


_DEFAULT_CONFIG_PATHS = [
    Path("config.yaml"),
    Path("config.yml"),
]


class EndpointConfig(BaseModel):
    url: str = "http://localhost:8000"
    api_format: Literal["openai", "anthropic"] = "openai"
    api_key_env: str = ""


class DatasetConfig(BaseModel):
    model_config = {"populate_by_name": True}

    source: str = "huggingface://HuggingFaceH4/ultrachat_200k"
    max_samples: int = 1000
    split: str = "train_sft"
    dataset_schema: str = Field(default="", alias="schema")
    hf_token_env: str = ""


class RequestConfig(BaseModel):
    model_override: str = ""
    max_tokens: int = 256
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False


class LocustConfig(BaseModel):
    users: int = 10
    spawn_rate: int = 2
    run_time: str = ""


class AppConfig(BaseModel):
    endpoint: EndpointConfig = EndpointConfig()
    dataset: DatasetConfig = DatasetConfig()
    request: RequestConfig = RequestConfig()
    locust: LocustConfig = LocustConfig()


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _find_config_file() -> Optional[Path]:
    for p in _DEFAULT_CONFIG_PATHS:
        if p.exists():
            return p
    return None


def load_config(config_path: Optional[str] = None) -> AppConfig:
    if config_path:
        raw = _load_yaml(Path(config_path))
    else:
        found = _find_config_file()
        raw = _load_yaml(found) if found else {}

    raw = _apply_env_overrides(raw)
    return AppConfig(**raw)


def _apply_env_overrides(raw: dict) -> dict:
    prefix = "TRACE_REPLAY_"
    env_map = {
        f"{prefix}ENDPOINT_URL": ("endpoint", "url"),
        f"{prefix}API_FORMAT": ("endpoint", "api_format"),
        f"{prefix}API_KEY_ENV": ("endpoint", "api_key_env"),
        f"{prefix}DATASET_SOURCE": ("dataset", "source"),
        f"{prefix}DATASET_MAX_SAMPLES": ("dataset", "max_samples"),
        f"{prefix}DATASET_SPLIT": ("dataset", "split"),
        f"{prefix}DATASET_SCHEMA": ("dataset", "dataset_schema"),
        f"{prefix}HF_TOKEN_ENV": ("dataset", "hf_token_env"),
        f"{prefix}MODEL_OVERRIDE": ("request", "model_override"),
        f"{prefix}MAX_TOKENS": ("request", "max_tokens"),
        f"{prefix}TEMPERATURE": ("request", "temperature"),
        f"{prefix}STREAM": ("request", "stream"),
        f"{prefix}USERS": ("locust", "users"),
        f"{prefix}SPAWN_RATE": ("locust", "spawn_rate"),
        f"{prefix}RUN_TIME": ("locust", "run_time"),
    }

    for env_key, (section, field) in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            section_dict = raw.setdefault(section, {})
            section_dict[field] = val

    return raw


def apply_cli_overrides(config: AppConfig, **overrides) -> AppConfig:
    data = config.model_dump()
    mapping = {
        "endpoint_url": ("endpoint", "url"),
        "api_format": ("endpoint", "api_format"),
        "api_key_env": ("endpoint", "api_key_env"),
        "dataset_source": ("dataset", "source"),
        "max_samples": ("dataset", "max_samples"),
        "split": ("dataset", "split"),
        "schema": ("dataset", "dataset_schema"),
        "hf_token_env": ("dataset", "hf_token_env"),
        "model_override": ("request", "model_override"),
        "max_tokens": ("request", "max_tokens"),
        "temperature": ("request", "temperature"),
        "stream": ("request", "stream"),
        "users": ("locust", "users"),
        "spawn_rate": ("locust", "spawn_rate"),
        "run_time": ("locust", "run_time"),
    }

    for cli_key, (section, field) in mapping.items():
        val = overrides.get(cli_key)
        if val is not None:
            data[section][field] = val

    return AppConfig(**data)
