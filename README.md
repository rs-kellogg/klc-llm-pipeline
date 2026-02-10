# Running LLMs Locally on KLC

## Create Environment
```
eval "$('/hpc/software/mamba/24.3.0/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
source "/hpc/software/mamba/24.3.0/etc/profile.d/mamba.sh"
mamba create --prefix=./llm-pipeline-env python=3.13
python -m pip install .
```

## Start the Ollama Server
```
source ./helper_scripts/start_ollama_server.sh
```
