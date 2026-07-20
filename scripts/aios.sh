#!/usr/bin/env bash
#===============================================================================
# AIOS Server Manager - start, stop, restart, status
# Self-hosted server for Termux/Debian
#===============================================================================
set -euo pipefail

AIOS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${AIOS_DIR}/.aios/daemon.pid"
LOG_DIR="${AIOS_DIR}/logs"
MAIN_PORT=${AIOS_PORT:-8080}
KERNEL_API_PORT=${KERNEL_API_PORT:-8000}

mkdir -p "${LOG_DIR}" "${AIOS_DIR}/.aios"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[AIOS]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[AIOS]${NC} $1"; }
log_err()   { echo -e "${RED}[AIOS]${NC} $1"; }

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"
            return 0
        fi
    done
    log_err "Python 3 not found"
    exit 1
}

PYTHON=$(find_python)
export AIOS_DIR

cleanup_existing() {
    if [ -f "${PID_FILE}" ]; then
        local old_pid
        old_pid=$(cat "${PID_FILE}")
        if kill -0 "${old_pid}" 2>/dev/null; then
            log_warn "Stopping existing AIOS (PID ${old_pid})"
            kill "${old_pid}" 2>/dev/null || true
            sleep 2
            if kill -0 "${old_pid}" 2>/dev/null; then
                kill -9 "${old_pid}" 2>/dev/null || true
                sleep 1
            fi
        fi
        rm -f "${PID_FILE}"
    fi
}

start_services() {
    log_info "Starting AIOS server..."
    cleanup_existing
    cd "${AIOS_DIR}"

    # Start Mission Control API + WebSocket
    nohup "${PYTHON}" -m src.api.server \
        --host "${AIOS_HOST:-0.0.0.0}" \
        --port "${MAIN_PORT}" \
        --project-root "${AIOS_DIR}" \
        --log-level "${AIOS_LOG_LEVEL:-info}" \
        >> "${LOG_DIR}/server.log" 2>&1 &
    MAIN_PID=$!
    echo ${MAIN_PID} > "${PID_FILE}"

    log_info "API server starting on port ${MAIN_PORT} (PID ${MAIN_PID})"

    # Start Kernel API for Mission Control
    nohup "${PYTHON}" -m src.api.kernel_api \
        --port ${KERNEL_API_PORT} \
        --project-root "${AIOS_DIR}" \
        >> "${LOG_DIR}/kernel_api.log" 2>&1 &
    KERNEL_PID=$!
    echo ${KERNEL_PID} > "${PID_FILE}.kernel"

    log_info "Kernel API starting on port ${KERNEL_API_PORT} (PID ${KERNEL_PID})"

    # Wait a bit for services to start
    sleep 2

    # Verify
    if kill -0 ${MAIN_PID} 2>/dev/null; then
        log_info "AIOS started successfully"
        log_info "  API:          http://localhost:${MAIN_PORT}"
        log_info "  Mission Ctrl: http://localhost:${MAIN_PORT}/mission-control/"
        log_info "  Kernel API:   http://localhost:${KERNEL_API_PORT}"
        log_info "  Health:       http://localhost:${MAIN_PORT}/api/health"
    else
        log_err "Failed to start AIOS"
        tail -5 "${LOG_DIR}/server.log" 2>/dev/null || true
        exit 1
    fi
}

stop_services() {
    log_info "Stopping AIOS server..."
    if [ -f "${PID_FILE}" ]; then
        local pid=$(cat "${PID_FILE}")
        if kill -0 "${pid}" 2>/dev/null; then
            kill "${pid}" 2>/dev/null || true
        fi
        rm -f "${PID_FILE}"
    fi
    if [ -f "${PID_FILE}.kernel" ]; then
        local kpid=$(cat "${PID_FILE}.kernel")
        if kill -0 "${kpid}" 2>/dev/null; then
            kill "${kpid}" 2>/dev/null || true
        fi
        rm -f "${PID_FILE}.kernel"
    fi
    sleep 1
    log_info "AIOS stopped"
}

restart_services() {
    stop_services
    start_services
}

check_status() {
    local main_alive=false
    local kernel_alive=false

    if [ -f "${PID_FILE}" ]; then
        local pid=$(cat "${PID_FILE}")
        if kill -0 "${pid}" 2>/dev/null; then
            main_alive=true
        fi
    fi
    if [ -f "${PID_FILE}.kernel" ]; then
        local kpid=$(cat "${PID_FILE}.kernel")
        if kill -0 "${kpid}" 2>/dev/null; then
            kernel_alive=true
        fi
    fi

    echo -e "${CYAN}AIOS Server Status${NC}"
    echo "======================"
    if ${main_alive}; then
        echo -e "  API Server:     ${GREEN}RUNNING${NC} (PID $(cat ${PID_FILE}))"
    else
        echo -e "  API Server:     ${RED}STOPPED${NC}"
    fi
    if ${kernel_alive}; then
        echo -e "  Kernel API:     ${GREEN}RUNNING${NC} (PID $(cat ${PID_FILE}.kernel))"
    else
        echo -e "  Kernel API:     ${RED}NOT FOUND${NC}"
    fi

    if ${main_alive}; then
        echo "======================"
        echo -e "  API:          http://localhost:${MAIN_PORT}"
        echo -e "  Mission Ctrl: http://localhost:${MAIN_PORT}/mission-control/"
        echo -e "  Health:       http://localhost:${MAIN_PORT}/api/health"
        echo "======================"
        curl -sf "http://localhost:${MAIN_PORT}/api/health" 2>/dev/null && echo "" || echo -e "${YELLOW}Health check failed${NC}"
    fi
}

show_logs() {
    if [ $# -ge 1 ]; then
        local which="$1"
        case "${which}" in
            api|server)
                tail -f "${LOG_DIR}/server.log"
                ;;
            kernel)
                tail -f "${LOG_DIR}/kernel_api.log"
                ;;
            all)
                tail -f "${LOG_DIR}"/*.log
                ;;
            *)
                echo "Usage: $0 logs {api|kernel|all}"
                exit 1
                ;;
        esac
    else
        tail -f "${LOG_DIR}/server.log"
    fi
}

case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        check_status
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    setup)
        cd "${AIOS_DIR}"
        log_info "Installing dependencies..."
        "${PYTHON}" -m pip install -r requirements.txt 2>&1
        log_info "Dependencies installed"
        mkdir -p data
        log_info "Setup complete"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|setup}"
        echo ""
        echo "  start    Start AIOS server"
        echo "  stop     Stop AIOS server"
        echo "  restart  Restart AIOS server"
        echo "  status   Check AIOS server status"
        echo "  logs     View server logs"
        echo "  setup    Install dependencies"
        exit 1
        ;;
esac
