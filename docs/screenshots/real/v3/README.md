# Real Lucent OS, look v3: screenshots next to the mockups

Real captures of the image built by CI from `b1f5023` (build run
[42627151707](https://github.com/sidun-av/lucent-os/actions/runs/42627151707),
test-only qcow2 from `vm` run
[42631597857](https://github.com/sidun-av/lucent-os/actions/runs/42631597857)),
booted **fresh** with `LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`, the same
size and scale (1x) as `docs/mockups/*.png`. Software rendering (QEMU on an
Apple M4, llvmpipe).

What was done by hand after the first boot, and nothing else: screen
blanking off; four sample documents for Okular and the list view (Office
files copied from `/usr/share/templates`, a PDF printed with PySide6); the
first-run wizard closed; windows opened; Dolphin's view mode switched
between icons and details; light/dark switched with
`plasma-apply-lookandfeel` (what Quick Settings' Theme does). The first-boot
Flatpak setup (apps + the Kvantum extension for Okular) ran on its own. The
login screen was captured after logging out of the test image's autologin
session, then used to log back in; the lock screen was unlocked with the
real password through the new UI.

| Real (this folder) | Mockup | What to compare |
| --- | --- | --- |
| `01-desktop-dolphin-light.png`, `-dark.png` | `01-desktop.png`, `01-desktop-dark.png` | Files: rounded path field right after back/forward/up, segmented view toggle, flat split/search, sidebar with the mockup's accent line glyphs and a selected pill, plain full-width status bar, 64 px icon grid |
| `02-dolphin-list-light.png`, `-dark.png` | `01-desktop.png` (list rows of "Recent files") | Details view: light accent selection with normal text, grey hover, no zebra stripes, quiet header |
| `03-system-settings-light.png`, `-dark.png` | `03-settings.png` | System Settings (Kirigami on Kvantum): fields, buttons, radio, slider; opens at the mockup's large size |
| `04-okular-flatpak-light.png`, `-dark.png` | — | Okular from Flathub with Lucent's Kvantum theme (Flathub's `org.kde.KStyle.Kvantum` extension, per-app `QT_STYLE_OVERRIDE`, theme synced per user) |
| `05-context-menu-light.png`, `-dark.png` | popups in `01`/`04` | Right-click menu: radius 12, translucent + blur, hairline, soft shadow, inset pill on hover, compact rows |
| `06-alt-tab-light.png`, `-dark.png` | — (popup tokens of `lucent.css`) | Alt+Tab, captured with Alt held through QMP `input-send-event`: Lucent card (radius 20, hairline, shadow), thumbnails with an accent ring on the current window |
| `07-tray-light-3x.png`, `07-tray-dark-3x.png` | tray of `01` | Tray at 3x: full-contrast Lucent line glyphs in both modes (new: notifications bell and updates glyphs) |
| `08-lock-screen.png`, `08b-lock-screen-password.png` | — | Lucent lock screen: dimmed dark wallpaper (also in light mode), clock; then blur, initials avatar, 340 px pill field with the arrow inside, round session actions, no virtual keyboard |
| `09-login-screen.png` | — | Login screen: own SDDM theme `lucent`, same language, power row (Sleep, Restart, Shut Down) |

## What changed since v2

| Area | v2 | v3 |
| --- | --- | --- |
| Native Qt apps | Breeze with Lucent colours | **Kvantum** with a generated Lucent theme (`design/gen_kvantum.py` from `lucent.css`: 10 px fields, segmented toggle groups, 12 px menus, 8 px pills, thin overlay scrollbars, 18 px checks), under Lucent's **style plugin** (`build_files/lucent-style`, a QProxyStyle) that fixes what Kvantum and Dolphin disagree on: the path bar is drawn as a field and starts right after back/forward/up; plain toolbar actions stay flat (only toggle groups are segmented); selected file names keep normal text on the light tint; Qt Quick lists get a solid accent pill (their selected text is white); the free-space line is hidden when it would describe the read-only image |
| Flatpak Qt apps | Breeze from the runtime | Kvantum extension per KDE runtime + `QT_STYLE_OVERRIDE=kvantum` (first-boot service), Lucent theme copied into each app's config dir and switched light/dark by a user path unit |
| Login | Plasma Login Manager, compiled-in greeter | **SDDM** with Lucent's own QML theme; Fedora's plasmalogin autologin config is carried over at boot; presets keep SDDM |
| Lock screen | stock, near-white in light mode | Lucent `LockScreenUi.qml` (Plasma 6.8 keeps the lock screen in the desktop *shell* package, not the look-and-feel package, so it replaces the stock file at build time; if Plasma reshapes that package the build keeps the stock one) on the dark wallpaper in both modes |
| Alt+Tab | not captured | captured; the switcher draws its own card instead of the theme frame KWin gave it |
| Tray | Papirus bell and update glyphs (bell almost invisible in light) | Lucent line glyphs for them, accent badge for new items |

## Still different from the mockups, and why

1. **No "This PC" page.** Files opens on Home. A drive-card overview would
   need a KIO worker or a Dolphin view plugin; not robust enough for this
   round. The places headers are KIO's ("Places", "Devices"), not the
   mockup's "Quick access/Devices/Other", and "Local Disk (C:)" keeps
   Papirus's drive icon.
2. **No free space in the status bar.** Dolphin asks Solid for the mount of
   `/var/home`, and Solid matches the composefs root (`/`, 0 B free) because
   the OS partition's first mount point is `/etc`, not `/var`. Lucent's
   style hides that line, so the bar is plain (item count only); USB and
   Windows disks still show their real space.
3. **Segmented toggle**: the selected segment fills the track (white, hairline)
   instead of a chip with 3 px padding; Kvantum draws grouped buttons edge to
   edge.
4. **Flatpak apps don't get the style plugin**: in Okular every adjacent
   toolbar button group is segmented (including zoom in/out), and Kdenlive's
   runtime (KDE 6.11) has no Kvantum build on Flathub yet, so it stays
   Breeze. Flatpaks installed later by the user keep Breeze until
   `lucent-flatpak-setup` runs again.
5. **System Settings / Discover lists** are Kirigami's own: 28 px rows
   instead of 46, monochrome/colour icons instead of the mockup's coloured
   squares, and a solid accent selection (their white selected text needs
   it), while Dolphin uses the light tint.
6. **Empty Office templates** preview as blank pages in Files; real documents
   show their content.
7. **Login/lock**: no media controls on the lock screen; the keyboard-layout
   pill appears only with two or more layouts. The OEM path (Fedora's
   `plasma-setup` with no user yet) was written for Plasma Login Manager and
   is untested with SDDM.
8. **Tray**: the overflow arrow is still Plasma's filled triangle; the VM has
   no Wi-Fi, battery or audio device, so it shows wired + muted.
9. Software rendering in the VM: blur and shadows are what a GPU draws,
   only slower.

Reproduce: `tools/vm/fetch.sh 42631597857 && LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`.
Licenses: `THIRD_PARTY.md` (Kvantum GPL-3.0-or-later, SDDM GPL-2.0-or-later,
the lock screen file GPL-2.0-or-later as a derivative of Plasma's; Lucent's
theme, style plugin and SDDM theme Apache-2.0).
