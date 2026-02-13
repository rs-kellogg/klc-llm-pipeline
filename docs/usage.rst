Usage
=====

Install
-------

.. code-block:: console

   $ mamba create --name klc-llm-pipeline-env python=3.13
   $ pip install git+https://github.com/rs-kellogg/klc-llm-pipeline.git

Load on KLC
-----------

.. code-block:: console

    $ module load klc-llm-pipeline/1.0

Start Ollama Server
-------------------

.. code-block:: console

    $ module load klc-llm-pipeline/1.0
    $ start_ollama
