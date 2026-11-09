# x86_64 acceptance test: install, log in, double-click a Windows installer

Real screenshots (QMP `screendump`, 1920x1080, software rendering) from the
CI acceptance test [run 42707252994](https://github.com/sidun-av/lucent-os/actions/runs/42707252994)
(job "standard": 4 vCPU, 8 GB; the "low-spec" job, 2 vCPU and 4 GB, passed
too), which installed the amd64 ISO of `iso` run
[42692554347](https://github.com/sidun-av/lucent-os/actions/runs/42692554347)
unattended in QEMU/KVM on a GitHub `ubuntu-24.04` runner, **with no
network**, booted it (still no network) and did what the owner promises a
new user can do: double-click a Windows installer and use the program, with
nothing else to install. That image has **lucent-bridge 0.2.0** (launch
sheet, programs not elevated, the desktop's look in Windows programs,
bundled DXVK). How: [`.github/workflows/acceptance.yml`](../../../../.github/workflows/acceptance.yml),
[`tests/acceptance/`](../../../../tests/acceptance/). Result: **PASSED**.

The only test-only additions to the installed system (from the test
kickstart, never in a release): user `anna` with automatic login, the test
runner service, and (while the test waits) `kde-inhibit` keeping the screen
on.

| Screenshot | What it shows |
| --- | --- |
| `01-desktop-after-login.png` | The Lucent desktop right after the automatic login of the freshly installed system |
| `02-launcher-offline-apps.png` | The launcher (Win key): the ten apps installed from the ISO without a network |
| `03-launch-sheet.png` | **New in 0.2**: 1 s after `npp.8.9.9.Installer.x64.exe` was opened from `~/Downloads` the way a double-click does, lucent-bridge's "Preparing Windows program" sheet (`apps/lucent-bridge-sheet`): the installer's own icon, name, file and size, "x86-32 · direct execution" (the NSIS installer is a 32-bit program), progress. The Windows environment was ready from the template in about a second, so it already says "Starting Notepad++…" (the number now follows the bar, which was still easing to the end here: fixed after this run) |
| `03-installer-01-language.png` | The installer's own window, 5 s after the double-click, its dialogs in the desktop's UI font (Figtree) and Pebble Drift colours |
| `03-installer-02-welcome.png` | The installer's pages, clicked through with Enter (real key presses through KWin) |
| `03-installer-07-finish.png` | Its last page, "Run Notepad++" checked as it comes |
| `04-bridge-notification.png` | Lucent Bridge's "Notepad++ is installed" notification, while the Notepad++ that the installer started is still open |
| `04b-notepadpp-from-installer.png` | That Notepad++, started by the installer's last page: it still says "[Administrator]". On Windows the installer asks Explorer to start it, so it runs unelevated; Wine's `explorer.exe` is a child of the (elevated) installer and passes its token on. Started from the launcher (06) it isn't |
| `05-launcher-notepadpp-badge.png` | The launcher finds Notepad++ (typed "Notepad++"), with the Windows-program badge |
| `06-notepadpp-running.png` | Notepad++ started from that launcher entry, with text typed into it: **no "[Administrator]"** in its title (it was there until lucent-bridge 0.1.2), menus in Figtree on Pebble Drift's light surface |

## Checks

| | check | detail |
| --- | --- | --- |
| ✅ | Plasma session after autologin | Plasma session of anna running 17.07 s after kernel start (autologin, boot 1) |
| ✅ | 10 offline apps installed from the ISO | all 10 apps installed system-wide from the ISO, no network |
| ✅ | all 10 in the launcher's favorites | all 10 in the launcher's pinned favorites (first under All apps) |
| ✅ | all 10 in the launcher (application menu) | kbuildsycoca6 --menutest, the KService menu the launcher reads |
| ✅ | prefix template built by its service within ~5 min of boot | lucent-bridge-template.service succeeded: started 209 s, finished 235 s after kernel start |
| ✅ | Notepad++ installer in ~/Downloads, hash pinned | 7028968 bytes, SHA-256 as pinned in lucent-bridge's E2E, `user_home_t` |
| ✅ | .exe defaults to lucent-bridge | type application/vnd.microsoft.portable-executable; xdg-mime and gio: lucent-bridge.desktop |
| ✅ | double-click (KIO) runs lucent-bridge.desktop | `kioclient exec` → `/usr/bin/lucent-bridge run -- …/npp.8.9.9.Installer.x64.exe`, in `app-lucent\x2dbridge@….service` |
| ✅ | "Preparing Windows program" sheet after the double-click | 'Preparing Windows program' (class lucent-bridge, 720x547) 1 s after the double-click |
| ✅ | Wine never asks to download anything (Mono, Gecko) | no Wine Mono/Gecko download dialog |
| ✅ | installer GUI driven to the end | 7 Enter presses, 41 s |
| ✅ | Notepad++ launcher entry appears | `lucent-bridge-notepadplusplus-bdf24a17-notepadplusplus.desktop` 1 s after the installer closed |
| ✅ | entry valid (Exec, icon, StartupWMClass) | `Exec=lucent-bridge run ".../notepad++.exe"`; `StartupWMClass=notepad++.exe`; 256x256 PNG icon |
| ✅ | Notepad++ window after launching it from the launcher | window 'C:\Program Files\Notepad++\change.log - Notepad++' 5 s after Enter in the launcher |
| ✅ | Notepad++ not elevated: no "[Administrator]" in its title | caption 'C:\Program Files\Notepad++\change.log - Notepad++'; started through lucent-start.exe |
| ✅ | process runs in its launcher entry's unit | `app-lucent\x2dbridge\x2dnotepadplusplus\x2dbdf24a17\x2dnotepadplusplus@….service` |
| ✅ | Windows environment in the desktop's look | `"Window"="253 253 255"` (Pebble Drift `--surface-raised`), `"MS Shell Dlg"="Figtree"` (the desktop font), `LogPixels` 96 |
| ✅ | Direct3D through lucent-bridge's DXVK | `system32/d3d11.dll` is lucent-bridge's DXVK (3.1.1) |
| ✅ | SELinux enforcing | getenforce: Enforcing |
| ✅ | no AVC denials during the flow | none from the download to Notepad++ running (ausearch) |
| ✅ | wine-systemd not installed | package wine-systemd is not installed |
| ✅ | prefix SELinux labels | 2247 files, all `data_home_t` |
| ✅ | boot / second boot: no failed units, no SELinux denials | both boots |

The run also checks power profiles, networking, Bluetooth, printing,
updates and search, and times Files, Settings, Store, Firefox and Notepad++
from the launcher: all in the run's summary.

## Numbers (KVM, 4 vCPU, 8 GB, virtio disk; software rendering)

| | |
| --- | --- |
| `systemd-analyze` | Startup finished in 949ms (kernel) + 2.672s (initrd) + 10.977s (userspace) = 14.599s |
| second boot | 944ms (kernel) + 2.653s (initrd) + 7.161s (userspace) = 10.759s |
| RAM used, idle 2 min after login | 1415 MiB of 7921 MiB (PSS of all processes 1053 MiB) |
| running services, idle | 28 system, 33 user |
| Windows prefix template | ready 235 s after kernel start, 1.7G |
| double-click to the launch sheet | 1 s |
| double-click to installer window | 5 s |
| software | Lucent OS 0.1 (prototype, Fedora 45 base), kernel 7.2.15-300.fc45.x86_64, wine-11.20 (Staging), lucent-bridge 0.2.0 |

## Bugs this test found (all fixed)

1. **32-bit Windows programs could not run on the installed system.** On
   composefs `/usr`, Linux also checks `mprotect` against the backing file
   with the mounter's credentials (`kernel_t`), and relocating a 32-bit Wine
   DLL needs `execmod`: Notepad++'s installer never appeared and Wine offered
   to *download* Wine Mono. Fixed with a small SELinux module
   (`lucent_composefs_execmod.cil`).
2. **The prefix template was never built on a real boot**: the service has
   no `HOME`, and `lucent-bridge build-template` required one. Fixed in
   lucent-bridge 0.1.1.
3. **The installed program wasn't in the launcher while it was running**:
   entries came only after every process in the prefix had exited. Fixed in
   lucent-bridge 0.1.1.
4. **The new Wine prefix kept the template's SELinux labels**. Fixed in
   lucent-bridge 0.1.2 (`restorecon` after the copy).
5. **`mcelog.service` failed on every boot on AMD CPUs.** Now skipped there.
6. **Notepad++ said "[Administrator]"**: Wine gives every process the
   Administrators group enabled. lucent-bridge 0.2.0 starts installed
   programs with the filtered token, as Windows does for an administrator
   with UAC (the instance an installer starts itself still inherits its
   rights, see `04b`).
7. **The first 0.2.0 run**: the check expected Inter for Windows dialogs, but
   the desktop's font had become Figtree; lucent-bridge follows the desktop,
   so the check now does too.
