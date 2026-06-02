from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from trace_replay.config import AppConfig, apply_cli_overrides, load_config
from trace_replay.dataset.huggingface import HuggingFaceLoader
from trace_replay.dataset.jsonl import JSONLLoader
from trace_replay.dataset.registry import resolve_schema
from trace_replay.session import SESSION_ENV_VAR, write_session

app = typer.Typer(
    name="trace-replay",
    help="Replay LLM request traces against a configurable endpoint for live traffic demos.",
    add_completion=False,
)


def _parse_dataset_source(source: str) -> tuple[str, str | None, str | None]:
    if source.startswith("huggingface://"):
        repo_id = source[len("huggingface://"):]
        return "huggingface", repo_id, None
    elif source.startswith("file://"):
        path = source[len("file://"):]
        return "file", None, path
    else:
        if Path(source).exists():
            return "file", None, source
        return "huggingface", source, None


@app.command()
def replay(
    endpoint_url: Optional[str] = typer.Option(None, "--endpoint", help="Target LLM endpoint URL"),
    api_format: Optional[str] = typer.Option(None, "--api-format", help="API format: openai | anthropic"),
    api_key_env: Optional[str] = typer.Option(None, "--api-key-env", help="Env var name holding API key"),
    dataset_source: Optional[str] = typer.Option(None, "--dataset", help="Dataset source (huggingface://repo or file://path)"),
    max_samples: Optional[int] = typer.Option(None, "--max-samples", help="Max traces to load"),
    split: Optional[str] = typer.Option(None, "--split", help="HF dataset split"),
    schema: Optional[str] = typer.Option(None, "--schema", help="Dataset schema: openai_messages | sharegpt | arena"),
    model_override: Optional[str] = typer.Option(None, "--model-override", help="Override model name in requests"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Max tokens for responses"),
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature"),
    stream: Optional[bool] = typer.Option(None, "--stream", help="Enable streaming responses"),
    users: Optional[int] = typer.Option(None, "--users", help="Number of concurrent Locust users"),
    spawn_rate: Optional[int] = typer.Option(None, "--spawn-rate", help="Users spawned per second"),
    run_time: Optional[str] = typer.Option(None, "--run-time", help="Run duration (e.g. 5m, 1h)"),
    config_path: Optional[str] = typer.Option(None, "--config", help="Path to config.yaml"),
    locust_host: Optional[str] = typer.Option(None, "--host", help="Locust web UI host"),
    locust_port: Optional[int] = typer.Option(None, "--port", help="Locust web UI port"),
    headless: bool = typer.Option(False, "--headless", help="Run Locust without web UI"),
) -> None:
    config = load_config(config_path)

    overrides = {}
    if endpoint_url is not None:
        overrides["endpoint_url"] = endpoint_url
    if api_format is not None:
        overrides["api_format"] = api_format
    if api_key_env is not None:
        overrides["api_key_env"] = api_key_env
    if dataset_source is not None:
        overrides["dataset_source"] = dataset_source
    if max_samples is not None:
        overrides["max_samples"] = max_samples
    if split is not None:
        overrides["split"] = split
    if model_override is not None:
        overrides["model_override"] = model_override
    if max_tokens is not None:
        overrides["max_tokens"] = max_tokens
    if temperature is not None:
        overrides["temperature"] = temperature
    if stream is not None:
        overrides["stream"] = stream
    if users is not None:
        overrides["users"] = users
    if spawn_rate is not None:
        overrides["spawn_rate"] = spawn_rate
    if run_time is not None:
        overrides["run_time"] = run_time

    config = apply_cli_overrides(config, **overrides)

    typer.echo(f"Loading dataset: {config.dataset.source}")
    typer.echo(f"  schema: {schema or 'auto-detected'}, split: {config.dataset.split}, max_samples: {config.dataset.max_samples}")

    source_type, repo_id, file_path = _parse_dataset_source(config.dataset.source)

    resolved_schema = resolve_schema(repo_id or "", schema or config.dataset.dataset_schema)

    if source_type == "huggingface":
        if not repo_id:
            raise typer.BadParameter("HuggingFace source requires a repo ID")
        loader = HuggingFaceLoader(repo_id=repo_id, split=config.dataset.split, schema=resolved_schema)
    elif source_type == "file":
        if not file_path:
            raise typer.BadParameter("File source requires a path")
        loader = JSONLLoader(path=file_path, schema=resolved_schema)
    else:
        raise typer.BadParameter(f"Unknown dataset source type: {source_type}")

    traces = loader.load(config.dataset.max_samples)
    typer.echo(f"  loaded {len(traces)} traces")

    session_path = write_session(config, traces)
    typer.echo(f"  session written to {session_path}")

    typer.echo(f"Target endpoint: {config.endpoint.url} ({config.endpoint.api_format})")
    typer.echo(f"Request defaults: model={config.request.model_override or 'from-trace'}, max_tokens={config.request.max_tokens}, temperature={config.request.temperature}, stream={config.request.stream}")
    typer.echo(f"Locust: users={config.locust.users}, spawn_rate={config.locust.spawn_rate}")

    locust_args = _build_locust_args(config, headless, locust_host, locust_port)
    typer.echo(f"Launching Locust: {' '.join(locust_args)}")

    spec = importlib.util.find_spec("trace_replay.locustfile")
    if spec is None or spec.origin is None:
        raise RuntimeError("Could not locate trace_replay.locustfile module")
    locustfile_path = str(Path(spec.origin).resolve())

    env = os.environ.copy()
    env[SESSION_ENV_VAR] = session_path

    try:
        subprocess.run(
            [sys.executable, "-m", "locust", "-f", locustfile_path] + locust_args,
            env=env,
            check=False,
        )
    finally:
        try:
            os.unlink(session_path)
        except OSError:
            pass


def _build_locust_args(config: AppConfig, headless: bool, host: Optional[str], port: Optional[int]) -> list[str]:
    args: list[str] = []

    args.extend(["--users", str(config.locust.users)])
    args.extend(["--spawn-rate", str(config.locust.spawn_rate)])

    if config.locust.run_time:
        args.extend(["--run-time", config.locust.run_time])

    if headless:
        args.append("--headless")

    if host:
        args.extend(["--host", host])

    if port:
        args.extend(["--port", str(port)])

    return args


if __name__ == "__main__":
    app()
