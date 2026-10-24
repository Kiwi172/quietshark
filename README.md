# quietshark

**Wireshark, minus the visual noise.** A drop-in profile, muted color
palette, Qt stylesheet, and native theme file that turn Wireshark's
wall-of-buttons default into something a human can scan.

Wireshark is deep. Its default first screen is not: eleven columns,
four toolbars, a rainbow packet list, and a welcome page that talks at
you. You can fix all of it by hand through preferences — or install
quietshark and get a calm layout (7 columns, 2 toolbars, 3 panes,
low-saturation row tints) in one step. Nothing is removed from the app;
every hidden pane and toolbar is one View-menu click away.

```
 default Wireshark                quietshark
 +----------------------+         +----------------------+
 | ▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣ |  ->     | ▣ ▣ ▣                |   2 toolbars
 | 11 columns, 4 panes  |         | 7 columns, 3 panes   |   no diagram/bytes
 | 🌈 colorfilters      |         | 🎨 muted tints       |   calm palette
 | tips + learn sidebar |         | clean welcome page   |   quiet sidebar
 +----------------------+         +----------------------+
```

## Install

```sh
git clone https://github.com/Kiwi172/quietshark
cd quietshark
./install.sh
./quietshark.sh
```

`install.sh` copies the profile into your Wireshark config directory
(`~/.config/wireshark/profiles/quietshark` on Linux,
`~/Library/Preferences/Wireshark/profiles/quietshark` on macOS),
activates it via `gui.last_used_profile` in `recent_common` (Wireshark
has no command-line profile flag — `-p` is the capture interface!),
and drops the theme file into your Personal Themes folder. Re-running
it is safe; it only touches quietshark files.

## What it changes

| Layer | File | Applies on |
|---|---|---|
| Layout profile | `profile/quietshark/` | Wireshark 4.2 – 4.6 and master |
| Muted row colors | `profile/quietshark/colorfilters` | same |
| Starter filters | `profile/quietshark/dfilters` | same |
| Flat Qt stylesheet | `skin/quietshark.qss` | 4.2 – 4.6, via [qt6ct] |
| Native theme | `themes/quietshark.jsonc` | Wireshark master (theme system lands in 4.7) |

The profile is the real workhorse: columns, pane visibility, toolbar
visibility, and colors are all profile data, so switching back is just
`wireshark -p "Default"`.

### The QSS layer (4.2 – 4.6)

Wireshark does not load Qt stylesheets itself — its option parser
rejects Qt's `-stylesheet` argument — so the skin rides in through
[qt6ct]:

```sh
sudo apt install qt6ct            # or dnf/pacman equivalent
qt6ct                             # Stylesheets tab -> skin/quietshark.qss
export QT_QPA_PLATFORMTHEME=qt6ct
```

`install.sh` wires this up automatically if `~/.config/qt6ct/qt6ct.conf`
exists. `quietshark.sh` also sets `QT_STYLE_OVERRIDE=Fusion` so the
widget style is flat and identical on every desktop.

### The native theme layer (master / 4.7+)

Wireshark master gained a real theme system (`theme.jsonc`, selected in
Preferences → Appearance → Theme). `themes/quietshark.jsonc` is a
personal theme for it: warm-neutral surfaces, desaturated accents,
soft filter-validity tints. On 4.2 – 4.6 the file is simply ignored.

## Uninstall

Delete `profiles/quietshark` from your Wireshark config dir and
`themes/quietshark.jsonc` from Personal Themes, then restore
`recent_common.quietshark-bak` (or set `gui.last_used_profile: Default`).
Your default profile was never touched.

## Tests / CI

```sh
python3 tests/test_quietshark.py
```

Validates every shipped file against the formats Wireshark's parsers
actually accept (checked against 4.2 – 4.6 and master sources). CI runs
the tests on three Python versions and additionally boots Wireshark
under Xvfb with the profile installed, failing on any preference
warning and uploading a screenshot of the result.

## Known limits

- The welcome-page sidebar keys are 4.6+; older releases ignore them.
- Heavy QSS can slow the packet list on very large captures; this one
  stays conservative, but remove the qt6ct wiring if you notice it.
- `Interface Style: Basic/Advanced/Classic` no longer exists in Wireshark
  4.x — pane/toolbar toggles in the profile replace it.

[qt6ct]: https://www.fredpalmer.com/qt5ct-qt-configuration-for-all-desktops/

## License

MIT
