# Real Lucent OS: Files opens on "This PC"

Real captures (QMP `screendump`, 2560x1440 at 1x, software rendering) of the
aarch64 test VM (`tools/vm/`, QEMU + HVF on an Apple M4), booted fresh from the
`vm` workflow's image of run
[42668937173](https://github.com/sidun-av/lucent-os/actions/runs/42668937173)
(image `def066d`), with the fake Windows disk (`windows-disk.qcow2`) and a USB
stick image hot-plugged through `tools/vm/usb.sh` (FAT32, label `KINGSTON`).
Target: `docs/mockups/concepts-2026/pebble-drift/01-desktop.png` (light) and
`02-desktop-dark.png`. How and why: [`docs/this-pc.md`](../../../this-pc.md).

**How This PC got into that image:** the CI images with these commits were
not built yet when this was captured (the main builds were queued behind each
other), so `kio_thispc` was compiled in a Fedora 45 container in the VM from
this repository's `build_files/thispc/`, and it and the files from
`system_files/` (dolphinrc, design-defaults, the Eject action, the MIME type,
the ring icons, the translation) were put into the running system with
`bootc usr-overlay` (a writable `/usr` until the next reboot). The user's
sidebar and This PC's view were set up by running `design-defaults` as a new
user's login does. Files was opened with **Win+E** (keyboard through QMP), so
it runs in the graphical session as a user's would. The look of the window
itself (title bar, sidebar, toolbar) is whatever the other tracks had in that
image, not part of this work.

Separately, the real image build ran `build_files/thispc.sh` (CI build run
[42675510995](https://github.com/sidun-av/lucent-os/actions/runs/42675510995),
amd64): built against the image's KF6, unit tests passed with Fedora's ICU,
`kioclient ls thispc:/` listed `drive-home` in the build container. That run
failed later, in `papirus-indigo.sh` (another track). Compiling and testing
on Fedora 45 for both architectures: run
[42674363195](https://github.com/sidun-av/lucent-os/actions/runs/42674363195).

| File | What it shows |
| --- | --- |
| `00-before-files-opened-on-home.png` | Before (older image `9751df3`): Win+E opened Home; the status bar had no free-space part (hidden because it would say "0 B free") |
| `01-this-pc-light.png` | Win+E: **This PC** first in the sidebar and selected; Drives and devices: Home (the system drive, "18 GiB free / of 40 GiB" = `df`: 18G of 40G), KINGSTON ("1.8 GiB free / USB drive · 4.0 GiB", violet ring at 55 %), **Local Disk (C:)** ("4.0 GiB free / Read-only", lock emblem; opened read-only by the page itself); Folders with item counts; Recent files with folder and date |
| `02-this-pc-dark.png` | The same in Lucent Dark (rings and glyphs legible on the dark window) |
| `03-usb-plugged-in-light.png` | The stick plugged in while This PC is open: it appears on the page by itself (kded refresher) next to Plasma's own Disks & Devices popup ("1.8 GiB free of 4.0 GiB", the same number) |
| `04-eject-menu-light.png` | Right-click on the stick: **Eject** (Rename, Cut and Delete are off on this page) |
| `05-after-eject-light.png` | After Eject: the stick is gone from the page and the sidebar (`lsblk /dev/sda`: no such device) |
| `06-eject-notification-light.png` | "It is safe to remove the drive now." after Eject (an earlier run of the same session: the 32 GB stick, C:'s second line still "Read-only · 4.0 GiB" before it was shortened) |
| `07-this-pc-russian-light.png` | Files started with `LANGUAGE=ru`: Диски и устройства / Папки / Недавние файлы, «Свободно 18 ГиБ / из 40 ГиБ», «USB · 4,0 ГиБ», «Только чтение», plural forms (1 объект, 5 объектов). "This PC" stays English in the sidebar: the sidebar was made at this user's first (English) login, in that language |
| `08-windows-drive-opened-light.png` | Local Disk (C:) opened from This PC: its folders (`Users`, `Windows`), the drive selected in the sidebar (earlier build of the same session) |

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Win+E opens Files on This PC | PASS | `01`, title "This PC — Dolphin" |
| This PC is the first entry of the sidebar | PASS | `01` (new user); adding it once to an existing sidebar: `tests/test_design_defaults.py` |
| Free space of the home volume is right | PASS | 17.9 GiB free of 40.0 GiB on the page and for the status bar on This PC; `df -h /var/home/lucent`: 18G free of 40G. Dolphin's own path for `~/Documents` (Solid → composefs `/`): 0.0 GiB, reproduced, see `docs/this-pc.md` |
| Windows partition: "Local Disk (C:)", read-only | PASS | `01`, `08`; `findmnt`: `ro`; the name is `lucent-drive-letters`' (unchanged) |
| Windows partition opened by the page without a password | PASS | mounted on the first listing (`auth.no_user_interaction`, Lucent's polkit rule for wheel); not when Files runs from an SSH session (polkit: not local), as expected |
| USB stick appears when plugged in | PASS | `03`, no reload |
| Eject | PASS | `04`, `05`, `06`; first try failed (exit 2): Dolphin passes the mount point, not `thispc:/drive-sda`; fixed and tested |
| A drive not mounted yet opens | PASS, with a flaw | C: unmounted by hand, double-click: mounted and opened; that one folder showed This PC's grouped view (Dolphin doesn't reload view properties after a redirection). Opened while mounted it looks as usual (`08`) |
| Recent files | PASS | `01`: the five files of `~/.local/share/recently-used.xbel`, newest ten at most, with folder and "Today" / "Yesterday" / date |
| Light and dark | PASS | `01`, `02` |
| Russian | PASS | `07` |
| Speed | 0.08–0.09 s | `kioclient ls thispc:/` in the session, three runs, process start included |

## Found in the VM and fixed

1. Solid's view of the drives inside the long-lived worker went stale: C:
   was mounted, the page still said "not opened". The worker now reads
   `lsblk` on every listing (parser tested with this VM's output).
2. One grey line was cut off under 64 px icons ("21.3 GiB free of 4…"): two
   lines now, and sizes keep at most three digits ("18 GiB").
3. Groups: hair spaces meant to put Folders first are ignored by Fedora's
   ICU (the unit test failed on Fedora, passed on macOS); the page now shows
   Drives and devices first, the same in English and Russian.
4. The ring icons used KDE colour-scheme classes; hicolor isn't recoloured,
   so in dark mode the glyphs were dark on dark. Colours now sit between the
   light and dark tokens.
5. Eject got the mount point instead of the `thispc:` URL (above).
6. Russian detail lines were cut off: "Read-only" stands alone, "USB · %1".

Not verified here: a real BitLocker partition (not shown on the page by
design), an SD card, Windows with Fast Startup (read-only mount only), a
user outside `wheel` (the page then shows the size and polkit asks on open),
and the x86_64 image at runtime (compiled and unit-tested for both
architectures in CI).
