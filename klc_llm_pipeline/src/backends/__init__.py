from .ollama_backend import OllamaBackend
from .hf_backend import HuggingFaceBackend


def get_backend(kind: str, **kwargs):
    if kind == "ollama":
        return OllamaBackend(**kwargs)
    if kind in {"hf", "huggingface"}:
        return HuggingFaceBackend(**kwargs)
    raise ValueError(f"Unknown backend: {kind}")

