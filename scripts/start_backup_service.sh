#!/usr/bin/env bash
#
# start_backup_service.sh - Auto-start wrapper for backup daemon
#
# Checks if the backup service is already running and starts it if not.
# Designed to be called at environment startup or login.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_SCRIPT="${SCRIPT_DIR}/auto_backup.sh"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/backup_startup.log"
PID_FILE="${LOG_DIR}/auto_backup.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local log_line="[${timestamp}] [${level}] ${message}"
    echo "$log_line" >> "$LOG_FILE"
    case "$level" in
        ERROR)   echo -e "${RED}${log_line}${NC}" ;;
        WARN)    echo -e "${YELLOW}${log_line}${NC}" ;;
        SUCCESS) echo -e "${GREEN}${log_line}${NC}" ;;
        *)       echo "$log_line" ;;
    esac
}

is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

cleanup_stale_pid() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE")"
        if ! kill -0 "$pid" 2>/dev/null; then
            log "WARN" "Removing stale PID file (dead PID: ${pid})"
            rm -f "$PID_FILE"
        fi
    fi
}

main() {
    mkdir -p "$LOG_DIR"

    log "INFO" "─── Backup service startup check ───"

    cleanup_stale_pid

    if is_running; then
        local pid
        pid="$(cat "$PID_FILE")"
        log "INFO" "Backup service already running (PID: ${pid}). Skipping."
        echo "Backup service already running (PID: ${pid})."
        return 0
    fi

    log "INFO" "Starting backup service..."
    if [[ ! -x "$BACKUP_SCRIPT" ]]; then
        chmod +x "$BACKUP_SCRIPT"
    fi

    nohup "$BACKUP_SCRIPT" --daemon >> "$LOG_FILE" 2>&1 &
    local new_pid=$!
    sleep 1

    if is_running; then
        log "SUCCESS" "Backup service started successfully (PID: ${new_pid})"
        echo "Backup service started (PID: ${new_pid})."
    else
        log "ERROR" "Failed to start backup service."
        echo "ERROR: Failed to start backup service. Check ${LOG_FILE}"
        return 1
    fi
}

main "$@"
