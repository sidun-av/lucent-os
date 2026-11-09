# Boot time and idle memory

How fast Lucent OS boots, how much memory an idle desktop takes, what was
changed to improve both, and what was looked at and deliberately left alone.
Every number comes from the x86_64 acceptance test in CI
([`.github/workflows/acceptance.yml`](../.github/workflows/acceptance.yml),
[`tests/acceptance/`](../tests/acceptance/)); every change was measured
before and after.

## How it is measured

The acceptance test installs the amd64 ISO unattended in QEMU/KVM with no
network, then:

1. **First boot** (right after the install): the whole Windows-app flow,
   plus boot and memory numbers 2 min after the automatic login. This boot
   also does one-time work (machine ID, `ldconfig`, a full man-db build), so
   its time is not what a user sees every day.
2. **Second boot** (an ordinary one, like every later day): the same numbers
   again, then how quickly the desktop answers: the launcher opened with the
   Win key (timed on the host's screen from the key press to the first
   visible change; once cold, then the median of three) and five apps
   started from it (Win key, name, Enter; timed until KWin adds their
   window): Dolphin, Settings, Store, Firefox (Flatpak, its very first start)
   and Notepad++ (a Windows program).
3. The **reboot** in between, by wall clock: from the reboot command to the
   next desktop session, split into the first boot's shutdown and firmware +
   GRUB (the part `systemd-analyze` can't see).

Two machines run in parallel: **standard** (4 vCPU, 8 GB) and **low-spec**
(2 vCPU, 4 GB). Both are VMs on GitHub runners with software rendering
(llvmpipe, no GPU), so absolute numbers are higher than on real hardware,
especially for `kwin_wayland` and `plasmashell`.

**Noise.** GitHub hands out runners with different host CPUs, and that
matters more than anything changed here: the same image measured twice on a
Xeon 6973P-C and on a Xeon 8370C took 9.1 s and 10.1 s to boot and 3.7 s
and 5.7 s to start Firefox. Times are therefore compared on the same CPU
model, and the changes are judged by what doesn't depend on CPU speed:
what sits on the boot's critical chain, memory per process, failed units,
SELinux denials, file sizes, and timeouts.

Memory is reported two ways: "RAM used" is `MemTotal - MemAvailable`, and
per process the **PSS** (proportional set size, from
`/proc/<pid>/smaps_rollup`): a shared page is split between the processes
that map it, so the column adds up to what each process really costs. RSS
counts every shared library in full for every process and overstates what
removing one would save (xwaylandvideobridge: 142 MiB RSS, 58 MiB PSS).

## Results

Before: the image as of 9 November 2026 (ISO runs 42653778609 and
42676756681), measured three times on each machine, on different host CPUs:
acceptance runs [42673799202](https://github.com/sidun-av/lucent-os/actions/runs/42673799202),
[42680019860](https://github.com/sidun-av/lucent-os/actions/runs/42680019860) and
[42689989142](https://github.com/sidun-av/lucent-os/actions/runs/42689989142).
After: image `7841365` with every change below except the deferred
third-party refresh (see "Housekeeping after the login"), and with a KDE
Connect change since reverted because it made no difference (see "Looked at
and left alone"): [acceptance run 42702946132](https://github.com/sidun-av/lucent-os/actions/runs/42702946132)
(ISO run 42692564706). Other work landed in the image in between too
(lucent-bridge 0.2, This PC, Settings), so totals include it; the text below
names the processes these changes removed.

### Standard machine (4 vCPU, 8 GB)

| | before, run 1 | before, run 2 | before, run 3 | **after** |
|---|---|---|---|---|
| host CPU | Xeon 6973P-C | Xeon Platinum 8370C | EPYC 9V45 | EPYC 9V74 |
| **first boot** (kernel + initrd + userspace) | 17.554 s (854ms + 2.495s + 14.204s) | 20.630 s (918ms + 2.567s + 17.144s) | 18.087 s (777ms + 2.531s + 14.779s) | 12.328 s (802ms + 2.562s + 8.963s) |
| first boot: desktop session up (s) | 13.60 | 16.49 | 14.86 | 14.66 |
| **ordinary boot** (kernel + initrd + userspace) | 9.086 s (874ms + 2.492s + 5.719s) | 10.086 s (885ms + 2.521s + 6.679s) | 10.273 s (823ms + 2.551s + 6.899s) | 9.235 s (814ms + 2.546s + 5.873s) |
| ordinary boot: desktop session up (s) | 9.62 | 11.53 | 10.88 | 11.51 |
| reboot command → desktop session (s) | 46.3 | 49.5 | 46.3 | 26.6 |
| … of which shutdown (s) | 31.9 | 31.8 | 31.7 | 11.4 |
| … of which firmware + GRUB (s) | 4.8 | 6.1 | 3.7 | 3.7 |
| **RAM used**, idle, ordinary boot (MiB) | 1606 | 1620 | 1600 | 1407 |
| PSS of all processes, idle, ordinary boot (MiB) | 1119.1 | 1128.5 | 1119.1 | 1037.5 |
| running services, system / user | 30 / 34 | 30 / 34 | 29 / 34 | 28 / 33 |
| **failed units** (both boots) | systemd-remount-fs.service / systemd-remount-fs.service | systemd-remount-fs.service / systemd-remount-fs.service | systemd-remount-fs.service / systemd-remount-fs.service | none / none |
| **SELinux denial records** at boot (first / ordinary) | 12 / 4 | 12 / 4 | 12 / 4 | 0 / 0 |
| launcher opens: first time / warm (ms) | 615 / 315 | 880 / 439 | 591 / 257 | 680 / 297 |
| Dolphin (ms) | 568 | 1082 | 544 | 795 |
| Settings (ms) | 926 | 1646 | 1035 | 1085 |
| Store (ms) | 1000 | 1814 | 1109 | 1175 |
| Firefox, first start (ms) | 3670 | 5698 | 2950 | 3491 |
| Notepad++ (ms) | 3211 | 5775 | 3238 | 3742 |

### Low-spec machine (2 vCPU, 4 GB)

| | before, run 1 | before, run 2 | before, run 3 | **after** |
|---|---|---|---|---|
| host CPU | Xeon Platinum 8370C | EPYC 9V74 | EPYC 9V74 | EPYC 7763 64-Core Processor |
| **first boot** (kernel + initrd + userspace) | 18.463 s (796ms + 2.461s + 15.206s) | 23.707 s (948ms + 2.626s + 20.132s) | 21.189 s (825ms + 2.557s + 17.806s) | 15.603 s (917ms + 2.658s + 12.027s) |
| first boot: desktop session up (s) | 14.90 | 19.38 | 16.69 | 18.35 |
| **ordinary boot** (kernel + initrd + userspace) | 9.663 s (772ms + 2.429s + 6.462s) | 12.776 s (928ms + 2.601s + 9.246s) | 11.013 s (784ms + 2.539s + 7.689s) | 10.890 s (894ms + 2.603s + 7.391s) |
| ordinary boot: desktop session up (s) | 11.17 | 14.48 | 11.74 | 13.62 |
| reboot command → desktop session (s) | 48.1 | 51.7 | 48.0 | 29.4 |
| … of which shutdown (s) | 31.5 | 31.9 | 31.8 | 11.3 |
| … of which firmware + GRUB (s) | 5.4 | 5.3 | 4.4 | 4.5 |
| **RAM used**, idle, ordinary boot (MiB) | 1543 | 1562 | 1562 | 1351 |
| PSS of all processes, idle, ordinary boot (MiB) | 1108.1 | 1117.1 | 1119.7 | 1022.1 |
| running services, system / user | 30 / 34 | 29 / 34 | 29 / 34 | 28 / 33 |
| **failed units** (both boots) | systemd-remount-fs.service / systemd-remount-fs.service | systemd-remount-fs.service / systemd-remount-fs.service | systemd-remount-fs.service / systemd-remount-fs.service | none / none |
| **SELinux denial records** at boot (first / ordinary) | 12 / 4 | 12 / 4 | 12 / 4 | 0 / 0 |
| launcher opens: first time / warm (ms) | 815 / 403 | 800 / 369 | 647 / 293 | 829 / 350 |
| Dolphin (ms) | 994 | 878 | 717 | 842 |
| Settings (ms) | 1572 | 1759 | 1744 | 1637 |
| Store (ms) | 1461 | 1664 | 1310 | 1611 |
| Firefox, first start (ms) | 4978 | 5005 | 4079 | 4289 |
| Notepad++ (ms) | 4041 | 5579 | 3764 | 5214 |

What the numbers say:

- **Zero failed units and zero SELinux denials at boot**, on both machines
  and both boots (were: `systemd-remount-fs.service` failed on every boot;
  12 denial records on the first boot, 4 on every later one). Both are gates
  of the acceptance test now.
- **Reboot 46-52 s → 27-29 s.** The first boot's shutdown went from 32 s to
  11 s (a Windows program was open; see below). Firmware + GRUB stayed
  within the runners' noise (3.7-6.1 s before, 3.7-4.5 s after): with a
  virtio disk, reading 100 MB less initramfs isn't visible in a VM.
- **First boot 17.5-23.7 s → 12.3-15.6 s** (`graphical.target`, the owner's
  baseline number): the full man-db build no longer holds it (−6 to −8 s of
  userspace). The desktop came up at about the same time as before (the
  login screen never waited for man-db).
- **Idle memory −190 to −200 MiB "RAM used"** (1600-1620 → 1407 MiB on
  standard, 1543-1562 → 1351 MiB on low-spec) and **−82 to −98 MiB PSS**.
  The processes that are gone: xwaylandvideobridge (56.7-58.0 MiB PSS),
  tuned (27.9-28.0) and tuned-ppd (24.5-24.6), replaced by
  power-profiles-daemon (below 6.1 MiB, no longer among the 25 largest).
  "RAM used" falls further than PSS because the bridge's shared graphics
  buffers (shmem/memfd, mapped by Xwayland too) count fully there.
- **Ordinary boot:** TuneD is off the critical chain (it held
  `graphical.target` for 1.2 s on standard, 1.8 s on low-spec); the time is
  within the runners' noise because the next item, `fedora-third-party-refresh`
  (0.8 s), took its place, and because the first 3-4 s of userspace are
  Fedora's `systemd-resolved`, `-oomd` and `-nsresourced` starting at the
  same time (up to 2.6 s on the slowest host). The third-party refresh now
  runs after the login too (last row of the changes below).
- **Responsiveness** is unchanged within noise: the desktop answers the Win
  key in 0.26-0.44 s warm (0.6-0.9 s the first time) and opens native apps
  in 0.5-1.8 s on both machines.

### Is the low-spec machine responsive?

Yes. On 2 vCPU and 4 GB, with software rendering: the launcher opens in
0.29-0.40 s (0.65-0.83 s the first time after login), Dolphin in 0.7-1.0 s,
Settings and the Store in 1.3-1.8 s, Firefox's very first start in 4.1-5.0 s
and Notepad++ (a Windows program, after reboot) in 3.8-5.6 s. Idle, the
desktop uses 1.35 GB of 3.9 GB; with Firefox open 1.7 GB stayed available
and zram swap held at most 1 MiB, so the machine never had to swap in any
measured workload. The first boot's Windows flow (install Notepad++ by
double-click, start it from the launcher) passes there too.

### The ordinary boot, after

```
graphical.target @5.819s
└─power-profiles-daemon.service @5.735s +83ms
  └─multi-user.target @5.729s
    └─fedora-third-party-refresh.service @4.873s +853ms   (now after the login)
      └─basic.target @4.820s
        └─ ... sysinit.target @4.694s
              └─systemd-resolved.service @2.042s +2.648s
```

The login screen's own path: `sddm` ← `systemd-user-sessions` ←
`remote-fs.target` ← `nfs-client.target` ← `gssproxy` (+0.1-0.17 s) ←
`network.target` ← NetworkManager (+0.46-0.53 s) ← `basic.target`; the
desktop session follows 2.6-3.0 s later (`plasmashell` +1.4 s, `kded6`
+1.5 s).

## What changed, and why

Every change is in the image ([`build_files/performance.sh`](../build_files/performance.sh)
and the files it names) and checked by the image's smoke test, so a base
image update can't undo it silently. The acceptance test now fails on any
failed unit or SELinux denial at boot.

### `systemd-remount-fs.service` no longer fails at every boot

**Cause.** Lucent's `/` is composefs: a read-only overlay built from the
image, while the real btrfs root is mounted at `/sysroot` in the initramfs,
from `root=` and `rootflags=subvol=root` on the kernel command line.
Anaconda nevertheless writes an `/etc/fstab` line for `/`
(`subvol=root,compress=zstd:1`; bootc's `bootc-fstab-edit.service` adds
`ro`), and `systemd-remount-fs` runs `mount -o remount /` with those
options. Through the new mount API overlayfs refuses any option change:
`mount: /: fsconfig() failed: overlay: No changes allowed in reconfigure`.
This is [bootc#971](https://github.com/bootc-dev/bootc/issues/971) and the
Fedora Atomic Desktops tracker's issue 72 (every Atomic Desktop on btrfs
since composefs in Fedora 42). bootc's own installs (`bootc install`,
bootc-image-builder disk images such as the aarch64 VM's) write no line for
`/`, which is what bootc's maintainers recommend.

**Fix**, in two parts:

- The installer keeps that line only as a comment
  ([`iso/lucent-apps.ks`](../iso/lucent-apps.ks) runs
  [`fstab-drop-root`](../system_files/usr/libexec/lucent/fstab-drop-root)
  on the new system), so new installs look like bootc's.
- Systems installed earlier: `systemd-remount-fs` gets an `ExecCondition`
  ([`remount-fs-needed`](../system_files/usr/libexec/lucent/remount-fs-needed))
  that skips it exactly when `/` is an overlay and its fstab line is all
  there is to remount (no `/usr` or API file system lines, whose options it
  must still apply). Read-only: nothing is edited at boot.

**Measured:** no failed unit on either boot of either machine (was one on
every boot); on the new install `/etc/fstab` carries the line as a comment
and `systemd-remount-fs` finishes normally.

Nothing changes at runtime: those options never applied on composefs. One
consequence predates Lucent: Fedora's intended `compress=zstd:1` for the
root file system has not been in effect since composefs either. Turning it
on means putting it into `rootflags=` at install time (btrfs installs only);
that is a disk-space decision, not a boot one, and is left for later.

### No SELinux denials at boot: power-profiles-daemon instead of TuneD

**Cause.** The SELinux denials at boot (`mac_admin` for `chcon`, scontext
`tuned_t`, each with a `SELINUX_ERR` for `invalid_bootcinstall_testlabel_t`)
came from TuneD's bootloader plugin. On a bootc system TuneD 2.28 adds a
bootloader unit to every profile and, whenever a profile is applied, runs
`rpm-ostree status` and `bootc loader-entries set-options-for-source --source
tuned`, even when the profile sets no kernel arguments ("No changes needed
for source 'tuned'"). That happened three times on the first boot and once
on every later one: rpm-ostreed was started for it, `/boot` was remounted
read-write, and each `bootc` run tested whether it may write an invalid
SELinux label, which `tuned_t` may not: two denial records per run.

TuneD was also on the critical chain of every ordinary boot:
`graphical.target` waited for `tuned.service` (+0.96 s on the 4 vCPU
machine, +1.53 s on the 2 vCPU one) and `tuned-ppd.service` (+0.21 s,
+0.24 s), which orders itself before `multi-user.target`. And it is two
resident Python processes: 28 + 24.5 MiB PSS.

**Fix.** `tuned` and `tuned-ppd` are replaced by `power-profiles-daemon`
(Fedora 45 ships both; Fedora's KDE edition used power-profiles-daemon until
Fedora 40). Both serve the same D-Bus API,
`org.freedesktop.UPower.PowerProfiles`, that Plasma's battery applet and
PowerDevil use: Power Save / Balanced / Performance, switched on battery.
What TuneD's desktop profiles set beyond that is either the kernel's
default on Fedora already (schedutil, SATA link power management) or done by
power-profiles-daemon as well (energy-performance preference, ACPI platform
profile, AMD panel power savings). Lucent used no kernel arguments from a
TuneD profile; on an image-based system they belong in
`/usr/lib/bootc/kargs.d/` anyway.

**Measured:** 0 SELinux denial records on both boots of both machines (were
12 on the first boot and 4 on every later one); the power-profile API
answers (`ActiveProfile` "balanced", served by power-profiles-daemon, an
acceptance check now); tuned (28 MiB) and tuned-ppd (24.5 MiB) are gone and
power-profiles-daemon is below 6.1 MiB PSS; `graphical.target` no longer
waits for a power daemon's startup (power-profiles-daemon: +83 ms).

Alternatives considered: allowing `mac_admin` to `tuned_t` (weakens the
policy for a probe whose answer TuneD doesn't need), a `dontaudit` rule
(hides the AVCs, but the kernel logs `SELINUX_ERR` regardless), and keeping
TuneD with its bootloader plugin disabled (removing `/etc/grub.d/00_tuned`
disables the plugin: no denials, no `/boot` remounts, but both Python
daemons and the second on the boot chain stay).

### Xwayland Video Bridge no longer runs in every session

`xwaylandvideobridge` was the third-largest process of an idle desktop:
58 MiB PSS, after plasmashell and KWin, from login to logout. It lets
X11-only apps (Webex and the like) screen-share Wayland windows. KDE has
archived it and recommends distributions stop shipping it; Firefox, OBS and
current Chromium-based apps share the screen through the desktop portal
without it. Its autostart entry is hidden; the package stays, and copying
`/etc/xdg/autostart/org.kde.xwaylandvideobridge.desktop` to
`~/.config/autostart/` without the `Hidden=true` line turns it back on.

**Measured:** 56.7-58.0 MiB PSS (142-143 MiB RSS) less from login to logout,
on both machines. Xwayland itself still runs (22-23 MiB) for the session's
other X11 clients, such as the proxy that shows legacy (X11) tray icons,
which Windows programs use.

### Housekeeping after the login, not during the boot

Fedora's Atomic Desktops rebuild two caches in `multi-user.target` at every
boot: `fedora-atomic-desktop-mandb-update` (`mandb -q`; on the first boot a
full build that held `graphical.target` for 6.9-7.0 s) and
`fedora-atomic-desktop-appstream-cache-refresh` (`appstreamcli refresh
--force`, about 1 s every boot). Both now run from
[`lucent-after-boot.timer`](../system_files/usr/lib/systemd/system/lucent-after-boot.timer),
5 minutes after boot, with their own idle priorities; a preset keeps it so
after `systemctl preset-all`. Measured: the first boot's `graphical.target`
6-8 s earlier.

With TuneD gone, `fedora-third-party-refresh.service` (0.8 s of Python at
every boot, keeping Fedora's optional third-party repositories in step with
the user's choice) became the last thing `graphical.target` waited for, so
the same timer runs it after the login. That last step is in the image after
`7841365` and not measured yet: the next acceptance run shows it as the ordinary boot's critical chain.

### A smaller initramfs: 233 MB → 131 MB

The image's initramfs is generic (it must boot any machine), so it carried
every GPU driver with all its firmware; NVIDIA's GSP firmware for `nouveau`
alone is 105 MB of it. GRUB reads the initramfs from `/boot` at every boot,
dracut unpacks it into RAM at every shutdown (`dracut-shutdown.service`),
and every kernel update downloads it. Measured on Kinoite 45 with the same
`dracut` call as `build_files/design.sh`: 232.6 MB as shipped, 131.5 MB
without nouveau, 87.3 MB without any GPU driver. Lucent leaves out nouveau
only
([`90-lucent-no-nouveau.conf`](../system_files/usr/lib/dracut/dracut.conf.d/90-lucent-no-nouveau.conf)):
AMD and Intel GPUs, most machines, keep early KMS for the boot splash. On
NVIDIA machines nouveau loads from the installed system right after the
initramfs; until it does, the splash (and a disk-encryption prompt) is drawn
on the firmware's framebuffer.

**Measured:** `/boot` 252 MB → 151 MB used on the installed system; the
kernel frees 238 MB → 135 MB of initramfs memory at every boot ("Freeing
initrd memory"). The time GRUB needs to read it isn't visible in these VMs
(virtio disk; firmware + GRUB stayed at 3.7-6.1 s, the runners' spread); on
real disks and slow firmware reading 100 MB less is the point.

### Shutdown doesn't wait 30 s for a Windows program

The reboot in the acceptance test took 46-50 s, 32 of them shutting the
first boot down. The shutdown journal showed why: Notepad++, left open,
runs in Wine, and Wine's `winedevice.exe` ignores SIGTERM. After the stop
timeout (15 s) Fedora's `service.d/10-timeout-abort.conf` sent SIGABRT for
a core dump and waited another 15 s before SIGKILL, and the whole user
session waited for it. So any Windows program open at shutdown made it 30 s
slower.
[`50-lucent-stop-kill.conf`](../system_files/usr/lib/systemd/user/service.d/50-lucent-stop-kill.conf)
kills a user unit that doesn't stop in time instead (Lucent ships no crash
reporter, so those core dumps helped nobody), and apps get 10 s instead of
15 s after SIGTERM, which keeps one stuck app below the system's 15 s for
the whole session.

**Measured:** shutdown 31.5-31.9 s → 11.3-11.4 s on both machines (the
journal: "State 'stop-sigterm' timed out. Killing." after 10 s, the session
stopped 0.2 s later, no core dump); the whole reboot 46-52 s → 27-29 s.
lucent-bridge could avoid even the 10 s by ending its prefix with
`wineserver -k` when it receives SIGTERM.

## Looked at and left alone

| Candidate | Finding | Decision |
| --- | --- | --- |
| KDE Connect's daemon | 25-26.5 MiB PSS from login to logout, and it announces the computer on the local network. Tried (measured, then reverted): hiding its autostart entry and starting it only once `~/.config/kdeconnect/trusted_devices` exists. The daemon still ran: Plasma's system tray loads KDE Connect's tray applet, whose D-Bus interface starts the daemon (`DaemonDbusInterface::activatedService()` calls `startService`). | Reverted, it didn't pay. What would: not loading KDE Connect's tray applet until a phone is paired (the panel's tray configuration, the shell's call). |
| Baloo (file search) | Already names only (`/etc/xdg/baloofilerc`: `only basic indexing=true`, no hidden folders); `baloo_file` 6.7 MiB PSS, idle. | Keep: it is the launcher's file search. Content indexing stays off (a freshly migrated Windows library would keep a core and the disk busy for hours). |
| Discover's update notifier | 26 MiB PSS. Lucent Store checks for updates only while it is open (`apps/lucent-store/lucent_store/backend.py`) and has no background notifier, so `DiscoverNotifier` is the only thing that tells a user about app updates. (Its system-update check fails on Lucent's `ostree-unverified-registry:` origin; system updates are Settings' job.) | Keep until the Store has a notifier of its own; then it can go. |
| PackageKit | Not in Fedora Kinoite 45. | Nothing to do. |
| abrt | Not in Fedora Kinoite 45 (`build.sh`'s removal list is a safeguard). | Nothing to do. |
| geoclue | `geoclue.service` is D-Bus activated and not running when idle; the agent that authorises location requests (Night Light's "sunset at my location") is below 6.7 MiB PSS. | Keep. |
| ModemManager | 6.7 MiB PSS, not on the boot's critical chain. Starting it from udev only when a modem appears would save that, but modems show up as WWAN, `cdc-wdm`, plain USB serial and USB network devices; a rule that misses one leaves a laptop without mobile broadband. | Keep as it is: the saving doesn't justify the risk. |
| `nfs-client.target` and gssproxy | `nfs-client.target` (enabled by Fedora) puts gssproxy (+0.17 s) on the path to the login screen: `sddm` ← `systemd-user-sessions` ← `remote-fs.target` ← `nfs-client.target` ← `gssproxy` ← `network.target`. gssproxy is below 6.7 MiB PSS. | Left for now: the login screen waits for NetworkManager through `network.target` anyway, so the gain is 0.17 s, and NFS with Kerberos needs it. A candidate. |
| KUnifiedPush distributor, GTK global-menu proxy | Each below 6.7 MiB PSS (not among the 25 largest). The global-menu proxy stays idle without a global-menu widget. | Keep: too small to be worth departing from Plasma. |
| firewalld | 36 MiB PSS, the largest system daemon (Python). A static nftables ruleset would save that. | Keep: it is the firewall NetworkManager's zones and the rest of the OS expect. A candidate if the owner wants it. |
| KAccess | 19 MiB PSS. | Keep: sticky keys, slow keys and the visual bell depend on it. |
| zram and swappiness | Fedora's zram: lzo-rle, min(RAM, 8 GB), `vm.swappiness=60`, `page-cluster=3`. Even on the 4 GB machine with Firefox open, 1.7 GB stayed available and zram held 0-1 MiB. | Fedora's defaults stay: with no swapping in any measured workload, a different swappiness or compressor can't show a benefit here. |
| Kernel command line | Already `rhgb quiet` (`/usr/lib/bootc/kargs.d/10-lucent-splash.toml`); `console=ttyS0` is only on the test install. | Nothing to gain. |
| TuneD profile | tuned-ppd set `balanced` (TuneD itself recommends `virtual-guest` in a VM). | Moot: TuneD is gone. |
| `systemd-resolved` before `sysinit.target` | 1.8 s on the second boot's chain while dozens of units start at once (contention, not work). | Fedora's; left alone. |
| `lucent-drive-letters.service` | 0.4-0.5 s of Python at every boot, ordered before the login screen, which in these runs waited for NetworkManager instead, so it cost nothing visible. | Belongs to the This PC/migration code; starting it from udev only when NTFS partitions exist would make it free where it isn't. |
| `fedora-third-party-refresh.service` | 0.8 s at every boot, not on the critical chain. | Left: it keeps Fedora's third-party repository state. |

## Reproducing

Run the `acceptance` workflow (manually with an `iso` run ID, or after an
`iso` run). Each machine uploads an artifact (`acceptance-x86_64`,
`acceptance-x86_64-low-spec`) with `summary.md`, the screenshots and
`results/logs/` (first boot) and `results/logs/boot2/` (second boot):
`top-pss.tsv`, `systemd-analyze-*` (blame, critical chains, plot),
`avc-boot.txt`, `journal-boot1-shutdown.txt`, `diag/` (units, presets,
tuned, zram, initramfs). The memory table comes from
[`tests/acceptance/guest/perf.py`](../tests/acceptance/guest/perf.py).
