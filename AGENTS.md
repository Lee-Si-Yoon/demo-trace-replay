# AGENTS.md

Reference for AI coding agents working on this codebase.

## Project Purpose

demo-trace-replay is a **load generation client** that replays LLM conversation traces against a configurable API endpoint for live traffic demos. It does NOT host, serve, or run models — it only sends requests to an existing LLM API.

## Architecture

```
CLI (cli.py)
  → loads config (config.py)
  → loads dataset (dataset/)
  → writes temp session file (session.py)
  → spawns Locust subprocess (locustfile.py)
    → Locust users pick random traces (state.py)
    → send via API adapter (api/)
    → report metrics to Locust
```

The CLI and Locust run in separate processes. Session state (config + traces) is serialized to a temp JSON file and passed to Locust via the `TRACE_REPLAY_SESSION` env var.

## Source Map

```
src/trace_replay/
  cli.py            Typer CLI entry point; orchestrates startup + Locust launch
  config.py         Pydantic config models (EndpointConfig, DatasetConfig, RequestConfig, LocustConfig, AppConfig)
                    YAML loading, env var overrides, CLI override resolution
  models.py         TraceRequest pydantic model
  session.py        Write/load temp session file bridging CLI and Locust subprocess
  state.py          Global mutable state: configure adapter + traces for Locust workers
  locustfile.py     Locust User definition; picks random trace, applies request overrides, sends via adapter
  api/
    base.py         BaseAPIAdapter ABC + APIResponse dataclass
    openai.py       OpenAI-compatible adapter (works with any OpenAI-format endpoint: Friendli, together, etc.)
    anthropic.py    Anthropic Messages API adapter
  dataset/
    base.py         BaseDatasetLoader ABC
    huggingface.py  HuggingFace dataset loader (streaming via `datasets` lib, optional token)
    jsonl.py        Local JSONL file loader
    registry.py     Auto-schema detection registry for known HuggingFace datasets
```

## Config Resolution

Precedence: **CLI args > env vars > config.yaml > defaults**

1. `load_config()` reads `config.yaml` (or `config.yml`)
2. `_apply_env_overrides()` applies any `TRACE_REPLAY_*` env vars
3. `apply_cli_overrides()` applies any CLI `--flag` values

Env var convention: `TRACE_REPLAY_<SECTION>_<FIELD>` uppercased, e.g. `TRACE_REPLAY_API_KEY` → `endpoint.api_key`. For aliased fields (`schema` → `dataset_schema`), the env var uses the python field name.

## Key Invariants

- `config.yaml` is **gitignored** (contains API keys); only `config.yaml.example` is tracked
- API adapters must **never** silently fall back to fake keys (no `"sk-placeholder"`)
- Locust runs as a **subprocess**; session state is passed via temp file + env var, not shared memory
- All adapters extend `BaseAPIAdapter` and return `APIResponse`
- All dataset loaders extend `BaseDatasetLoader` and return `list[TraceRequest]`
- `api_key` and `hf_token` hold **direct values**, not env var names
- Empty string `""` means "not configured"; converted to `None` at the boundary (state.py, cli.py)

## Adding a New API Adapter

1. Create `src/trace_replay/api/<provider>.py` extending `BaseAPIAdapter`
2. Implement `__init__(self, base_url: str, api_key: str | None)` and `send(self, request: TraceRequest) -> APIResponse`
3. Register in `state.py` `configure_user()` with an `api_format` check
4. Add the new format literal to `EndpointConfig.api_format` in `config.py`
5. Update `config.yaml.example` and README with the new format option

## Adding a New Dataset Schema

1. Add a `_parse_<schema>(self, row: dict) -> TraceRequest | None` method to both `huggingface.py` and `jsonl.py`
2. Wire it into `_parse_row()` in both files
3. Add an entry to `dataset/registry.py` `DATASET_REGISTRY` if auto-detection is desired
4. Update `--schema` help text in `cli.py`

## Adding a New Config Field

1. Add field to the relevant Pydantic config model in `config.py`
2. Add env var mapping in `_apply_env_overrides()` `env_map` dict
3. Add CLI override mapping in `apply_cli_overrides()` `mapping` dict
4. Add CLI option in `cli.py` `replay()` function
5. Add override forwarding in `cli.py` `overrides` dict
6. Add to `config.yaml.example` with description comment
7. Update README if user-facing (not needed for internal-only fields)

## Build & Run

```bash
cp config.yaml.example config.yaml   # edit with your API key
uv pip install -e .
trace-replay
```

## Docker

```bash
docker build -t trace-replay .
docker run -p 8089:8089 trace-replay --endpoint https://api.openai.com --api-key sk-...
```
