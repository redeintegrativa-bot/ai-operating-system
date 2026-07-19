#!/usr/bin/env bash
#
# view_logs.sh - Log viewer for backup service
#
# Features:
#   - View last N lines of log
#   - Search logs by date/time
#   - Filter by log level (INFO, WARN, ERROR, SUCCESS)
#   - Color-coded output for terminal
#
# Usage:
#   ./view_logs.sh                  # Show last 50 lines
#   ./view_logs.sh -n 100           # Show last 100 lines
#   ./view_logs.sh -l ERROR         # Show only ERROR lines
#   ./view_logs.sh -d 2025-01-15    # Show logs from specific date
#   ./view_logs.sh -t "14:30"       # Show logs from specific time
#   ./view_logs.sh -s "connection"  # Search for text
#   ./view_logs.sh -f               # Follow log in real-time
#
# Environment variables:
#   BACKUP_PROJECT_DIR - Project directory (default: parent of scripts/)
#

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${BACKUP_PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"
LOG_FILE="${PROJECT_DIR}/logs/backup.log"

# ─── Colors ─────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Help ───────────────────────────────────────────────────────────────────────

show_help() {
    cat <<'HELP'
view_logs.sh - Log viewer for backup service

Usage:
  ./view_logs.sh [OPTIONS]

Options:
  -n, --lines N       Show last N lines (default: 50)
  -l, --level LEVEL   Filter by level: INFO, WARN, ERROR, SUCCESS
  -d, --date DATE     Filter by date (YYYY-MM-DD format)
  -t, --time TIME     Filter by time (HH:MM format)
  -s, --search TEXT   Search for text in log lines
  -f, --follow        Follow log in real-time (tail -f)
  -a, --all           Show all log lines (no limit)
  -h, --help          Show this help message

Examples:
  ./view_logs.sh -n 100              # Last 100 lines
  ./view_logs.sh -l ERROR            # Only ERROR lines
  ./view_logs.sh -d 2025-01-15       # Logs from Jan 15, 2025
  ./view_logs.sh -t "14:30"          # Logs at 14:30
  ./view_logs.sh -s "push failed"    # Search for "push failed"
  ./view_logs.sh -l WARN -d 2025-01-15  # WARN from specific date
  ./view_logs.sh -f                  # Follow real-time

Log Levels (color-coded):
  INFO    - Cyan
  WARN    - Yellow
  ERROR   - Red
  SUCCESS - Green
HELP
}

# ─── Colorization ───────────────────────────────────────────────────────────────

colorize_line() {
    local line="$1"
    case "$line" in
        *"[ERROR]"*)   echo -e "${RED}${line}${NC}" ;;
        *"[WARN]"*)    echo -e "${YELLOW}${line}${NC}" ;;
        *"[SUCCESS]"*) echo -e "${GREEN}${line}${NC}" ;;
        *"[INFO]"*)    echo -e "${CYAN}${line}${NC}" ;;
        *)             echo "$line" ;;
    esac
}

colorize_output() {
    while IFS= read -r line; do
        colorize_line "$line"
    done
}

# ─── Validation ─────────────────────────────────────────────────────────────────

validate_log_file() {
    if [[ ! -f "$LOG_FILE" ]]; then
        echo -e "${RED}ERROR: Log file not found: ${LOG_FILE}${NC}" >&2
        echo "Make sure the backup service has been run at least once." >&2
        exit 1
    fi

    if [[ ! -r "$LOG_FILE" ]]; then
        echo -e "${RED}ERROR: Log file not readable: ${LOG_FILE}${NC}" >&2
        echo "Check file permissions." >&2
        exit 1
    fi
}

validate_date() {
    local date_str="$1"
    if ! [[ "$date_str" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo -e "${RED}ERROR: Invalid date format: ${date_str}${NC}" >&2
        echo "Use YYYY-MM-DD format (e.g., 2025-01-15)." >&2
        exit 1
    fi
}

validate_level() {
    local level="$1"
    case "$level" in
        INFO|WARN|ERROR|SUCCESS) return 0 ;;
        *)
            echo -e "${RED}ERROR: Invalid log level: ${level}${NC}" >&2
            echo "Valid levels: INFO, WARN, ERROR, SUCCESS" >&2
            exit 1
            ;;
    esac
}

# ─── Main Logic ─────────────────────────────────────────────────────────────────

main() {
    local num_lines=50
    local filter_level=""
    local filter_date=""
    local filter_time=""
    local search_text=""
    local follow_mode=0
    local show_all=0

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--lines)
                num_lines="$2"
                shift 2
                ;;
            -l|--level)
                filter_level="$2"
                shift 2
                ;;
            -d|--date)
                filter_date="$2"
                shift 2
                ;;
            -t|--time)
                filter_time="$2"
                shift 2
                ;;
            -s|--search)
                search_text="$2"
                shift 2
                ;;
            -f|--follow)
                follow_mode=1
                shift
                ;;
            -a|--all)
                show_all=1
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}" >&2
                echo "Use --help for usage information." >&2
                exit 1
                ;;
        esac
    done

    # Validate inputs
    validate_log_file
    [[ -n "$filter_level" ]] && validate_level "$filter_level"
    [[ -n "$filter_date" ]] && validate_date "$filter_date"

    # Build grep command
    local grep_args=()
    [[ -n "$filter_level" ]] && grep_args+=(-e "\[${filter_level}\]")
    [[ -n "$search_text" ]] && grep_args+=(-e "$search_text")

    # Follow mode
    if [[ $follow_mode -eq 1 ]]; then
        echo -e "${BOLD}Following log file (Ctrl+C to stop)...${NC}"
        echo -e "${BOLD}File: ${LOG_FILE}${NC}"
        echo ""
        if [[ ${#grep_args[@]} -gt 0 ]]; then
            tail -f "$LOG_FILE" | grep --line-buffered "${grep_args[@]}" | colorize_output
        else
            tail -f "$LOG_FILE" | colorize_output
        fi
        exit 0
    fi

    # Read and filter log lines
    local lines
    if [[ $show_all -eq 1 ]]; then
        lines="$(cat "$LOG_FILE")"
    else
        lines="$(tail -n "$num_lines" "$LOG_FILE")"
    fi

    # Apply date filter
    if [[ -n "$filter_date" ]]; then
        lines="$(echo "$lines" | grep "^\\[${filter_date}" || true)"
    fi

    # Apply time filter
    if [[ -n "$filter_time" ]]; then
        lines="$(echo "$lines" | grep "${filter_time}" || true)"
    fi

    # Apply level/search filters
    if [[ ${#grep_args[@]} -gt 0 ]]; then
        lines="$(echo "$lines" | grep "${grep_args[@]}" || true)"
    fi

    # Check if we have results
    if [[ -z "$lines" ]]; then
        echo -e "${YELLOW}No matching log entries found.${NC}"
        echo "Log file: ${LOG_FILE}"
        echo "Total lines in log: $(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)"
        exit 0
    fi

    # Display results with color
    echo "$lines" | colorize_output

    # Show count
    local count
    count="$(echo "$lines" | wc -l)"
    echo ""
    echo -e "${BOLD}Showing ${count} log entries.${NC}"
}

main "$@"
