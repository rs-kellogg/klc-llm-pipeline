import ollama
from time import perf_counter
from .base import LLMBackend


class OllamaBackend(LLMBackend):
    def __init__(self, host: str):
        self.client = ollama.Client(host=host)

    def ensure_model(self, model: str) -> None:
        available = [m.model for m in self.client.list().models]
        if model not in available:
            self.client.pull(model)

    def run_prompt(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None,
        temperature: float | None,
        options: dict | None,
        stream: bool,
    ):
        opts = options.copy() if options else {}
        if temperature is not None:
            opts["temperature"] = temperature

        start = perf_counter()

        response = self.client.generate(
            model=model,
            prompt=prompt,
            system=system,
            options=opts or None,
            stream=stream,
        )

        if stream:
            chunks, stats = [], {}
            for chunk in response:
                chunks.append(chunk.get("response", ""))
                stats = chunk
            text = "".join(chunks)
        else:
            text = response.get("response", "")
            stats = response

        return {
            "text": text,
            "stats": stats,
            "wall_time_s": perf_counter() - start,
        }
