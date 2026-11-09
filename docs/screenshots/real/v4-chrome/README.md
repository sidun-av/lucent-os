# One header row: Settings and Store (org.lucent.chrome)

Real screenshots of the test VM (QEMU, aarch64, 2560x1440), Lucent image from
CI `vm` run 42668937173 with Settings and the Store from commit 87e5388 and the
`org.lucent.chrome` module built in a `fedora:45` container in the VM (same Qt
6.11.2 / KF 6.31 as the image). Final check on a fresh CI image: see
`../v4-store/` and `../v4-settings/`.

Both apps are frameless and draw one header row, as in
`docs/mockups/concepts-2026/pebble-drift/04-settings.png`: app icon (opens
KWin's window menu), title, back/forward, search, minimise/maximise/close.
The pieces come from one shared QML module, `build_files/lucent-chrome`.

| File | What it shows |
|---|---|
| `01-settings-light.png` | Settings, light: one row, KWin-drawn shadow, corners clipped and outlined by the same KDE-Rounded-Corners effect as decorated windows |
| `02-settings-dark.png` | the same after Light → Dark, live (shadow, buttons and surface follow) |
| `03-dark-corners-store-settings-kwrite.png` | Store and Settings (frameless) next to KWrite (KWin's Lucent decoration): same corners, shadows and button glyphs |
| `04-close-hover.png` | close button hover: `--status-danger`, white glyph; minimise/maximise hover `--state-hover` |
| `05-win-left-snap.png` | Win+← tiles the Store to the left half (Win+→ to the right half, also checked) |
| `06-win-up-maximised.png` | Win+↑ maximises; maximise turns into restore; dragging the header to the top edge and double-clicking the header do the same |
| `07-window-menu.png` | click on the app icon (or right-click on the header, or Alt+F3): KWin's own window menu |
| `08-alt-tab.png` | Alt+Tab: one entry per window, title and icon as before ("Settings", "Store") |
| `09-buttons-left-live.png` | Settings > Like Windows > buttons on the left: the open Settings window moves its buttons at once (kwinrc, followed live), like KWrite's title bar |
| `10-scale-125.png` | display scale 125 %: crisp glyphs, header, drag and resize still right |

Checked by hand in the same session, no screenshot: edge and corner resize
(KWin's interactive resize), Alt+F4, minimise and restore from the taskbar,
the taskbar entry and icon unchanged (one entry, highlighted).

Alt+Space opens KRunner on Lucent for every window (it is bound to the
launcher search in `/usr/share/lucent/kglobalshortcutsrc`), decorated or
not; the window menu shortcut is Alt+F3.
