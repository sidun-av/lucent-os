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

All apps are Flatpaks from Flathub, installed system-wide. From the
installer ISO they are **already there before the first login, without a
network**: the ISO carries them (see [Apps offline](#apps-offline-from-the-installer)).
On the online path (`bootc switch`), `lucent-flatpak-setup.service` downloads
whatever is missing in the background, retried until online.

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
   **read-only** through udisks (no root needed; see
   [Windows disks](#windows-disks)). Errors are explained in plain language
   (no permission, Windows hibernated / Fast Startup).
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

[Lucent Bridge](https://github.com/sidun-av/lucent-bridge) runs a Windows
`.exe`/`.msi` on double-click: Wine on x86_64, FEX + ARM64EC Wine on aarch64.
Nothing to install or download first:

- **The release RPM is in the image.** `build_files/build.sh` downloads
  `lucent-bridge-<v>-1.fc45.<arch>.rpm`, checks it against the release's
  `SHA256SUMS` and against the hash pinned in
  `build_files/lucent-bridge.sha256`, and installs it with `dnf`.
- **Wine is piecewise** (`wine-core wine-common wine-winefonts wine-mono` …,
  Gecko, `wine-dxvk`; on aarch64 Fedora's `fex-emu` plus ARM64EC Wine and
  `fex-emu-wine` from COPR `lacamar/wine-arm64ec`), never the `wine`
  metapackage: it pulls `wine-systemd`, whose binfmt handler would compete
  with lucent-bridge's (the RPM conflicts with it).
- **DXVK is really on.** Fedora's `wine-dxvk` looks for a GPU when it is
  installed; in an image build there is none and DXVK silently loses to
  wined3d. The build switches the alternatives to DXVK
  (`build_files/enable-dxvk.sh`, from lucent-bridge) and fails if it didn't.
- **Double-click and `./setup.exe`**: `.exe`/`.msi` MIME types default to
  lucent-bridge (merged into `/usr/share/applications/mimeapps.list`); its
  binfmt entry handles executable `.exe` files.
- **Fast first launch, light image.** A ready Wine prefix ("template") makes
  a program's first launch ~1 s instead of ~8 s, but it is 1.7–2.4 GB, so it
  is **not** in the image. `lucent-bridge-template.timer` builds it 3 min
  after boot, at idle CPU/IO priority, into `/var/lib/lucent-bridge/` (and
  again only after an update changes Wine or lucent-bridge).
  `/usr/share/lucent-bridge/prefix-template`, where lucent-bridge looks, is
  a link there. Until it exists, programs still start, via `wineboot`.
- The build fails unless `lucent-bridge --version` works, the
  `application/x-ms-dos-executable` default resolves to lucent-bridge, and
  `wine-systemd` is absent. CI then starts a Windows program in the built
  image, before and after the template exists (`build_files/smoke-test.sh`).

## Apps offline, from the installer

The ten default apps (with their runtimes ≈ 8.6 GB installed) are on the
installer ISO, so a new system has them before its first boot, with no
network and nothing to wait for:

- `iso/build-app-bundle.sh` (CI, in a Fedora 45 container) installs the apps
  from Flathub with Fedora's own flatpak and packs the resulting
  `/var/lib/flatpak` (zstd, split into 1 GB parts, `SHA256SUMS`).
  `iso/check-app-bundle.sh` unpacks it in the Lucent image with the network
  off and checks that flatpak sees every app and runtime.
- The ISO from bootc-image-builder gets the bundle as `/lucent-apps`
  (`mkksiso -a`); its kickstart (`iso/lucent-apps.ks`, merged by
  `iso/make-config.py`) unpacks it into the new system's `/var/lib/flatpak`
  with the new system's tools, verifies it and relabels it for SELinux. The
  installer stays interactive.
- If anything fails, the install still completes and
  `lucent-flatpak-setup.service` downloads the apps after first boot.
- CI's `iso` workflow can install the ISO unattended in QEMU/KVM **with no
  network** and check the apps on the installed disk.

Why not the alternatives: bootc-image-builder has no Flatpak support for
`anaconda-iso` (upstream only demos a `%post` that downloads from Flathub),
and Anaconda's own Flatpak source covers only the old rpm-ostree
(Silverblue) payload. Baking the apps into the image (`/usr` or a `/var`
seed) would add ~3 GB to the image and to every atomic update, while a
`/var` seed is applied only at install time anyway. On the ISO the cost is
paid once, by the download of the installer.

## Windows disks

The "Move from Windows" assistant and Dolphin open the computer's own
Windows partitions **read-only**, without a password for the administrator
at the computer: `50-lucent-windows-disks.rules` (polkit) grants udisks'
"mount a system device" action only to an active local session of a `wheel`
member, for NTFS on a non-removable drive, and
`99-lucent-windows-readonly.rules` (udev) makes udisks refuse `rw` for those
partitions, so Windows' hibernated/Fast-Startup data can't be damaged. Other
users get the normal password prompt. USB drives are not affected.

## Building

There is no local build requirement; CI does it all.

| Workflow | What |
| --- | --- |
| `build` | pytest → `podman build` natively on `ubuntu-24.04` (amd64) and `ubuntu-24.04-arm` (arm64) → push `ghcr.io/sidun-av/lucent-os:latest-<arch>` → multi-arch `:latest` |
| `iso` (manual) | offline app bundle → bootc-image-builder `anaconda-iso` from `:latest` → bundle added to the ISO → optional unattended offline install test in QEMU/KVM; ISO uploaded as a workflow artifact, sizes in the run summary |
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
build_files/build.sh          declutter, packages, lucent-bridge, DXVK, services
build_files/smoke-test.sh     CI: start a Windows program in the built image
system_files/                 copied to / : /etc/xdg defaults, look-and-feel,
                              colour schemes, systemd units, scripts, templates
migration-wizard/             "Move from Windows" wizard (lucent_migrate, po/, tests)
tools/vm/                     boot the real image in QEMU (test-only VM images from CI)
iso/                          installer ISO: offline app bundle, kickstart, config
.github/workflows/            CI
```

## Known gaps

- Not booted on real hardware yet; Plasma layout and shortcut defaults are
  verified only by review, not by a running session.
- On the online path (`bootc switch`, or a disk image without the app
  bundle) apps still arrive in the background after login, with no
  progress UI; the installer ISO doesn't have this gap.
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
Scribus, Firefox. При установке с ISO они ставятся с самого носителя, без сети,
и есть уже при первом входе. Программы Windows (.exe, .msi) запускаются двойным
щелчком через **Lucent Bridge** — ничего доустанавливать не нужно. При первом
входе помощник **«Переезд с Windows»** переносит документы, фото, закладки
браузеров и названия сетей Wi-Fi с диска Windows (диск открывается только для
чтения, без пароля для администратора компьютера).

**Статус: прототип.** Образ собирается в CI для x86_64 и ARM64, но на реальном
железе ещё не проверялся. Поддержка ARM-ноутбуков зависит от поддержки
конкретного устройства ядром Linux.

## License

Apache-2.0 — see [LICENSE](LICENSE).
