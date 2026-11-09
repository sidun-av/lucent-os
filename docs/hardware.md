# Hardware: what works out of the box

On Windows you often install drivers after Windows itself: from Windows
Update, from the laptop maker's website or from a CD that came with the
printer. On Lucent OS the drivers are **part of the system**. They are in
the Linux kernel and in the packages Lucent ships, they are on the
installation USB stick, and they are updated together with the rest of the
system. After installation there is nothing to download and no driver
installer to run, and that is also true with no internet connection.

This page says, by type of device, what works right after installation,
what does not work and why, and what you can do about it.

> **Status.** Lucent OS is a prototype. Everything below was checked by
> looking inside the published system image on GitHub Actions (x86_64 and
> aarch64). It lists which drivers, firmware files and helper programs are
> in the image. It has **not** been checked on real PCs and laptops yet.
> Inside a virtual machine Lucent only sees emulated devices (a virtual
> network card, virtual sound, a virtual graphics card), so a VM proves
> nothing about your Wi-Fi card or your webcam. "Works" below means "the
> driver and everything it needs are in the system". Testing on real
> machines will follow.

## What works out of the box

| Device | What is included | Notes |
| --- | --- | --- |
| **Wi-Fi** | Intel (Wireless-AC 7260 and newer, Wi-Fi 6/6E/7 AX200-AX411, BE200/BE201), Realtek (rtw88/rtw89: RTL8821CE, RTL8822CE, RTL8852AE/BE/CE and similar), MediaTek (MT7921/MT7922, also sold as AMD RZ608/RZ616, and MT7925), Qualcomm Atheros (ath9k, ath10k QCA6174/QCA9377, ath11k, ath12k), newer Broadcom (brcmfmac), and USB Wi-Fi sticks with these chips | The firmware and the Wi-Fi regulatory database (which channels are allowed in your country) are in the system. Older Broadcom cards are the exception: see below. |
| **Wired network (Ethernet)** | Onboard Realtek and Intel network ports, USB and USB-C network adapters (Realtek RTL8152/8153/8156, ASIX AX88179), the network port of USB-C and Thunderbolt docks, USB tethering from Android phones and iPhones | Plug in the cable and you are online. |
| **Mobile internet** | 4G/5G USB sticks and many built-in laptop modems (ModemManager), sticks that first pretend to be a CD drive (usb_modeswitch), internet through a phone over Bluetooth | Some built-in laptop modems need a vendor "FCC unlock" step first: see below. |
| **VPN** | OpenVPN, Cisco AnyConnect-compatible, GlobalProtect, Pulse/Ivanti and Fortinet SSL VPN (all through OpenConnect), L2TP/IPsec and IKEv2/IPsec (the VPN types built into Windows), Microsoft SSTP, WireGuard | Set up in the network settings. Company VPNs that need their own client program (for example a Zscaler or Cisco Secure Client with posture checks) depend on that vendor offering a Linux client. |
| **Bluetooth** | Intel, Realtek, MediaTek, Qualcomm and Broadcom adapters, built-in or USB; headphones, speakers, mice, keyboards, game controllers; sending files | Dongles that start in "keyboard and mouse only" mode (some Dell and Logitech) are switched to full Bluetooth automatically. |
| **Sound** | Ordinary desktop and laptop sound (HD Audio), the sound DSP of most Intel laptops since 2019 (Sound Open Firmware), AMD laptop audio (ACP), laptop smart amplifiers from Cirrus Logic, Texas Instruments and Realtek, sound over HDMI and DisplayPort, USB headsets and USB sound cards, Bluetooth audio | Headset jacks, speakers and HDMI outputs are switched automatically. |
| **USB** | USB sticks and drives (also exFAT and NTFS), keyboards, mice, hubs, USB-C and Thunderbolt/USB4 docks (screens, network, USB and charging through the dock) | A new Thunderbolt device asks once whether to trust it, as on Windows. DisplayLink docks are the exception: see below. |
| **Graphics** | Intel (HD Graphics, Iris Xe, Arc), AMD Radeon (also the graphics in Ryzen processors), NVIDIA GeForce through the open driver (nouveau for the desktop, NVK for Vulkan and games, with NVIDIA's own firmware for GeForce GTX 16 and RTX cards) | Several screens, high resolution, scaling and Vulkan games work. Laptops with two graphics chips can start a program on the faster one from its right-click menu. On NVIDIA, see the notes below. |
| **Video playback** | Hardware video decoding (VA-API) on Intel (Intel media driver), AMD and NVIDIA (open driver) | Smooth video with less battery use. Which formats a GPU decodes depends on the GPU; on AMD and NVIDIA, H.264 and H.265 are decoded by the processor instead: see below. |
| **Webcams** | USB webcams and most built-in laptop webcams (UVC), and the newer "MIPI" laptop cameras on Intel IPU6 (2021-2024 Intel laptops) through libcamera, with the Intel Visual Sensing Controller firmware | IPU6 cameras work with a simpler picture than on Windows: see below. |
| **Touchpad, touchscreen, pen** | Precision touchpads with gestures, touchscreens, pens (Wacom, Microsoft Pen Protocol / USI through the touchscreen), drawing tablets | |
| **Card readers** | SD card readers (Realtek PCIe and USB, the usual USB card readers) | |
| **Sensors** | Screen auto-rotation for 2-in-1 laptops and tablets, ambient light sensor (Intel ISH, AMD sensor hub) | |
| **Fingerprint readers** | Readers supported by libfprint (many Synaptics, some Goodix, Elan and Validity models) | Many readers are not supported: see below. |
| **Laptop keys and battery** | Volume, brightness, mute, airplane-mode and keyboard-backlight keys (Lenovo, Dell, HP, ASUS, Acer and others), battery level, power profiles (power saving, balanced, performance), Intel thermal management | Vendor utilities such as Lenovo Vantage, MyASUS or Armoury Crate do not exist on Linux; their basic settings (for example a battery charge limit) are available where the laptop exposes them. |
| **Printers** | Printers that work without a driver (AirPrint, IPP Everywhere, Mopria: almost every network or Wi-Fi printer since about 2015, and USB printers that support "IPP over USB"), HP (HPLIP), Brother lasers, Brother label printers, Samsung and Xerox lasers, many Canon and Epson inkjets (Gutenprint), and older printers through the Foomatic database | Most printers are found automatically on the network. |
| **Scanners** | Network and USB scanners that work without a driver (eSCL/AirScan, WSD), and many older USB scanners (SANE) | |
| **Game controllers** | Xbox controllers (USB cable, and Bluetooth on newer models), PlayStation DualShock 4 and DualSense, Nintendo Switch Pro, Steam controllers, 8BitDo; VR headsets for Steam | The Xbox Wireless Adapter (the USB dongle) is the exception: see below. |
| **Firmware updates** | Updates for docks, SSDs, Thunderbolt controllers and many laptops (through LVFS, as Windows Update does for firmware) | |
| **Processor** | Intel and AMD microcode (security and stability fixes for the processor) | |

## What does not work, and why

These do **not** work right after installation. Most of them are not
missing by accident: the maker does not allow the driver or the firmware to
be passed on, or there is no open-source driver at all. Lucent ships only
open-source software and firmware that may be redistributed.

- **Some older Broadcom Wi-Fi (about 2008-2016).** Some older HP, Dell and
  Lenovo laptops and 2013-2015 MacBooks have a Broadcom chip that Linux
  cannot use with open software alone:
  - BCM4360, BCM4352 and BCM43142 work only with Broadcom's closed `wl`
    driver, which Lucent does not include;
  - BCM4312, BCM4321, BCM4322, BCM43227, BCM43228 and BCM4331 have an open
    driver (`b43`), but it needs firmware that has to be cut out of
    Broadcom's own driver and may not be passed on.

  BCM4313, BCM43224 and BCM43225 work (open `brcmsmac` driver, firmware
  included), and so do the newer Broadcom chips. The oldest 802.11g chips
  (BCM4306, BCM4311, BCM4318) get a basic open firmware. **What you can
  do:** use the Ethernet port or a USB Wi-Fi stick with a Realtek or
  MediaTek chip, or replace the small M.2/mini-PCIe Wi-Fi card with an
  Intel one (an inexpensive part). The details, and the options for
  shipping `wl` later, are in [drivers.md](drivers.md).
- **Apple Macs.** The Wi-Fi and Bluetooth firmware of Intel Macs with a T2
  chip and of Apple silicon Macs comes only with macOS. Lucent does not
  target Macs.
- **NVIDIA: the closed NVIDIA driver is not included.** Lucent uses the
  open driver. For GeForce GTX 16 and RTX cards it uses NVIDIA's own
  firmware and works well on the desktop and with many games, but games run
  slower than with NVIDIA's closed driver, and CUDA, NVENC, DLSS and other
  NVIDIA-only features are not available. Older GeForce cards (GTX 900 and
  GTX 1000 series and older) stay at a low clock speed, because NVIDIA never
  released the firmware the open driver would need to run them faster: fine
  for the desktop and video, slow for games.
- **Some video formats on AMD and NVIDIA.** Fedora builds its graphics
  library (Mesa) with Mesa's patent-free set of video codecs, which leaves
  out hardware decoding of H.264 and H.265 (HEVC). On AMD and NVIDIA those
  formats are decoded by the processor: it works, but uses more power. AV1
  and VP9, used by YouTube and most streaming services, are decoded in
  hardware where the GPU supports them. Video apps from Flathub (Firefox,
  VLC, mpv and others) bring their own codecs and graphics libraries. This
  comes from Fedora 45's `mesa.spec` (no `video-codecs` option, so Mesa's
  default) and was not measured on real hardware.
- **DisplayLink docks and adapters.** Many cheap USB docks and some "USB
  to HDMI" adapters use DisplayLink chips, which need a closed driver. The
  screens on such a dock stay dark; its USB ports and often its network port
  still work. USB-C docks that use DisplayPort Alt Mode, and Thunderbolt
  docks, work.
- **Xbox Wireless Adapter (the USB dongle for Xbox controllers).** It needs
  firmware that only Microsoft may pass on. **What you can do:** connect
  the controller by cable or over Bluetooth (Xbox Series controllers and
  newer Xbox One controllers support Bluetooth).
- **Many fingerprint readers.** Fingerprint readers use their makers'
  closed protocols, and many (several Goodix, Elan, FPC and Synaptics
  "match-on-chip" models) have no open driver. If yours is not found, you
  sign in with your password as before.
- **IPU6 laptop cameras look plainer than on Windows; Lunar Lake (IPU7)
  cameras may not work yet.** The Windows driver uses Intel's closed image
  processing tuned for each camera. Lucent uses libcamera's open "software
  ISP": the camera works for video calls, with simpler colour and exposure
  handling, and some camera sensors are not supported yet. Support for
  Lunar Lake and newer (IPU7) is still being added to Linux.
- **Snapdragon (Windows on Arm) laptops.** The aarch64 version of Lucent
  needs Linux support for each laptop model, which still varies a lot from
  model to model. Parts such as the audio processor and the modem also need
  firmware files signed by the laptop maker. These cannot be shipped and
  have to be copied from that laptop's own Windows installation. Expect some
  devices not to work.
- **Very new hardware.** A chip that came out after this version of the
  system may not have its driver or firmware yet. Examples at the time of
  writing: some Intel Wi-Fi 7 chips released this year, the MediaTek MT7927
  and AMD graphics that have not been launched yet. Support arrives with
  system updates, and Lucent updates itself.
- **Built-in 5G modems that need an "FCC unlock".** Some laptop modems
  (for example certain Fibocom and Quectel models in Lenovo and Dell
  laptops) refuse to switch on until a vendor tool unlocks them. Fedora
  includes unlock scripts for several of them, but for legal reasons they
  are not turned on by default.
- **Epson's own inkjet drivers (ESC/P-R).** They are not in Fedora. Epson
  printers from the last ten years print without a driver, and many older
  ones work through Gutenprint.
- **Server and data-centre network cards and switch chips** (Mellanox
  Spectrum, Netronome, QLogic FastLinQ and similar). Their firmware (about
  120 MB) is left out because these are not parts of a PC.

## What you can do

- **Keep Lucent up to date.** New drivers and firmware arrive with system
  updates. Lucent installs them in the background and uses them after the
  next restart.
- **No Wi-Fi?** Connect a network cable or share your phone's connection
  over USB. Both work without any driver. Then update the system.
- **Something does not work?** Open *Konsole* from the launcher and type
  `lucent-devices`. It lists your devices and says which ones have no
  driver or a driver that is missing its firmware (it reads only this
  computer's own data and sends nothing anywhere). Then open an issue at
  <https://github.com/sidun-av/lucent-os/issues> with your computer's
  model and what `lucent-devices`, `lspci -nn` and `lsusb` print.
- **Before you buy a part,** Intel Wi-Fi cards, Realtek or ASIX USB
  network adapters, and printers that say "AirPrint" or "Mopria" are the
  safest choices.

## How this is checked (for developers)

- `build_files/hardware-packages.txt` lists every hardware package Lucent
  relies on. `build_files/hardware.sh` installs whatever the base image lacks
  and prints how much space each one adds to the build log. The image build
  fails if a listed package is missing.
- `tests/hardware/hw_audit.py` runs inside the published image (workflow
  `hardware-audit`, both architectures, after every image build). It
  1. takes every firmware file that the Wi-Fi, Ethernet, Bluetooth, sound,
     graphics, webcam, USB, input, card-reader and laptop drivers can ask
     for (`modinfo -F firmware`), checks that it is in `/usr/lib/firmware`,
     and looks up every missing file in the Fedora repositories;
  2. checks the files each device class needs (drivers, firmware, VA-API
     and Vulkan drivers, libcamera, printing and scanning);
  3. compares the image with Fedora's `hardware-support`, `printing`,
     `networkmanager-submodules` and `multimedia` package groups.
- The audit **fails** if a Wi-Fi, Ethernet, Bluetooth, sound or graphics
  firmware file is missing and a Fedora package ships it, or if it is
  missing and not explained in `tests/hardware/firmware-allowlist.txt`. It
  also fails if a device-class file or a listed package is missing. So a
  base-image update that drops firmware turns the check red instead of
  breaking someone's Wi-Fi.
