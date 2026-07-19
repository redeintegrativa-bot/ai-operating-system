#!/usr/bin/env bash
#
# cleanup_logs.sh - Log cleanup and archival for backup service
#
# Features:
#   - Remove logs older than N days (default: 30)
#   - Archive old logs to compressed tar.gz format
#   - Run manually or via cron
#   - Dry-run mode for safe preview
#
# Usage:
#   ./cleanup_logs.sh                    # Remove logs older than 30 days
#   ./cleanup_logs.sh -d 7               # Remove logs older than 7 days
#   ./cleanup_logs.sh -a                 # Archive before removing
#   ./cleanup_logs.sh -a --archive-dir /backups/logs
#   ./cleanup_logs.sh -n                 # Dry run (preview only)
#   ./cleanup_logs.sh -v                 # Verbose output
#
# Cron example (daily at 2 AM):
#   0 2 * * * /root/ai-operating-system/scripts/cleanup_logs.sh -a
#
# Environment variables:
#   BACKUP_PROJECT_DIR    - Project directory (default: parent of scripts/)
#   LOG_RETENTION_DAYS    - Days to keep logs (default: 30)
#   LOG_ARCHIVE_DIR       - Archive directory (default: logs/archive/)
#

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${BACKUP_PROJECT_DIR:-$(dirname "$SCRIPT_DIR")}"
LOG_DIR="${PROJECT_DIR}/logs"
ARCHIVE_DIR="${LOG_ARCHIVE_DIR:-${LOG_DIR}/archive}"
RETENTION_DAYS="${LOG_RETENTION_DAYS:-30}"
DRY_RUN=0
VERBOSE=0
ARCHIVE=0

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
cleanup_logs.sh - Log cleanup and archival for backup service

Usage:
  ./cleanup_logs.sh [OPTIONS]

Options:
  -d, --days N        Remove logs older than N days (default: 30)
  -a, --archive       Archive logs before removing
  --archive-dir DIR   Directory for archives (default: logs/archive/)
  -n, --dry-run       Preview what would be done without making changes
  -v, --verbose       Show detailed output
  -h, --help          Show this help message

Examples:
  ./cleanup_logs.sh                    # Remove logs >30 days old
  ./cleanup_logs.sh -d 7               # Remove logs >7 days old
  ./cleanup_logs.sh -a                 # Archive then remove old logs
  ./cleanup_logs.sh -a -n              # Preview archive + removal
  ./cleanup_logs.sh -v -a -d 14        # Verbose, archive, 14-day retention

Cron Setup (daily at 2 AM):
  crontab -e
  0 2 * * * /root/ai-operating-system/scripts/cleanup_logs.sh -a >> /root/ai-operating-system/logs/cleanup.log 2>&1

Environment Variables:
  LOG_RETENTION_DAYS    Days to keep logs (default: 30)
  LOG_ARCHIVE_DIR       Archive directory (default: logs/archive/)
HELP
}

# ─── Logging ────────────────────────────────────────────────────────────────────

log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

    case "$level" in
        INFO)    echo -e "${CYAN}[${timestamp}] [INFO]    ${message}${NC}" ;;
        WARN)    echo -e "${YELLOW}[${timestamp}] [WARN]    ${message}${NC}" ;;
        ERROR)   echo -e "${RED}[${timestamp}] [ERROR]   ${message}${NC}" ;;
        SUCCESS) echo -e "${GREEN}[${timestamp}] [SUCCESS] ${message}${NC}" ;;
        *)       echo "[${timestamp}] [${level}] ${message}" ;;
    esac
}

# ─── Archive ────────────────────────────────────────────────────────────────────

archive_old_logs() {
    local files_to_archive=()
    local archive_name
    archive_name="logs-archive-$(date '+%Y%m%d-%H%M%S').tar.gz"

    # Find old log files
    while IFS= read -r -d '' file; do
        files_to_archive+=("$file")
    done < <(find "$LOG_DIR" -maxdepth 1 -name "*.log.*" -mtime +"$RETENTION_DAYS" -type f -print0 2>/dev/null)

    # Also find rotated logs (backup.log-YYYYMMDD.gz)
    while IFS= read -r -d '' file; do
        files_to_archive+=("$file")
    done < <(find "$LOG_DIR" -maxdepth 1 -name "backup.log-*" -type f -print0 2>/dev/null)

    # Also find rotated logs (backup.log-YYYYMMDD)
    while IFS= read -r -d '' file; do
        files_to_archive+=("$file")
    done < <(find "$LOG_DIR" -maxdepth 1 -name "backup.log-*" -type f ! -name "*.gz" -print0 2>/dev/null)

    if [[ ${#files_to_archive[@]} -eq 0 ]]; then
        log "INFO" "No old log files to archive."
        return 0
    fi

    log "INFO" "Archiving ${#files_to_archive[@]} log files..."

    if [[ $DRY_RUN -eq 1 ]]; then
        log "INFO" "[DRY RUN] Would create archive: ${ARCHIVE_DIR}/${archive_name}"
        for f in "${files_to_archive[@]}"; do
            log "INFO" "  Would archive: $(basename "$f")"
        done
        return 0
    fi

    mkdir -p "$ARCHIVE_DIR"

    if tar -czf "${ARCHIVE_DIR}/${archive_name}" -C "$LOG_DIR" "$(printf '%s\n' "${files_to_archive[@]}" | xargs -I{} basename "{}" | sed 's|^[^/]*/||')" 2>/dev/null; then
        local archive_size
        archive_size="$(du -h "${ARCHIVE_DIR}/${archive_name}" | cut -f1)"
        log "SUCCESS" "Archive created: ${ARCHIVE_DIR}/${archive_name} (${archive_size})"
    else
        log "ERROR" "Failed to create archive."
        return 1
    fi
}

# ─── Cleanup ────────────────────────────────────────────────────────────────────

cleanup_old_logs() {
    local files_removed=0
    local total_size=0

    # Find and remove old rotated log files
    while IFS= read -r -d '' file; do
        local size
        size="$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)"

        if [[ $DRY_RUN -eq 1 ]]; then
            log "INFO" "[DRY RUN] Would remove: $(basename "$file") ($(numfmt --to=iec "$size" 2>/dev/null || echo "${size} bytes"))"
        else
            rm -f "$file"
            log "INFO" "Removed: $(basename "$file")"
        fi

        files_removed=$((files_removed + 1))
        total_size=$((total_size + size))
    done < <(find "$LOG_DIR" -maxdepth 1 -name "*.log.*" -mtime +"$RETENTION_DAYS" -type f -print0 2>/dev/null)

    while IFS= read -r -d '' file; do
        local size
        size="$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)"

        if [[ $DRY_RUN -eq 1 ]]; then
            log "INFO" "[DRY RUN] Would remove: $(basename "$file")"
        else
            rm -f "$file"
            log "INFO" "Removed: $(basename "$file")"
        fi

        files_removed=$((files_removed + 1))
        total_size=$((total_size + size))
    done < <(find "$LOG_DIR" -maxdepth 1 -name "backup.log-*" -type f -mtime +"$RETENTION_DAYS" -print0 2>/dev/null)

    return $files_removed
}

# ─── Cleanup Archives ───────────────────────────────────────────────────────────

cleanup_old_archives() {
    if [[ ! -d "$ARCHIVE_DIR" ]]; then
        return 0
    fi

    local archives_removed=0

    while IFS= read -r -d '' file; do
        if [[ $DRY_RUN -eq 1 ]]; then
            log "INFO" "[DRY RUN] Would remove old archive: $(basename "$file")"
        else
            rm -f "$file"
            log "INFO" "Removed old archive: $(basename "$file")"
        fi
        archives_removed=$((archives_removed + 1))
    done < <(find "$ARCHIVE_DIR" -maxdepth 1 -name "*.tar.gz" -mtime +"$RETENTION_DAYS" -type f -print0 2>/dev/null)

    log "INFO" "Cleaned ${archives_removed} old archives."
}

# ─── Report ─────────────────────────────────────────────────────────────────────

show_disk_usage() {
    log "INFO" "Current log directory usage:"
    du -sh "$LOG_DIR" 2>/dev/null || log "WARN" "Cannot calculate disk usage."

    if [[ -d "$ARCHIVE_DIR" ]]; then
        log "INFO" "Archive directory usage:"
        du -sh "$ARCHIVE_DIR" 2>/dev/null || log "WARN" "Cannot calculate archive disk usage."
    fi
}

# ─── Main ───────────────────────────────────────────────────────────────────────

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d|--days)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            -a|--archive)
                ARCHIVE=1
                shift
                ;;
            --archive-dir)
                ARCHIVE_DIR="$2"
                shift 2
                ;;
            -n|--dry-run)
                DRY_RUN=1
                shift
                ;;
            -v|--verbose)
                VERBOSE=1
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

    # Ensure log directory exists
    if [[ ! -d "$LOG_DIR" ]]; then
        log "WARN" "Log directory not found: ${LOG_DIR}"
        log "INFO" "Creating log directory..."
        mkdir -p "$LOG_DIR"
    fi

    echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Log Cleanup - Backup Service${NC}"
    echo -e "${BOLD}  Retention: ${RETENTION_DAYS} days${NC}"
    [[ $DRY_RUN -eq 1 ]] && echo -e "${YELLOW}  MODE: DRY RUN (no changes will be made)${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
    echo ""

    # Show current disk usage
    if [[ $VERBOSE -eq 1 ]] || [[ $DRY_RUN -eq 1 ]]; then
        show_disk_usage
        echo ""
    fi

    # Archive if requested
    if [[ $ARCHIVE -eq 1 ]]; then
        archive_old_logs
        echo ""
    fi

    # Cleanup old logs
    log "INFO" "Cleaning up logs older than ${RETENTION_DAYS} days..."
    cleanup_old_logs
    echo ""

    # Cleanup old archives
    cleanup_old_archives
    echo ""

    # Show final disk usage
    if [[ $VERBOSE -eq 1 ]]; then
        show_disk_usage
    fi

    echo -e "${GREEN}${BOLD}Cleanup completed.${NC}"
}

main "$@"
