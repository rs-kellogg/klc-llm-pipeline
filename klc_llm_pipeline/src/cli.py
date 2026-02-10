import argparse
import sys
import logging
from pathlib import Path

from .config import load_config
from .runner import run_model_prompts
from .backends import get_backend


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def main():
    logger = setup_logger()

    parser = argparse.ArgumentParser(
        description="Run shared prompts across multiple LLM backends."
    )

    parser.add_argument(
        "config",
        type=Path,
        help="Path to TOML config",
    )

    parser.add_argument(
        "--backend",
        choices=["ollama", "huggingface"],
        help="Override LLM backend (ollama or huggingface)",
    )

    parser.add_argument(
        "--server-url",
        default="http://localhost:11434",
        help="Ollama server URL (ollama backend only)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Output directory",
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Force streaming mode",
    )

    parser.add_argument(
        "--filter-model",
        type=str,
        help="Run only models containing this string",
    )

    parser.add_argument(
        "--filter-prompt",
        type=str,
        help="Run only prompts containing this string",
    )

    args = parser.parse_args()

    if not args.config.exists():
        logger.error("Config file not found: %s", args.config)
        sys.exit(1)

    config = load_config(args.config)

    # -------------------------
    # Backend selection
    # -------------------------
    backend_name = (
        args.backend
        or config.get("llm", {}).get("backend")
        or "ollama"
    )

    try:
        backend = get_backend(
            backend_name,
            host=args.server_url,
        )
        logger.info("Using backend: %s", backend_name)
    except Exception as e:
        logger.error("Failed to initialize backend '%s': %s", backend_name, e)
        sys.exit(1)

    # -------------------------
    # Execution options
    # -------------------------
    stream_mode = (
        args.stream
        or config.get("ollama", {}).get("stream", False)
    )

    prompt_registry = config.get("prompts", {})
    models = config.get("models", [])

    if not models:
        logger.error("No models defined in config.")
        sys.exit(1)

    # -------------------------
    # Run models
    # -------------------------
    for model_cfg in models:
        if args.filter_model and args.filter_model not in model_cfg["name"]:
            continue

        run_model_prompts(
            backend=backend,
            model_cfg=model_cfg,
            prompt_registry=prompt_registry,
            stream=stream_mode,
            output_dir=args.output_dir,
            backend_name=backend_name,
            filter_prompt=args.filter_prompt,
            logger=logger,
        )


if __name__ == "__main__":
    main()
