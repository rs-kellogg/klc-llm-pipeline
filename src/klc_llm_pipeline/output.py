from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json


def save_result(
    *,
    output_dir: Path,
    backend: str,
    model: str,
    prompt_id: str,
    prompt: str,
    system: str | None,
    result: Dict[str, Any],
):
    model_dir = output_dir / backend / model
    model_dir.mkdir(parents=True, exist_ok=True)

    # current date in yyyy-mm-dd format
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_file = model_dir / f"output_{date_str}.json"
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stats = result["stats"]

    def ns_to_ms(ns: int | None) -> float | None:
        return ns / 1_000_000 if ns else None

    prompt_tokens = stats.get("prompt_tokens")
    response_tokens = stats.get("eval_count")
    total_tokens = (
        (prompt_tokens or 0) + (response_tokens or 0)
        if prompt_tokens or response_tokens
        else None
    )

    content_dict = {
        "prompt_id": prompt_id,
        "backend": backend,
        "model": model,
        "prompt": prompt,
        "response": result["text"],
        "timestamp": time_str,
        "stats": {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "prompt_eval_time_ms": ns_to_ms(stats.get("prompt_eval_duration")),
            "generation_time_ms": ns_to_ms(stats.get("eval_duration")),
            "total_backend_time_ms": ns_to_ms(stats.get("total_duration")),
            "wall_time_ms": result["wall_time_s"] * 1000,
        },
    }

    if system:
        content_dict["system"] = system

    # Model / backend metadata (shown if available)
    model_info = {}
    
    if stats.get("transformers_version"):
        model_info["transformers_version"] = stats.get("transformers_version")
    if stats.get("model_revision"):
        model_info["model_revision"] = stats.get("model_revision")
    if stats.get("max_context_tokens"):
        model_info["max_context_tokens"] = stats.get("max_context_tokens")
    if stats.get("quantization"):
        model_info["quantization"] = stats.get("quantization")
    if stats.get("device"):
        model_info["device"] = stats.get("device")
    if stats.get("seed"):
        model_info["seed"] = stats.get("seed")
    if stats.get("generation_options_overrides"):
        model_info["generation_options_overrides"] = stats.get("generation_options_overrides")
    if stats.get("generation_options_defaults"):
        model_info["generation_options_defaults"] = stats.get("generation_options_defaults")

    if model_info:
        content_dict["model_info"] = model_info

    # Append to JSON file as a JSON Lines format (each line is a JSON object)
    with output_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(content_dict, ensure_ascii=False) + "\n")