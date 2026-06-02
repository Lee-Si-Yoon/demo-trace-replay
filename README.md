# Demo Trace Replay

Replay LLM request traces against a configurable endpoint for live traffic demos. Powered by Locust.

## Quick Start

```bash
cp config.yaml.example config.yaml   # then edit with your API key
uv pip install -e .
trace-replay
```

Opens Locust web UI at http://localhost:8089. Default: 1000 conversations from `HuggingFaceH4/ultrachat_200k` against `http://localhost:8000`.

## Usage

```bash
# Custom endpoint + model
trace-replay --endpoint http://my-vllm:8000 --model-override meta-llama/Llama-3-8B

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

Unknown HuggingFace datasets require `--schema`:
```bash
trace-replay --dataset huggingface://some/repo --schema sharegpt
```

## Configuration

Precedence: CLI args > env vars > `config.yaml` > defaults.

**config.yaml** (copy from `config.yaml.example`)
```yaml
endpoint:
  url: "http://localhost:8000"
  api_format: "openai"          # openai | anthropic
  api_key: ""                   # API key for LLM endpoint

dataset:
  source: "huggingface://HuggingFaceH4/ultrachat_200k"
  max_samples: 1000
  split: "train_sft"
  hf_token: ""                  # HuggingFace token for gated datasets

request:
  model_override: ""
  max_tokens: 256
  temperature: 0.7
  stream: false

locust:
  users: 10
  spawn_rate: 2
  run_time: ""
```

**Environment Variables**

| Variable | Config Key | Example |
|---|---|---|
| `TRACE_REPLAY_ENDPOINT_URL` | `endpoint.url` | `http://my-vllm:8000` |
| `TRACE_REPLAY_API_FORMAT` | `endpoint.api_format` | `openai` |
| `TRACE_REPLAY_API_KEY` | `endpoint.api_key` | `sk-...` |
| `TRACE_REPLAY_HF_TOKEN` | `dataset.hf_token` | `hf_...` |
| `TRACE_REPLAY_DATASET_SOURCE` | `dataset.source` | `huggingface://HuggingFaceH4/ultrachat_200k` |
| `TRACE_REPLAY_DATASET_MAX_SAMPLES` | `dataset.max_samples` | `1000` |
| `TRACE_REPLAY_DATASET_SPLIT` | `dataset.split` | `train_sft` |
| `TRACE_REPLAY_DATASET_SCHEMA` | `dataset.dataset_schema` | `openai_messages` |
| `TRACE_REPLAY_MODEL_OVERRIDE` | `request.model_override` | `meta-llama/Llama-3-8B` |
| `TRACE_REPLAY_MAX_TOKENS` | `request.max_tokens` | `256` |
| `TRACE_REPLAY_TEMPERATURE` | `request.temperature` | `0.7` |
| `TRACE_REPLAY_STREAM` | `request.stream` | `true` |
| `TRACE_REPLAY_USERS` | `locust.users` | `10` |
| `TRACE_REPLAY_SPAWN_RATE` | `locust.spawn_rate` | `2` |
| `TRACE_REPLAY_RUN_TIME` | `locust.run_time` | `5m` |

## Docker

```bash
docker build -t trace-replay .
docker run -p 8089:8089 trace-replay --endpoint http://host.docker.internal:8000
```

## JSONL Format

One `TraceRequest` per line:

```json
{"messages": [{"role": "user", "content": "Hello"}], "model": "gpt-3.5-turbo", "max_tokens": 256, "temperature": 0.7}
```
