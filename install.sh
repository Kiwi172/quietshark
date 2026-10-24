#!/usr/bin/env bash
# quietshark installer — copies the profile and (where supported) the
# native theme into your Wireshark personal configuration.
# Safe to re-run; it overwrites only the quietshark files.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"

case "$(uname -s)" in
    Darwin)
        cfg="${HOME}/Library/Preferences/Wireshark"
        themes="${cfg}/themes"   # confirm via Help -> About -> Folders
        ;;
    *)
        cfg="${XDG_CONFIG_HOME:-${HOME}/.config}/wireshark"
        themes="${HOME}/.local/lib/wireshark/themes"
        ;;
esac

mkdir -p "${cfg}/profiles"
rm -rf "${cfg}/profiles/quietshark"
cp -R "${here}/profile/quietshark" "${cfg}/profiles/quietshark"
echo "profile  -> ${cfg}/profiles/quietshark"

# Activate the profile. Wireshark has no CLI profile flag (-p is the
# capture interface!); it restores the profile named by
# gui.last_used_profile in <config>/recent_common at startup.
rc="${cfg}/recent_common"
[ -f "$rc" ] && [ ! -f "${rc}.quietshark-bak" ] && cp "$rc" "${rc}.quietshark-bak"
if [ -f "$rc" ] && grep -q '^gui.last_used_profile:' "$rc"; then
    sed -i 's/^gui.last_used_profile:.*/gui.last_used_profile: quietshark/' "$rc"
else
    printf '\ngui.last_used_profile: quietshark\n' >> "$rc"
fi
echo "active   -> gui.last_used_profile: quietshark in $rc"

# Native theme: only read by Wireshark master (4.7+). Harmless elsewhere.
mkdir -p "${themes}"
cp "${here}/themes/quietshark.jsonc" "${themes}/quietshark.jsonc"
echo "theme    -> ${themes}/quietshark.jsonc"

# Optional Qt stylesheet wiring (Wireshark 4.2-4.6 dark/flat look).
if [ -f "${XDG_CONFIG_HOME:-${HOME}/.config}/qt6ct/qt6ct.conf" ]; then
    qss="${here}/skin/quietshark.qss"
    conf="${XDG_CONFIG_HOME:-${HOME}/.config}/qt6ct/qt6ct.conf"
    if grep -q '^stylesheet=' "$conf"; then
        sed -i "s|^stylesheet=.*|stylesheet=${qss}|" "$conf"
    else
        printf '\n[Appearance]\nstylesheet=%s\n' "$qss" >> "$conf"
    fi
    echo "qss      -> wired into qt6ct ($conf)"
    echo "         remember: export QT_QPA_PLATFORMTHEME=qt6ct"
else
    echo "qss      -> not wired (qt6ct not configured; see README)"
fi

echo
echo "Launch with:  ${here}/quietshark.sh"
echo "Uninstall:    delete profiles/quietshark and themes/quietshark.jsonc,"
echo "              restore recent_common.quietshark-bak if present."
