#!/usr/bin/env python3
"""quietshark self-tests.

Runs standalone (python3 tests/test_quietshark.py) or under pytest.
Stdlib only. Validates every shipped file against the formats Wireshark
actually parses (verified against Wireshark 4.2-4.6 and master sources).
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$|"
                      r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$")

# Top-level sections accepted by Wireshark's theme.schema.json (master).
THEME_SECTIONS = {"meta", "brand", "accent", "expert", "packets", "conversation",
                  "palette", "filter", "separator", "graphs", "fonts", "images", "syntax"}

# gui.* recent keys present in the Wireshark 4.6.6 binary, plus master additions.
KNOWN_RECENT_KEYS = {
    "gui.additional_toolbar_show", "gui.airpcap_toolbar_show",
    "gui.allow_hover_selection", "gui.bytes_encoding", "gui.bytes_view",
    "gui.byte_view_show", "gui.color_scheme", "gui.conversation_tabs",
    "gui.conversation_tabs_columns", "gui.custom_colors", "gui.endpoint_tabs",
    "gui.endpoint_tabs_columns", "gui.fileopen_remembered_dir",
    "gui.filter_toolbar_show", "gui.follow_delta", "gui.follow_show",
    "gui.geometry_leftalign_actions", "gui.geometry_main",
    "gui.geometry_main_extra_split", "gui.geometry_main_height",
    "gui.geometry_main_lower_pane", "gui.geometry_main_master_split",
    "gui.geometry_main_maximized", "gui.geometry_main_upper_pane",
    "gui.geometry_main_width", "gui.geometry_main_x", "gui.geometry_main_y",
    "gui.interface_toolbar_show", "gui.last_used_profile",
    "gui.packet_diagram_field_values", "gui.packet_diagram_show",
    "gui.packet_list_colorize", "gui.packet_list_show",
    "gui.profile_switch_check_count", "gui.rlc_pdus_from_mac_frames",
    "gui.search_case_sensitive", "gui.search_char_set", "gui.search_in",
    "gui.search_multiple_occurs", "gui.search_reverse_dir", "gui.search_type",
    "gui.seconds_format", "gui.show_bytes_decode", "gui.show_bytes_show",
    "gui.statusbar_show", "gui.theme_name", "gui.time_format",
    "gui.time_precision", "gui.toolbar_main_show", "gui.tree_view_show",
    "gui.tsd_goodput_show", "gui.tsd_ma_window_size", "gui.tsd_throughput_show",
    "gui.welcome_page.sidebar.learn_visible",
    "gui.welcome_page.sidebar.tips_auto_advance",
    "gui.welcome_page.sidebar.tips_events",
    "gui.welcome_page.sidebar.tips_interval",
    "gui.welcome_page.sidebar.tips_sponsorship",
    "gui.welcome_page.sidebar.tips_tips",
    "gui.welcome_page.sidebar.tips_visible",
    "gui.wireless_toolbar_show", "gui.zoom_level",
}


def strip_jsonc(text):
    """Remove // and /* */ comments outside string literals."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise ValueError("unterminated block comment")
            i = j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def check_color_pair(pair, where, errors):
    if not isinstance(pair, dict) or set(pair) != {"light", "dark"}:
        errors.append("%s: expected {light, dark}" % where)
        return
    for mode, val in pair.items():
        if not (isinstance(val, str) and COLOR_RE.match(val)):
            errors.append("%s.%s: bad color %r" % (where, mode, val))


def test_theme_jsonc():
    errors = []
    path = os.path.join(ROOT, "themes", "quietshark.jsonc")
    with open(path, encoding="utf-8") as f:
        doc = json.loads(strip_jsonc(f.read()))

    for req in ("meta", "brand", "accent"):
        if req not in doc:
            errors.append("missing required section %r" % req)
    extra = set(doc) - THEME_SECTIONS
    if extra:
        errors.append("unknown top-level sections: %s" % sorted(extra))

    meta = doc.get("meta", {})
    if meta.get("version") != 1:
        errors.append("meta.version must be 1")
    if not meta.get("name"):
        errors.append("meta.name required")

    brand = doc.get("brand", {})
    if "primary" not in brand:
        errors.append("brand.primary required")
    accent = doc.get("accent", {})
    if set(accent) != {"success", "warning", "error", "info"}:
        errors.append("accent must define exactly success/warning/error/info")

    for section, body in doc.items():
        if section in ("meta", "fonts", "images", "syntax"):
            continue
        if section == "separator":
            check_color_pair(body, "separator", errors)
        elif section == "graphs":
            if not isinstance(body, list) or not body:
                errors.append("graphs: non-empty list required")
            for k, pair in enumerate(body):
                check_color_pair(pair, "graphs[%d]" % k, errors)
        elif isinstance(body, dict):
            for key, pair in body.items():
                check_color_pair(pair, "%s.%s" % (section, key), errors)

    # Selection text must stay readable: require explicit selectionText.
    if "selectionText" not in doc.get("packets", {}):
        errors.append("packets.selectionText should be pinned")
    return errors


def test_profile_preferences():
    errors = []
    path = os.path.join(ROOT, "profile", "quietshark", "preferences")
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip() and not ln.startswith("#")]
    if len(lines) < 2:
        errors.append("preferences: expected gui.column.format + pair lines")
    if not lines[0].startswith("gui.column.format:"):
        errors.append("preferences: first key must be gui.column.format")
    body = " ".join(lines[1:])
    tokens = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
    if len(tokens) % 2 != 0:
        errors.append("preferences: column format needs title/format pairs")
    titles, fmts = tokens[0::2], tokens[1::2]
    for fmt in fmts:
        if not fmt.startswith("%"):
            errors.append("preferences: column format %r must start with %% " % fmt)
    if "Info" not in titles or "%i" not in fmts:
        errors.append("preferences: Info column required")
    if len(titles) > 9:
        errors.append("preferences: too many columns for a simple profile")
    return errors


def test_recent_file():
    errors = []
    path = os.path.join(ROOT, "profile", "quietshark", "recent")
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                errors.append("recent:%d: missing ':'" % ln)
                continue
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if key not in KNOWN_RECENT_KEYS:
                errors.append("recent:%d: unknown key %r" % (ln, key))
            if val.lower() not in ("true", "false"):
                errors.append("recent:%d: %r is not TRUE/FALSE" % (ln, val))
    return errors


def test_colorfilters():
    errors = []
    path = os.path.join(ROOT, "profile", "quietshark", "colorfilters")
    # @name@filter@[bg r,g,b][text r,g,b] per epan/color_filters.c
    pat = re.compile(r"^@([^@]+)@([^@]+)@\[(\d+),(\d+),(\d+)\]\[(\d+),(\d+),(\d+)\]$")
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = pat.match(line)
            if not m:
                errors.append("colorfilters:%d: bad line %r" % (ln, line))
                continue
            for v in m.groups()[2:]:
                if not 0 <= int(v) <= 65535:
                    errors.append("colorfilters:%d: value %s out of 0-65535" % (ln, v))
    return errors


def test_dfilters():
    errors = []
    path = os.path.join(ROOT, "profile", "quietshark", "dfilters")
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^"([^"]+)"\s+(\S.*)$', line)
            if not m:
                errors.append("dfilters:%d: bad line %r" % (ln, line))
    return errors


def test_qss():
    errors = []
    path = os.path.join(ROOT, "skin", "quietshark.qss")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if text.count("{") != text.count("}"):
        errors.append("qss: unbalanced braces")
    if "wstheme(" in text:
        errors.append("qss: wstheme() is Wireshark-internal; qt6ct cannot resolve it")
    return errors


TESTS = [test_theme_jsonc, test_profile_preferences, test_recent_file,
         test_colorfilters, test_dfilters, test_qss]


def main():
    failed = False
    for t in TESTS:
        errors = t()
        status = "ok" if not errors else "FAIL"
        print("%-28s %s" % (t.__name__, status))
        for e in errors:
            failed = True
            print("    %s" % e)
    return 1 if failed else 0


# pytest entry points
def test_theme():
    assert test_theme_jsonc() == []
def test_prefs():
    assert test_profile_preferences() == []
def test_recent():
    assert test_recent_file() == []
def test_colors():
    assert test_colorfilters() == []
def test_df():
    assert test_dfilters() == []
def test_qss_balanced():
    assert test_qss() == []


if __name__ == "__main__":
    sys.exit(main())
