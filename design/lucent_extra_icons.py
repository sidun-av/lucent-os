"""More Lucent icons, drawn here in the mockups' style (docs/mockups/lucent.js):

- app tiles for the remaining launcher apps (same tile as lucent.js `tile()`:
  60/64 rounded square, vertical gradient, hairline, top sheen, white glyph);
- line icons (24-unit grid, 1.8 stroke, round caps, the mockups' `sym()`
  look) for the tray (volume, network, Wi-Fi) and the session actions
  (sleep, restart, shut down, log out, lock, switch user). They use KDE's
  ColorScheme-Text class, so Plasma draws them in full-contrast text colour
  in light and dark.
"""

TILE = """<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<rect x="2" y="2" width="60" height="60" rx="15" fill="url(#g)"/>
<rect x="2.5" y="2.5" width="59" height="59" rx="14.5" fill="none" stroke="rgb(0,0,0)" stroke-opacity="{edge}"/>
<path d="M17 2.5h30a14.5 14.5 0 0 1 14.5 14.5v2C50 12 30 10 2.5 18v-1A14.5 14.5 0 0 1 17 2.5z" fill="#fff" opacity="{sheen}"/>
{glyph}</svg>"""


def tile(c1, c2, glyph, light=False):
    return TILE.format(c1=c1, c2=c2, glyph=glyph, edge=".12" if light else ".08", sheen="0" if light else ".10")


# name of the drawing -> (svg, icon names it provides)
TILES = {
    "archives": (tile("#ffcf6b", "#e8930c",
        '<rect x="11" y="14" width="42" height="10" rx="3" fill="#fff"/>'
        '<path d="M14 24h36v20a4 4 0 0 1-4 4H18a4 4 0 0 1-4-4z" fill="#fff" opacity=".88"/>'
        '<path d="M32 26v4M32 33v4" stroke="#e8930c" stroke-width="3" stroke-linecap="round"/>'
        '<rect x="28" y="39" width="8" height="6" rx="1.5" fill="#e8930c"/>'),
        ["org.kde.ark", "ark"]),
    "disk-usage": (tile("#4fd1c5", "#0f8f86",
        '<circle cx="32" cy="32" r="18" fill="#fff" opacity=".45"/>'
        '<path d="M32 32V14a18 18 0 0 1 17.1 23.6z" fill="#fff"/>'
        '<circle cx="32" cy="32" r="7" fill="#0f8f86"/>'),
        ["org.kde.filelight", "filelight"]),
    "phone-link": (tile("#8b9bff", "#4a4fd6",
        '<rect x="15" y="12" width="21" height="40" rx="4.5" fill="#fff"/>'
        '<rect x="18.5" y="17" width="14" height="26" rx="1.5" fill="#4a4fd6" opacity=".3"/>'
        '<circle cx="25.5" cy="47.5" r="1.8" fill="#4a4fd6"/>'
        '<path d="M42 25a9 9 0 0 1 0 14M47 21a15 15 0 0 1 0 22" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round"/>'),
        ["kdeconnect", "org.kde.kdeconnect.app", "org.kde.kdeconnect"]),
    "text-editor": (tile("#ffffff", "#eef2f8",
        '<rect x="15" y="12" width="30" height="40" rx="4" fill="#fff" stroke="#c9d3e3" stroke-width="1.6"/>'
        '<path d="M21 22h18M21 28h18M21 34h12" stroke="#5b6b87" stroke-width="2.6" stroke-linecap="round"/>'
        '<path d="M46 30l5 5-12 12-6 1 1-6z" fill="#f07a1e"/><path d="M46 30l5 5" stroke="#fff" stroke-width="1.5"/>', light=True),
        ["org.kde.kwrite", "kwrite", "accessories-text-editor"]),
    "screenshot": (tile("#b69cff", "#6d28d9",
        '<path d="M15 25v-7a3 3 0 0 1 3-3h7M39 15h7a3 3 0 0 1 3 3v7M49 39v7a3 3 0 0 1-3 3h-7M25 49h-7a3 3 0 0 1-3-3v-7" '
        'stroke="#fff" stroke-width="3.4" fill="none" stroke-linecap="round"/><circle cx="32" cy="32" r="7.5" fill="#fff"/>'),
        ["org.kde.spectacle", "spectacle"]),
    "system-monitor": (tile("#3a4150", "#1b1f28",
        '<path d="M13 40h8l5-13 7 19 5-14 4 8h9" stroke="#7ef0a8" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
        ["utilities-system-monitor", "org.kde.plasma-systemmonitor", "plasma-systemmonitor"]),
    "layout": (tile("#ff8fb1", "#d6336c",
        '<rect x="16" y="12" width="32" height="40" rx="3.5" fill="#fff"/>'
        '<rect x="20.5" y="17" width="23" height="10" rx="1.5" fill="#d6336c" opacity=".85"/>'
        '<path d="M20.5 33h10M20.5 38.5h10M20.5 44h10M35 33h8.5M35 38.5h8.5M35 44h5.5" stroke="#d6336c" stroke-width="2.2" stroke-linecap="round" opacity=".7"/>'),
        ["net.scribus.Scribus", "scribus"]),
    "next-generation": (tile("#ff8a5c", "#ec3f86",
        '<path d="M2 46 L46 2 H50 L2 50z" fill="#fff" opacity=".10"/>'
        '<path d="M32 13l4.8 14.2L51 32l-14.2 4.8L32 51l-4.8-14.2L13 32l14.2-4.8z" fill="#fff"/>'),
        ["lucent-nextgen"]),
}

LINE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
        '<style type="text/css" id="current-color-scheme">.ColorScheme-Text {{ color:{color}; }}</style>'
        '{paths}</svg>')


def line(*ds, dots=(), color="#1b1f27"):
    style = "fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round"
    paths = "".join(f'<path class="ColorScheme-Text" style="{style}" d="{d}"/>' for d in ds)
    paths += "".join(f'<circle class="ColorScheme-Text" style="fill:currentColor" cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in dots)
    return LINE.format(paths=paths, color=color)


def recolor(svg, color):
    """The same icon with another default colour: apps that don't apply KDE's
    icon recolouring (e.g. the login screen) show the default."""
    return svg.replace("color:#1b1f27;", f"color:{color};")


SPEAKER = "M4 9.5h3.5L12 5.5v13l-4.5-4H4z"
WAVE1 = "M15.5 9a4.5 4.5 0 0 1 0 6"
WAVE2 = "M18 6.5a8 8 0 0 1 0 11"
WIFI3 = "M3 9.5a13 13 0 0 1 18 0"
WIFI2 = "M6 13a8.5 8.5 0 0 1 12 0"
WIFI1 = "M9 16.4a4 4 0 0 1 6 0"
WIRED = ("M8.5 3.5h7a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z",
         "M12 9.5v4.5M5 14h14M5 14v2.5M19 14v2.5M12 14v2.5",
         "M3.5 16.5h3v3h-3zM10.5 16.5h3v3h-3zM17.5 16.5h3v3h-3z")
CROSS = "M16 15.5l4 4M20 15.5l-4 4"

# line icon -> names (each also gets a -symbolic alias)
LINES = {
    "volume-high": (line(SPEAKER, WAVE1, WAVE2), ["audio-volume-high"]),
    "volume-medium": (line(SPEAKER, WAVE1), ["audio-volume-medium"]),
    "volume-low": (line(SPEAKER), ["audio-volume-low", "audio-volume-zero"]),
    "volume-muted": (line(SPEAKER, "M15.5 9.5l5 5M20.5 9.5l-5 5"), ["audio-volume-muted", "audio-off"]),
    "wired": (line(*WIRED), ["network-wired", "network-wired-activated", "network-connect"]),
    "wired-off": (line(*WIRED[:2], "M3.5 16.5h3v3h-3zM10.5 16.5h3v3h-3z", CROSS),
                  ["network-wired-disconnected", "network-wired-unavailable", "network-wired-offline",
                   "network-disconnect", "network-offline"]),
    "wifi-4": (line(WIFI3, WIFI2, WIFI1, dots=[(12, 19.3, 1.1)]),
               ["network-wireless", "network-wireless-signal-excellent", "network-wireless-connected-100",
                "network-wireless-100", "network-wireless-connected-75", "network-wireless-signal-good"]),
    "wifi-2": (line(WIFI2, WIFI1, dots=[(12, 19.3, 1.1)]),
               ["network-wireless-signal-ok", "network-wireless-connected-50", "network-wireless-50"]),
    "wifi-1": (line(WIFI1, dots=[(12, 19.3, 1.1)]),
               ["network-wireless-signal-weak", "network-wireless-connected-25", "network-wireless-25",
                "network-wireless-signal-none", "network-wireless-connected-00", "network-wireless-0"]),
    "wifi-off": (line(WIFI3, WIFI2, "M3 3l18 18", dots=[(12, 19.3, 1.1)]),
                 ["network-wireless-disconnected", "network-wireless-offline", "network-wireless-off"]),
    "shutdown": (line("M12 3.5v8", "M7 6.5a7.5 7.5 0 1 0 10 0"), ["system-shutdown"]),
    "reboot": (line("M19.5 12a7.5 7.5 0 1 1-2.2-5.3", "M19.5 4.5v4.2h-4.2"), ["system-reboot", "system-restart"]),
    "sleep": (line("M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"), ["system-suspend", "system-suspend-hibernate"]),
    "log-out": (line("M14 4.5H6.5A1.5 1.5 0 0 0 5 6v12a1.5 1.5 0 0 0 1.5 1.5H14", "M10 12h10m-3.5-3.5L20 12l-3.5 3.5"),
                ["system-log-out", "application-exit"]),
    "lock": (line("M7.5 10.5h9a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2h-9a2 2 0 0 1-2-2v-5.5a2 2 0 0 1 2-2z",
                  "M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"), ["system-lock-screen"]),
    "users": (line("M9 5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z", "M3 19.5c.6-3.3 3-5 6-5s5.4 1.7 6 5",
                   "M15.5 5.3a3.3 3.3 0 0 1 0 6.4M17.8 14.6c1.6.7 2.8 2.3 3.2 4.9"),
              ["system-switch-user", "system-users", "system-user-list"]),
}
