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

- **One taskbar** attached to the bottom edge (Pebble Drift,
  `docs/mockups/concepts-2026/pebble-drift/`): start button and a search
  field on the left, pinned and running apps in the middle (active app on a
  raised tile with an accent bar, running apps with a dot), system tray and
  a two-line clock on the right. A matte, near-opaque 68 px slab. No global
  menu — menus stay inside each window, which is what Windows users expect
  and what Flatpak/GTK/ONLYOFFICE apps actually support.
- **Launcher** (Win key, start button or the search field): full screen,
  a large search field, category tabs and a grid of large app icons;
  typing searches apps, files and settings at once; your account and
  Lock / Restart / Sleep / Shut down at the bottom.
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
- **Files (Dolphin)** opens on **This PC**, as Explorer does: the user
  folders with item counts, the drives with their free space (ring gauges;
  Windows partitions read-only, USB drives with Eject) and recent files; it
  is also the first entry of the sidebar (`kio_thispc`, see
  [docs/this-pc.md](docs/this-pc.md) for why it is a KIO worker and not a
  Dolphin patch). Double-click opens (single-click off), file extensions
  always visible, Windows partitions appear as **"Local Disk (C:)"**,
  "Data (D:)" (the partition containing `\Windows` gets C:; Russian:
  «Локальный диск (C:)»), and right-click → **Create New → Document /
  Spreadsheet / Presentation** creates blank `.docx/.xlsx/.pptx` that open
  in ONLYOFFICE.
- **Look**: Pebble Drift, light and dark, generated from the design's
  tokens (`pebble-drift.css`): own Plasma theme (taskbar, matte popovers),
  Kvantum widget style (raised controls, sunken fields), window frame (a
  header row in the window colour, rounded minimise/maximise/close buttons,
  18 px corners), eight accent colours (`lucent-theme`, see
  `docs/theming.md`), Lucent app and folder icons on top of Papirus
  (folders in the accent's indigo at every size, Papirus's own recoloured
  to match), colour schemes, Figtree at 11 pt as the UI font (Inter in
  languages Figtree has no letters for, such as Russian), the "Drift"
  wallpaper (its night version in dark mode; also on the lock and login
  screens), a boot
  splash with the Lucent mark on Drift night and the Alt+Tab switcher.
  Generators and sources: `design/`, licenses: `THIRD_PARTY.md`.

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
- A launcher with apps, not tools: Info Center, Help Center, Firewall,
  KCharSelect, Emoji Selector, KDE Connect SMS, KFind, Partition Manager,
  Menu Editor, KWallet Manager and KDebugSettings stay installed but are
  hidden from it (NoDisplay); the first three are reachable from Settings
  and F1. The on-screen keyboard isn't started (session and login screen).
- Fedora's own Flatpak remote is disabled in favour of a single, unfiltered
  Flathub remote, so apps aren't listed twice in Discover.

## Performance tweaks (each justified in the file that sets it)

- Fedora already provides zram swap and systemd-oomd — Lucent does **not**
  duplicate them.
- Baloo indexes file **names only** — content indexing of a freshly migrated
  Windows library would pin CPU and disk for hours after first login.
- Animations at 0.7× duration — snappier without losing spatial cues
  (scale for open/close, squash for minimise; wobbly windows off).
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
layer with offscreen smoke and style tests:

```sh
cd migration-wizard
pip install pytest PySide6   # PySide6 optional: only for the GUI tests
pytest
```

Its look is Pebble Drift, light or dark with the system (and it switches
live, as does Settings → Text size): every colour and size comes from
`lucent_migrate/tokens.css`, a copy of the design's `pebble-drift.css`
part 1 that a test keeps identical (`python3 design/sync-wizard-tokens.py`
refreshes it). `python3 design/preview-wizard.py OUT [--dark] [--lang ru]`
screenshots every page in a real window; previews of all the Pebble Drift
assets are in `docs/screenshots/pebble-drift-assets/`.

## Lucent Store

`apps/lucent-store/` — the "Store" in the launcher and taskbar (PySide6 +
QML, light/dark following the system; every colour, size, radius and shadow
is a token in `lucent_store/theme.py`, ported from the "Pebble Drift"
direction, `docs/mockups/concepts-2026/pebble-drift/`). KDE Discover stays
installed (it still opens `.flatpakref` files) but is hidden from the launcher.

- **No recommendations, ads, AI or tracking.** Home and the category pages
  show only the curated, versioned catalog shipped in the image
  (`lucent_store/catalog.toml`): "Instead of Microsoft Word → ONLYOFFICE",
  Photoshop → GIMP, Acrobat → Okular + PDF Arranger, … 7-Zip → Archives,
  each with Installed/Install, plus a "Have a Windows installer? Just
  double-click it" card explaining Lucent Bridge.
- **Search covers all of Flathub** from flatpak's local AppStream copy
  (`/var/lib/flatpak/appstream/flathub/<arch>/active/appstream.xml.gz`):
  typing never touches the network. Ranking: name, keywords, summary;
  verified publishers and curated apps win ties; a Windows program's name
  ("photoshop", "acrobat") brings its curated replacement first. Results
  show the verified-publisher mark and the license.
- **App page**: description, screenshots (downloaded on that page only and
  cached in `~/.cache/lucent-store`), version, size, license and the
  sandbox permissions in plain words ("Can read and change all your files").
- **Installed** and **Updates** (Flatpak apps; Lucent itself updates in
  Settings → Updates). The only other network use is flatpak's own update
  check and AppStream refresh (at most daily) against Flathub.
- Installs run the `flatpak` CLI as the user (`flatpak install --system -y`,
  progress parsed from its output); flatpak's system helper and polkit
  decide, as Fedora configures them: an active local admin needs no
  password, others get Plasma's prompt. The store never runs as root.
- English UI with a Russian gettext catalog (`apps/lucent-store/po/`);
  a test checks that every Python, QML and catalog string is translated.

```sh
cd apps/lucent-store
pip install pytest PySide6
pytest                                    # 68 tests: catalog, AppStream search, flatpak
                                          # commands/progress, permissions, i18n, QML smoke
python -m lucent_store --fake             # preview anywhere (no flatpak needed)
```

## Lucent Settings

`apps/lucent-settings/` — the "Settings" in the launcher and taskbar
(PySide6 + QML). The look is the 2026 "Pebble Drift" direction
(`docs/mockups/concepts-2026/pebble-drift/04-settings.png`, `05-settings-dark.png`):
matte surfaces with grain, raised "pillow" controls, sunken wells, soft
shadows, Figtree (the system UI font, SIL OFL), an indigo accent; light and dark follow
the system. Every visual value is a token in
`lucent_settings/qml/Lucent/Theme.qml`, ported 1:1 from `pebble-drift.css`.
Sections: Network & internet, Bluetooth & devices, Display, Sound,
Appearance, Wallpaper, Like Windows, Keyboard & language, Windows apps,
Updates, Users, About this PC. KDE System Settings stays installed but hidden
from the launcher; About this PC → "Advanced settings…" opens it.

The Pebble Drift wallpapers (Drift, Tide, Aurora, each with a night version
that Plasma switches to in dark mode) are in `system_files/usr/share/wallpapers/`,
rendered at 4K and at 2560x1440 from the mockups by
`design/render-drift-wallpapers.sh`. Drift is the default (desktop, lock and
login screens, login splash); the older "Lucent Flow" stays as a choice.

| Section | Does | Through |
| --- | --- | --- |
| Wi-Fi & Network | Wi-Fi on/off, nearby networks, connect with a password, cable connect/disconnect | NetworkManager (`nmcli`; the password goes on stdin, never in argv) |
| Bluetooth | on/off, paired devices (connect, forget), pair new ones | BlueZ D-Bus (pairing prompts come from Plasma's agent) |
| Display | resolution (with a 15 s "keep or go back"), scale 100–200 %, night light | `kscreen-doctor`, KWin (`[NightColor]`, D-Bus state) |
| Sound | output/input device, volume, mute | PipeWire (`pactl -f json`, `wpctl`) |
| Appearance, Wallpaper | Light / Dark / Auto, accent color (or "Match wallpaper"), text size, reduce motion; wallpapers (Lucent's, the system's, `~/Pictures`) | `plasma-apply-lookandfeel` (Kvantum and Flatpak follow as before), Plasma's automatic mode, `plasma-apply-colorscheme`, Plasma's accent-from-wallpaper, `plasma-apply-wallpaperimage`, kdeglobals |
| Like Windows, Keyboard & language | the Win-key shortcuts, window buttons right/left, double-click; layouts in use, layout switch (Alt+Shift / Ctrl+Shift / Win+Space), language | kwinrc, kdeglobals, kxkbrc (+ KDE's reload signals), `localectl` |
| Users | name, picture (initials by default), password | AccountsService D-Bus; the password is hashed in-process (libxcrypt) and sent over D-Bus, polkit asks for the current one |
| Updates | versions on disk in plain words, check, download (applied at restart), roll back, Flatpak app updates, automatic downloads | the registry's manifest digest for this CPU (`skopeo inspect --raw`, no root) against the deployments' digests, since `rpm-ostree upgrade --check` is unreliable for container images; rpm-ostree's daemon to stage and roll back (polkit; Fedora lets an active admin do it without a prompt); `flatpak`; `settings-helper` via pkexec for `/etc/rpm-ostreed.conf` |
| Windows apps | installed programs with icon, size, compatibility, "Open folder", Remove; whether this CPU runs them natively or translated | `lucent-bridge list/plan/remove --json` |
| About | Lucent version, model, CPU, memory, storage, links to KDE System Settings and Info Center | os-release, `lscpu`, sysfs |

Never runs as root; each change goes through the service's own polkit
check. English UI with a Russian gettext catalog (`apps/lucent-settings/po/`).

```sh
cd apps/lucent-settings
pip install pytest PySide6
pytest            # backends against captured fixtures (argv and D-Bus calls, parsing),
                  # the pkexec helper, i18n, and every page offscreen in light and dark
```

## "Next generation (beta)": ArtCraft

[ArtCraft](https://getartcraft.com/apps) (`github.com/storytold`, Apache-2.0)
is a new suite of creative/office apps written from scratch in Rust. It is
weeks old and alpha, so it is **not preinstalled**: the Store's "Next
generation · beta" section (also the launcher entry "Next generation
(beta)") installs an app with `lucent-nextgen install --yes --version V
--sha256 H APP`: the app's official Flatpak bundle for your CPU, verified
against the release's `SHA256SUMS.txt` **and** the hash pinned in the
Store's catalog, installed for the current user only.

**AI audit (2026-11-09, at the pinned tags):** VectorCraft, WordCraft,
GridCraft and DeckCraft link no AI library (`craft-ai-integrations`, ONNX,
cloud clients) and have no AI features; they get portals plus one or two
XDG folders, no home or host access. Not offered: **PhotoCraft** (a local
face-detection neural network) and **PdfCraft** (neural OCR models and
visible "AI assistant" menu entries), and the **ArtCraft launcher** (it can
run host commands and installs apps Lucent hasn't checked). Caveats: every
Craft app checks GitHub for a newer release at startup (a plain GET, no
identifiers), and each includes a dormant MCP server (an interface for AI
agents to drive the app) that runs only when started from the command line. Each version
bump in `catalog.toml` needs a re-audit.

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
  image, before and after the template exists (`build_files/smoke-test.sh`),
  the template build with a system service's environment (no `HOME`).
- **SELinux and composefs.** `/usr` is a composefs mount made in the
  initrd, and Linux also checks `mmap`/`mprotect` on its files with the
  *mounter's* credentials (`kernel_t`). Relocating a 32-bit Windows DLL from
  `/usr/lib64/wine/i386-windows` needs `execmod`, which `kernel_t` lacked:
  every 32-bit program (most installers, Wine Mono's own helper) died, and
  Wine offered to *download* Mono. A small CIL module
  (`/usr/share/selinux/packages/lucent/lucent_composefs_execmod.cil`, loaded
  at build time) allows exactly that; the program's own domain is still
  checked. Containers don't use composefs, so only a real install shows it.
- **Proven end to end** on the installed ISO by the
  [acceptance test](#acceptance-test-x86_64).

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
  with the new system's tools, verifies it and labels it for SELinux with the
  new system's policy (if that is ever refused,
  `lucent-flatpak-relabel.service` does it once at first boot). The
  installer stays interactive.
- If anything fails, the install still completes and
  `lucent-flatpak-setup.service` downloads the apps after first boot.
- CI's `iso` workflow installs the ISO unattended in QEMU/KVM **with no
  network** and checks the apps on the installed disk. Measured (amd64,
  Nov 2026): all 10 apps and their runtimes present and labelled
  (`var_lib_t`), unpacking took 77 s of a 6.7 min install.
- Size: the ISO is **6.7 GB** (amd64; arm64 6.5 GB): the bundle is
  2.0–2.1 GB for 8.3–8.6 GB installed (zstd -19, files of two runtime
  versions side by side), and the system image on the ISO is recompressed
  from gzip to zstd -19 (4.6 → 3.4 GB), down from 8.3/8.45 GB
  ([docs/distribution.md](docs/distribution.md#making-the-iso-smaller)).
  The image and its updates don't grow at all.

Why not the alternatives: bootc-image-builder has no Flatpak support for
`anaconda-iso` (upstream only demos a `%post` that downloads from Flathub),
and Anaconda's own Flatpak source covers only the old rpm-ostree
(Silverblue) payload. Baking the apps into the image (`/usr` or a `/var`
seed) would add ~3 GB to the image and to every atomic update, while a
`/var` seed is applied only at install time anyway. On the ISO the cost is
paid once, by the download of the installer.

## Acceptance test (x86_64)

The owner's promise, checked on a real install: *install the OS, log in,
double-click a Windows installer, and the app just works with nothing else
to install.* `.github/workflows/acceptance.yml` (after every `iso` run, or
manual) on a GitHub `ubuntu-24.04` runner with KVM:

1. installs the amd64 ISO unattended in QEMU/KVM **with no network**
   (`tests/acceptance/test.ks`, on a throw-away copy of the ISO: user
   `anna`, autologin, the test runner; none of it is in a release);
2. boots the installed disk, still with no network, and from inside the
   Plasma session (`tests/acceptance/guest/acceptance.sh`) checks the ten
   offline apps in the launcher's favorites and menu, waits for
   `lucent-bridge-template.service`, copies Notepad++'s official installer
   into `~/Downloads` (the same file and SHA-256 as lucent-bridge's E2E) and
   opens it **the way a double-click in Dolphin does** (`kioclient exec`; the
   process must run in `lucent-bridge.desktop`'s unit), clicks through the
   installer's own pages with real key presses (QEMU input through KWin),
   waits for the launcher entry, starts Notepad++ **from the launcher** (Win,
   type, Enter) and finds its window (KWin scripting);
3. checks SELinux (enforcing, no AVC denial during the flow, the new Wine
   prefix labelled as policy expects), that `wine-systemd` is absent and
   lucent-bridge is the only `.exe` binfmt handler, and that Wine never
   asks to download anything;
4. records `systemd-analyze`, RAM 2 min after login, running services and
   disk usage, takes QMP screenshots, uploads them with `summary.md`/`.json`,
   and fails on any failed check (`tests/acceptance/summarize.py`).

Latest run: [42657634944](https://github.com/sidun-av/lucent-os/actions/runs/42657634944); screenshots and numbers in
[`docs/screenshots/real/x86-acceptance/`](docs/screenshots/real/x86-acceptance/README.md).
Its first runs found five real bugs, all fixed: the template service never
built the template (no `HOME`; lucent-bridge 0.1.1), launcher entries
appeared only after the program an installer starts was closed (0.1.1),
32-bit Windows programs couldn't run at all on composefs (SELinux, above),
the copied prefix kept the template's `var_lib_t` labels (0.1.2), and
`mcelog.service` failed on every boot on AMD CPUs (now skipped there).

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
| `build` | pytest → `podman build` natively on `ubuntu-24.04` (amd64) and `ubuntu-24.04-arm` (arm64) → smoke and signature-policy tests in the image → multi-arch `ghcr.io/sidun-av/lucent-os:testing` (and `:latest`, the same image), signed with Sigstore ([docs/updates.md](docs/updates.md)) |
| `iso` (manual, or from `release`) | offline app bundle → bootc-image-builder `anaconda-iso` from an image tag (default `:latest`; the installed system follows it) → system image recompressed with zstd, bundle added → optional unattended offline install test in QEMU/KVM; ISO uploaded as a workflow artifact, sizes in the run summary |
| `release` (tag `vX.Y.Z`, or manual dry run) | image `:X.Y.Z` + `:stable` → both ISOs → a **draft** GitHub release: each ISO in parts under 2 GiB, `SHA256SUMS` signed with Sigstore, join scripts ([docs/distribution.md](docs/distribution.md), [docs/install-usb.md](docs/install-usb.md)) |
| `release-tools` | the join scripts' tests on Windows (PowerShell 5.1 and 7, cmd), Linux and macOS |
| `acceptance` (after `iso`, or manual) | installs the amd64 ISO in QEMU/KVM with no network and checks the Windows double-click flow in the real Plasma session; screenshots, numbers ([above](#acceptance-test-x86_64)) |
| `vm` (after `build`, or manual) | **test-only** qcow2 (autologin user, SSH key) + fake Windows disk for `tools/vm/`; never a release artifact |

Locally, on any Linux with podman:

```sh
sudo podman build -t lucent-os .
```

Switch an existing Fedora Atomic / bootc system to Lucent (`:testing`
follows `main`; `:stable` exists from the first release on):

```sh
sudo bootc switch ghcr.io/sidun-av/lucent-os:testing
```

Updates then download in the background and start at the next restart;
channels, signatures and the commands behind Settings → Updates are in
[docs/updates.md](docs/updates.md).

## Repository layout

```
Containerfile                 image definition (FROM Kinoite 45)
build_files/build.sh          declutter, packages, lucent-bridge, DXVK, services
build_files/smoke-test.sh     CI: start a Windows program in the built image
build_files/design.sh         look: Papirus, rounded corners, boot splash, caches
design/                       generators for the theme assets (from docs/mockups)
system_files/                 copied to / : /etc/xdg defaults, look-and-feel,
                              colour schemes, systemd units, scripts, templates
migration-wizard/             "Move from Windows" wizard (lucent_migrate, po/, tests)
apps/lucent-store/            the Store (lucent_store, catalog.toml, po/, tests)
apps/lucent-settings/         Settings (lucent_settings: backends/, qml/, po/, tests)
tools/vm/                     boot the real image in QEMU (test-only VM images from CI)
tools/release/                release assets: ISO parts, SHA256SUMS, join scripts for users
iso/                          installer ISO: offline app bundle, kickstart, config, zstd
tests/acceptance/             CI: install the ISO, double-click a Windows installer
tests/release/, tests/iso/    tests of the release and ISO tools
.github/workflows/            CI
```

## Known gaps

- Not booted on real hardware yet; Plasma layout and shortcut defaults are
  verified only by review, not by a running session.
- On the online path (`bootc switch`, or a disk image without the app
  bundle) apps still arrive in the background after login, with no
  progress UI; the installer ISO doesn't have this gap.
- Firefox's own telemetry settings are Mozilla's defaults (no enterprise
  policy shipped yet for the Flatpak).
- Fedora's `wine-dxvk` has no 32-bit build on x86_64, so 32-bit Direct3D
  9–11 programs use wined3d there (64-bit ones, and all on aarch64, use DXVK).
- Plasma's Devices list can't show udisks' `HintName` ("Local Disk (C:)"):
  per Solid's source, its udisks2 backend reads it with `QObject::property("HintName")`,
  which is never set, and falls back to the file-system label.
- Bookmarks are exported as HTML for a one-click manual import, not injected
  into a Firefox profile.
- Settings: Wi-Fi scanning/joining and Bluetooth pairing are covered by
  tests against the tools' documented output only: the test VM has neither
  (the wired NIC, display, sound, theme, users and update paths were run in
  the VM). A custom accent is kept across light/dark switches by a user
  path unit; Plasma itself drops it on a global-theme change.
- Look: where the real desktop still differs from `docs/mockups/` (menus are
  Breeze, Dolphin has no "This PC" page yet, the lock screen's password view
  is stock, ...) is listed in `docs/screenshots/real/v2/README.md`.

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
щелчком через **Lucent Bridge** — ничего доустанавливать не нужно. Новые программы — в
**Магазине**: подборка «вместо Word, Photoshop, Acrobat…» и поиск по всему Flathub,
без рекомендаций, рекламы и слежки. При первом
входе помощник **«Переезд с Windows»** переносит документы, фото, закладки
браузеров и названия сетей Wi-Fi с диска Windows (диск открывается только для
чтения, без пароля для администратора компьютера).

**Статус: прототип.** Образ собирается в CI для x86_64 и ARM64, но на реальном
железе ещё не проверялся. Поддержка ARM-ноутбуков зависит от поддержки
конкретного устройства ядром Linux.

## License

Apache-2.0 — see [LICENSE](LICENSE).
