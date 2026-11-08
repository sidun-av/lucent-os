# Lucent OS

Lucent OS is a calm, fast desktop Linux for people leaving Windows: no ads, no
recommendations, no AI, no telemetry. **English is the primary language**;
Russian (and any other language the installer offers) is a translation,
picked by the locale chosen at install time. A short Russian summary is at
the end of this file. It looks clean (macOS-quality polish,
not a macOS copy) but keeps **Windows habits** so a new user feels at home on
day one.

> **Status: prototype.** The image builds in CI for x86_64 and aarch64; it has
> **not been tested on real hardware yet**. ARM laptop support depends on the
> device's support in the mainline/Fedora kernel (e.g. Snapdragon X laptops
> vary model by model).

## What you get

| Area | Lucent |
| --- | --- |
| Base | Fedora Kinoite 45 (KDE Plasma 6) as a **bootc** image — atomic updates, one-step rollback |
| Architectures | x86_64 (primary), aarch64 |
| Office | ONLYOFFICE Desktop Editors (Word/Excel/PowerPoint formats) |
| PDF | Okular (view, annotate, sign), PDF Arranger (merge, split, reorder) |
| Creative | GIMP 3, Krita, Inkscape, darktable, Kdenlive, Scribus |
| Web | Firefox |
| Windows apps | Wine (x86_64) / FEX-Emu + ARM64EC Wine (aarch64), plus `lucent-bridge` |
| Moving in | "Move from Windows" wizard: files, bookmarks, Wi-Fi names |

All apps are Flatpaks from Flathub, installed system-wide in the background
on first boot (`lucent-flatpak-setup.service`, retried until online).

## Desktop: macOS-clean look, Windows habits

- **Top bar**: launcher button (left), system tray and clock (right). No
  global menu — menus stay inside each window, which is what Windows users
  expect and what Flatpak/GTK/ONLYOFFICE apps actually support.
- **Floating bottom dock = Windows taskbar**: icons-only task manager with
  pinned apps, running windows grouped per app, hover thumbnails, click to
  minimise/restore.
- **Windows**: minimise / maximise / close on the **right**; double-click the
  title bar to maximise; drag to a screen edge to snap (Aero Snap).
- **Shortcuts**: Win (alone) opens the launcher · Win+E Files · Win+D show
  desktop · Win+L lock · Win+↑/↓ maximise/minimise · Win+←/→ snap ·
  Win+Tab overview · Alt+Tab (thumbnails) · Alt+F4 · Ctrl+Shift+Esc System
  Monitor · PrintScreen and Win+Shift+S screenshot (Spectacle) · Ctrl+C/V
  everywhere.
- **Language and keyboard**: English (`en_US.UTF-8`, `us` layout) unless the
  installer chose otherwise. Extra layouts come from the installer; with two
  or more, switch with **Alt+Shift** or **Win+Space**.
- **Files (Dolphin)**: double-click opens (single-click off), file extensions
  always visible, Windows partitions appear as **"Local Disk (C:)"**,
  "Data (D:)" (the partition containing `\Windows` gets C:; Russian:
  «Локальный диск (C:)»), and right-click → **Create New → Document /
  Spreadsheet / Presentation** creates blank `.docx/.xlsx/.pptx` that open
  in ONLYOFFICE.
- **Look**: Lucent Light / Lucent Dark colour schemes and look-and-feel
  packages, Inter UI font, JetBrains Mono, KWin blur, own wallpaper.

Everything is done with stock Plasma 6 mechanisms — a look-and-feel package
with a layout script (`system_files/usr/share/plasma/look-and-feel/`) and
`/etc/xdg` defaults — so users can change any of it in System Settings, and
their own settings always win.

## Privacy and declutter

- No telemetry: KDE UserFeedback globally disabled, Fedora's weekly
  `countme` ping masked, ABRT/DrKonqi crash uploaders removed.
- No ads or nags: plasma-welcome (donation/promo pages) removed; KRunner's
  "install this app" and web-search suggestions disabled.
- Fewer rarely-used apps: games, PIM suite, Matrix client, desktop-sharing
  server etc. removed (all still installable from Flathub).
- Fedora's own Flatpak remote is disabled in favour of a single, unfiltered
  Flathub remote, so apps aren't listed twice in Discover.

## Performance tweaks (each justified in the file that sets it)

- Fedora already provides zram swap and systemd-oomd — Lucent does **not**
  duplicate them.
- Baloo indexes file **names only** — content indexing of a freshly migrated
  Windows library would pin CPU and disk for hours after first login.
- Animations at 0.7× duration — snappier without losing spatial cues.
- Stop timeout 15 s (Fedora: 45 s) — a hung service can't stall shutdown.
- Moderate KWin blur strength — cheap on weak GPUs.

## "Move from Windows" migration wizard

`migration-wizard/` — Python + PySide6 (Fedora's `python3-pyside6`).
Written in English; translations are gettext catalogs in
`migration-wizard/po/` (Russian: `ru.po`), compiled into the image and
picked by locale. A test checks that every UI string has a Russian
translation and that both languages load.
Starts once at first login if Windows disks are present
(`/etc/xdg/autostart/org.lucent.Migrate.desktop`), and is in the launcher.

1. Finds NTFS/BitLocker partitions with `lsblk -J`; mounts them
   **read-only** through udisks (no root needed).
2. Finds `Users\*` profiles (skips Public/Default…), including
   OneDrive-redirected Desktop/Documents/Pictures.
3. Maps Documents, Pictures, Desktop, Downloads, Music, Videos to the XDG
   folders, shows sizes, copies with a conflict policy (keep both as
   `file (2).ext` · replace if newer · skip). Never follows junctions, skips
   `desktop.ini`/`Thumbs.db`, keeps going on errors and lists them at the end.
4. Bookmarks from Chrome, Edge, Yandex Browser, Opera and Firefox (reads a
   copy of `places.sqlite` **with its -wal**, so recent bookmarks aren't
   lost) → standard `bookmarks.html` files to import into Firefox.
5. **Wi-Fi: names only.** Windows stores Wi-Fi keys DPAPI-encrypted, bound
   to that Windows installation; they cannot be decrypted from Linux. The
   wizard adds the networks to NetworkManager and Plasma asks for each
   password once on first connect. Enterprise (802.1X) networks need manual
   setup.
6. BitLocker volumes are reported with instructions (unlock in Dolphin with
   the recovery key).

Core logic is pure and tested against a fake Windows tree; the GUI is a thin
layer with one offscreen smoke test:

```sh
cd migration-wizard
pip install pytest PySide6   # PySide6 optional: only for the GUI smoke test
pytest
```

## "Next generation (beta)": ArtCraft

[ArtCraft](https://getartcraft.com/apps) (`github.com/storytold`, Apache-2.0)
is a new suite of creative/office apps written from scratch in Rust. It is
weeks old and alpha, so it is **not preinstalled**: the launcher entry
"Next generation (beta)" / `lucent-nextgen install` downloads the official
launcher Flatpak bundle for your CPU, verifies it against the release's
`SHA256SUMS.txt`, and installs it for the current user (`lucent-nextgen
remove` undoes it).

**AI audit (Nov 2026):** the launcher and the apps checked (e.g. PhotoCraft)
contain **no AI features** and no telemetry; the separate
`craft-ai-integrations` layer (cloud generative providers, local
segmentation models) is not linked by them. The launcher does contact
GitHub for update checks and screenshots. PhotoCraft's roadmap mentions a
future "AI / generative" tier, so each new version needs a re-check before
Lucent recommends it.

## Windows apps: `lucent-bridge`

The sibling project `lucent-bridge` (Wine on x86_64, FEX + Wine on aarch64)
is being built in parallel. The image already layers Wine on x86_64 and,
on aarch64, Fedora's `fex-emu` plus an ARM64EC-enabled Wine and FEX's
ARM64EC/WoW64 DLLs (`fex-emu-wine`) from COPR `lacamar/wine-arm64ec` (until
Fedora ships them). Wine is installed without `wine-systemd`, whose binfmt
handler for Windows executables would compete with the one lucent-bridge
ships. Its RPM is installed at the clearly marked
**LUCENT-BRIDGE HOOK** in `build_files/build.sh` — drop
`lucent-bridge-*.rpm` into `rpms/` until it has a package repository.

## Building

There is no local build requirement; CI does it all.

| Workflow | What |
| --- | --- |
| `build` | pytest → `podman build` natively on `ubuntu-24.04` (amd64) and `ubuntu-24.04-arm` (arm64) → push `ghcr.io/sidun-av/lucent-os:latest-<arch>` → multi-arch `:latest` |
| `iso` (manual) | bootc-image-builder `anaconda-iso` from `:latest`, uploaded as a workflow artifact |
| `vm` (after `build`, or manual) | **test-only** qcow2 (autologin user, SSH key) + fake Windows disk for `tools/vm/`; never a release artifact |

Locally, on any Linux with podman:

```sh
sudo podman build -t lucent-os .
```

Switch an existing Fedora Atomic / bootc system to Lucent:

```sh
sudo bootc switch ghcr.io/sidun-av/lucent-os:latest
```

## Repository layout

```
Containerfile                 image definition (FROM Kinoite 45)
build_files/build.sh          declutter, packages, services, lucent-bridge hook
system_files/                 copied to / : /etc/xdg defaults, look-and-feel,
                              colour schemes, systemd units, scripts, templates
migration-wizard/             "Move from Windows" wizard (lucent_migrate, po/, tests)
tools/vm/                     boot the real image in QEMU (test-only VM images from CI)
iso/config.toml               installer ISO settings
.github/workflows/            CI
```

## Known gaps

- Not booted on real hardware yet; Plasma layout and shortcut defaults are
  verified only by review, not by a running session.
- First-boot apps arrive in the background after login (needs network);
  there is no progress UI yet.
- Discover's home page still shows Flathub's editorial picks.
- Firefox's own telemetry settings are Mozilla's defaults (no enterprise
  policy shipped yet for the Flatpak).
- Bookmarks are exported as HTML for a one-click manual import, not injected
  into a Firefox profile.

## Кратко (по-русски)

**Lucent OS** — чистый и быстрый Linux для тех, кто уходит с Windows. Без рекламы,
рекомендаций, ИИ и телеметрии. Внешне — аккуратный, «маковский» по качеству вид;
по привычкам — как Windows: кнопки окна справа, панель задач внизу, Win открывает
меню, Win+E — файлы, Alt+Tab, Alt+F4, Ctrl+Shift+Esc, Alt+Shift / Win+Space для
смены раскладки (если раскладок две и больше). Основной язык системы —
английский; русский — перевод, выбирается языком, указанным при установке. Основа — Fedora Kinoite (KDE Plasma 6) в виде bootc-образа:
обновления атомарные, при проблеме можно откатиться к прошлой версии.

Предустановлены (Flatpak): ONLYOFFICE (вместо Word/Excel/PowerPoint), Okular и
PDF Arranger (вместо Acrobat), GIMP 3, Krita, Inkscape, darktable, Kdenlive,
Scribus, Firefox. При первом входе помощник **«Переезд с Windows»** переносит
документы, фото, закладки браузеров и названия сетей Wi-Fi с диска Windows.

**Статус: прототип.** Образ собирается в CI для x86_64 и ARM64, но на реальном
железе ещё не проверялся. Поддержка ARM-ноутбуков зависит от поддержки
конкретного устройства ядром Linux.

## License

Apache-2.0 — see [LICENSE](LICENSE).
