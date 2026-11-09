# x86_64 acceptance test: install, log in, double-click a Windows installer

Real screenshots (QMP `screendump`, 1920x1080, software rendering) from the
CI acceptance test [run 42657634944](https://github.com/sidun-av/lucent-os/actions/runs/42657634944), which installed the
amd64 ISO of `iso` run [42653778609](https://github.com/sidun-av/lucent-os/actions/runs/42653778609) unattended in
QEMU/KVM on a GitHub `ubuntu-24.04` runner, **with no network**, booted it
(still no network) and did what the owner promises a new user can do:
double-click a Windows installer and use the program, with nothing else to
install. How: [`.github/workflows/acceptance.yml`](../../../../.github/workflows/acceptance.yml),
[`tests/acceptance/`](../../../../tests/acceptance/). Result: **PASSED**.

The only test-only additions to the installed system (from the test
kickstart, never in a release): user `anna` with automatic login, the test
runner service, and (while the test waits) `kde-inhibit` keeping the screen
on.

| Screenshot | What it shows |
| --- | --- |
| `01-desktop-after-login.png` | The Lucent desktop right after the automatic login of the freshly installed system |
| `02-launcher-offline-apps.png` | The launcher (Win key): the ten apps installed from the ISO without a network, first under All apps |
| `03-installer-01-language.png` | `npp.8.9.9.Installer.x64.exe` opened from `~/Downloads` the way a double-click does: the installer's own window, 4 s later |
| `03-installer-02-welcome.png` | The installer's pages, clicked through with Enter (real key presses through KWin) |
| `03-installer-07-finish.png` | Its last page, "Run Notepad++" checked as it comes |
| `04-bridge-notification.png` | Lucent Bridge's "Notepad++ is installed" notification, while the Notepad++ that the installer started is still open |
| `05-launcher-notepadpp-badge.png` | The launcher finds Notepad++ (typed "Notepad++"), with the Windows-program badge |
| `06-notepadpp-running.png` | Notepad++ started from that launcher entry, with text typed into it |

## Checks

| | check | detail |
| --- | --- | --- |
| ✅ | Plasma session after autologin | Plasma session of anna running 14.64 s after kernel start (autologin) |
| ✅ | 10 offline apps installed from the ISO | all 10 apps installed system-wide from the ISO, no network: org.onlyoffice.desktopeditors org.kde.okular com.github.jeromerobert.pdfarranger org.gimp.GIMP org.kde.krita org.inkscape.Inkscape org.darktable.Darktable org.kde.kdenlive net.scribus.Scribus org.mozilla.firefox |
| ✅ | all 10 in the launcher's favorites | all 10 in the launcher's pinned favorites (first under All apps) |
| ✅ | all 10 in the launcher (application menu) | all 10 in the session's application menu (kbuildsycoca6 --menutest, the KService menu the launcher reads) |
| ✅ | prefix template built by its service within ~5 min of boot | lucent-bridge-template.service succeeded: started 210 s, finished 234 s after kernel start |
| ✅ | Notepad++ installer in ~/Downloads, hash pinned | /home/anna/Downloads/npp.8.9.9.Installer.x64.exe (7028968 bytes, SHA-256 as pinned in lucent-bridge's E2E, unconfined_u:object_r:user_home_t:s0) |
| ✅ | .exe defaults to lucent-bridge | type application/vnd.microsoft.portable-executable; default application: xdg-mime 'lucent-bridge.desktop', gio 'lucent-bridge.desktop' |
| ✅ | double-click (KIO) runs lucent-bridge.desktop | kioclient exec -> '/usr/bin/lucent-bridge run -- /home/anna/Downloads/npp.8.9.9.Installer.x64.exe ', in 0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-lucent\x2dbridge@db031840762c42b893a05b64d7708cdf.service  (KIO started lucent-bridge.desktop) |
| ✅ | Wine never asks to download anything (Mono, Gecko) | no Wine Mono/Gecko download dialog |
| ✅ | installer GUI driven to the end | Notepad++ installer GUI completed with its default buttons: 7 Enter presses, 39 s  |
| ✅ | Notepad++ launcher entry appears | lucent-bridge-notepadplusplus-bdf24a17-notepadplusplus.desktop 2 s after the installer closed |
| ✅ | entry valid (Exec, icon, StartupWMClass) | Exec=lucent-bridge run "/home/anna/.local/share/lucent-bridge/prefixes/notepadplusplus-bdf24a17/drive_c/Program Files/Notepad++/notepad++.exe"; StartupWMClass=notepad++.exe; icon PNG image data, 256 x 256 |
| ✅ | Notepad++ window after launching it from the launcher | window 'C:\Program Files\Notepad++\change.log - Notepad++ [Administrator]' (class notepad++.exe, pid 4388) 3 s after Enter in the launcher |
| ✅ | process runs in its launcher entry's unit | the process runs in its entry's unit: 0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-lucent\x2dbridge\x2dnotepadplusplus\x2dbdf24a17\x2dnotepadplusplus@21f3dccf318d46839f1fb42f718e3552.service  |
| ✅ | SELinux enforcing | getenforce: Enforcing |
| ✅ | no AVC denials during the flow | no AVC denials from the download to Notepad++ running (ausearch; 12 since boot) |
| ✅ | wine-systemd not installed | package wine-systemd is not installed |
| ℹ️ | session.inhibit | screen locking and power management inhibited for the test (kde-inhibit) |
| ℹ️ | installer.window | installer window 4 s after the double-click |
| ℹ️ | bridge.finished | lucent-bridge exited after the prefix emptied |
| ✅ | prefix.selinux-labels | /home/anna/.local/share/lucent-bridge/prefixes/notepadplusplus-bdf24a17: labels as policy expects (   2245 data_home_t ) |
| ℹ️ | binfmt.mz | the only MZ (.exe) binfmt handler: LucentBridge=/usr/libexec/lucent-bridge/lucent-bridge-binfmt  |
| ℹ️ | system.failed-units | systemd-remount-fs.service  |

## Numbers (KVM, 4 vCPU, 8 GB, virtio disk; software rendering)

| | |
| --- | --- |
| `systemd-analyze` | Startup finished in 797ms (kernel) + 2.540s (initrd) + 14.210s (userspace) = 17.548s |
| graphical.target | 14.209s in userspace. |
| RAM used, idle 2 min after login | 1650 MiB of 7921 MiB |
| running services, idle | 29 system, 34 user |
| installed disk usage (btrfs) | 13.0 GB, of which the ten apps (`/var/lib/flatpak`) 8.9 GB |
| Windows prefix template | ready 234 s after kernel start, 1.7G |
| double-click to installer window | 4 s |
| software | Lucent OS 0.1 (prototype, Fedora 45 base), kernel 7.2.15-300.fc45.x86_64, wine-11.20 (Staging), lucent-bridge 0.1.2 |

## Bugs this test found (all fixed)

1. **32-bit Windows programs could not run on the installed system.** On
   composefs `/usr`, Linux also checks `mprotect` against the backing file
   with the mounter's credentials (`kernel_t`), and relocating a 32-bit Wine
   DLL needs `execmod`: Notepad++'s installer never appeared and Wine offered
   to *download* Wine Mono. Fixed with a small SELinux module
   (`lucent_composefs_execmod.cil`). Containers don't use composefs, so the
   image's smoke test and lucent-bridge's E2E couldn't see it.
2. **The prefix template was never built on a real boot**: the service has
   no `HOME`, and `lucent-bridge build-template` required one. Fixed in
   lucent-bridge 0.1.1; the smoke test now runs it with a service's
   environment.
3. **The installed program wasn't in the launcher while it was running**:
   lucent-bridge added entries only after every process in the prefix had
   exited, and Notepad++'s installer starts Notepad++ on its last page.
   Fixed in lucent-bridge 0.1.1 (entries when the installer exits).
4. **The new Wine prefix kept the template's SELinux labels** (`var_lib_t`
   in `~/.local/share`): `cp -a` copies them as an xattr. Fixed in
   lucent-bridge 0.1.2 (`restorecon` after the copy).
5. **`mcelog.service` failed on every boot on AMD CPUs.** Now skipped there.

Not Lucent's, seen on every boot: `systemd-remount-fs.service` fails
("overlay: No changes allowed in reconfigure", bootc/composefs), and
something running as `tuned_t` calls `chcon` with an invalid test label
before the session starts (six attempts, each an AVC denial plus a
`SELINUX_ERR`). Neither touches the Windows flow, which had no denials.
