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

        seed = opts.get("seed")

        start = perf_counter()

        response = self.client.generate(
            model=model,
            prompt=prompt,
            system=system,
            options=opts or None,
            stream=stream,
        )

        if stream:
            chunks, final_chunk = [], {}
            for chunk in response:
                chunks.append(chunk.get("response", ""))
                final_chunk = chunk
            text = "".join(chunks)
            raw_stats = final_chunk
        else:
            text = response.get("response", "")
            raw_stats = response

        wall_time = perf_counter() - start

        # Normalize Ollama stats into HF-like structure
        stats = {
            "backend": "ollama",
            "model": model,
            "prompt_tokens": raw_stats.get("prompt_eval_count"),
            "eval_count": raw_stats.get("eval_count"),
            "prompt_eval_duration": raw_stats.get("prompt_eval_duration"),
            "eval_duration": raw_stats.get("eval_duration"),
            "total_duration": raw_stats.get("total_duration"),
            # HF-compatible fields (when possible)
            "generation_options_overrides": opts,
            "generation_options_defaults": {},
            "seed": seed,
            # Not available in Ollama
            "transformers_version": None,
            "model_revision": None,
            "max_context_tokens": None,
            "quantization": None,
        }

        return {
            "text": text.strip(),
            "stats": stats,
            "wall_time_s": wall_time,
        }

