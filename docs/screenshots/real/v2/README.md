# Real Lucent OS, look v2: screenshots next to the mockups

Real captures of the image built by CI from `a33aa91` (build run
[42605127495](https://github.com/sidun-av/lucent-os/actions/runs/42605127495),
test-only qcow2 from `vm` run
[42609248861](https://github.com/sidun-av/lucent-os/actions/runs/42609248861)), booted **fresh** with
`LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`, the same size and scale
(1x) as `docs/mockups/*.png`. Software rendering (QEMU on an Apple M4,
llvmpipe), so blur and shadows are exactly what a GPU would draw, only slower.
Nothing was changed by hand after boot except opening the windows shown
(and turning off screen blanking).
Two exceptions, both because of the test VM, not the product: the boot
splash was captured with `plymouth.ignore-serial-consoles` added and one reboot (the
test image logs to a serial console, and Plymouth stays in text mode
there; installs have no serial console), and Alt+Tab (see below).

| Real (this folder) | Mockup | What to compare |
| --- | --- | --- |
| `01-desktop-dolphin-light.png` | `01-desktop.png` | Taskbar (start, search, centred apps with active tile and dots, tray, two-line clock), wallpaper, window frame, Files with menu bar and toolbar |
| `01-desktop-dolphin-dark.png` | `01-desktop-dark.png` | The same in Lucent Dark |
| `01b-taskbar-hover-preview.png` | `01-desktop.png` (preview card) | Hover preview card above a taskbar app |
| `02-launcher-light.png` | `02-launcher.png` | Full-screen launcher |
| `02-launcher-dark.png` | — | The launcher in Lucent Dark |
| `02b-launcher-search.png` | `02-launcher.png` | Typing searches apps, files and settings |
| `04-context-menu-light.png`, `04-context-menu-dark.png` | popups in `01`/`04` | Right-click menu in Files |
| `05-calendar-popup-light.png` | popups in `01` | Clock popup from the taskbar |
| `06-lock-screen.png`, `06b-lock-screen-password.png` | — (no mockup) | Lock screen, idle and with the password field |
| `08-login-screen.png` | — (no mockup) | Login screen (Plasma Login Manager) |
| `09-boot-splash.png` | — (no mockup) | Plymouth boot splash |
| `07-migration-wizard-welcome.png`, `07b-migration-wizard-account.png`, `07c-migration-wizard-folders.png` | `04-migration.png` | "Move from Windows" wizard (welcome, whose files, what to copy) |

## What the look is made of

| Part | Choice | Why |
| --- | --- | --- |
| Taskbar | One floating Plasma panel, Lucent Plasma theme (`desktoptheme/lucent*`), own search-field applet | Exactly the mockup's bar: 64 px, radius 20, 14/12 px gap, translucent + blur; active tile with accent bar, running dot. Stock Plasma panel, so it stays configurable. |
| Launcher | `org.lucent.launcher` (QML on Plasma's kicker backend) | Neither Kickoff nor Application Dashboard can be styled into `02-launcher`; the kicker backend keeps Plasma's app list, KRunner search and session actions. |
| Window frame | Aurorae v2 theme `Lucent` / `LucentDark` + KDE-Rounded-Corners | Aurorae v2 is KWin's native SVG decoration in 6.8 (no QML, fast). Klassy/Darkly have no maintained Fedora 45 builds for both arches; the rounded-corners effect does (author's COPR, built per KWin release). |
| Widgets | Breeze, driven by Lucent colour schemes from the mockup tokens, Inter 11 pt, frosted menus | Most Lucent apps are Flatpaks: they get Breeze from the KDE runtime but not a host Kvantum theme. One engine everywhere beats a prettier host-only one. |
| Icons | Lucent theme (the mockups' tiles and folders, 80 % safe area) over Papirus (Fedora package) | Papirus is maintained, GPL-3.0, flat, blue folders close to the mockups; Fluent/Colloid aren't packaged in Fedora. |
| Wallpaper | "Lucent Flow" rendered from the mockup SVG at 3840x2160 / 3840x2400, light + dark | Pixel-identical to the mockups; also on the lock and login screens. |
| Login, lock, boot | Plasma Login Manager greeter in Lucent Dark on the Lucent wallpaper; lock screen on the Lucent wallpaper; Plymouth theme `lucent` (logo + Fedora's spinner) with `rhgb quiet` | Same wallpaper and type from boot to desktop; the dark greeter keeps the wallpaper's colour instead of washing it out. |
| Motion | 0.7x durations, scale for open/close, squash for minimise, fading popups; wobbly off | Quick and calm; no genie (macOS) or wobble. |

## Still different from the mockups, and why

1. **Files shows Dolphin's Home view, not the "This PC" page** (folder cards,
   drive cards, recent files). That page is a separate phase; the window
   around it (title bar, menu bar, back/forward/up + path + view toggles +
   search toolbar, places panel) is in place. The path field and the search
   field are Breeze's (small radius, square-ish): Dolphin draws them through
   the widget style, and Breeze has no radius setting. Dolphin also aligns
   the path field with the file view, so it starts at the sidebar's edge.
2. **Status bar** is Dolphin's small item-count label, not a plain
   full-width bar: Dolphin 26's full-width bar always includes free space,
   and Dolphin measures it on the read-only composefs root ("0 B free")
   because Solid skips the OS partition. Remounting `/` with `x-gvfs-hide`
   is refused by the kernel and an fstab entry for `/` would risk the boot.
3. **Menus** (right-click, app menus) are Breeze `QMenu`s: frosted and in
   Inter, but with Breeze's smaller corner radius and denser rows than the
   mockup's 16 px popups. Breeze has no knobs for those metrics; a custom
   widget style would not reach the Flatpak apps.
4. **Tray**: Lucent line glyphs, full contrast, for volume, wired and Wi-Fi
   networks; the VM has wired networking and no audio device or battery,
   so it shows a wired icon and a muted speaker (battery stays Papirus's).
   No `RU` badge with one keyboard layout. The clock's date line is
   semibold like the time (Plasma's clock has one font).
5. **Taskbar icons** are 48 px with Lucent tiles drawn at ~38 px (mockup:
   40 px boxes, 37.5 px tiles). Kirigami only renders 16/22/32/48 px, and the
   tray only stays on one row below 52 px, so the bar keeps 64 px with
   7 px applet padding.
6. **Launcher** shows the installed apps (22), all with Lucent tiles; the
   chips are Plasma's menu categories (Graphics, Office, System, Utilities)
   rather than the mockup's curated set, which belongs to the store/apps
   phase. Admin tools are hidden (see the README's declutter list).
7. **Login screen**: the text field and power icons are Lucent's (rounded
   translucent field with an accent ring, line icons), the avatar is the
   initials picture, the on-screen keyboard no longer runs. Still stock:
   the field's width (~200 px) and the arrow as a separate button, and a
   "Show On-Screen Keyboard" button in the corner. Both live in QML that is
   compiled into `plasma-login-greeter` / plasma-workspace's
   `loginlockscreen` plugin and can't be overridden without patching them.
8. **Lock screen** with the password field: same compiled components, and
   Breeze blurs and brightens the wallpaper 1.6x under a light colour
   scheme, so in Lucent Light it turns almost white (the login screen avoids
   this by running in Lucent Dark). The idle lock screen is fine.
9. **Alt+Tab could not be captured**: in this VM KWin switches windows but
   no switcher overlay reaches the framebuffer: not the Lucent one, not
   KWin's stock layouts, not even a bare test window, at 1920x1080 and
   2560x1440 (software rendering). The Lucent switcher
   (`kwin/tabbox/org.lucent.switcher`) loads without QML errors; it needs a
   look on real hardware.
10. **Wizard**: the step sidebar is inset ~16 px from the window edge (Qt's
    wizard layout margins) and the pages are the real ones, so there's no
    "found disk" card or summary footer as in `04-migration`.
11. **Window title** is centred between the app icon and the buttons, not
    on the window (Aurorae), a few dozen px left of the mockup's position.

Generators: `design/` (each script names its source in `docs/mockups/`).
Licenses: `THIRD_PARTY.md`. Reproduce: `tools/vm/fetch.sh &&
LUCENT_VM_RES=2560x1440 tools/vm/run.sh --fresh`.
