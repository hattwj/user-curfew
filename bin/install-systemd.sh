#!/usr/bin/env bash
# Install user-curfew as a systemd service driven by a systemd timer.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
USER_CURFEW="${SCRIPT_DIR}/user-curfew"
EXAMPLE_CONFIG="${SCRIPT_DIR}/../user-curfew.toml.example"
DEFAULT_CONFIG="/etc/user-curfew.toml"
UNIT_DIR="/etc/systemd/system"
SERVICE_UNIT="${UNIT_DIR}/user-curfew.service"
TIMER_UNIT="${UNIT_DIR}/user-curfew.timer"

CONFIG="${DEFAULT_CONFIG}"
INTERVAL=5
UNINSTALL=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install user-curfew as a systemd service run by a systemd timer.

Options:
  -i, --interval MINUTES  Run every MINUTES minutes (default: 5)
  -c, --config PATH       Config file to use (default: ${DEFAULT_CONFIG})
  -u, --uninstall         Remove the user-curfew service and timer
  -h, --help              Show this help
EOF
}

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

# Escape a value for use in a systemd unit file.
systemd_escape() {
    printf '%s' "${1//%/%%}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--interval)
            [[ $# -ge 2 ]] || die "$1 requires a value"
            INTERVAL="$2"
            shift 2
            ;;
        --interval=*)
            INTERVAL="${1#*=}"
            shift
            ;;
        -c|--config)
            [[ $# -ge 2 ]] || die "$1 requires a value"
            CONFIG="$2"
            shift 2
            ;;
        --config=*)
            CONFIG="${1#*=}"
            shift
            ;;
        -u|--uninstall)
            UNINSTALL=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

[[ "$INTERVAL" =~ ^[0-9]+$ ]] || die "interval must be a positive integer"
(( INTERVAL >= 1 && INTERVAL <= 59 )) || die "interval must be between 1 and 59 minutes"
[[ "$CONFIG" == /* ]] || die "config path must be absolute: ${CONFIG}"

[[ $EUID -eq 0 ]] || die "must be run as root (use sudo)"

if (( UNINSTALL )); then
    if command -v systemctl >/dev/null 2>&1; then
        systemctl disable --now user-curfew.timer >/dev/null 2>&1 || true
    fi
    rm -f "$SERVICE_UNIT" "$TIMER_UNIT"
    if command -v systemctl >/dev/null 2>&1; then
        systemctl daemon-reload
        systemctl reset-failed user-curfew.service >/dev/null 2>&1 || true
    fi
    printf 'removed %s and %s\n' "$SERVICE_UNIT" "$TIMER_UNIT"
    exit 0
fi

[[ -f "$USER_CURFEW" ]] || die "not found: ${USER_CURFEW} (run this from the user-curfew repo)"
command -v systemctl >/dev/null 2>&1 || die "systemctl not found; is systemd installed?"

PYTHON="$(command -v python3 || true)"
[[ -n "$PYTHON" ]] || die "python3 not found"

if [[ ! -e "$CONFIG" ]]; then
    [[ -f "$EXAMPLE_CONFIG" ]] || die "not found: ${EXAMPLE_CONFIG}"
    install -m 0644 "$EXAMPLE_CONFIG" "$CONFIG"
    printf 'installed example config at %s\n' "$CONFIG"
    printf 'edit it before relying on the lock schedules.\n\n'
fi

cat >"$SERVICE_UNIT" <<EOF
[Unit]
Description=user-curfew account lock enforcement

[Service]
Type=oneshot
ExecStart="$(systemd_escape "$PYTHON")" "$(systemd_escape "$USER_CURFEW")" --config "$(systemd_escape "$CONFIG")"
EOF

cat >"$TIMER_UNIT" <<EOF
[Unit]
Description=Run user-curfew every ${INTERVAL} minute(s)

[Timer]
OnActiveSec=1min
OnCalendar=*:0/${INTERVAL}
AccuracySec=1min
Persistent=true
Unit=user-curfew.service

[Install]
WantedBy=timers.target
EOF

chmod 0644 "$SERVICE_UNIT" "$TIMER_UNIT"

systemctl daemon-reload
systemctl enable user-curfew.timer
systemctl restart user-curfew.timer

printf '\ninstalled systemd timer: %s\n' "$TIMER_UNIT"
printf 'the script will run every %d minute(s) as root.\n' "$INTERVAL"
printf 'check status with: systemctl status user-curfew.timer\n'
printf 'view logs with:    journalctl -u user-curfew.service\n'
