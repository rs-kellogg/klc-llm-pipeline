"""
Command-line interface for running shared prompts across multiple LLM backends.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import requests

from .config import load_config
from .runner import run_model_prompts
from .backends import get_backend


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger() -> logging.Logger:
    """
    Configure and return the application logger.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend validation
# ---------------------------------------------------------------------------

def check_ollama_server(server_url: str, logger: logging.Logger) -> None:
    """
    Validate connectivity to an Ollama server.

    Parameters
    ----------
    server_url : str
        Base URL of the Ollama server.
    logger : logging.Logger
        Logger instance for status reporting.

    Raises
    ------
    RuntimeError
        If the server cannot be reached or returns an error.
    """
    try:
        resp = requests.get(f"{server_url}/api/version", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Failed to reach Ollama server at {server_url}: {exc}"
        ) from exc

    version = resp.json().get("version", "unknown")
    logger.info("Connected to Ollama server %s (version %s)", server_url, version)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Build the CLI argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Run shared prompts across multiple LLM backends."
    )

    parser.add_argument("config", type=Path, help="Path to TOML config")

    parser.add_argument(
        "--backend",
        choices=["ollama", "huggingface"],
        help="Override LLM backend",
    )

    parser.add_argument(
        "--server-url",
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
        help="Run only models containing this string",
    )

    parser.add_argument(
        "--filter-prompt",
        help="Run only prompts containing this string",
    )

    return parser


# ---------------------------------------------------------------------------
# Backend resolution
# ---------------------------------------------------------------------------

def resolve_backend_name(args, config: dict) -> str:
    """
    Determine which backend should be used.

    Priority order:
    1. CLI argument
    2. Config file
    3. Default ("ollama")

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.
    config : dict
        Loaded configuration.

    Returns
    -------
    str
        Backend name.
    """
    return (
        args.backend
        or config.get("llm", {}).get("backend")
        or "ollama"
    )


def validate_backend_requirements(
    backend_name: str,
    args,
    logger: logging.Logger,
) -> None:
    """
    Validate backend-specific requirements.

    Parameters
    ----------
    backend_name : str
        Selected backend name.
    args : argparse.Namespace
        Parsed CLI arguments.
    logger : logging.Logger
        Logger instance.

    Raises
    ------
    SystemExit
        If validation fails.
    """
    if backend_name == "ollama":
        if args.server_url is None:
            logger.error(
                "Backend 'ollama' requires --server-url to be provided."
            )
            sys.exit(1)

        try:
            check_ollama_server(args.server_url, logger)
        except Exception as exc:
            logger.error(str(exc))
            sys.exit(1)


def initialize_backend(
    backend_name: str,
    server_url: Optional[str],
    logger: logging.Logger,
):
    """
    Initialize the selected backend.

    Parameters
    ----------
    backend_name : str
        Backend identifier.
    server_url : str | None
        Backend host URL.
    logger : logging.Logger
        Logger instance.

    Returns
    -------
    object
        Backend instance.
    """
    try:
        backend = get_backend(backend_name, host=server_url)
        logger.info("Using backend: %s", backend_name)
        return backend
    except Exception as exc:
        logger.error(
            "Failed to initialize backend '%s': %s",
            backend_name,
            exc,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    """
    Execute the CLI workflow.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.
    """
    logger = setup_logger()

    if not args.config.exists():
        logger.error("Config file not found: %s", args.config)
        sys.exit(1)

    config = load_config(args.config)

    backend_name = resolve_backend_name(args, config)
    validate_backend_requirements(backend_name, args, logger)
    backend = initialize_backend(backend_name, args.server_url, logger)

    stream_mode = args.stream or config.get("ollama", {}).get("stream", False)

    prompt_registry = config.get("prompts", {})
    models = config.get("models", [])

    if not models:
        logger.error("No models defined in config.")
        sys.exit(1)

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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

