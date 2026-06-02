# Demo Trace Replay

Replay LLM conversation traces against a configurable API endpoint for live traffic demos. This is a load generation client — it sends requests to an existing LLM API, it does not host or serve models. Powered by [Locust](https://locust.io).

## Quick Start

```bash
cp config.yaml.example config.yaml   # edit with your API key and endpoint
uv pip install -e .
trace-replay
```

Opens Locust web UI at http://localhost:8089. Default: 1000 conversations from `HuggingFaceH4/ultrachat_200k` against `http://localhost:8000`.

## Usage

```bash
# Custom endpoint + model
trace-replay --endpoint https://api.friendli.ai/dedicated --api-key flp_... --model-override my-model

# Local JSONL traces
trace-replay --dataset file://datasets/example_traces.jsonl --schema openai_messages

# Anthropic API
trace-replay --endpoint https://api.anthropic.com --api-format anthropic --api-key sk-ant-...

# Headless run
trace-replay --headless --run-time 5m --users 20 --spawn-rate 5

# Streaming
trace-replay --stream
```

## Datasets

| Source | Format | Auto-detected |
|---|---|---|
| `huggingface://HuggingFaceH4/ultrachat_200k` | OpenAI messages | Yes |
| `huggingface://lmsys/chatbot_arena_conversations` | Arena | Yes |
| `file://path/to/traces.jsonl` | Any | No — requires `--schema` |

Schemas: `openai_messages`, `sharegpt`, `arena`

## Configuration

Precedence: **CLI args > env vars > config.yaml > defaults**

See [`config.yaml.example`](config.yaml.example) for all options with descriptions.

Env var convention: `TRACE_REPLAY_<FIELD>` uppercased (e.g. `TRACE_REPLAY_API_KEY`, `TRACE_REPLAY_HF_TOKEN`).

## Docker

```bash
docker build -t trace-replay .
docker run -p 8089:8089 trace-replay --endpoint https://api.openai.com --api-key sk-...
```

## JSONL Format

One `TraceRequest` per line:

```json
{"messages": [{"role": "user", "content": "Hello"}], "model": "gpt-3.5-turbo", "max_tokens": 256, "temperature": 0.7}
```
