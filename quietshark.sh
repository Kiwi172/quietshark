#!/usr/bin/env bash
# Launch Wireshark with the quietshark profile (activated by install.sh
# via gui.last_used_profile) and a flat widget style.
set -euo pipefail
export QT_STYLE_OVERRIDE="${QT_STYLE_OVERRIDE:-Fusion}"
exec wireshark "$@"
