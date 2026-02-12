Command Line Interface
======================

The ``klc-llm-pipeline`` command enables helps streamline trying out open-source models on KLC.

Examples
--------

Log into a KLC node and run the following

.. code-block:: console

   $ mkdir test_klc_llm_pipeline
   $ cd test_klc_llm_pipeline
   $ module load klc-llm-pipeline/1.0
   $ start_ollama

Ollama server should now be started and a file that contains the server logs called `serve_ollama_*` should now
appear in this folder.

Now create a file called `config.ollama.toml` and add the following content.


.. code-block:: toml

   [llm]
   backend = "ollama"

   [prompts.kellogg]
   prompt = "Tell me about the Kellogg School of Management"
   system = "You love AI."

   [[models]]
   name = "llama3:8b"
   prompts = ["kellogg"]

       [models.options]
       temperature = 0.7
       seed = 42
       num_thread = 8

Now run the pipeline.

.. code-block:: console

     $ klc-llm-pipeline config.ollama.toml --server-url http://localhost:${OLLAMA_PORT}

If this was successful, you should see a folder called `results` in your current working directory and be able to run

.. code-block:: console

    $ cat results/ollama/llama3\:8b/kellogg.txt 

in order to see the log.

Full Argument Reference For `klc-llm-pipeline`
----------------------------------------------

.. argparse::
   :module: klc_llm_pipeline.cli
   :func: build_parser
   :prog: klc-llm-pipeline
