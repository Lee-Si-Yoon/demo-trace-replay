from __future__ import annotations

DATASET_REGISTRY: dict[str, str] = {
    "HuggingFaceH4/ultrachat_200k": "openai_messages",
    "lmsys/chatbot_arena_conversations": "arena",
}

KNOWN_DATASETS_STR = ", ".join(sorted(DATASET_REGISTRY.keys()))


def resolve_schema(hf_repo_id: str, explicit_schema: str) -> str:
    if explicit_schema:
        return explicit_schema

    if hf_repo_id in DATASET_REGISTRY:
        return DATASET_REGISTRY[hf_repo_id]

    raise ValueError(
        f"Unknown dataset '{hf_repo_id}'. "
        f"Specify --schema (openai_messages, sharegpt, arena). "
        f"Known datasets with auto-detected schemas: {KNOWN_DATASETS_STR}"
    )
