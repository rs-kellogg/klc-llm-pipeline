Command Line Interface
======================

The ``klc-llm-pipeline`` command provides utilities for interacting with
Redivis datasets.

Examples
--------

Upload a new dataset version with two tables:

.. code-block:: bash

     mkdir test_klc_llm_pipeline; cd test_klc_llm_pipeline
     module load klc-llm-pipeline/1.0
     start_ollama
     cp /kellogg/software/envs/klc-llm-pipeline/share/klc_llm_pipeline/examples/config.ollama.toml .
     cp /kellogg/software/envs/klc-llm-pipeline/share/klc_llm_pipeline/examples/config.hf.toml .
     # Ollama Backend Example
     klc-llm-pipeline config.ollama.toml --server-url http://localhost:${OLLAMA_PORT}
     # HF/Transformers Backend Example
     klc-llm-pipeline config.hf.toml


Full Argument Reference
-----------------------

.. argparse::
   :module: klc_llm_pipeline.cli
   :func: build_parser
   :prog: klc-llm-pipeline
