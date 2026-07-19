#!/usr/bin/env bash
#
# auto_backup.sh - Automatic git backup script with file monitoring
#
# Monitors project directory for changes, commits, and pushes automatically.
# Supports inotifywait (preferred) or polling fallback.
#
# Usage:
#   ./auto_backup.sh              # Run in foreground
#   ./auto_backup.sh --daemon     # Run as background daemon
#
# Environment variables:
#   BACKUP_PROJECT_DIR   - Project directory to monitor (default: script's parent's parent)
#   BACKUP_INTERVAL      - Polling interval in seconds (default: 30)
#   BACKUP_BRANCH        - Git branch to push to (default: auto-detect)
#   BACKUP_EXCLUDE       - Glob patterns to exclude, comma-separated
#   BACKUP_USE_INOTIFY   - Force inotifywait usage (1=yes, 0=no, auto-detect by default)
#   BACKUP_COMMIT_PREFIX - Commit message prefix (default: "Auto-backup:")
#

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${BACKUP_PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/backup.log"
PID_FILE="${LOG_DIR}/auto_backup.pid"
POLL_INTERVAL="${BACKUP_INTERVAL:-30}"
COMMIT_PREFIX="${BACKUP_COMMIT_PREFIX:-Auto-backup:}"
BRANCH="${BACKUP_BRANCH:-}"
USE_INOTIFY="${BACKUP_USE_INOTIFY:-auto}"
EXCLUDE_PATTERNS="${BACKUP_EXCLUDE:-}"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ─── Logging ────────────────────────────────────────────────────────────────────

log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local log_line="[${timestamp}] [${level}] ${message}"

    # Always write to log file
    echo "$log_line" >> "$LOG_FILE"

    # Write to stdout if not in daemon mode
    if [[ "${DAEMON_MODE:-0}" -ne 1 ]]; then
        case "$level" in
            ERROR)   echo -e "${RED}${log_line}${NC}" ;;
            WARN)    echo -e "${YELLOW}${log_line}${NC}" ;;
            SUCCESS) echo -e "${GREEN}${log_line}${NC}" ;;
            *)       echo "$log_line" ;;
        esac
    fi
}

# ─── Signal Handling & Cleanup ──────────────────────────────────────────────────

RUNNING=1

cleanup() {
    log "INFO" "Shutdown signal received. Cleaning up..."
    RUNNING=0

    # Remove PID file
    if [[ -f "$PID_FILE" ]]; then
        rm -f "$PID_FILE"
        log "INFO" "PID file removed: ${PID_FILE}"
    fi

    log "INFO" "Auto-backup stopped."
    exit 0
}

trap cleanup SIGTERM SIGINT SIGHUP

# ─── PID File Management ───────────────────────────────────────────────────────

check_pid_file() {
    mkdir -p "$(dirname "$PID_FILE")"

    if [[ -f "$PID_FILE" ]]; then
        local old_pid
        old_pid="$(cat "$PID_FILE")"

        # Check if process is still running (and not our own PID)
        if [[ "$old_pid" != "$$" ]] && kill -0 "$old_pid" 2>/dev/null; then
            echo "ERROR: Another instance is already running (PID: ${old_pid})."
            echo "       Remove ${PID_FILE} if this is stale."
            exit 1
        else
            log "WARN" "Removing stale PID file (old PID: ${old_pid})."
            rm -f "$PID_FILE"
        fi
    fi

    echo "$$" > "$PID_FILE"
    log "INFO" "PID file created: ${PID_FILE} (PID: $$)"
}

# ─── Git Helpers ────────────────────────────────────────────────────────────────

get_current_branch() {
    if [[ -n "$BRANCH" ]]; then
        echo "$BRANCH"
    else
        git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main"
    fi
}

has_remote() {
    local remote_name
    remote_name="$(git -C "$PROJECT_DIR" remote 2>/dev/null | head -1)"
    [[ -n "$remote_name" ]]
}

has_staged_changes() {
    ! git -C "$PROJECT_DIR" diff --cached --quiet 2>/dev/null
}

has_working_changes() {
    ! git -C "$PROJECT_DIR" status --porcelain 2>/dev/null | grep -q .
}

is_git_repository() {
    git -C "$PROJECT_DIR" rev-parse --git-dir &>/dev/null
}

# ─── Core Backup Logic ─────────────────────────────────────────────────────────

perform_backup() {
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local commit_msg="${COMMIT_PREFIX} ${timestamp}"

    log "INFO" "─── Backup cycle started ───"

    # Verify git repository
    if ! is_git_repository; then
        log "ERROR" "Not a git repository: ${PROJECT_DIR}"
        return 1
    fi

    # Stage all changes
    log "INFO" "Staging changes..."
    if ! git -C "$PROJECT_DIR" add . 2>>"$LOG_FILE"; then
        log "ERROR" "Failed to stage changes (git add .). Check permissions."
        return 1
    fi

    # Check if there are staged changes
    if ! has_staged_changes; then
        log "INFO" "No changes to commit."
        return 0
    fi

    log "INFO" "Changes detected. Committing..."

    # Commit
    if ! git -C "$PROJECT_DIR" commit -m "$commit_msg" 2>>"$LOG_FILE"; then
        log "ERROR" "Failed to commit. Possible merge conflict or hook rejection."
        log "INFO" "Attempting to abort staged changes..."
        git -C "$PROJECT_DIR" reset HEAD -- 2>/dev/null || true
        return 1
    fi

    log "SUCCESS" "Committed: ${commit_msg}"

    # Push if remote exists
    if has_remote; then
        local branch
        branch="$(get_current_branch)"
        log "INFO" "Pushing to remote (branch: ${branch})..."

        if ! git -C "$PROJECT_DIR" push origin "$branch" 2>>"$LOG_FILE"; then
            local push_exit=$?

            # Detect specific error types
            if [[ $push_exit -eq 128 ]]; then
                log "ERROR" "Network error during push. Check your internet connection."
            elif git -C "$PROJECT_DIR" pull --rebase origin "$branch" 2>/dev/null; then
                log "WARN" "Rebased on remote changes. Retrying push..."
                if git -C "$PROJECT_DIR" push origin "$branch" 2>>"$LOG_FILE"; then
                    log "SUCCESS" "Push succeeded after rebase."
                else
                    log "ERROR" "Push failed even after rebase. Manual intervention needed."
                    return 1
                fi
            else
                log "ERROR" "Push failed. Exit code: ${push_exit}. Manual merge may be needed."
                return 1
            fi
        else
            log "SUCCESS" "Pushed to remote (branch: ${branch})"
        fi
    else
        log "WARN" "No remote configured. Skipping push."
    fi

    log "INFO" "─── Backup cycle completed ───"
    return 0
}

# ─── Monitoring: inotifywait ────────────────────────────────────────────────────

monitor_inotify() {
    log "INFO" "Using inotifywait for file monitoring."

    # Build exclude arguments
    local exclude_args=()
    if [[ -n "$EXCLUDE_PATTERNS" ]]; then
        IFS=',' read -ra patterns <<< "$EXCLUDE_PATTERNS"
        for pattern in "${patterns[@]}"; do
            exclude_args+=(--exclude "$pattern")
        done
    fi

    # Debounce: wait for file system to settle
    local debounce_counter=0
    local debounce_limit=3

    while [[ $RUNNING -eq 1 ]]; do
        # Watch for modify, create, delete, move events recursively
        inotifywait -r -q \
            -e modify -e create -e delete -e move \
            --timeout "$POLL_INTERVAL" \
            "${exclude_args[@]}" \
            --include '\.(py|js|ts|tsx|jsx|go|rs|java|c|cpp|h|hpp|rb|php|sh|yaml|yml|json|toml|md|txt|env|cfg|conf|ini|html|css|sql|dockerfile|docker-compose)$' \
            "$PROJECT_DIR" 2>/dev/null

        # Debounce multiple rapid changes
        if [[ $? -eq 0 ]]; then
            debounce_counter=$((debounce_counter + 1))
            if [[ $debounce_counter -ge $debounce_limit ]]; then
                perform_backup || true
                debounce_counter=0
            fi
        else
            # Timeout (no events) - reset debounce
            debounce_counter=0
        fi
    done
}

# ─── Monitoring: Polling Fallback ───────────────────────────────────────────────

monitor_polling() {
    log "INFO" "Using polling mode (interval: ${POLL_INTERVAL}s)."

    local last_status=""

    # Capture initial status
    last_status="$(git -C "$PROJECT_DIR" status --porcelain 2>/dev/null)"

    # Commit any existing uncommitted changes at startup
    if [[ -n "$last_status" ]]; then
        log "INFO" "Existing uncommitted changes detected at startup. Committing..."
        perform_backup || true
        last_status="$(git -C "$PROJECT_DIR" status --porcelain 2>/dev/null)"
    fi

    while [[ $RUNNING -eq 1 ]]; do
        sleep "$POLL_INTERVAL" &
        wait $! 2>/dev/null || true

        [[ $RUNNING -eq 1 ]] || break

        local current_status
        current_status="$(git -C "$PROJECT_DIR" status --porcelain 2>/dev/null)"

        if [[ "$current_status" != "$last_status" ]]; then
            log "INFO" "Change detected via polling."
            perform_backup || true
            last_status="$(git -C "$PROJECT_DIR" status --porcelain 2>/dev/null)"
        fi
    done
}

# ─── Daemon Management ─────────────────────────────────────────────────────────

start_daemon() {
    check_pid_file

    log "INFO" "Starting auto-backup daemon..."
    log "INFO" "Project: ${PROJECT_DIR}"
    log "INFO" "Log: ${LOG_FILE}"

    # Check for inotifywait availability
    local use_inotify="$USE_INOTIFY"
    if [[ "$use_inotify" == "auto" ]]; then
        if command -v inotifywait &>/dev/null; then
            use_inotify="1"
        else
            use_inotify="0"
        fi
    fi

    if [[ "$use_inotify" == "1" ]]; then
        if command -v inotifywait &>/dev/null; then
            monitor_inotify
        else
            log "WARN" "inotifywait requested but not installed. Falling back to polling."
            log "WARN" "Install with: sudo apt-get install inotify-tools"
            monitor_polling
        fi
    else
        monitor_polling
    fi
}

stop_daemon() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            log "INFO" "Stopping auto-backup (PID: ${pid})..."
            kill -TERM "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
                log "WARN" "Force-killed process ${pid}."
            fi
            rm -f "$PID_FILE"
            echo "Auto-backup stopped."
        else
            log "WARN" "PID ${pid} not running. Cleaning up stale PID file."
            rm -f "$PID_FILE"
            echo "Stale PID file cleaned up."
        fi
    else
        echo "No auto-backup process running."
    fi
}

show_status() {
    echo "=== Auto-Backup Status ==="
    echo "Project:  ${PROJECT_DIR}"
    echo "Log:      ${LOG_FILE}"
    echo "PID File: ${PID_FILE}"

    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            echo "Status:   RUNNING (PID: ${pid})"
        else
            echo "Status:   STALE PID (dead process)"
        fi
    else
        echo "Status:   NOT RUNNING"
    fi

    echo ""
    echo "=== Recent Log Entries ==="
    tail -10 "$LOG_FILE" 2>/dev/null || echo "(no log entries yet)"
}

show_help() {
    cat <<'HELP'
auto_backup.sh - Automatic git backup with file monitoring

Usage:
  ./auto_backup.sh              Run in foreground (interactive)
  ./auto_backup.sh --daemon     Run as background daemon
  ./auto_backup.sh --stop       Stop background daemon
  ./auto_backup.sh --status     Show daemon status
  ./auto_backup.sh --help       Show this help

Environment Variables:
  BACKUP_PROJECT_DIR     Project directory (default: parent of scripts/)
  BACKUP_INTERVAL        Polling interval in seconds (default: 30)
  BACKUP_BRANCH          Git branch to push (default: auto-detect)
  BACKUP_EXCLUDE         Comma-separated exclude globs
  BACKUP_USE_INOTIFY     Force inotify (1) or polling (0), default: auto
  BACKUP_COMMIT_PREFIX   Commit message prefix (default: "Auto-backup:")

Examples:
  BACKUP_INTERVAL=10 ./auto_backup.sh --daemon
  BACKUP_BRANCH=develop ./auto_backup.sh --daemon
  BACKUP_EXCLUDE="*.log,*.tmp,node_modules" ./auto_backup.sh

Requirements:
  - git (required)
  - inotifywait (optional, recommended) - install: apt-get install inotify-tools
HELP
}

# ─── Main ───────────────────────────────────────────────────────────────────────

main() {
    # Ensure log directory exists
    mkdir -p "$LOG_DIR"

    case "${1:-}" in
        --daemon|-d)
            DAEMON_MODE=1
            log "INFO" "═══════════════════════════════════════════════════"
            log "INFO" "  Auto-Backup Daemon Starting"
            log "INFO" "  Project: ${PROJECT_DIR}"
            log "INFO" "  PID File: ${PID_FILE}"
            log "INFO" "═══════════════════════════════════════════════════"
            start_daemon
            ;;
        --stop|-k)
            stop_daemon
            ;;
        --status|-s)
            show_status
            ;;
        --help|-h)
            show_help
            ;;
        "")
            DAEMON_MODE=0
            log "INFO" "═══════════════════════════════════════════════════"
            log "INFO" "  Auto-Backup Starting (foreground mode)"
            log "INFO" "  Project: ${PROJECT_DIR}"
            log "INFO" "  Press Ctrl+C to stop"
            log "INFO" "═══════════════════════════════════════════════════"
            check_pid_file
            start_daemon
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
}

main "$@"
