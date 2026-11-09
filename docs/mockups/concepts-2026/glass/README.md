# Lucent OS: Glass Card (variant of Pebble Drift)

This direction follows the owner's November brief: one consistent style that is light,
minimal and informative. Nothing looks pressed in. Everything is a light glass card. The
taskbar is a centred, semi-transparent dock with a Spotlight-like quick search.

The palette, the Drift wallpapers, Figtree/Inter, the 4 px grid and the Windows habits all
stay the same: window buttons on the right, menus inside windows, Win-key shortcuts, Alt+Tab.

| Screen | Light | Dark |
| --- | --- | --- |
| Desktop + dock, window-group preview | `01-desktop-light.png` | `01-desktop-dark.png` |
| Spotlight (Win+Space), query "pdf" | `02-spotlight-light.png` | `02-spotlight-dark.png` |
| Settings → Appearance | `03-settings-light.png` | `03-settings-dark.png` |
| Settings, "Reduce transparency" fallback | `03-settings-solid.png` | |
| Files → This PC | `04-files-light.png` | `04-files-dark.png` |
| Start menu (launcher) | `05-launcher-light.png` | `05-launcher-dark.png` |
| Spotlight, calculator | | `06-spotlight-calc-dark.png` |

All screens are 2560×1440 at 1x. Each HTML file renders both modes: add `#dark` and/or
`#solid` to the URL, then use headless Chrome with `--window-size=2560,1440
--virtual-time-budget=6000 --screenshot`. `glass.css` holds the tokens (part 1, with the cost
model in its header) and the components (part 2). `glass-shell.js` draws the dock. The
wallpapers, folders and glyphs come from `../pebble-drift/drift-shell.js` and `../../lucent.js`.

## What was sunken (Pebble Drift → Glass Card)

| Where | Today (mockups + real build) | Glass Card |
| --- | --- | --- |
| Settings sidebar | sunken well, `Main.qml` `Well {}` | floating glass card (e2) |
| Store sidebar | `Sidebar.qml` `Well {}` | same glass card |
| Files places panel | well painted by `lucentstyle.cpp` (`_lucent_well`, item 7) | same glass card |
| Sidebar selection | raised pillow tile inside the well | soft `--accent-soft` pill, no shadow |
| Taskbar search box | sunken (`org.lucent.search`) | dock search button that opens Spotlight |
| Taskbar app group | sunken well (`.tb-apps`) | gone; apps sit straight on the dock |
| Launcher | full-screen scrim, sunken category track (`Dashboard.qml`), raised "on" chip | compact popup over the dock; Spotlight handles search |
| Text and search fields | `LTextField`, Kvantum `LineEdit`, Dolphin path bar | light glass field, hairline, accent ring on focus |
| Segmented controls | sunken track + raised segment (`Segmented.qml`, Kvantum, Dolphin view modes) | glass strip, accent-pill segment |
| Mode / theme tiles, "Add a picture", choice tiles | sunken tiles (`ThemeCard`, `AddPictureTile`, `habits.qml`) | cards, accent ring when chosen |
| Icon tiles in rows | sunken `IconTile` | flat `--state-hover` tint |
| Switch / slider / progress tracks | inset shadow | flat `--track` tint |
| Store notes and buttons | `BridgeHint` and `ActionButton` wells, `wellStrong` in `ReplacementCard`/`AppPage` | cards, glass buttons, flat pills |
| Empty states, Updates list | `EmptyState`, `UpdatesPage` wells | cards |
| Preview thumbnails | sunken frame | hairline only |

## Feasibility on Plasma 6.8

| Element | Mechanism | Cost | Verdict |
| --- | --- | --- | --- |
| Dock: centred, floating, fit width | layout JS: `bar.floating = true`, `bar.lengthMode = "fit"`, `bar.alignment = "center"`, drop both spacers | none | cheap |
| Dock glass | Lucent Plasma theme `widgets/panel-background.svg` (translucent + `opaque/` twin), KWin blur, adaptive opacity (turns opaque when a window is maximised) | one ~1050×72 blur region over a mostly static backdrop | cheap |
| Launcher + search buttons | `org.lucent.launcher` icon; `org.lucent.search` becomes an icon button that runs KRunner | none | cheap |
| Running dots | `icontasks` indicators from the theme's `tasks` SVG | none | cheap; one dot per app. A dot per window needs an icontasks patch, so skip it |
| Window-group preview | stock icontasks tooltip thumbnails (already on) | live thumbnails only while hovered | cheap |
| Compact tray + clock in the dock | `systemtray` + `digitalclock` | none | cheap |
| Spotlight: list | KRunner 6, free-floating (`krunnerrc [General] FreeFloating=true`), styled by the Plasma theme `dialogs/background` + blur; calculator, services, settings and baloo runners; webshortcuts stays off | blur only while open | cheap |
| Spotlight: right preview pane, "Web (Off)" row | KRunner has no preview pane and no "disabled" rows | — | **not cheap**: needs our own frontend (a centred `PlasmaCore.Dialog` in `org.lucent.launcher` that reuses its runner model). Ship plain KRunner first |
| Start menu as compact popup | `Dashboard.qml` drops full-screen for a ~940 px `PlasmaCore.Dialog` above the dock | less than today (no full-screen scrim) | cheap |
| Popups / menus glass | Plasma theme dialogs; Kvantum `menu_blur` + translucent menus | transient | cheap |
| Cards, fields, segmented, tracks (Qt widgets) | `gen_kvantum.py`: `well()` → glass fill + top highlight + soft drop; tracks flat | prerendered SVG pixmaps, same as today | cheap |
| Cards, fields, sidebar pill (our QML) | `Theme.qml` / `theme.py` tokens; `Well.qml` → `GlassCard.qml`; `Segmented`, `LTextField`, `IconTile`, `ThemeCard`, Store `Sidebar` | plain Rectangles, no `layer`/`MultiEffect` | cheap |
| Sidebar as a card, tier 1 (default) | the card is painted over the window's own surface (`lucentstyle.cpp` item 7 + QML), so no wallpaper shows through | none | cheap |
| Sidebar tier 2: wallpaper blur behind the sidebar (as in the mockups) | window translucent only in the sidebar rect + `KWindowEffects::enableBlurBehind(win, sidebarRect)`; region updated on resize | one window-height strip per visible window; re-blurred whenever what is behind it changes | **risky for responsiveness**. Dolphin through the QStyle means fragile region bookkeeping. Our QML apps need a small C++ helper. Ship only for Settings and Store, and only behind the transparency switch |
| Reduce transparency / software rendering | Plasma already picks the theme's `opaque/` SVGs when blur is unavailable. The switch writes an opaque theme + solid Kvantum variant through `lucent-theme` | saves cost | cheap |

## Shortcut proposal

Today `Meta+Space` = next keyboard layout (`kglobalshortcutsrc`), `Alt+Space` / `Alt+F2` =
KRunner, `Alt+Shift` = layout toggle (`kxkbrc`). Settings › Keyboard offers a "Win+Space" switch
choice (`habits.py` `win_space`).

- **Win+Space → Spotlight.** Typing in the Start menu leads to the same results.
- **Layout switching:** `Alt+Shift` stays the default, the same as Windows. `Ctrl+Shift` stays an
  option. `Meta+Alt+K` stays as KDE's fallback. The "Win+Space" choice in Settings goes away. The
  page says "Win+Space opens search" instead. One line in `habits.py` and one in
  `kglobalshortcutsrc`.
- **Alt+Space → window menu (Windows habit).** It currently opens KRunner. KRunner keeps `Alt+F2`.
- The Meta-alone tap still opens Start. KWin fires a modifier-only shortcut only when no other key
  was pressed, so Win+Space does not open both.

## Implementation order (by user impact)

1. **Dock** (layout JS + panel SVG): cheap, visible on every screen.
2. **Sidebars → glass cards, tier 1, + selection pill** (lucent-style item 7, Settings/Store QML,
   Kvantum item-view selection): cheap, and it fixes the main "sunken" complaint.
3. **Fields, segmented controls, tracks** (`gen_kvantum.py` `well()`, `LTextField`, `Segmented`,
   switches): cheap.
4. **Win+Space → KRunner, styled** + shortcut change: cheap.
5. **Start menu → compact popup** (`Dashboard.qml`): cheap, and less GPU work than today.
6. **Cards everywhere** (tiles, `IconTile`, Store wells, buttons): cheap, but it touches many files.
7. **Reduce transparency switch** (opaque theme + solid Kvantum variant): cheap.
8. **Spotlight preview pane / own frontend:** medium effort, cheap at runtime.
9. **Sidebar tier 2 (wallpaper blur behind sidebars):** **risky for responsiveness**. Do it last,
   only for our own apps, and measure on an iGPU and in the VM before it is turned on by default.
