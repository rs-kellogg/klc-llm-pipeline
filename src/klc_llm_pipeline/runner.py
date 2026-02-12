import sys
from pathlib import Path

from .prompts import resolve_prompt, load_prompts_from_file
from .output import save_result


def run_model_prompts(
    *,
    backend,
    model_cfg: dict,
    prompt_registry: dict,
    stream: bool,
    output_dir: Path,
    backend_name: str,
    filter_prompt: str | None = None,
    logger,
):
    model_name = model_cfg["name"]

    # Ensure model exists / is downloaded
    try:
        backend.ensure_model(model_name)
    except Exception as e:
        logger.error("Failed to prepare model '%s': %s", model_name, e)
        return

    prompt_ids = model_cfg.get("prompts", [])

    logger.info("=== Model: %s ===", model_name)

    for prompt_id in prompt_ids:
        if filter_prompt and filter_prompt not in prompt_id:
            continue

        try:
            pdef = resolve_prompt(prompt_id, prompt_registry)
        except KeyError as e:
            logger.error(e)
            continue

        # Merge model + prompt configuration
        system = pdef.get("system", model_cfg.get("system"))
        temperature = pdef.get("temperature", model_cfg.get("temperature"))
        options = {
            **model_cfg.get("options", {}),
            **pdef.get("options", {}),
        }

        logger.info(
            "Running prompt '%s' on model '%s' with options: %s",
            prompt_id,
            model_name,
            options,
        )

        # Load prompt text(s)
        if "prompt_file" in pdef:
            prompt_file = Path(pdef["prompt_file"])
            if not prompt_file.exists():
                logger.error("Prompt file not found: %s", prompt_file)
                continue
            prompts = load_prompts_from_file(prompt_file)
        else:
            prompts = [pdef["prompt"]]

        for idx, prompt_text in enumerate(prompts, start=1):
            run_id = f"{prompt_id}-{idx}" if len(prompts) > 1 else prompt_id

            logger.info("--- Prompt: %s ---", run_id)

            try:
                result = backend.run_prompt(
                    model=model_name,
                    prompt=prompt_text,
                    system=system,
                    temperature=temperature,
                    options=options,
                    stream=stream,
                )

                logger.info("Result:\n%s", result["text"])

                save_result(
                    output_dir=output_dir,
                    backend=backend_name,
                    model=model_name,
                    prompt_id=run_id,
                    prompt=prompt_text,
                    system=system,
                    result=result,
                )

            except Exception as e:
                logger.error("Error running prompt '%s': %s", run_id, e)

