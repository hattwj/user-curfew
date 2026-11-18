#!/usr/bin/env bash
# Install user-curfew as a root crontab entry.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
USER_CURFEW="${SCRIPT_DIR}/user-curfew"
EXAMPLE_CONFIG="${SCRIPT_DIR}/../user-curfew.toml.example"
DEFAULT_CONFIG="/etc/user-curfew.toml"

CONFIG="${DEFAULT_CONFIG}"
INTERVAL=5
UNINSTALL=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install user-curfew as a root crontab entry.

Options:
  -i, --interval MINUTES  Run every MINUTES minutes (default: 5)
  -c, --config PATH       Config file to use (default: ${DEFAULT_CONFIG})
  -u, --uninstall         Remove the user-curfew crontab entry
  -h, --help              Show this help
EOF
}

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
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
[[ -f "$USER_CURFEW" ]] || die "not found: ${USER_CURFEW} (run this from the user-curfew repo)"

PYTHON="$(command -v python3 || true)"
[[ -n "$PYTHON" ]] || die "python3 not found"

# Avoid recursing back into this installer when user-curfew dispatches here.
export USER_CURFEW_BUILTIN_CRON=1

if (( UNINSTALL )); then
    command -v crontab >/dev/null 2>&1 || {
        printf 'crontab not found; nothing to remove.\n'
        exit 0
    }
    exec "$PYTHON" "$USER_CURFEW" --config "$CONFIG" --uninstall-crontab
fi

command -v crontab >/dev/null 2>&1 || die "crontab not found; use install-systemd.sh on systems without cron"

if [[ ! -e "$CONFIG" ]]; then
    [[ -f "$EXAMPLE_CONFIG" ]] || die "not found: ${EXAMPLE_CONFIG}"
    install -m 0644 "$EXAMPLE_CONFIG" "$CONFIG"
    printf 'installed example config at %s\n' "$CONFIG"
    printf 'edit it before relying on the lock schedules.\n\n'
fi

exec "$PYTHON" "$USER_CURFEW" --config "$CONFIG" --install-crontab "$INTERVAL"
