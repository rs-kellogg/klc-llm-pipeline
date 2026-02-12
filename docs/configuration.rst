Configuration
=============

The application is configured using a ``config.toml`` file.

The configuration consists of three main sections:

- ``[llm]`` – Selects the backend
- ``[prompts.*]`` – Shared prompt registry
- ``[[models]]`` – Model definitions and runtime options

Overview
--------

A minimal example configuration:

.. code-block:: toml

   [llm]
   backend = "ollama"

   [prompts.kellogg]
   prompt = "Tell me about the Kellogg School of Management"
   system = "You love AI."

   [[models]]
   name = "llama3:8b"
   prompts = ["kellogg"]


LLM Backend
-----------

.. code-block:: toml

   [llm]
   backend = "ollama"

``backend``
    Selects which inference backend to use.

    Currently configured:

    - ``"ollama"`` – Inference via Ollama
    - ``"huggingface"`` – Inference via HuggingFace/Transformers


Prompt Registry
---------------

Prompts are defined once and can be reused across multiple models.

Each prompt has:

- ``prompt`` – The user message
- ``system`` – The system instruction

Example:

.. code-block:: toml

   [prompts.kellogg]
   prompt = """
   Tell me about the Kellogg School of Management
   """

   system = """
   You love AI.
   """

   [prompts.northwestern]
   prompt = """
   Tell me about Northwestern
   """

   system = """
   You love AI.
   """

Prompt blocks are referenced by name inside model definitions.


Models
------

Each model is defined using a ``[[models]]`` block.

Example:

.. code-block:: toml

   [[models]]
   name = "llama3:8b"
   prompts = ["kellogg"]

``name``
    The model identifier. For Ollama, this corresponds to the local model tag
    (e.g., ``llama3:8b``, ``mistral:7b``).

``prompts``
    A list of prompt names defined in the prompt registry that this model should run.


Multiple Models
---------------

You may define multiple models:

.. code-block:: toml

   [[models]]
   name = "mistral:7b"
   prompts = ["northwestern"]

   [[models]]
   name = "qwen3:8b"
   prompts = ["northwestern"]


Model Options (Ollama Backend)
------------------------------

Models may optionally include an ``[models.options]`` section
to configure runtime generation parameters.

Example:

.. code-block:: toml

   [[models]]
   name = "llama3:8b"
   prompts = ["kellogg"]

       [models.options]
       num_ctx = 4096
       repeat_last_n = 64
       repeat_penalty = 1.1
       temperature = 0.7
       seed = 42
       num_predict = 128
       top_k = 40
       top_p = 0.9
       min_p = 0.05
       num_thread = 8


Available Options
~~~~~~~~~~~~~~~~~

``num_ctx`` (int, default: 2048)
    Context window size. Larger values allow the model to consider more prior tokens.

``repeat_last_n`` (int, default: 64)
    Number of tokens to look back when applying repetition penalty.
    ``0`` disables. ``-1`` uses ``num_ctx``.

``repeat_penalty`` (float, default: 1.1)
    Controls repetition suppression.
    Higher values reduce repetition.

``temperature`` (float, default: 0.8)
    Sampling temperature.
    Lower values produce more deterministic outputs.
    Higher values increase creativity.

``seed`` (int, default: 0)
    Random seed for reproducible generation.
    ``0`` enables random seeding.

``num_predict`` (int, default: -1)
    Maximum number of tokens to generate.
    ``-1`` allows unlimited generation.

``top_k`` (int, default: 40)
    Top-K sampling parameter.
    Higher values increase diversity.

``top_p`` (float, default: 0.9)
    Nucleus sampling probability threshold.

``min_p`` (float, default: 0.0)
    Minimum probability threshold relative to the most likely token.
    Alternative filtering strategy to ``top_p``.

``num_thread`` (int)
    Number of parallel threads used during inference.


Complete Example
----------------

Full configuration example:

.. code-block:: toml

   [llm]
   backend = "ollama"

   [prompts.kellogg]
   prompt = """
   Tell me about the Kellogg School of Management
   """
   system = """
   You love AI.
   """

   [prompts.northwestern]
   prompt = """
   Tell me about Northwestern
   """
   system = """
   You love AI.
   """

   [[models]]
   name = "llama3:8b"
   prompts = ["kellogg"]

       [models.options]
       num_ctx = 4096
       repeat_last_n = 64
       repeat_penalty = 1.1
       temperature = 0.7
       seed = 42
       num_predict = 128
       top_k = 40
       top_p = 0.9
       min_p = 0.05
       num_thread = 8

   [[models]]
   name = "mistral:7b"
   prompts = ["northwestern"]

   [[models]]
   name = "qwen3:8b"
   prompts = ["northwestern"]

