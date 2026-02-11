from time import perf_counter
import logging
import transformers
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    GenerationConfig,
    set_seed,
)
import torch

from .base import LLMBackend

logger = logging.getLogger(__name__)


class HuggingFaceBackend(LLMBackend):
    def __init__(
        self,
        device: str | None = None,
        dtype: str | None = None,
        **_ignored,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype
        self._pipelines = {}
        self.transformers_version = transformers.__version__

    def ensure_model(self, model: str) -> None:
        AutoTokenizer.from_pretrained(model)
        AutoModelForCausalLM.from_pretrained(model)

    def _get_pipeline(self, model: str):
        if model not in self._pipelines:
            tokenizer = AutoTokenizer.from_pretrained(model)
            model_obj = AutoModelForCausalLM.from_pretrained(
                model,
                torch_dtype=getattr(torch, self.dtype) if self.dtype else None,
            ).to(self.device)

            # Determine model quantization
            if getattr(model_obj, "is_loaded_in_4bit", False):
                quantization = "4bit"
            elif getattr(model_obj, "is_loaded_in_8bit", False):
                quantization = "8bit"
            else:
                quantization = str(model_obj.dtype)

            # Determine max context tokens
            max_context_tokens = getattr(tokenizer, "model_max_length", None)

            # Determine model revision / SHA
            model_revision = getattr(model_obj.config, "_commit_hash", None) or getattr(model_obj.config, "revision", None)

            # Save model metadata in the pipeline dict
            self._pipelines[model] = {
                "pipeline": pipeline(
                    "text-generation",
                    model=model_obj,
                    tokenizer=tokenizer,
                    device=0 if self.device == "cuda" else -1,
                ),
                "model_obj": model_obj,
                "tokenizer": tokenizer,
                "max_context_tokens": max_context_tokens,
                "quantization": quantization,
                "model_revision": model_revision,
            }

        return self._pipelines[model]["pipeline"]

    def _make_generation_config(
        self,
        model,
        options: dict | None = None,
        temperature: float | None = None,
    ):
        user_options = options.copy() if options else {}

        # Extract seed (NOT a GenerationConfig field)
        seed = user_options.pop("seed", None)

        if temperature is not None:
            user_options["temperature"] = temperature
        user_options.setdefault("max_new_tokens", 512)

        base_config: GenerationConfig = model.generation_config
        base_dict = base_config.to_dict()

        valid_keys = set(base_dict.keys())
        unused_keys = set(user_options.keys()) - valid_keys
        for key in unused_keys:
            logger.warning(
                "Ignoring invalid generation option '%s' (not in GenerationConfig)",
                key,
            )

        filtered_options = {
            k: v for k, v in user_options.items() if k in valid_keys
        }

        gen_config = GenerationConfig.from_dict(
            {**base_dict, **filtered_options}
        )
        final_dict = gen_config.to_dict()

        overrides = {}
        defaults = {}

        for key, default_value in base_dict.items():
            final_value = final_dict.get(key)
            if key in filtered_options and final_value != default_value:
                overrides[key] = final_value
            else:
                defaults[key] = final_value

        if seed is not None:
            overrides["seed"] = seed

        return gen_config, overrides, defaults, seed

    def run_prompt(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        options: dict | None = None,
        stream: bool = False,
    ):
        pipe = self._get_pipeline(model)
        pipeline_info = self._pipelines[model]
        model_obj = pipeline_info["model_obj"]
        tokenizer = pipeline_info["tokenizer"]

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        # Calculate prompt length in tokens
        prompt_tokens = len(tokenizer(full_prompt, return_tensors="pt")["input_ids"][0])

        gen_config, overrides, defaults, seed = self._make_generation_config(
            model_obj, options, temperature
        )

        if seed is not None:
            set_seed(seed)
            logger.info("Set Hugging Face random seed to %s", seed)

        logger.info("Generation config overrides (user-specified): %s", overrides)
        logger.info("Generation config defaults (model): %s", defaults)

        start = perf_counter()

        out = pipe(
            full_prompt,
            generation_config=gen_config,
        )

        text = out[0]["generated_text"][len(full_prompt):]

        return {
            "text": text.strip(),
            "stats": {
                "backend": "huggingface",
                "model": model,
                "device": self.device,
                "generation_options_overrides": overrides,
                "generation_options_defaults": defaults,
                "seed": seed,
                "max_context_tokens": pipeline_info["max_context_tokens"],
                "transformers_version": self.transformers_version,
                "model_revision": pipeline_info["model_revision"],
                "quantization": pipeline_info["quantization"],
                "prompt_tokens": prompt_tokens,
            },
            "wall_time_s": perf_counter() - start,
        }

