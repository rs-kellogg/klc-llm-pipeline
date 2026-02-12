from pathlib import Path
from typing import Dict, Any


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

    path = model_dir / f"{prompt_id}.txt"
    stats = result["stats"]

    def ns_to_ms(ns: int | None) -> str:
        return f"{ns / 1_000_000:.1f} ms" if ns else "n/a"

    prompt_tokens = stats.get("prompt_tokens")
    response_tokens = stats.get("eval_count")
    total_tokens = (
        (prompt_tokens or 0) + (response_tokens or 0)
        if prompt_tokens or response_tokens
        else "n/a"
    )

    content_lines = [
        f"Result: {prompt_id}",
        f"Backend: {backend}",
        f"Model: {model}",
        "",
        "Prompt:",
        prompt,
    ]

    if system:
        content_lines.extend(["", "System:", system])

    content_lines.extend([
        "",
        "Response:",
        result["text"],
        "",
        "Stats:",
        f"- Prompt tokens: {prompt_tokens or 'n/a'}",
        f"- Response tokens: {response_tokens or 'n/a'}",
        f"- Total tokens: {total_tokens}",
        f"- Prompt eval time: {ns_to_ms(stats.get('prompt_eval_duration'))}",
        f"- Generation time: {ns_to_ms(stats.get('eval_duration'))}",
        f"- Total backend time: {ns_to_ms(stats.get('total_duration'))}",
        f"- Wall time: {result['wall_time_s'] * 1000:.1f} ms",
    ])

    # Model / backend metadata (shown if available)
    metadata_fields = [
        ("Transformers version", stats.get("transformers_version")),
        ("Model revision / SHA", stats.get("model_revision")),
        ("Max context tokens", stats.get("max_context_tokens")),
        ("Quantization", stats.get("quantization")),
        ("Device", stats.get("device")),
        ("Seed", stats.get("seed")),
    ]

    generation_overrides = stats.get("generation_options_overrides")
    generation_defaults = stats.get("generation_options_defaults")

    if any(value is not None for _, value in metadata_fields) or generation_overrides:
        content_lines.append("")
        content_lines.append("Model Info:")

        for label, value in metadata_fields:
            if value is not None:
                content_lines.append(f"- {label}: {value}")

        if generation_overrides:
            content_lines.append(
                f"- Generation options overrides: {generation_overrides}"
            )

        if generation_defaults:
            content_lines.append(
                f"- Generation options defaults: {generation_defaults}"
            )

    path.write_text("\n".join(content_lines) + "\n", encoding="utf-8")
