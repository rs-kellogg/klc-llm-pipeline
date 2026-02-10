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
    # Include backend in the directory structure
    model_dir = output_dir / backend / model
    model_dir.mkdir(parents=True, exist_ok=True)

    path = model_dir / f"{prompt_id}.txt"
    stats = result["stats"]

    def ns_to_ms(ns: int | None) -> str:
        return f"{ns / 1_000_000:.1f} ms" if ns else "n/a"

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
        f"- Prompt tokens: {stats.get('prompt_eval_count', 'n/a')}",
        f"- Response tokens: {stats.get('eval_count', 'n/a')}",
        f"- Total tokens: {(stats.get('prompt_eval_count') or 0) + (stats.get('eval_count') or 0)}",
        f"- Prompt eval time: {ns_to_ms(stats.get('prompt_eval_duration'))}",
        f"- Generation time: {ns_to_ms(stats.get('eval_duration'))}",
        f"- Total Ollama time: {ns_to_ms(stats.get('total_duration'))}",
        f"- Wall time: {result['wall_time_s'] * 1000:.1f} ms",
    ])

    path.write_text("\n".join(content_lines) + "\n", encoding="utf-8")

