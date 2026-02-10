from pathlib import Path
from typing import List

PROMPT_SEPARATOR = "\n---\n"


def load_prompts_from_file(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8").strip()
    if PROMPT_SEPARATOR.strip() in text:
        return [p.strip() for p in text.split(PROMPT_SEPARATOR) if p.strip()]
    return [line.strip() for line in text.splitlines() if line.strip()]


def resolve_prompt(prompt_id: str, prompt_registry: dict) -> dict:
    if prompt_id not in prompt_registry:
        raise KeyError(f"Prompt '{prompt_id}' not found in [prompts]")
    return prompt_registry[prompt_id]

