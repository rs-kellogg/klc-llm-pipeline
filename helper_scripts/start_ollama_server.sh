# Source in all the helper functions - No need to change any of this
source_helpers () {
  # Generate random integer in range [$1..$2]
  random_number () {
    shuf -i ${1}-${2} -n 1
  }
  export -f random_number

  port_used_python() {
    python -c "import socket; socket.socket().connect(('$1',$2))" >/dev/null 2>&1
  }

  port_used_python3() {
    python3 -c "import socket; socket.socket().connect(('$1',$2))" >/dev/null 2>&1
  }

  port_used_nc(){
    nc -w 2 "$1" "$2" < /dev/null > /dev/null 2>&1
  }

  port_used_lsof(){
    lsof -i :"$2" >/dev/null 2>&1
  }

  port_used_bash(){
    local bash_supported=$(strings /bin/bash 2>/dev/null | grep tcp)
    if [ "$bash_supported" == "/dev/tcp/*/*" ]; then
      (: < /dev/tcp/$1/$2) >/dev/null 2>&1
    else
      return 127
    fi
  }

  # Check if port $1 is in use
  port_used () {
    local port="${1#*:}"
    local host=$((expr "${1}" : '\(.*\):' || echo "localhost") | awk 'END{print $NF}')
    local port_strategies=(port_used_nc port_used_lsof port_used_bash port_used_python port_used_python3)

    for strategy in ${port_strategies[@]};
    do
      $strategy $host $port
      status=$?
      if [[ "$status" == "0" ]] || [[ "$status" == "1" ]]; then
        return $status
      fi
    done

    return 127
  }
  export -f port_used

  # Find available port in range [$2..$3] for host $1
  # Default: [2000..65535]
  find_port () {
    local host="${1:-localhost}"
    local port=$(random_number "${2:-2000}" "${3:-65535}")
    while port_used "${host}:${port}"; do
      port=$(random_number "${2:-2000}" "${3:-65535}")
    done
    echo "${port}"
  }
  export -f find_port

  # Wait $2 seconds until port $1 is in use
  # Default: wait 30 seconds
  wait_until_port_used () {
    local port="${1}"
    local time="${2:-30}"
    for ((i=1; i<=time*2; i++)); do
      port_used "${port}"
      port_status=$?
      if [ "$port_status" == "0" ]; then
        return 0
      elif [ "$port_status" == "127" ]; then
         echo "commands to find port were either not found or inaccessible."
         echo "command options are lsof, nc, bash's /dev/tcp, or python (or python3) with socket lib."
         return 127
      fi
      sleep 0.5
    done
    return 1
  }
  export -f wait_until_port_used

}
export -f source_helpers

source_helpers

# Find available port to run server on
OLLAMA_PORT=$(find_port localhost 7000 11000)
export OLLAMA_PORT

module load ollama/0.12.10

export OLLAMA_HOST=0.0.0.0:${OLLAMA_PORT}
export SINGULARITYENV_OLLAMA_HOST=0.0.0.0:${OLLAMA_PORT} 

## Set your models directory
export OLLAMA_MODELS=/scratch/$USER/Ollama-Models
export SINGULARITYENV_OLLAMA_MODELS=/scratch/$USER/Ollama-Models

echo "Setting the folder for the Ollama Models to ${OLLAMA_MODELS}"

export OLLAMA_NUM_PARALLEL=16
export SINGULARITYENV_OLLAMA_NUM_PARALLEL=16

echo "Setting the number of CPU Threads Ollama can use to ${OLLAMA_NUM_PARALLEL}"

# start Ollama service
export SLURM_JOBID=${SLURM_JOBID:="`hostname`"}
ollama serve &> serve_ollama_${SLURM_JOBID}.log &
OLLAMA_PID=$!

echo "Ollama server started on port ${OLLAMA_PORT}"
echo "  PID: ${OLLAMA_PID}"
echo "  To stop it manually, run:"
echo "    kill -9 ${OLLAMA_PID}"

echo "Sleeping for 15 seconds for the Ollama server to fully start"
# wait until Ollama service has been started
sleep 15
