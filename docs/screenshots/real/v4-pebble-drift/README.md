# Real Lucent OS, look v4 "Pebble Drift": screenshots next to the mockups

Real captures of the image built by CI from `d6f7cfb` (build run
[42677206920](https://github.com/sidun-av/lucent-os/actions/runs/42677206920),
test-only qcow2 from `vm` run
[42682697952](https://github.com/sidun-av/lucent-os/actions/runs/42682697952)),
booted **fresh** with `LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`: the
size and scale (1x) of the Pebble Drift mockups in
`docs/mockups/concepts-2026/pebble-drift/`. aarch64 QEMU on an Apple M4,
software rendering (llvmpipe). That image has every restyle-shell change
except two that landed after it: `lucent-theme` writing kdeglobals with
`--notify` (checked live on the VM: `apply --mode auto` then switched the
session to dark through Plasma's own schedule), and the Figtree UI font (another
track's work); the text here is still Inter.

What was done by hand after the first boot, and nothing else: screen
locking and dimming off; four sample documents (a PDF printed with
PySide6, Office files copied from `/usr/share/templates`); the first-run
wizard closed with Cancel; one log-out and log-in (to capture the login
screen; it also replaced the first-login placeholder of Firefox in the
taskbar, whose Flatpak was still installing); windows opened; light and
dark switched with `lucent-theme apply --mode dark`. The first-boot
Flatpak setup (10 apps and the Kvantum extension for Okular) ran on its
own, and so did the per-user Kvantum sync into Okular.

| Real (this folder) | Mockup | What to compare |
| --- | --- | --- |
| `01-desktop-files-light.png`, `-dark.png` | `01-desktop.png`, `02-desktop-dark.png` | Drift wallpaper; taskbar attached to the bottom edge (search well, Files on a raised pillow with the accent bar); window radius 18 with the long soft shadow; a 48 px header in the window colour, buttons right; Files: sidebar as a sunken well with the current place as a raised pillow, sunken path field, segmented view toggle, content on the matte window surface. The This PC page itself is this-pc's |
| `02-launcher-light.png`, `-dark.png` | `03-launcher.png` | near-opaque scrim, raised 68 px query field with the 2 px focus ring and halo, the first result on a raised tile, account and Lock / Restart / Sleep / Shut down at the bottom |
| `03-context-menu-light.png`, `-dark.png` | popover tokens (`--surface-popover`, radius 12-16, `--shadow-popover`) | Files' menu on a file: matte popover, accent-soft hover rows; the right-clicked file shows `.card.sel` (selected tint + accent ring) |
| `04-calendar-light.png`, `-dark.png` | popover tokens | the clock's calendar: Plasma popover in Pebble materials, solid accent tab underline |
| `05-notification-light.png`, `-dark.png` | popover tokens | a notification popover |
| `06-alt-tab-light.png`, `-dark.png` | the hover-preview card of `01-desktop.png` | Alt+Tab (Alt held through QMP): Drift night popover card in both modes, the current window on `--surface-selected` with the accent ring |
| `07-login.png` | — (Drift night tokens) | SDDM: night Drift wallpaper, rounded-square avatar on the design's gradient, matte 360 px field with the indigo button, rounded power actions |
| `08-lock.png`, `08b-lock-password.png` | — (Drift night tokens) | lock screen idle, then the prompt (unlocked with the real password through it) |
| `09-okular-light.png`, `-dark.png` | — | Okular from Flathub, styled by Lucent's Kvantum theme through Flathub's `org.kde.KStyle.Kvantum` extension: sunken search field, segmented zoom and tool groups |
| `10-wizard-light.png`, `-dark.png` | — | "Move from Windows" as restyle-assets restyled it, under the new window frame |

## What changed since v3

| Area | v3 (Lucent) | v4 (Pebble Drift) |
| --- | --- | --- |
| Source of the look | values copied by hand from `docs/mockups/lucent.css` | every generator reads `pebble-drift.css` through `design/tokens.py` (CI tests the parser, the accent maths, and that the committed themes are what the generators produce) |
| Taskbar | floating, 20 px corners, translucent | attached to the bottom edge, full width, 68 px, matte near-opaque slab with a hairline and top light; search as a sunken well; active app on a raised pillow with the 16 x 3 accent bar |
| Popups (menus, calendar, tray, OSD, notifications, tooltips) | frosted, radius 16 | matte `--surface-popover`, `--shadow-popover`; light blur with grain (KWin noise) |
| Window frame | 44 px bar, centred title, full-height red close | 48 px header in the window colour, icon and title left, 44 x 36 rounded buttons right, close turns `--status-danger`; radius 18 (decoration and KDE-Rounded-Corners), `--shadow-window` |
| Qt apps (Kvantum) | flat fields, light pills | raised pillow buttons, combos, tabs and on-segments; sunken wells for fields, segmented tracks and progress; Files' sidebar a sunken well (Lucent's style plugin) |
| Accent and mode | fixed blue | eight swatches and light/dark/auto through `lucent-theme` (`docs/theming.md`) |
| Launcher | chips, user and power top right | raised query field, segmented category track, raised hover tiles, footer with account and power actions |
| Alt+Tab, login, lock | Lucent dark card, round controls | Drift night, rounded squares |

## Still different from the mockups, and why

1. **The header is three rows, not one.** The mockup puts the app icon,
   menus, navigation, path, view toggles, search and window buttons in one
   64 px row. KWin's decoration can't hold an app's widgets (Qt widget apps
   have no client-side decorations), so Files has the 48 px title row, its
   menu bar and its toolbar; all three share the window colour with no
   lines between them. Files' search is a button that opens Dolphin's
   search bar, not a field.
2. **Taskbar:** the app tiles sit 68 px apart without the mockup's sunken
   group well; Plasma's task manager sizes each cell to the panel's
   thickness and has no container background. The tray's overflow arrow is
   still the icon theme's filled triangle (the tray draws `arrow-up` from
   the icon theme). The clock's date line has the time's weight. The VM has
   no Wi-Fi, battery or sound device, so the tray shows wired + muted.
3. **Launcher:** it covers the taskbar (a full-screen Plasma dashboard
   window); results are one grid of apps, actions and files, not the
   mockup's grouped Best match / Apps / Files / Settings sheets with counts
   in the tabs (the tabs are app categories). Okular isn't found by "pdf"
   because KRunner matches names, and the mockup's "PDF Viewer" is a name
   Lucent doesn't use yet.
4. **Accent in running apps.** `lucent-theme apply --accent` recolours
   Plasma, Kirigami apps, the launcher and the colour scheme at once, but a
   Qt widget app that is already running (Files) keeps its Kvantum theme
   until it is started again (checked on this image: Files kept the Indigo
   ring after switching to Azure). Light/dark does switch native apps live
   (the widget style changes); a running **Flatpak** app (Okular) keeps the
   mode it started with.
5. **Files details:** the free-space bar in the status bar is Dolphin's own
   grey bar (it paints itself); the selected segment of the view toggle
   fills its track edge to edge instead of a chip with 3 px padding
   (Kvantum draws grouped buttons that way); the grain of `--grain-image`
   is on shell surfaces only (KWin's blur noise), not in app windows.
6. **Okular** draws its thumbnail selection itself in the solid accent.
7. **Login and lock** use Drift night in both modes on purpose; the
   keyboard-layout pill appears only with two or more layouts, and there
   are no media controls.
8. **Rendering:** software rendering in the VM; blur and shadows are what
   a GPU draws, only slower.

Not this track's (see their own notes): the wallpapers, folder icons, boot
splash and the wizard's restyle (restyle-assets); Files' This PC page, its
places and the drive rings, which read dim in dark mode (this-pc); the
Figtree UI font.

## Reproduce

```sh
tools/vm/fetch.sh 42682697952
LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh
tools/vm/ssh.sh --session lucent-theme apply --mode dark
```

Licenses: `THIRD_PARTY.md`.
