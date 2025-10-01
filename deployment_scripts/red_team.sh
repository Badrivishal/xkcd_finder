#!/usr/bin/env bash
set -euo pipefail

# ssh_port_scan.sh
# Usage: ./ssh_port_scan.sh /path/to/private_key [host]
# Tries SSH on ports 22001..22035 and runs "whoami; hostname; uptime" for successful connections.
# Appends all findings to ~/ssh_port_scan.log

KEY_PATH="${1:-}"
HOST="${2:-paffenroth-23.dyn.wpi.edu}"
USER="student-admin"
PORT_START=22001
PORT_END=22035
CONNECT_TIMEOUT=5
LOGFILE="${HOME}/ssh_port_scan.log"

# Validate key argument
if [[ -z "$KEY_PATH" ]]; then
  echo "Usage: $0 /path/to/private_key [host]" >&2
  exit 2
fi

if [[ ! -f "$KEY_PATH" ]]; then
  echo "Error: Key file not found: $KEY_PATH" >&2
  exit 3
fi

if ! command -v ssh >/dev/null 2>&1; then
  echo "Error: ssh is required but not found in PATH." >&2
  exit 4
fi

# Header for this run in the log
run_ts=$(date --iso-8601=seconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")
{
  echo "===================="
  echo "SSH port scan run: ${run_ts}"
  echo "Host: ${HOST}"
  echo "Key: ${KEY_PATH}"
  echo "Ports: ${PORT_START}-${PORT_END}"
  echo ""
} >>"$LOGFILE"

echo "Starting scan ${PORT_START}-${PORT_END} against ${USER}@${HOST} (log: ${LOGFILE})"

found_any=0

for port in $(seq "$PORT_START" "$PORT_END"); do
  printf "Testing port %5d ... " "$port"
  tmp=$(mktemp)
  # run the verification commands on the remote host; BatchMode prevents password prompts
  if ssh -i "$KEY_PATH" -p "$port" \
         -o StrictHostKeyChecking=no -o ConnectTimeout="$CONNECT_TIMEOUT" \
         -o BatchMode=yes -o IdentitiesOnly=yes \
         "${USER}@${HOST}" "whoami; hostname; uptime" >"$tmp" 2>&1; then
    printf "SUCCESS\n"
    found_any=1
    ts=$(date +"%Y-%m-%d %H:%M:%S")
    {
      echo "----"
      echo "Port: $port"
      echo "Time: $ts"
      echo "Result:"
      cat "$tmp"
      echo "----"
      echo ""
    } >>"$LOGFILE"
    echo "  -> Logged successful result for port $port to $LOGFILE"
  else
    ssh_ret=$?
    printf "no connection (exit=%d)\n" "$ssh_ret"
    echo "$(date +"%Y-%m-%d %H:%M:%S") - port $port - exit $ssh_ret" >>"$LOGFILE"
  fi
  rm -f "$tmp"
done

if [[ $found_any -eq 1 ]]; then
  echo "One or more successful SSH connections were logged to: $LOGFILE"
  exit 0
else
  echo "No reachable SSH server found in ports ${PORT_START}-${PORT_END}."
  exit 1
fi
