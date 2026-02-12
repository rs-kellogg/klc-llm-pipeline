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
export SINGULARITYENV_OLLAMA_HOST=${OLLAMA_HOST} 

## Set your models directory

if [ -n "${OLLAMA_MODELS:-}" ]; then
    # OLLAMA_MODELS already set — use existing value
    :
elif [ -d "/scratch/$USER/" ]; then
    # /scratch/$USER exists — set custom models directory
    export OLLAMA_MODELS="/scratch/$USER/Ollama-Models"
else
    # /scratch/$USER does not exist — warn and fall back to default
    echo "Warning: OLLAMA_MODELS is not set and /scratch/$USER does not exist."
    echo "Models will be downloaded to the default location: ~/.ollama/"
fi

# Export to Singularity if OLLAMA_MODELS is set
if [ -n "${OLLAMA_MODELS:-}" ]; then
    export SINGULARITYENV_OLLAMA_MODELS="$OLLAMA_MODELS"
fi

echo "Ollama server will listen for request on the following port: ${OLLAMA_PORT}"
echo "Setting the folder for the Ollama Models to ${OLLAMA_MODELS}"

export OLLAMA_NUM_PARALLEL=4
export SINGULARITYENV_OLLAMA_NUM_PARALLEL=$OLLAMA_NUM_PARALLEL

echo "A reminder that Ollama will launch as many threads as there are cores on the node."
echo "Please consider passing the option 'num_thread' set to a value such as 12 when using the"
echo "ollama client."

# start Ollama service
export SLURM_JOBID=${SLURM_JOBID:="`hostname`"}
ollama serve &> serve_ollama_${SLURM_JOBID}.log &

# wait until Ollama service has been started
echo "Sleeping for 15 seconds for the Ollama server to fully start"
sleep 15

OLLAMA_PIDS=$(pgrep -u "$USER" -f "ollama serve")

if [[ -z "$OLLAMA_PIDS" ]]; then
  echo "No Ollama server processes found"
else
  for pid in $OLLAMA_PIDS; do
    echo "Found Ollama server PID: $pid"
    echo "To manually terminate the Ollama Server, run"
    echo "    kill -9 $pid"
  done
fi
