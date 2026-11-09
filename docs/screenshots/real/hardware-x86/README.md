# x86_64 hardware-live test: plug it in, it works, it shows up

Real screenshots (QMP `screendump`, 1920x1080, software rendering) from the
CI run [42717072346](https://github.com/sidun-av/lucent-os/actions/runs/42717072346) of
[`.github/workflows/hardware-live.yml`](../../../../.github/workflows/hardware-live.yml)
(test code: [`tests/hardware/`](../../../../tests/hardware/), `hwlive.py`).
It installed the published amd64 image
`ghcr.io/sidun-av/lucent-os:d1b454b0167f0d72978fd880c3ef38bfa7b2be5c-amd64`
(commit `d1b454b`, kernel `7.2.15-300.fc45`) as a qcow2 and booted it in QEMU/KVM on a GitHub `ubuntu-24.04`
runner **with Secure Boot on**, as a Windows PC ships: OVMF's Secure Boot
firmware with Microsoft's keys enrolled (`OVMF_CODE_4M.secboot.fd`,
`OVMF_VARS_4M.ms.fd`). Then it plugged in hardware the way a user does and
looked at both sides: the system (drivers, services, mounts, internet, over
SSH) and the screen (real clicks and key presses through QEMU's input
devices). Result: **PASSED, 50 of 50 checks**.

> **Emulated hardware is not real hardware.** Every device here is one of
> QEMU's models (or a Linux test driver for Wi-Fi and Bluetooth). This proves
> that Lucent's drivers, services and taskbar work for these models and that
> nothing breaks under Secure Boot. It does not prove that a particular
> laptop's Wi-Fi card or sound chip works; for that, see
> [docs/hardware.md](../../../hardware.md) (what the image contains).

What the test machine has that a release does not (test-only, never pushed;
[`tests/hardware/image/`](../../../../tests/hardware/image/)): user `lucent`
with autologin and password-less sudo, sshd, and two NICs NetworkManager
ignores (the runner's SSH link, and the uplink of the test's own Wi-Fi
access point), so the taskbar shows only the hardware under test. The
qcow2 has no Flatpak apps (they come from the installer ISO or are
downloaded on first boot, and this machine has no network at login), which
is why the pinned apps on the taskbar show "?" placeholders.

## Screenshots

| Screenshot | What it shows |
| --- | --- |
| `01-desktop-secure-boot.png` | The desktop after autologin, with Secure Boot on (`mokutil --sb-state`: SecureBoot enabled) |
| `10-volume-key-osd.png` | The Volume Up key (a keyboard media key, sent as a key press): the volume OSD, 50% -> 55% |
| `11-audio-devices.png` | The taskbar's sound popup: the Intel HD Audio output and the USB headphones, and the line-in input |
| `20-usb-fat32-plugged.png` | A FAT32 USB stick plugged in: Disks & Devices opens by itself and offers it ("Mount and Open") |
| `21-usb-fat32-this-pc.png` | Win+E: Files opens on This PC with the stick as "LUCENTFAT32, USB drive", next to the computer's own Windows disk, "Read-only" |
| `20-usb-ntfs-plugged.png` | The NTFS stick plugged in |
| `22-usb-ntfs-ejected.png` | After Eject: "It is safe to remove the drive now." |
| `30-bluetooth-adapter-in-tray.png` | A Bluetooth adapter appears: its icon in the taskbar |
| `32-bluetooth-switch-1.png`, `32-bluetooth-switch-2.png` | The Bluetooth popup's "Enable Bluetooth" switch, clicked off and on again |
| `33-bluetooth-paired-device.png` | The Bluetooth popup after pairing with a second (virtual) controller |
| `41-wifi-network-list.png` | The network popup lists the "Lucent Test" Wi-Fi network |
| `42b-wifi-password-field.png` | Connect clicked: the password field opens in the row |
| `42c-wifi-password-typed.png` | The password typed (key presses through QEMU's keyboard) |
| `43-wifi-connected-popup.png` | Enter: "Connection 'Lucent Test' activated", the popup shows it Connected |
| `44-wifi-connected-tray.png` | The Wi-Fi icon in the taskbar |
| `50-ethernet-e1000e-tray.png` | An Intel e1000e network card plugged in (PCIe hot-plug): connected by itself |
| `50-ethernet-igb-tray.png` | An Intel igb card on a LAN with a router and a printer: connected by itself ("Wired connection 3"; "Wired connection 2" is the USB adapter, still plugged in) |
| `60-print-dialog.png` | KWrite > Ctrl+P: the network printer, found by itself ("Test Printer - IPP Everywhere") |

## Checks

All 50 checks passed (and 17 informational records), from `results.tsv`
in the run's `hardware-live-x86_64` artifact (with the logs: journal, dmesg,
lsmod, lspci, pw-dump, the udev properties of each stick, the printer's
spool listing).

| Area | Check | Evidence (from the run) |
| --- | --- | --- |
| Secure Boot | on, enforced | `mokutil --sb-state`: SecureBoot enabled; kernel: "Secure boot enabled", "Kernel is locked down from EFI Secure Boot mode"; Microsoft's UEFI CA 2011 and Fedora's kernel key loaded |
| | the desktop comes up | `01`; Plasma session of `lucent` running |
| | nothing failed to load for lack of a signature | `journalctl -b \| grep -iE 'module verification failed\|Key was rejected\|PKCS#7 signature not signed\|Loading of unsigned module\|Lockdown: .*(unsigned\|module)\|required key not available\|firmware: failed to load\|Direct firmware load .* failed\|bad shim signature\|Invalid signature'`: no matches, at login (78 modules) and at the end (103 modules, after `mac80211_hwsim`, `hci_vhci`, `e1000e`, `igb`, `cdc_ether` were loaded; `mac80211_hwsim` and `hci_vhci` are signed with the Fedora kernel signing key) |
| Sound | outputs and input | PipeWire: "Built-in Audio Analog Stereo" (HDA, `snd_hda_intel`), "QEMU USB Audio Analog Stereo"; source "Built-in Audio Analog Stereo" (`11`) |
| | sound really comes out | 2 s of 1 kHz to each output: the runner's `hda.wav` and `usb-audio.wav` each got 2.1 s loud, 95 % of the energy at 1 kHz |
| | volume key | Volume Up twice: 0.50 -> 0.60, OSD (`10`) |
| USB sticks | FAT32, exFAT, NTFS | each: shows up (`20`), This PC lists it by its label as a USB drive (`21`), `hello.txt` reads back, a new file and 4 MB are written (mounted `rw`; NTFS through ntfs-3g), Eject: "It is safe to remove the drive now" (`22`), device gone; the runner then finds the new file on each ejected image and `fsck.vfat -n` / `fsck.exfat -n` / `ntfsfix -n` report it clean |
| | not caught by the Windows read-only rule | no `UDISKS_MOUNT_OPTIONS_DEFAULTS=ro` on any stick; a USB NTFS disk that reports `ID_BUS=ata` (SATA enclosure, simulated) is writable under the image's rule |
| Internal Windows disk | read-only | NTFS "Windows" on PCIe, mounted by the user's session without a password: `ro`, writing fails with "Read-only file system" (`21`: "Read-only") |
| Bluetooth | adapter | `hci_vhci` + `btvirt -l2`: two controllers, `bluetooth.service` active, icon in the taskbar (`30`) |
| | the taskbar switch | clicked off and on: `bluetoothctl show`: Powered: no, then Powered: yes (`32`) |
| | pairing | first controller pairs with the second: Paired: yes, Bonded: yes (`bluetoothctl`, Just Works); listed in the popup (`33`) |
| Wi-Fi | found | NetworkManager: "Lucent Test", WPA2, signal 100, on `wlan0` (driver `mac80211_hwsim`) (`41`) |
| | joined from the taskbar | Connect, password, Enter (`42b`, `42c`): connected, 192.168.77.83/24 (`43`, `44`); the password is stored by NetworkManager for the system, no wallet prompt |
| | internet | NetworkManager connectivity "full"; `curl --interface wlan0 https://fedoraproject.org/`: 200 |
| Ethernet | e1000e (PCIe hot-plug) | connected by itself, 10.0.2.15/24, `curl` 200 over it (`50-ethernet-e1000e-tray`) |
| | igb (PCIe hot-plug, LAN with router and printer) | connected by itself, 192.168.100.65/24, `curl` 200 over it (`50-ethernet-igb-tray`) |
| | USB network adapter | see "Not shown, and why": as plugged in, link-local only (emulator IDs); as a dock NIC: connected by itself, `curl` 200 |
| Printing | found by itself | `lpstat -e`: `Lucent_Test_Printer` (CUPS, DNS-SD, IPP Everywhere) |
| | prints | `lp`: the printer received a 186 KB PDF; KWrite > Ctrl+P > Enter (`60`): it received a 16 KB PDF |
| System | no failed units, no SELinux denials | `systemctl --failed`: 0 units; `ausearch -m AVC,USER_AVC --start boot`: no matches |

## How each device is emulated

| Device | Emulation | How "it works" is checked |
| --- | --- | --- |
| Sound | QEMU `ich9-intel-hda` + `hda-duplex` (snd_hda_intel) and `usb-audio` (snd-usb-audio), each into a WAV file on the runner (`-audiodev wav`) | PipeWire lists both outputs and an input; a 1 kHz tone played to each output (`pw-play`) arrives in that output's WAV on the runner: loud for 2 s, >90 % of its energy at 1 kHz |
| USB sticks | 512 MB images made on the runner (MBR, FAT32 / exFAT / NTFS, with a file on each), hot-plugged as `usb-storage` | appears, This PC lists it by its label, the file reads back, a new file is written, Eject (`thispc-eject`, what This PC's Eject runs) powers it off; the runner then mounts the ejected image: the new file is there and fsck finds it clean |
| Internal Windows disk | an NTFS disk with `Windows\System32` (virtio on PCIe) | mounted by the user's session: read-only, writing fails |
| Wi-Fi | `mac80211_hwsim` (two radios) from `kernel-modules-internal` for the exact kernel, installed only in the test VM into a transient `/usr` overlay; the second radio runs a WPA2-PSK access point (hostapd, DHCP and NAT) in its own network namespace | joined from the taskbar by clicking and typing the password; `curl` over the Wi-Fi interface |
| Bluetooth | `hci_vhci` (in the image) + BlueZ's `btvirt -l2` (two virtual controllers; built from the bluez release tarball, not in Fedora) | the adapter appears, the taskbar switch powers it off and on, the first controller pairs with the second (`bluetoothctl`, "Just Works") |
| Ethernet | PCIe hot-plug of `e1000e` and `igb`, USB hot-plug of `usb-net` | NetworkManager connects by itself; `curl` over that interface |
| Printer | CUPS's `ippeveprinter` on the runner, announced over DNS-SD on the igb card's LAN | CUPS lists it with no setup (`lpstat -e`); a page printed from the command line and one from KWrite reach the printer |

## Fixed on the way

- **NTFS USB hard disks were read-only** (`d8ed827`). The rule that keeps the
  computer's own Windows partitions read-only
  (`99-lucent-windows-readonly.rules`) skipped only `ID_BUS=usb`, but a USB
  hard disk or SSD in a SATA enclosure gets `ID_BUS=ata` (systemd runs
  `ata_id` through the bridge; `usb_id` keeps it). It now skips any device
  with a USB parent. USB sticks were never affected. QEMU's USB stick can't
  answer `ata_id`, so the test simulates that case with a runtime udev rule
  and checks the result under the image's rule (check
  `ntfs.usb-sata-enclosure-*`); `tests/system/test_windows_readonly_rule.py`
  evaluates the rule file.
- **Bluetooth's taskbar icon was near-invisible** (`53ac362`). Lucent's own
  line icons covered volume, network and Wi-Fi but not Bluetooth or Disks &
  Devices, so those fell through to Papirus's light-on-dark symbolic icons:
  a faint white rune on the light taskbar. They are now drawn in the same
  style.

## Not shown, and why

- **The USB network adapter as plugged in.** QEMU's only USB NIC
  (`usb-net`) carries the Linux USB gadget's IDs (0525:a4a2), which
  systemd's hwdb marks "link-local only" (a Raspberry Pi or phone in gadget
  mode), and the legacy `cdc_subset` driver also claims them. So it gets a
  169.254 address and no internet. Real USB and dock adapters have their own
  IDs (the image has r8152, ax88179_178a, cdc_ncm, cdc_ether). The test
  records that and then makes it look like one (runtime udev rule, test VM
  only; bound to `cdc_ether`): NetworkManager then connects it by itself and
  the internet works (check `ethernet.usb-net-as-dock-nic`).
- **Pairing from the taskbar.** The two virtual controllers pair with each
  other through `bluetoothctl` (the result is in the taskbar popup,
  `33-...`). Pairing a real headset by clicking it in the popup was not
  driven through the UI.
- **Sound from a real speaker, a real microphone.** The sound card's output
  is checked in QEMU's WAV file; the `wav` backend records no input, so the
  input device is only checked to exist.
